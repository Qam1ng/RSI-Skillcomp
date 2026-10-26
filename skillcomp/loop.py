"""内环主逻辑：校准 → 逐轮（执行→落账→裁决）→ 决策点停驻。

运行纪律的落点：运行期唯一入口是根目录 run_rsi.py（调本模块），
全部代码在 skillcomp/ 包内；外部输入只有任务计划、技能库、检定证书。
没有噪声线的尺子拒绝开跑（battery.require_floor 硬卡）。

v1 范围：代码载体。裁决出的"继续训/拆分"不自动开火——写成待办
（pending action）停给监督者；训练触发的自动化随合成模块化接入。
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path

from . import battery as battery_mod
from . import casestore, collect, exec_aspire, ledger, triage
from .battery import Battery, NoiseFloor, Registry


@dataclass
class TaskPlan:
    """一条任务线：评测组 + 程序 + 技能链。program 是完整可执行程序文本。"""
    battery: Battery
    program_text: str
    plan: list[tuple[str, str, str]]          # (技能名, 参数源码, 返回名)
    versions: dict[str, int]
    target: int | None = None                 # 达标线（通过数）


@dataclass
class RoundRecord:
    round_no: int
    ts: str
    battery: str
    passes: int
    total: int
    decisions: dict[str, dict]                # 技能 -> {action, reason}
    pending: list[str]                        # 待监督批准的动作
    note: str = ""


def calibrate(tp: TaskPlan, registry: Registry, repeats: int,
              workdir_prefix: str, runner=None) -> NoiseFloor:
    """同配置重复批 → 噪声线 → 写入登记册。这就是"校准批跑"。"""
    scores = []
    prog = Path(f"/tmp/{workdir_prefix}_cal.py")
    prog.write_text(tp.program_text)
    for i in range(repeats):
        kw = {"runner": runner} if runner else {}
        res = exec_aspire.run_battery(str(prog), tp.battery,
                                      f"{workdir_prefix}_cal{i}", **kw)
        scores.append(res.passes)
    nf = NoiseFloor(battery=tp.battery.name, scores=scores,
                    total=len(tp.battery.seeds),
                    measured_at=datetime.now().date().isoformat(),
                    provenance=f"{workdir_prefix}_cal0..{repeats-1}")
    registry.register(tp.battery)
    registry.set_floor(nf)
    return nf


def run_round(tp: TaskPlan, registry: Registry, round_no: int,
              ledger_path: str, cases_path: str,
              workdir_prefix: str, runner=None) -> RoundRecord:
    """一轮：执行 → 落账落病历 → 逐技能裁决。"""
    floor = registry.require_floor(tp.battery.name)   # 无证书在此拒跑
    prog = Path(f"/tmp/{workdir_prefix}_r{round_no}.py")
    prog.write_text(tp.program_text)
    kw = {"runner": runner} if runner else {}
    res = exec_aspire.run_battery(str(prog), tp.battery,
                                  f"{workdir_prefix}_r{round_no}", **kw)
    collect.from_batch(res, tp.battery, tp.plan, tp.versions,
                       ledger_path, cases_path)
    entries = ledger.read(ledger_path)
    cases = casestore.read(cases_path)
    decisions, pending = {}, []
    for skill, _a, _r in tp.plan:
        d = triage.decide(skill, cases, entries=entries, target=tp.target)
        decisions[skill] = {"action": d.action, "reason": d.reason}
        if d.action in ("refine", "split"):
            pending.append(f"{d.action}:{skill}")
    return RoundRecord(
        round_no=round_no, ts=datetime.now().isoformat(timespec="seconds"),
        battery=tp.battery.name, passes=res.passes, total=res.total,
        decisions=decisions, pending=pending,
        note=f"floor={floor}")


def run_loop(tp: TaskPlan, registry: Registry, max_rounds: int,
             ledger_path: str, cases_path: str, rounds_log: str,
             workdir_prefix: str, mode: str = "supervised",
             runner=None) -> list[RoundRecord]:
    """主环。supervised：出现待批动作即停驻；auto：仅停机条件停。

    v1 两种模式在"待批动作"上行为一致（训练触发未自动化），区别在
    全 hold 时 auto 继续、supervised 也继续——监督点只设在花钱处。
    """
    if mode not in ("supervised", "auto"):
        raise ValueError(f"未知模式: {mode}")
    records = []
    for rn in range(1, max_rounds + 1):
        rec = run_round(tp, registry, rn, ledger_path, cases_path,
                        workdir_prefix, runner=runner)
        records.append(rec)
        with open(rounds_log, "a") as f:
            f.write(json.dumps(asdict(rec), ensure_ascii=False) + "\n")
        if tp.target is not None and rec.passes >= tp.target:
            rec.note += " | 达标停机"
            break
        if rec.pending:
            rec.note += " | 停驻待批: " + ", ".join(rec.pending)
            break
    return records
