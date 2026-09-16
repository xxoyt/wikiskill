"""SkillRuntime —— SKILL.state 主循环。

对应论文 Algorithm 1:

    for t in 0..T:
        接收观测 Ot
        构造 prompt (P, Σt, Ot)
        用 LLM 生成 (Rt, ΔΣt, at)
        校验 ΔΣt                      <- 失败则重试；重试耗尽则回滚，Σ 保持不变
        Σ_{t+1} <- Σt ⊕ ΔΣt
        执行 at
        丢弃 Rt                       <- 关键：推理不进历史

关键保证:
    - Σ 永不被非法补丁污染（校验失败走 rollback-retry，最多 max_retries 次）
    - 单步 prompt 长度与步数 t 无关
    - 每一步的状态变更都有 diff 记录，可审计
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from .patch import apply_patch, diff_summary
from .prompt import LLMClient, ParseError, PromptAssembler, parse_llm_output
from .schema import StateSchema
from .state import ExecutionState

logger = logging.getLogger(__name__)


@dataclass
class StepResult:
    """单步执行结果。

    Attributes:
        action:      本步执行的动作 at。
        reasoning:   模型的推理轨迹 Rt。**仅用于日志**，不会被拼进下一步 prompt。
        state:       执行后的状态 Σ_{t+1}。
        diff:        状态变更摘要，用于审计与展示。
        retries:     补丁校验重试次数。
        rollback:    是否发生了回滚（补丁被丢弃，Σ 保持原样）。
        error:       错误信息；None 表示本步完全正常。
        elapsed_ms:  本步耗时。
        prompt_chars: 本步 prompt 字符数，用于监控 Σ 是否膨胀。
    """

    action: Any
    reasoning: str
    state: ExecutionState
    diff: list[str] = field(default_factory=list)
    retries: int = 0
    rollback: bool = False
    error: str | None = None
    elapsed_ms: float = 0.0
    prompt_chars: int = 0

    @property
    def ok(self) -> bool:
        """本步是否无错误且无回滚。"""
        return self.error is None and not self.rollback


@dataclass
class SkillRuntime:
    """SKILL.state 运行时。

    Attributes:
        assembler:    prompt 组装器，持有不可变的 P 与 schema。
        llm:          LLM 客户端，需实现 `complete(messages) -> str`。
        schema:       状态 schema（与 assembler 中的应为同一份）。
        max_retries:  补丁校验失败后的重试次数。论文中非法 patch 由运行时
                      rollback-retry 处理；小模型建议设为 2，并配合约束解码。
        fallback_action: 重试耗尽时执行的动作。**强烈建议显式设置**——
                      医疗等高风险场景应退回人工，而非让 Agent 猜测。
        on_step:     每步回调，签名 (StepResult) -> None，用于日志/埋点/落库。

    Example:
        >>> rt = SkillRuntime(asm, llm, schema)
        >>> res = rt.step(state, "我头痛三天了")
        >>> res.state["chief_complaint"]
        '头痛三天'
    """

    assembler: PromptAssembler
    llm: LLMClient
    schema: StateSchema
    max_retries: int = 2
    fallback_action: Callable[[str], dict[str, Any]] | None = None
    on_step: Callable[[StepResult], None] | None = None

    # ---------------------------------------------------------------- 单步

    def step(self, state: ExecutionState, observation: str) -> StepResult:
        """执行一步状态转移。

        Args:
            state:       当前状态 Σt。本方法不会修改它（失败时回滚，成功时返回新状态）。
            observation: 本步观测 Ot。

        Returns:
            StepResult，其 .state 为合并后的新状态（或回滚后的原状态）。
        """
        started = time.perf_counter()
        snapshot = state.snapshot()

        reasoning, patch, action = "", {}, None
        errors: list[str] = []
        retries = 0
        prompt_chars = 0

        while True:
            messages = (
                self.assembler.build(state, observation)
                if retries == 0
                else self.assembler.build_retry(state, observation, patch, errors)
            )
            prompt_chars = sum(len(m["content"]) for m in messages)

            try:
                raw = self.llm.complete(messages)
                reasoning, patch, action = parse_llm_output(raw)
            except ParseError as exc:
                errors = [str(exc)]
                action = None
            else:
                errors = self.schema.validate_patch(patch)
                if not errors:
                    break  # 校验通过

            retries += 1
            if retries > self.max_retries:
                return self._finish_rollback(
                    state, snapshot, reasoning, action, errors, retries,
                    started, prompt_chars,
                )
            logger.warning("状态补丁校验失败（第 %d 次重试）：%s", retries, errors)

        # ---- 校验通过：应用补丁 ----
        new_data = apply_patch(state.data, patch)
        diff = diff_summary(state.data, new_data)

        state.data = new_data
        state.version += 1

        result = StepResult(
            action=action,
            reasoning=reasoning,
            state=state,
            diff=diff,
            retries=retries,
            rollback=False,
            error=None,
            elapsed_ms=(time.perf_counter() - started) * 1000,
            prompt_chars=prompt_chars,
        )
        self._emit(result)
        return result

    def _finish_rollback(
        self,
        state: ExecutionState,
        snapshot: dict[str, Any],
        reasoning: str,
        action: Any,
        errors: list[str],
        retries: int,
        started: float,
        prompt_chars: int,
    ) -> StepResult:
        """重试耗尽：恢复现场，Σ 保持原样，执行兜底动作。"""
        state.restore(snapshot)
        error_msg = "；".join(errors)

        if self.fallback_action is not None:
            action = self.fallback_action(error_msg)
            logger.error("补丁 %d 次重试后仍失败，执行兜底动作：%s", retries - 1, error_msg)
        else:
            action = None
            logger.error("补丁 %d 次重试后仍失败，且未配置兜底动作：%s", retries - 1, error_msg)

        result = StepResult(
            action=action,
            reasoning=reasoning,
            state=state,
            diff=[],
            retries=retries,
            rollback=True,
            error=error_msg,
            elapsed_ms=(time.perf_counter() - started) * 1000,
            prompt_chars=prompt_chars,
        )
        self._emit(result)
        return result

    def _emit(self, result: StepResult) -> None:
        if self.on_step is not None:
            self.on_step(result)

    # ---------------------------------------------------------------- 多步

    def run(
        self,
        state: ExecutionState,
        observations: "list[str] | Callable[[ExecutionState, int], str | None]",
        max_steps: int = 30,
        is_done: Callable[[Any, ExecutionState], bool] | None = None,
    ) -> tuple[ExecutionState, list[StepResult]]:
        """连续执行多步。

        Args:
            state:        初始状态 Σ0。
            observations: 观测序列（列表）或观测生成函数 (state, step) -> Ot | None
                          （返回 None 表示结束）。后者适用于交互式场景：
                          观测来自外部（患者下一条消息 / 工具返回），无法预先列出。
            max_steps:    最大步数，防止失控。
            is_done:      终止判定 (action, state) -> bool。

        Returns:
            (最终状态, 每步结果列表)。
        """
        history: list[StepResult] = []
        iterable = (
            observations if isinstance(observations, list) else _fn_iter(observations, state)
        )

        for t, obs in enumerate(iterable):
            if t >= max_steps:
                logger.warning("达到最大步数 %d，提前终止", max_steps)
                break
            result = self.step(state, obs)
            history.append(result)
            if is_done is not None and is_done(result.action, state):
                break

        return state, history


def _fn_iter(fn: Callable[[ExecutionState, int], str | None], state: ExecutionState):
    """把观测生成函数包装为迭代器。"""
    step = 0
    while True:
        obs = fn(state, step)
        if obs is None:
            return
        yield obs
        step += 1


# ---------------------------------------------------------------------------
# 统计工具
# ---------------------------------------------------------------------------


def cumulative_tokens(history: list[StepResult], state: ExecutionState) -> int:
    """估算累计 token 消耗。

    注意这是粗估（按字符折算）。若要精确对比，接入 tiktoken 后替换此处即可。
    """
    total = sum(r.prompt_chars // 4 for r in history)
    total += state.estimate_tokens()
    return total


def summarize_run(history: list[StepResult]) -> dict[str, Any]:
    """汇总一次运行的统计信息，用于监控与对比实验。"""
    if not history:
        return {"steps": 0}
    return {
        "steps": len(history),
        "rollbacks": sum(1 for r in history if r.rollback),
        "total_retries": sum(r.retries for r in history),
        "avg_prompt_chars": sum(r.prompt_chars for r in history) // len(history),
        "max_prompt_chars": max(r.prompt_chars for r in history),
        "total_ms": round(sum(r.elapsed_ms for r in history), 1),
    }
