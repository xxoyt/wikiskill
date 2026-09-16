"""StateSchema —— 字段规格与补丁校验。

论文里 schema 是"按领域编写一次，而非按任务"。在医疗导诊中，
所有问诊会话共用同一份 schema（见 examples/triage_agent.py 的 TRIAGE_SCHEMA）。

校验的职责比"防错"更大，它同时保证三件事:

    1. 正确性   类型不符、未知字段的补丁会被拒绝，不污染 Σ
    2. 有界性   max_keys / max_items 上限防止状态随轮次膨胀
                （这是 Σ 保持 O(1) 提示体积的前提，别省略）
    3. 可解释   返回结构化错误列表，直接喂回模型做 retry，而不是笼统报错
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable


@dataclass(frozen=True)
class FieldSpec:
    """单个状态字段的规格。

    Attributes:
        name:      字段名。
        type:      期望类型，或类型元组。None 表示不校验类型（不推荐）。
        desc:      给模型看的描述。写进 prompt，直接影响模型能否正确更新状态，
                   务必写清"什么情况下该填、什么情况下必须是 null"。
        required:  是否必须在初始状态中存在。
        max_keys:  若字段为 dict，限制其键数量上限。
        max_items: 若字段为 list，限制其长度上限。
        default:   初始状态中的默认值工厂（无参调用）。

    Example:
        >>> FieldSpec("symptoms", dict, "症状槽位，只填患者明确说过的", max_keys=8)
    """

    name: str
    type: type | tuple[type, ...] | None = None
    desc: str = ""
    required: bool = False
    max_keys: int | None = None
    max_items: int | None = None
    default: Any = None

    def default_value(self) -> Any:
        """生成初始值。可变默认值（dict/list）会被复制，避免共享引用。"""
        d = self.default
        if isinstance(d, (dict, list, set)):
            return type(d)(d) if isinstance(d, (dict, set)) else list(d)
        return d


class StateSchema:
    """领域状态 schema。

    Example:
        >>> schema = StateSchema([
        ...     FieldSpec("turn", int, "已进行的轮次", default=0),
        ...     FieldSpec("slots", dict, "已采集槽位", max_keys=10, default={}),
        ... ])
        >>> schema.initial()["turn"]
        0
        >>> schema.validate_patch({"turn": "三"})   # 类型错误
        ['字段 turn 类型错误：期望 int，实际 str']
    """

    def __init__(self, fields: Iterable[FieldSpec]) -> None:
        self.fields: dict[str, FieldSpec] = {f.name: f for f in fields}
        if not self.fields:
            raise ValueError("schema 至少需要定义一个字段")

    # ---------------------------------------------------------------- 初始状态

    def initial(self) -> dict[str, Any]:
        """生成符合 schema 的初始状态 Σ0。"""
        data: dict[str, Any] = {}
        for name, spec in self.fields.items():
            if spec.required or spec.default is not None:
                data[name] = spec.default_value()
        return data

    def initial_state(self):
        """生成初始 ExecutionState（延迟导入避免循环依赖）。"""
        from .state import ExecutionState

        return ExecutionState(self.initial())

    # ---------------------------------------------------------------- 校验

    def validate_patch(self, patch: Any) -> list[str]:
        """校验状态补丁 ΔΣt，返回错误描述列表（空列表表示通过）。

        校验规则:
            - 补丁必须是对象
            - 顶层键必须已在 schema 中声明（未知键拒绝，防止模型乱加字段）
            - 值类型必须匹配；None 恒为合法，表示删除该键
            - dict 的键数、list 的长度不得超过上限
        """
        errors: list[str] = []

        if not isinstance(patch, dict):
            return [f"state_patch 必须是 JSON 对象，实际为 {type(patch).__name__}"]

        for key, value in patch.items():
            spec = self.fields.get(key)
            if spec is None:
                known = ", ".join(sorted(self.fields))
                errors.append(f"未知字段 '{key}'，schema 只允许：{known}")
                continue

            if value is None:
                continue  # null = 删除，恒合法

            if spec.type is not None and not isinstance(value, spec.type):
                errors.append(
                    f"字段 '{key}' 类型错误：期望 {_type_name(spec.type)}，"
                    f"实际 {type(value).__name__}"
                )
                continue

            if isinstance(value, dict) and spec.max_keys is not None:
                if len(value) > spec.max_keys:
                    errors.append(
                        f"字段 '{key}' 键数超限：{len(value)} > {spec.max_keys}"
                    )

            if isinstance(value, list) and spec.max_items is not None:
                if len(value) > spec.max_items:
                    errors.append(
                        f"字段 '{key}' 长度超限：{len(value)} > {spec.max_items}"
                    )

        return errors

    def validate_state(self, data: dict[str, Any]) -> list[str]:
        """校验完整状态（用于加载持久化状态时的完整性检查）。"""
        if not isinstance(data, dict):
            return [f"状态必须是对象，实际为 {type(data).__name__}"]
        errors: list[str] = []
        for key, value in data.items():
            if key not in self.fields:
                errors.append(f"状态中存在 schema 未声明的字段 '{key}'")
                continue
            spec = self.fields[key]
            if value is None:
                continue
            if spec.type is not None and not isinstance(value, spec.type):
                errors.append(
                    f"字段 '{key}' 类型错误：期望 {_type_name(spec.type)}，"
                    f"实际 {type(value).__name__}"
                )
        for name, spec in self.fields.items():
            if spec.required and name not in data:
                errors.append(f"缺少必填字段 '{name}'")
        return errors

    # ---------------------------------------------------------------- 提示注入

    def describe(self) -> str:
        """渲染给模型看的 schema 说明（写进 P 的补充部分）。

        这一步很关键：模型能否正确更新状态，八成取决于这里的描述质量。
        """
        lines: list[str] = []
        for name, spec in self.fields.items():
            tname = _type_name(spec.type) if spec.type else "any"
            limit = ""
            if spec.max_keys is not None:
                limit += f"，最多 {spec.max_keys} 个键"
            if spec.max_items is not None:
                limit += f"，最多 {spec.max_items} 项"
            lines.append(f"- {name} ({tname}{limit}): {spec.desc}")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"StateSchema(fields={list(self.fields)})"


def _type_name(t: type | tuple[type, ...] | None) -> str:
    if t is None:
        return "any"
    if isinstance(t, tuple):
        return "|".join(x.__name__ for x in t)
    return t.__name__


# ---------------------------------------------------------------------------
# 便捷别名，便于以字典形式快速声明 schema
# ---------------------------------------------------------------------------


def schema_from_dict(
    spec: dict[str, tuple[type | tuple[type, ...] | None, str]],
    **kwargs: Any,
) -> StateSchema:
    """用紧凑字典声明 schema。

    Example:
        >>> schema_from_dict({
        ...     "turn": (int, "轮次"),
        ...     "slots": (dict, "已采集槽位"),
        ... })
    """
    fields = [FieldSpec(name=name, type=t, desc=desc) for name, (t, desc) in spec.items()]
    return StateSchema(fields, **kwargs)
