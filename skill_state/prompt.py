"""PromptAssembler —— 把 (P, Σt, Ot) 组装成给模型的消息，并解析其输出。

这是 SKILL.state 与普通 Agent 差异最大的一个文件。对比:

    普通 Agent     messages = [system] + 全部历史轮次 + 本轮输入
    SKILL.state    messages = [P + schema] + [Σt] + [Ot]        <-- 长度恒定

无论执行到第 1 步还是第 200 步，这个列表的长度不变，只有 Σt 的内容在变。
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from .schema import StateSchema
from .state import ExecutionState


@runtime_checkable
class LLMClient(Protocol):
    """LLM 调用协议。实现它即可接入任何模型（OpenAI / 本地 vLLM / Ollama）。"""

    def complete(self, messages: list[dict[str, str]]) -> str:
        """传入 messages，返回模型原始文本输出。"""
        ...


# ---------------------------------------------------------------------------
# 输出解析
# ---------------------------------------------------------------------------


class ParseError(ValueError):
    """模型输出无法解析为 (推理, 补丁, 动作)。"""


_JSON_BLOCK = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


def parse_llm_output(raw: str) -> tuple[str, dict[str, Any], Any]:
    """解析模型输出为 (推理轨迹 Rt, 状态补丁 ΔΣt, 动作 at)。

    约定输出格式（也是 PromptAssembler 要求模型遵守的格式）:

        <多步推理过程，任意文本>

        ```json
        {
          "state_patch": { ... },
          "action": { ... }
        }
        ```

    Args:
        raw: 模型原始输出。

    Returns:
        (reasoning, patch, action)。reasoning 仅用于日志/审计，
        **绝不会**被拼进下一步的 prompt（这是 SKILL.state 的核心约束）。

    Raises:
        ParseError: 未找到 JSON 块、JSON 非法、或缺少必需键。

    Example:
        >>> r, p, a = parse_llm_output('想清楚了\\n```json\\n{"state_patch":{"a":1},"action":{"type":"ask"}}\\n```')
        >>> p, a
        ({'a': 1}, {'type': 'ask'})
    """
    if not raw or not raw.strip():
        raise ParseError("模型输出为空")

    matches = _JSON_BLOCK.findall(raw)
    block: str | None = None
    if matches:
        block = matches[-1]  # 取最后一个代码块，避免推理中的示例 JSON 干扰
    else:
        # 容错：模型忘了加代码块围栏，尝试直接找最外层 JSON 对象
        start, end = raw.find("{"), raw.rfind("}")
        if start != -1 and end > start:
            block = raw[start : end + 1]

    if block is None:
        raise ParseError("输出中未找到 JSON 块，要求以 ```json 包裹 state_patch 与 action")

    try:
        payload = json.loads(block)
    except json.JSONDecodeError as exc:
        raise ParseError(
            f"JSON 解析失败：{exc.msg}（行 {exc.lineno} 列 {exc.colno}）。"
            f"常见原因：尾随逗号、单引号、中文引号、注释。原始片段：{block[:200]}"
        ) from exc

    if not isinstance(payload, dict):
        raise ParseError(f"JSON 块必须是对象，实际为 {type(payload).__name__}")

    if "state_patch" not in payload:
        raise ParseError("JSON 块缺少 state_patch 键")
    if "action" not in payload:
        raise ParseError("JSON 块缺少 action 键")

    patch = payload["state_patch"]
    if patch is None:
        patch = {}
    if not isinstance(patch, dict):
        raise ParseError(f"state_patch 必须是对象，实际为 {type(patch).__name__}")

    # 推理部分 = JSON 块之前的文本
    reasoning = raw[: raw.find("```")].strip() if "```" in raw else ""

    return reasoning, patch, payload["action"]


# ---------------------------------------------------------------------------
# Prompt 组装
# ---------------------------------------------------------------------------

_OUTPUT_CONTRACT = """## 输出格式（必须严格遵守）

先输出你的推理过程（可长可短），然后**必须**以一个 JSON 代码块结尾：

```json
{
  "state_patch": { "...": "..." },
  "action": { "...": "..." }
}
```

约束：
1. JSON 块只能有 `state_patch` 和 `action` 两个键，不要加其他键。
2. `state_patch` 使用增量更新语义：
   - 只需写出**发生变化**的字段，未变化的字段不要重复写。
   - 删除某个键：把它设为 `null`。
   - 嵌套 dict 只更新你列出的子键，其余子键会被自动保留。
3. 不要输出注释、尾随逗号、单引号——JSON 必须可被标准解析器解析。
4. 你的推理过程只用于支撑本步决策，不会被带入下一轮。因此凡是对未来有用的信息，
   必须写进 `state_patch`，否则会永久丢失。"""


@dataclass
class PromptAssembler:
    """把 (P, Σt, Ot) 渲染为 messages。

    Attributes:
        spec:         P —— 不可变的技能规范（角色、规则、工具、合规要求）。
                      整个任务期间保持不变，绝不追加历史。
        schema:       状态 schema，其描述会渲染进 system 消息。
        output_hint:  action 的格式说明（每个领域的动作空间不同）。

    Example:
        >>> asm = PromptAssembler("你是导诊助手", schema, '{"type": "ask"|"done"}')
        >>> msgs = asm.build(state, "我头痛")
        >>> [m["role"] for m in msgs]
        ['system', 'user']
    """

    spec: str
    schema: StateSchema
    output_hint: str = '{"type": "...", "...": "..."}'
    max_observation_chars: int = 4000

    def system_message(self) -> str:
        """构建 system 消息：P + schema + 输出契约。长度恒定。"""
        return (
            f"{self.spec.strip()}\n\n"
            "## 执行状态 Σ（结构化，可变）\n"
            "你每轮都会收到当前状态。它的字段定义如下：\n\n"
            f"{self.schema.describe()}\n\n"
            "## 动作格式\n"
            f"{self.output_hint}\n\n"
            f"{_OUTPUT_CONTRACT}"
        )

    def build(self, state: ExecutionState, observation: str) -> list[dict[str, str]]:
        """构建一步的完整 messages。

        Args:
            state:       当前 Σt。
            observation: Ot —— 本步最新观测（患者原话 / 工具返回 / 环境变化）。

        Returns:
            OpenAI 风格的 messages 列表。注意：只有 2 条，不含任何历史。
        """
        obs = observation or "(无)"
        if len(obs) > self.max_observation_chars:
            obs = obs[: self.max_observation_chars] + "\n...[观测已截断]"

        user = (
            "## 当前执行状态 Σt\n"
            f"```json\n{state.to_json()}\n```\n\n"
            "## 本步最新观测 Ot\n"
            f"{obs}\n\n"
            "请更新状态并给出下一步动作。"
        )
        return [
            {"role": "system", "content": self.system_message()},
            {"role": "user", "content": user},
        ]

    def build_retry(
        self,
        state: ExecutionState,
        observation: str,
        bad_patch: dict[str, Any],
        errors: list[str],
    ) -> list[dict[str, str]]:
        """补丁校验失败后的重试提示。

        关键设计：把**具体错误**和**被拒的补丁**一起回传，而不是笼统说"格式错了"。
        这直接对应论文中小模型的主要失败模式——结构化输出遵循度不足，
        其中 68% 是"过早覆写/误删"，需要明确的错误定位才能纠正。
        """
        obs = observation or "(无)"
        if len(obs) > self.max_observation_chars:
            obs = obs[: self.max_observation_chars] + "\n...[观测已截断]"

        error_list = "\n".join(f"- {e}" for e in errors)
        user = (
            "## 当前执行状态 Σt\n"
            f"```json\n{state.to_json()}\n```\n\n"
            "## 本步最新观测 Ot\n"
            f"{obs}\n\n"
            "## 上一次的状态更新被拒绝\n"
            f"你提交的 state_patch：\n```json\n"
            f"{json.dumps(bad_patch, ensure_ascii=False, separators=(',', ':'))}\n```\n\n"
            f"校验错误：\n{error_list}\n\n"
            "请修正后重新输出。注意：state_patch 只写变化的字段；"
            "嵌套 dict 只更新需要变的子键，不要整体覆盖。"
        )
        return [
            {"role": "system", "content": self.system_message()},
            {"role": "user", "content": user},
        ]
