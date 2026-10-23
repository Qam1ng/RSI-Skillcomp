"""准入门 v1：静态检查 + 执行验证的统一裁定记录 + 证据回流轮数预算。

执行验证本身由底盘批跑（scripts/verify_*），本模块只做三件事：
1. 裁定：静态门过 + 冻结尺子全过 = 准入（v1 从严，与实践一致）；
2. 记录：每次裁定落一条可审计的 GateRecord；
3. 限轮：证据回流 ≤ max_rounds（预注册纪律），超了必须停下来报告。
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class GateRecord:
    skill: str
    version: int
    battery: str
    static_ok: bool
    exec_passes: int
    exec_total: int
    admitted: bool = field(init=False)
    note: str = ""

    def __post_init__(self) -> None:
        self.admitted = bool(self.static_ok and self.exec_total > 0
                             and self.exec_passes == self.exec_total)


class EvidenceBudget:
    """证据回流轮数预算：到顶即停，禁止"再试一轮"的诱惑。"""

    def __init__(self, max_rounds: int = 2) -> None:
        self.max_rounds = max_rounds
        self.used = 0

    def allow(self) -> bool:
        return self.used < self.max_rounds

    def spend(self) -> None:
        if not self.allow():
            raise RuntimeError(f"证据回流已用满 {self.max_rounds} 轮——停，记录证据，报告")
        self.used += 1
