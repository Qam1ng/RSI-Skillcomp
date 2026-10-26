#!/usr/bin/env python3
"""收割生产线：vla_prod 目录 → 统一 trace 文件 + 终轮失败病历 + 清单。

用法: python tools/harvest_vla.py <本地 vla_prod 目录> <traces 输出.jsonl>
（run 目录需先 rsync 到本地；病历追加进 data/cases.jsonl。）
"""
import ast
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from skillcomp import casestore                      # noqa: E402
from skillcomp.adapters.aspire import export_trace   # noqa: E402
from skillcomp.trace import save_jsonl               # noqa: E402


def count_vla_calls(program_text: str) -> int:
    tree = ast.parse(program_text)
    return sum(1 for n in ast.walk(tree)
               if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "vla_act")


def harvest(prod: Path, traces_out: Path, cases_path: str = "data/cases.jsonl"):
    traces, rows = [], []
    for tdir in sorted(prod.glob("task*")):
        tid = int(tdir.name[4:])
        meter = json.loads((tdir / "meter.json").read_text())
        final = bool(meter.get("final_success"))
        progs = sorted(tdir.glob("program_r*.py"))
        nvla = count_vla_calls(progs[-1].read_text()) if progs else 0
        toks = sum((r.get("prompt_tokens") or 0) + (r.get("output_tokens") or 0)
                   for r in meter["rounds"])
        runs = sorted((tdir / "runs").glob("*/run-*"))
        for run in runs:
            traces.append(export_trace(run))
        rows.append((tid, len(meter["rounds"]), final, nvla, toks, len(runs)))
        if not final and runs:
            out = json.loads((runs[-1] / "outcome.json").read_text())
            stage = out.get("termination_reason", "")
            casestore.append(cases_path, casestore.Case(
                task=f"libero_goal_task/{tid}", seed=51, skill="vla_act", version=1,
                stage=stage, pre_ok=True, eff_ok=False,
                kind="planner" if "error" in stage else "in_envelope",
                scene={"suite": "libero_goal_task", "mode": "osc_vla",
                       "vla_calls": nvla},
                run_dir=str(runs[-1]),
                diagnosis=f"final round failed: {stage}"))
    traces_out.parent.mkdir(parents=True, exist_ok=True)
    save_jsonl(traces, traces_out)
    return traces, rows


if __name__ == "__main__":
    prod, out = Path(sys.argv[1]), Path(sys.argv[2])
    traces, rows = harvest(prod, out)
    print(f"{len(traces)} traces -> {out}")
    print("task rounds final vla_calls tokens runs")
    for r in rows:
        print(" ", *r)
    print(f"final: {sum(1 for r in rows if r[2])}/{len(rows)} solved")
