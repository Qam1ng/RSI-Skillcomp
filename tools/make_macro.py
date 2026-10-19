#!/usr/bin/env python3
"""端到端：真实轨迹语料 → 升维挖掘 → 一次性 LLM 蒸馏 → 验证门 → 宏文件。

用法:
  GEMINI_API_KEY=... python3 tools/make_macro.py \
    --corpus ~/skillcomp_data/aspire_batch ~/skillcomp_data/harvest_spatial2 ~/skillcomp_data/harvest_goal2 \
    --sources ~/skillcomp_data/winning_programs/goal2.py ~/skillcomp_data/winning_programs/spatial2.py \
    --fn pick_object --params object_name --motif-contains close_gripper \
    --out macros/
"""
import argparse, json, os, sys, time, urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from skillcomp.adapters.aspire import export_trace
from skillcomp.lifted import mine_lifted, motif_report
from skillcomp.synthesize import synthesize_macro

API = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
_usage = {"prompt": 0, "output": 0, "calls": 0}


def gemini_llm(model: str, key: str):
    def call(prompt: str) -> str:
        body = json.dumps({"contents": [{"role": "user", "parts": [{"text": prompt}]}]}).encode()
        req = urllib.request.Request(API.format(model=model, key=key), data=body,
                                     headers={"Content-Type": "application/json"})
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=300) as r:
                    d = json.loads(r.read())
                u = d.get("usageMetadata", {})
                _usage["prompt"] += u.get("promptTokenCount", 0)
                _usage["output"] += u.get("candidatesTokenCount", 0)
                _usage["calls"] += 1
                return d["candidates"][0]["content"]["parts"][0]["text"]
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(15 * (attempt + 1))
    return call


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", nargs="+", required=True)
    ap.add_argument("--sources", nargs="+", required=True)
    ap.add_argument("--fn", required=True)
    ap.add_argument("--params", nargs="+", required=True)
    ap.add_argument("--motif-contains", default=None)
    ap.add_argument("--model", default="gemini-flash-latest")
    ap.add_argument("--out", default="macros")
    ap.add_argument("--min-tasks", type=int, default=2)
    args = ap.parse_args()

    traces = []
    for c in args.corpus:
        for run in sorted(Path(c).expanduser().glob("*/run-*")):
            traces.append(export_trace(run))
    print(f"语料: {len(traces)} 集, {len(set(t.task for t in traces))} 个任务")

    motifs = mine_lifted(traces, min_task_coverage=args.min_tasks)
    print("—— 升维动机（前 8）——")
    print(motif_report(motifs, top=8))
    pick = None
    for m in motifs:
        if args.motif_contains is None or args.motif_contains in m.names:
            pick = m
            break
    if pick is None:
        print("没有命中指定动机", file=sys.stderr)
        return 1
    print(f"\n选中动机: {pick.describe()}")

    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        print("缺 GEMINI_API_KEY", file=sys.stderr)
        return 2
    sources = [Path(s).expanduser().read_text() for s in args.sources]
    mc = synthesize_macro(pick, sources, args.fn, args.params,
                          llm=gemini_llm(args.model, key))

    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    (out / f"{mc.name}.py").write_text(mc.code)
    prov = {
        "fn": mc.name, "params": mc.params,
        "pre": mc.pre_line, "eff": mc.eff_line,
        "motif": list(pick.names),
        "episode_coverage": pick.episode_coverage,
        "task_coverage": pick.task_coverage, "tasks": pick.tasks,
        "sources": args.sources, "model": args.model,
        "synthesis_usage": dict(_usage),
        "status": "pending_execution_verification",  # 执行验证过门前不得入正式库
    }
    (out / f"{mc.name}.provenance.json").write_text(json.dumps(prov, indent=1, ensure_ascii=False))
    print(f"\n宏已产出: {out}/{mc.name}.py  (合成用量: {_usage})")
    print(f"PRE/EFF: {mc.pre_line} | {mc.eff_line}")
    print("状态: pending_execution_verification —— 过执行门才入库")
    return 0


if __name__ == "__main__":
    sys.exit(main())
