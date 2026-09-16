"""⊕ 合并算子 —— 把状态补丁 ΔΣt 应用到 Σt 上。

论文定义：Σ_{t+1} = Σ_t ⊕ ΔΣ_t，其中 ⊕ 是"带 null 删除语义的字典合并算子"。

三条规则:

    1. 值为 null            -> 删除该键
    2. 两侧都是 dict        -> 递归深合并（不是整体替换）
    3. 其他情况             -> 整体替换

规则 2 最容易写错，也最重要。以医疗导诊为例，患者说"我不发烧了"，
正确做法是只删掉 symptoms 里的 fever 子键，而不是用新 dict 覆盖整个 symptoms
——后者会连带丢掉咳嗽、胸痛等已采集信息。

    论文原文中的同构例子（仓库库存）:
        Σ:  {"inventory": {"shelf_42": "item_12", "shelf_7": "item_03"}}
        ΔΣ: {"inventory": {"shelf_42": null}}
        Σ': {"inventory": {"shelf_7": "item_03"}}

一个需要留意的语义细节：ΔΣ 中的空 dict `{}` 表示"无操作"，**不是清空**。
    因为无法区分"清空"与"未指定"。若要清空整个 dict，显式把每个键置为 null，
    或改用列表结构。论文未覆盖此边界，这里按最小意外原则实现。
"""

from __future__ import annotations

import copy
from typing import Any


class PatchError(ValueError):
    """补丁应用失败。"""


class _Deleted:
    """内部哨兵，标记"该键应被删除"。"""

    __slots__ = ()

    def __repr__(self) -> str:  # pragma: no cover - 仅调试用
        return "<DELETED>"


_DELETED = _Deleted()


def merge_state(base: Any, patch: Any) -> Any:
    """递归合并，返回新值。返回 _DELETED 表示调用方应删除该键。

    Args:
        base:  当前状态中的值。
        patch: 补丁中的值。

    Returns:
        合并后的新值，或 _DELETED 哨兵。

    Note:
        永不原地修改 base，始终返回新对象，保证 rollback 可用。
    """
    # 规则 1: null 表示删除
    if patch is None:
        return _DELETED

    # 规则 2: 两侧都是 dict -> 递归深合并
    if isinstance(base, dict) and isinstance(patch, dict):
        out: dict[str, Any] = dict(base)
        for key, sub_patch in patch.items():
            # 子键为 null -> 直接删除，无需递归
            if sub_patch is None:
                out.pop(key, None)
                continue

            if key in out:
                merged = merge_state(out[key], sub_patch)
                if merged is _DELETED:
                    out.pop(key, None)
                else:
                    out[key] = merged
            else:
                # 新键：深拷贝，避免与原状态共享可变引用
                out[key] = copy.deepcopy(sub_patch)
        return out

    # 规则 3: 其余情况整体替换
    return copy.deepcopy(patch)


def apply_patch(state: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    """把补丁应用到状态上，返回**新的**状态字典（不修改入参）。

    Args:
        state: 当前状态 Σt。
        patch: 补丁 ΔΣt。

    Returns:
        新状态 Σ_{t+1}。

    Raises:
        PatchError: 补丁不是对象，或应用后产生非法结构。

    Example:
        >>> s = {"a": {"x": 1, "y": 2}, "b": "old", "c": 1}
        >>> apply_patch(s, {"a": {"x": None}, "b": "new"})
        {'a': {'y': 2}, 'b': 'new', 'c': 1}
        >>> s   # 原状态未被修改
        {'a': {'x': 1, 'y': 2}, 'b': 'old', 'c': 1}
    """
    if not isinstance(patch, dict):
        raise PatchError(f"补丁必须是 dict，实际为 {type(patch).__name__}")

    result: dict[str, Any] = dict(state)

    for key, value in patch.items():
        if value is None:
            result.pop(key, None)
            continue

        if key in result:
            merged = merge_state(result[key], value)
            if merged is _DELETED:
                result.pop(key, None)
            else:
                result[key] = merged
        else:
            result[key] = copy.deepcopy(value)

    return result


def diff_summary(before: dict[str, Any], after: dict[str, Any]) -> list[str]:
    """生成人类可读的状态变更摘要，用于日志与审计。

    在医疗场景中，这份 diff 就是"为什么给出这个建议"的追溯依据。

    Example:
        >>> diff_summary({"a": 1}, {"a": 2, "b": 3})
        ['a: 1 -> 2', 'b: (新增) 3']
    """
    changes: list[str] = []
    for key in sorted(set(before) | set(after)):
        b, a = before.get(key, _DELETED), after.get(key, _DELETED)
        if b is _DELETED:
            changes.append(f"{key}: (新增) {_short(a)}")
        elif a is _DELETED:
            changes.append(f"{key}: (删除，原值 {_short(b)})")
        elif b != a:
            changes.append(f"{key}: {_short(b)} -> {_short(a)}")
    return changes


def _short(value: Any, limit: int = 60) -> str:
    text = repr(value)
    return text if len(text) <= limit else text[: limit - 3] + "..."
