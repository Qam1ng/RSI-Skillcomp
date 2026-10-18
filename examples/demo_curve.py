"""演示：玩具环境里的"越跑越快"曲线。

跑 N 集 → 第 5 集后合成 → 决策点下降、成功率不降。
玩具数字，仅供理解机制，不进任何报告。
用法: python3 examples/demo_curve.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from skillcomp.compose import propose_macros
from skillcomp.envs.drawer_world import DrawerWorld, plan_bfs
from skillcomp.runtime import run_skill
from skillcomp.trace import Trace


def episode(world, goal):
    world.reset()
    plan = plan_bfs(world.lib, world.state(), goal)
    steps, events = [], []
    for name, args in plan:
        r = run_skill(world.lib, world, name, args)
        steps.extend(r.steps)
        events.append(r.event)
        if not r.success:
            return False, len(plan), Trace(task="fetch2", steps=steps, success=False), events
    ok = goal <= world.state()
    return ok, len(plan), Trace(task="fetch2", steps=steps, success=ok), events


def main():
    goal = frozenset({"on_counter(cup)", "on_counter(pen)"})
    world = DrawerWorld(["cup", "pen"], fail_rate=0.0, seed=0)
    traces = []
    print(f"{'集':>3} {'决策点':>5} {'原子步':>5} {'成功':>4}  事件")
    for ep in range(1, 11):
        ok, decisions, tr, events = episode(world, goal)
        traces.append(tr)
        print(f"{ep:>3} {decisions:>5} {len(tr.steps):>6} {str(ok):>5}  {','.join(sorted(set(events)))}")
        if ep == 5:
            admitted = propose_macros(traces, world.lib, min_support=3, max_new=3)
            names = [m.name for m in admitted]
            print(f"  >> 第 {ep} 集后合成 {len(admitted)} 个宏: {names}")
    print("\n注意:决策点(规划者要做的决定)下降,原子步(物理动作)不变——变快省的是决策,不是动作。")


if __name__ == "__main__":
    main()
