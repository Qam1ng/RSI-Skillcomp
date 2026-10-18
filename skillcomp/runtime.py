"""运行时垫片：执行宏 + 条件核对 + 跑偏回退。

执行一个宏 = 沿身体逐个跑成分，每步前后核对条件：
- 成分失败或声明效果没出现 → 先原地重试一次（可配）；
- 还不行 → 返回结构化回退报告（在第几个成分断的），由上层决定拆回细粒度重规划。

事件标签（分级直方图的原料）：
  macro_clean       宏一气呵成
  dechunk_retry_ok  中途断过、细粒度重试后救回
  macro_abort       救不回，上报 harness 规划者
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from .skill import Library, SkillCard
from .trace import Step


class Executor(Protocol):
    """harness 侧执行器要实现的最小接口。"""

    def run(self, skill: str, args: tuple[str, ...]) -> Step: ...
    def state(self) -> frozenset[str]: ...


@dataclass
class RunResult:
    success: bool
    event: str                       # macro_clean / dechunk_retry_ok / macro_abort / atomic
    steps: list[Step] = field(default_factory=list)
    failed_at: int | None = None     # 断在身体的第几个成分
    reason: str = ""

    @property
    def decisions(self) -> int:
        """这次调用占用上层规划者的决策点数：恒为 1——宏的意义所在。"""
        return 1


def run_skill(
    lib: Library,
    ex: Executor,
    name: str,
    args: tuple[str, ...] = (),
    retry_per_step: int = 1,
    check_conditions: bool = True,
) -> RunResult:
    card = lib.get(name, args)
    if card.kind == "atomic":
        step = ex.run(name, args)
        return RunResult(success=step.success, event="atomic", steps=[step],
                         reason="" if step.success else "atomic_failed")

    # ---- 宏 ----
    if check_conditions and card.origin == "declared" and not card.pre <= ex.state():
        missing = card.pre - ex.state()
        return RunResult(False, "macro_abort", [], None, f"前置不满足: {sorted(missing)}")

    all_steps: list[Step] = []
    dechunked = False
    for i, (s_name, s_args) in enumerate(card.body):
        sub = lib.get(s_name, s_args)
        ok = False
        for attempt in range(1 + retry_per_step):
            step = ex.run(s_name, s_args)
            all_steps.append(step)
            if step.success and _effects_hold(sub, ex, check_conditions):
                ok = True
                if attempt > 0:
                    dechunked = True
                break
        if not ok:
            return RunResult(False, "macro_abort", all_steps, i,
                             f"成分 {s_name}{s_args} 重试后仍失败")
        if card.maintain and check_conditions and not card.maintain <= ex.state():
            broken = card.maintain - ex.state()
            return RunResult(False, "macro_abort", all_steps, i,
                             f"维持条件被破坏: {sorted(broken)}")
    event = "dechunk_retry_ok" if dechunked else "macro_clean"
    return RunResult(True, event, all_steps)


def _effects_hold(card: SkillCard, ex: Executor, check: bool) -> bool:
    if not check or card.origin != "declared":
        return True
    st = ex.state()
    return card.add <= st and not (card.delete & st)
