"""自动记录：一次批跑的结果 → 分数台账 + 失败档案。

这是口2（日志口）的最后一段管子：执行模块收回结果后，本模块把
每个技能的通过数与连续裕度写进台账、把每次失败归因成病历。
从此"量完就扔"成为历史——内环的每一轮都会留下可供裁决的记录。
"""
from __future__ import annotations

import ast

from . import casestore, ledger
from .battery import Battery
from .exec_aspire import BatchResult


def parse_report(stdout: str) -> dict:
    """程序末尾 print(report) 的原文 → 字典。解析不了返回空。"""
    s = stdout.strip().splitlines()
    for line in reversed(s):
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            try:
                return ast.literal_eval(line)
            except (ValueError, SyntaxError):
                return {}
    return {}


def from_batch(res: BatchResult, battery: Battery,
               plan: list[tuple[str, str, str]],
               versions: dict[str, int],
               ledger_path: str, cases_path: str,
               cost_rollouts: int | None = None) -> dict:
    """把一次批跑落账。返回摘要 {"entries": n, "cases": n}。

    plan 与生成程序时的一致：[(技能名, 参数源码, 返回名), ...]。
    逐技能记一条台账（通过数 = 该技能在各种子上 ok 的次数，裕度按种子收集）；
    逐失败种子记一条病历，怪到链条上第一个没通过的技能头上。
    """
    reports = {seed: parse_report(res.stdout_reports.get(seed, ""))
               for seed in (r.seed for r in res.results)}

    n_entries = 0
    for skill, _args, ret in plan:
        passes = sum(bool(reports[r.seed].get(f"{ret}_ok")) for r in res.results)
        margins: dict[str, list] = {}
        for r in res.results:
            for k, v in reports[r.seed].items():
                if k.startswith(f"margin_{ret}"):
                    margins.setdefault(k, []).append(round(float(v), 4))
        ledger.append(ledger_path, ledger.Entry(
            skill=skill, version=versions.get(skill, 0), battery=battery.name,
            passes=passes, total=res.total, margins=margins,
            cost={"rollouts": cost_rollouts if cost_rollouts is not None else res.total},
            note=f"program={res.program}"))
        n_entries += 1

    n_cases = 0
    for r in res.results:
        if r.task_success:
            continue
        rep = reports[r.seed]
        blamed, stage, pre_ok = None, "", True
        for skill, _args, ret in plan:
            if not rep.get(f"{ret}_ok", False):
                blamed = (skill, ret)
                stage = str(rep.get(f"{ret}_stage", r.termination))
                pre_ok = bool(rep.get(f"check_{ret}_pre_holding", True))
                break
        if blamed is None:
            # 程序全绿但任务判负：怪不到某个技能，记规划类
            blamed, stage, pre_ok = ((plan[-1][0], plan[-1][2]), "all_ok_task_failed", True)
        skill, ret = blamed
        planner_fault = stage in ("pre_violated", "all_ok_task_failed")
        kind = ("planner" if planner_fault
                else casestore.classify(pre_ok=pre_ok, eff_ok=False))
        casestore.append(cases_path, casestore.Case(
            task=f"{battery.suite}/{battery.task_id}", seed=r.seed,
            skill=skill, version=versions.get(skill, 0), stage=stage,
            pre_ok=pre_ok, eff_ok=False, kind=kind,
            scene={"battery": battery.name},
            run_dir=r.run_dir,
            diagnosis=f"termination={r.termination}, stage={stage}"))
        n_cases += 1

    return {"entries": n_entries, "cases": n_cases}
