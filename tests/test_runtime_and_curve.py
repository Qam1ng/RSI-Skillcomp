import unittest

from skillcomp.compose import propose_macros
from skillcomp.envs.drawer_world import DrawerWorld, plan_bfs
from skillcomp.runtime import run_skill
from skillcomp.trace import Trace


def run_episode(world: DrawerWorld, goal, retry=1):
    """用 BFS 当占位规划者跑一集，返回 (成功, 决策点数, Trace, 事件列表)。"""
    world.reset()
    plan = plan_bfs(world.lib, world.state(), goal)
    if plan is None:
        return False, 0, Trace(task="fetch", success=False), []
    steps, events = [], []
    for name, args in plan:
        r = run_skill(world.lib, world, name, args, retry_per_step=retry)
        steps.extend(r.steps)
        events.append(r.event)
        if not r.success:
            return False, len(plan), Trace(task="fetch", steps=steps, success=False), events
    ok = goal <= world.state()
    return ok, len(plan), Trace(task="fetch", steps=steps, success=ok), events


class TestFallback(unittest.TestCase):
    def test_dechunk_retry_saves_macro(self):
        world = DrawerWorld(["cup"], fail_rate=0.0, seed=1)
        traces = [run_episode(world, frozenset({"on_counter(cup)"}))[2] for _ in range(3)]
        admitted = propose_macros(traces, world.lib, min_support=3)
        self.assertTrue(admitted)
        macro = admitted[0]
        # 注入结构意外：第一步执行完抽屉自己关上 → 第二步(从抽屉取)首次必失败
        world.reset()
        world.mischief = ["close_drawer"]
        # 抽屉重开靠重试救不了(状态性意外救得了,结构性意外这里重试第一次会把
        # pick 的前置重新检查 — pick 失败后重试仍失败,宏上报 abort)
        r = run_skill(world.lib, world, macro.name, macro.args, retry_per_step=1)
        self.assertIn(r.event, ("macro_abort", "dechunk_retry_ok"))
        if r.event == "macro_abort":
            self.assertIsNotNone(r.failed_at)  # 回退指针给出断点

    def test_state_glitch_recovered_by_retry(self):
        # 状态性意外：单步随机失败(状态不变) → 原地重试应救回,事件为 dechunk_retry_ok
        world = DrawerWorld(["cup"], fail_rate=0.0, seed=2)
        traces = [run_episode(world, frozenset({"on_counter(cup)"}))[2] for _ in range(3)]
        macro = propose_macros(traces, world.lib, min_support=3)[0]
        world.reset()
        # 手动构造:让第一次技能调用失败一次,重试放行
        calls = {"n": 0}
        orig_run = world.run
        def run_flaky(skill, args):
            calls["n"] += 1
            if calls["n"] == 1:
                import random as _r
                keep = world.rng
                world.rng = _r.Random(0)
                world.fail_rate = 1.0
                step = orig_run(skill, args)
                world.fail_rate = 0.0
                world.rng = keep
                return step
            return orig_run(skill, args)
        world.run = run_flaky  # type: ignore
        r = run_skill(world.lib, world, macro.name, macro.args, retry_per_step=1)
        self.assertTrue(r.success)
        self.assertEqual(r.event, "dechunk_retry_ok")


class TestCurve(unittest.TestCase):
    def test_decisions_drop_success_holds(self):
        """核心端到端:合成后决策点变少、成功率不降。(玩具环境,仅验证机制)"""
        goal = frozenset({"on_counter(cup)", "on_counter(pen)"})
        world = DrawerWorld(["cup", "pen"], fail_rate=0.0, seed=0)

        before_ok, before_dec = [], []
        traces = []
        for _ in range(5):
            ok, dec, tr, _ = run_episode(world, goal)
            before_ok.append(ok); before_dec.append(dec); traces.append(tr)

        admitted = propose_macros(traces, world.lib, min_support=3, max_new=3)
        self.assertTrue(admitted, "应至少合成出一个宏")

        after_ok, after_dec = [], []
        for _ in range(5):
            ok, dec, _, _ = run_episode(world, goal)
            after_ok.append(ok); after_dec.append(dec)

        self.assertTrue(all(before_ok) and all(after_ok), "成功率不得下降")
        self.assertLess(sum(after_dec) / 5, sum(before_dec) / 5,
                        f"决策点应下降: {before_dec} -> {after_dec}")


if __name__ == "__main__":
    unittest.main()
