#!/usr/bin/env python3
"""内环唯一入口。

  python run_rsi.py calibrate --repeats 3     # 校准批跑：测噪声线、写登记册
  python run_rsi.py run --rounds 3            # 主环（默认 supervised，停驻待批）
  python run_rsi.py run --rounds 3 --mode auto

v1 任务线：代码载体的 goal2（抓酒瓶放碗），宏取自 macros/，程序带运行期
PRE/EFF 核查。证书文件 data/registry.json 缺失或无噪声线时 run 拒绝启动。
"""
import argparse
import sys
from pathlib import Path

from skillcomp import conditions, loop
from skillcomp.battery import Battery, Registry

ROOT = Path(__file__).parent
DATA = ROOT / "data"
REGISTRY = DATA / "registry.json"
LEDGER = DATA / "ledger.jsonl"
CASES = DATA / "cases.jsonl"
ROUNDS = DATA / "rounds.jsonl"


def goal2_taskplan() -> loop.TaskPlan:
    srcs = [(ROOT / "macros/pick_object.py").read_text(),
            (ROOT / "macros/place_into.py").read_text()]
    plan = [("pick_object", '"wine bottle"', "grasp"),
            ("place_into",
             'held_below_m=float(grasp.get("below_grasp_m", 0.25)), target_name="bowl"',
             "placed")]
    # 注意：place_into 的位置参数顺序是 (target_name, held_below_m)，上行用关键字以免错位
    return loop.TaskPlan(
        battery=Battery(name="task@goal2", suite="libero_goal_task", task_id=2,
                        seeds=(56, 57, 58, 59, 60)),
        program_text=conditions.checked_program(srcs, plan),
        plan=plan,
        versions={"pick_object": 5, "place_into": 3},
        target=5)


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    cal = sub.add_parser("calibrate")
    cal.add_argument("--repeats", type=int, default=3)
    run = sub.add_parser("run")
    run.add_argument("--rounds", type=int, default=3)
    run.add_argument("--mode", choices=["supervised", "auto"], default="supervised")
    args = ap.parse_args()

    DATA.mkdir(exist_ok=True)
    tp = goal2_taskplan()

    if args.cmd == "calibrate":
        reg = Registry.load(REGISTRY) if REGISTRY.exists() else Registry()
        nf = loop.calibrate(tp, reg, args.repeats, workdir_prefix="rsi")
        reg.save(REGISTRY)
        print(f"噪声线已登记: {nf.battery} scores={nf.scores} floor={nf.floor}")
        return 0

    if not REGISTRY.exists():
        print("拒绝启动：没有检定证书（先跑 calibrate）", file=sys.stderr)
        return 2
    reg = Registry.load(REGISTRY)
    recs = loop.run_loop(tp, reg, args.rounds, str(LEDGER), str(CASES),
                         str(ROUNDS), workdir_prefix="rsi", mode=args.mode)
    for r in recs:
        print(f"[round {r.round_no}] {r.passes}/{r.total} "
              f"decisions={ {k: v['action'] for k, v in r.decisions.items()} } {r.note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
