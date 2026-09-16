"""StateStore —— 状态持久化。

SKILL.state 的核心循环只关心内存中的 Σt，但真实业务需要跨请求续跑：
导诊会话可能跨越几十分钟、多次 HTTP 请求，患者中途关掉页面再回来还得接着问。

本模块提供两种零依赖实现，以及一个协议供你接入 Redis（你的项目已有 Redisson，
Python 侧接 redis-py 实现同名三个方法即可）。

设计要点:
    - 存的是**结构化状态**，不是对话历史。改存 Redis 时一个会话就是一个 hash，
      读写都是 O(1)，不需要追加日志再重放。
    - 保存时同时落一份 diff 审计流。医疗场景下，"为什么给出这个建议"
      比"给出了什么建议"更重要。
"""

from __future__ import annotations

import json
import os
import tempfile
import threading
import time
from typing import Any, Protocol, runtime_checkable

from .state import ExecutionState


@runtime_checkable
class StateStore(Protocol):
    """状态存储协议。实现 load/save/delete 三个方法即可替换后端。"""

    def load(self, session_id: str) -> ExecutionState | None: ...

    def save(self, session_id: str, state: ExecutionState) -> None: ...

    def delete(self, session_id: str) -> None: ...


class MemoryStore:
    """进程内存储，用于测试与单进程服务。

    线程安全（带锁）。进程重启即丢失。
    """

    def __init__(self) -> None:
        self._data: dict[str, tuple[str, int]] = {}
        self._lock = threading.Lock()

    def load(self, session_id: str) -> ExecutionState | None:
        with self._lock:
            entry = self._data.get(session_id)
        if entry is None:
            return None
        raw, version = entry
        return ExecutionState.from_json(raw, version)

    def save(self, session_id: str, state: ExecutionState) -> None:
        with self._lock:
            self._data[session_id] = (state.to_json(), state.version)

    def delete(self, session_id: str) -> None:
        with self._lock:
            self._data.pop(session_id, None)

    def __len__(self) -> int:
        return len(self._data)

    def keys(self) -> list[str]:
        with self._lock:
            return list(self._data)


class FileStore:
    """文件存储，每个会话一个 JSON 文件。

    适合开发与小规模部署；生产环境建议换 Redis。

    写入采用「临时文件 + 原子替换」，避免进程被杀时留下半截 JSON。
    """

    def __init__(self, directory: str) -> None:
        self.dir = directory
        os.makedirs(directory, exist_ok=True)

    def _path(self, session_id: str) -> str:
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in session_id)
        return os.path.join(self.dir, f"{safe}.json")

    def load(self, session_id: str) -> ExecutionState | None:
        path = self._path(session_id)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        return ExecutionState.from_json(payload["state"], payload.get("version", 0))

    def save(self, session_id: str, state: ExecutionState) -> None:
        path = self._path(session_id)
        payload = {
            "session_id": session_id,
            "version": state.version,
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "state": state.data,
        }
        fd, tmp = tempfile.mkstemp(dir=self.dir, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            os.replace(tmp, path)
        except BaseException:
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise

    def delete(self, session_id: str) -> None:
        path = self._path(session_id)
        if os.path.exists(path):
            os.unlink(path)


class AuditLog:
    """状态变更审计流。

    在医疗场景中，这份日志回答的是"AI 凭什么给出这个建议"——
    每一步采集了什么信息、依据哪些字段做了判断。

    与 Σ 的区别：Σ 是"当前快照"，审计流是"如何走到这里"。
    """

    def __init__(self, path: str | None = None) -> None:
        self.path = path
        self._entries: list[dict[str, Any]] = []
        self._lock = threading.Lock()

    def record(
        self,
        session_id: str,
        version: int,
        diff: list[str],
        action: Any,
        reasoning: str = "",
        error: str | None = None,
    ) -> None:
        entry = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "session_id": session_id,
            "version": version,
            "diff": diff,
            "action": action,
            "error": error,
        }
        if reasoning:
            # 推理默认不落盘（含冗余且可能包含敏感推测）；如需审计可开启
            entry["reasoning"] = reasoning
        with self._lock:
            self._entries.append(entry)
        if self.path:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    @property
    def entries(self) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._entries)
