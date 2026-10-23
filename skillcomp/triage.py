"""店长 v1：三叉裁决的规则版（预注册；VLM 版留作实验对照臂）。

规则表（跑之前写死，改规则 = 新版本号）：
  R1 无病历                       → hold   （没证据不动手）
  R2 病历数 < min_cases           → hold   （样本不足，噪声纪律）
  R3 台账最新分已达标              → hold   （不修没病的）
  R4 planner 类占比 > 半           → retry  （锅在调用方，零训练）
  R5 out_of_envelope 占比 ≥ split_ratio → split（能力圈外，分家+写新 PRE）
  R6 其余（in_envelope 为主）      → refine （圈内失败，修当前 expert）
"""
from __future__ import annotations

from dataclasses import dataclass

from . import casestore, ledger


@dataclass
class Decision:
    action: str          # "hold" | "retry" | "refine" | "split"
    reason: str
    evidence: dict       # 病历分布 + 台账摘要，可审计


def decide(skill: str,
           cases: list[casestore.Case],
           entries: list[ledger.Entry] | None = None,
           target: int | None = None,
           min_cases: int = 3,
           split_ratio: float = 0.5) -> Decision:
    dist = casestore.counts(cases, skill)
    n = sum(dist.values())
    ev = {"cases": dist, "n": n}

    if n == 0:
        return Decision("hold", "R1 无病历", ev)
    if n < min_cases:
        return Decision("hold", f"R2 病历数 {n} < {min_cases}，样本不足", ev)

    if entries is not None and target is not None:
        s = ledger.series(entries, skill)
        if s and s[-1].passes >= target:
            ev["latest"] = f"{s[-1].passes}/{s[-1].total}"
            return Decision("hold", f"R3 最新分 {s[-1].passes} 已达标 {target}", ev)

    if dist["planner"] > n / 2:
        return Decision("retry", f"R4 planner 类 {dist['planner']}/{n} 过半：锅在调用方", ev)
    if dist["out_of_envelope"] / n >= split_ratio:
        return Decision("split",
                        f"R5 圈外失败 {dist['out_of_envelope']}/{n} ≥ {split_ratio:.0%}：分家并写新 PRE", ev)
    return Decision("refine",
                    f"R6 圈内失败为主（{dist['in_envelope']}/{n}）：修当前 expert", ev)
