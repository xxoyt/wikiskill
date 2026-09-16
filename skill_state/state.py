"""Σt —— 结构化执行状态容器。

这是 SKILL.state 的核心抽象：它取代了传统的 `List[Message]` 对话历史。
与对话历史的本质区别：

    对话历史    只增不减，长度 O(t)，包含大量过时的观测与推理
    Σt          只保留"未来执行必需"的信息，长度有界，可被覆写与删除

设计约束（务必遵守，否则退化为另一种对话历史）:
    1. 只存结论，不存原文。工具返回的 2000 字文档 -> 存 20 字摘要。
    2. 允许覆写与删除。患者改口"其实不发烧了" -> 直接删字段，不要追加"患者又说..."。
    3. schema 固定。字段集由 StateSchema 限定，模型不能凭空新增顶层键。
"""

from __future__ import annotations

import copy
import json
from typing import Any, Iterator


class ExecutionState:
    """执行状态 Σt。

    Attributes:
        data:    状态数据本体，结构由 StateSchema 约束。
        version: 单调递增的状态版本号，每次成功应用补丁 +1。
                 可用于乐观并发控制与审计追溯。

    Example:
        >>> st = ExecutionState({"turn": 0})
        >>> st["turn"]
        0
        >>> st.to_json()
        '{"turn":0}'
    """

    __slots__ = ("data", "version")

    def __init__(self, data: dict[str, Any] | None = None, version: int = 0) -> None:
        self.data: dict[str, Any] = copy.deepcopy(data) if data else {}
        self.version: int = version

    # ---------------------------------------------------------------- 读写

    def __getitem__(self, key: str) -> Any:
        return self.data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.data[key] = value

    def __contains__(self, key: str) -> bool:
        return key in self.data

    def __iter__(self) -> Iterator[str]:
        return iter(self.data)

    def __len__(self) -> int:
        return len(self.data)

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def keys(self):
        return self.data.keys()

    def items(self):
        return self.data.items()

    # ---------------------------------------------------------------- 快照

    def snapshot(self) -> dict[str, Any]:
        """深拷贝快照，用于 rollback-retry 时恢复现场。"""
        return copy.deepcopy(self.data)

    def restore(self, snapshot: dict[str, Any]) -> None:
        """从快照恢复（补丁校验失败时不污染持久状态）。"""
        self.data = copy.deepcopy(snapshot)

    def fork(self) -> "ExecutionState":
        """复制出一个同版本号的独立状态。"""
        return ExecutionState(self.snapshot(), self.version)

    # ---------------------------------------------------------------- 序列化

    def to_json(self, *, indent: int | None = None) -> str:
        """紧凑序列化。

        论文中的实现同样使用紧凑格式（`separators=(',', ':')`）注入 prompt，
        以最小化 token 占用。
        """
        if indent is None:
            return json.dumps(self.data, ensure_ascii=False, separators=(",", ":"))
        return json.dumps(self.data, ensure_ascii=False, indent=indent)

    @classmethod
    def from_json(cls, text: str, version: int = 0) -> "ExecutionState":
        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError(f"状态 JSON 必须是对象，实际为 {type(data).__name__}")
        return cls(data, version)

    # ---------------------------------------------------------------- 观测

    def size_bytes(self) -> int:
        """序列化后字节数。用于监控 Σ 是否膨胀。"""
        return len(self.to_json().encode("utf-8"))

    def estimate_tokens(self) -> int:
        """粗估 token 数（中文约 1 字 1 token，英文约 4 字符 1 token）。

        这是估算不是精确值。接入 tiktoken 后可替换为本模型的真实编码。
        """
        text = self.to_json()
        cjk = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
        other = len(text) - cjk
        return cjk + max(1, other // 4)

    # ---------------------------------------------------------------- 表示

    def __repr__(self) -> str:
        return f"ExecutionState(v{self.version}, keys={list(self.data)}, ~{self.estimate_tokens()}tok)"
