"""病历档案 v1：每次失败（和值得记的成功）一条结构化 Case，追加式 JSONL。

Case 的三类（kind）就是三叉裁决的分拣依据：
- in_envelope   ：PRE 满足却 EFF 崩——技能自己的锅 → refine 候选
- out_of_envelope：失败源于 PRE 本不该放行的输入（能力圈外）→ split 候选
- planner       ：技能没错，是调用/规划失误 → retry 候选
场景特征（scene）是必填习惯：没有它，失败聚类无从谈起（盘子教训）。
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import date
from pathlib import Path

KINDS = ("in_envelope", "out_of_envelope", "planner")


@dataclass
class Case:
    task: str                      # 如 "libero_goal_task/1"
    seed: int
    skill: str                     # 被归因的技能
    version: int
    stage: str                     # 断在哪一环（宏返回的 stage / 调用名）
    pre_ok: bool
    eff_ok: bool
    kind: str                      # KINDS 之一
    scene: dict = field(default_factory=dict)   # 场景特征：物体类别/几何/光照……
    run_dir: str = ""              # 指向完整飞行记录（trace/calls）的指针
    diagnosis: str = ""            # 一句话：后端拒绝理由/几何原因
    fix: str = ""                  # 若已修复：怎么修的（给 Context Assembly 用）
    ts: str = field(default_factory=lambda: date.today().isoformat())

    def __post_init__(self) -> None:
        if self.kind not in KINDS:
            raise ValueError(f"kind 必须是 {KINDS} 之一: {self.kind}")


def classify(pre_ok: bool, eff_ok: bool, planner_fault: bool = False) -> str:
    """从条件链断点类型推 kind（反扫停止规则的编码化）。"""
    if planner_fault:
        return "planner"
    if pre_ok and not eff_ok:
        return "in_envelope"
    if not pre_ok:
        return "out_of_envelope"
    raise ValueError("pre_ok 且 eff_ok 的执行不构成失败病历")


def append(path: str | Path, c: Case) -> None:
    with open(path, "a") as f:
        f.write(json.dumps(asdict(c), ensure_ascii=False) + "\n")


def read(path: str | Path) -> list[Case]:
    p = Path(path)
    if not p.exists():
        return []
    return [Case(**json.loads(line)) for line in p.read_text().splitlines() if line.strip()]


def query(cases: list[Case], skill: str | None = None, kind: str | None = None,
          stage: str | None = None) -> list[Case]:
    return [c for c in cases
            if (skill is None or c.skill == skill)
            and (kind is None or c.kind == kind)
            and (stage is None or c.stage == stage)]


def counts(cases: list[Case], skill: str) -> dict[str, int]:
    """该技能的病历分布——triage 的直接输入。"""
    out = {k: 0 for k in KINDS}
    for c in query(cases, skill=skill):
        out[c.kind] += 1
    return out
