"""SKILL.state 运行时内核 —— 零依赖实现。

对应论文 arXiv:2608.26263《SKILL.state: Scalable Long-Horizon Agent Skills》。

核心思想：把 Agent 的"追加式对话历史"替换为"显式、可变、有 schema 约束的结构化执行状态"。
每一步模型只看到 (P, Σt, Ot)，产出的中间推理被永久丢弃，只有经过校验的状态补丁会合并进 Σ。

模块划分:
    schema.py   字段规格与补丁校验 —— 保证状态既正确又"有界"
    state.py    Σt 容器 —— 状态的载体
    patch.py    ⊕ 合并算子 —— null 表示删除，dict 递归深合并
    prompt.py   (P, Σt, Ot) -> messages，以及失败重试提示
    runtime.py  主循环 step()/run()，含 rollback-retry
    store.py    状态持久化（内存 / 文件），支撑多轮会话与断点续跑

典型用法见 examples/triage_agent.py（医疗导诊场景）。
"""

from .state import ExecutionState
from .schema import FieldSpec, StateSchema
from .patch import apply_patch, merge_state, PatchError
from .prompt import PromptAssembler, parse_llm_output, ParseError
from .runtime import SkillRuntime, StepResult
from .store import StateStore, MemoryStore, FileStore

__all__ = [
    "ExecutionState",
    "FieldSpec",
    "StateSchema",
    "apply_patch",
    "merge_state",
    "PatchError",
    "PromptAssembler",
    "parse_llm_output",
    "ParseError",
    "SkillRuntime",
    "StepResult",
    "StateStore",
    "MemoryStore",
    "FileStore",
]

__version__ = "1.0.0"
