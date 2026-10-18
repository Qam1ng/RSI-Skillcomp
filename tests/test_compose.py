import unittest

from skillcomp.skill import SkillCard, Library
from skillcomp.compose import (
    compose_declared, compose_observed, IncompatibleComposition,
    mine_candidates, propose_macros,
)
from skillcomp.trace import Trace, Step
from skillcomp.envs.drawer_world import atomic_cards


def _lib(items):
    lib = Library()
    for c in atomic_cards(items):
        lib.admit(c)
    return lib


class TestAlgebra(unittest.TestCase):
    def setUp(self):
        self.lib = _lib(["cup"])

    def test_three_step_macro_conditions(self):
        seq = [
            self.lib.get("open_drawer"),
            self.lib.get("pick_from_drawer", ("cup",)),
            self.lib.get("place_on_counter", ("cup",)),
        ]
        m = compose_declared(seq, "fetch_cup")
        # 前置：抽屉关着(第一步要求)；杯在抽屉、手空(第二步要求且之前没造出来)
        self.assertEqual(
            m.pre, frozenset({"drawer_closed", "in_drawer(cup)", "hand_empty"})
        )
        # 净效果：抽屉开了、杯在台面、手空(holding 中途出现又消失，不留在净效果)
        self.assertIn("on_counter(cup)", m.add)
        self.assertIn("drawer_open", m.add)
        self.assertNotIn("holding(cup)", m.add)
        self.assertIn("in_drawer(cup)", m.delete)
        self.assertEqual(len(m.body), 3)

    def test_incompatible_rejected(self):
        # 关抽屉之后再从抽屉里拿 → 前置被删且未重建，必须拒绝
        seq = [
            self.lib.get("open_drawer"),
            self.lib.get("close_drawer"),
            self.lib.get("pick_from_drawer", ("cup",)),
        ]
        with self.assertRaises(IncompatibleComposition):
            compose_declared(seq, "bad")

    def test_use_then_delete_is_legal(self):
        # 开抽屉(造出 drawer_open) → 取杯(用 drawer_open) → 关抽屉(删 drawer_open)
        seq = [
            self.lib.get("open_drawer"),
            self.lib.get("pick_from_drawer", ("cup",)),
            self.lib.get("close_drawer"),
        ]
        m = compose_declared(seq, "fetch_and_close")
        self.assertNotIn("drawer_open", m.add)
        self.assertIn("drawer_closed", m.add)


class TestObserved(unittest.TestCase):
    def test_observed_composition_from_snapshots(self):
        s1 = Step("a", (), frozenset({"p", "q"}), frozenset({"q", "r"}), True)
        s2 = Step("b", (), frozenset({"q", "r"}), frozenset({"q", "r", "t"}), True)
        occ = [[s1, s2], [s1, s2]]
        m = compose_observed(occ, "ab", (("a", ()), ("b", ())))
        self.assertEqual(m.pre, frozenset({"p", "q"}))
        self.assertEqual(m.add, frozenset({"r", "t"}))
        self.assertEqual(m.delete, frozenset({"p"}))
        self.assertEqual(m.origin, "observed")


class TestMiningAndAdmission(unittest.TestCase):
    def _trace(self, lib, keys, success=True):
        steps = []
        for name, args in keys:
            steps.append(Step(name, args, frozenset(), frozenset(), True))
        return Trace(task="t", steps=steps, success=success)

    def test_mine_and_admit(self):
        lib = _lib(["cup"])
        seq = [("open_drawer", ()), ("pick_from_drawer", ("cup",)),
               ("place_on_counter", ("cup",))]
        traces = [self._trace(lib, seq) for _ in range(4)]
        admitted = propose_macros(traces, lib, min_support=3, max_new=2)
        self.assertGreaterEqual(len(admitted), 1)
        # 收下的最长宏应覆盖整个三连
        self.assertEqual(len(admitted[0].body), 3)
        self.assertTrue(lib.has(admitted[0].name))

    def test_failed_traces_excluded(self):
        lib = _lib(["cup"])
        seq = [("open_drawer", ()), ("pick_from_drawer", ("cup",))]
        traces = [self._trace(lib, seq, success=False) for _ in range(5)]
        self.assertEqual(mine_candidates(traces, min_support=2), [])


if __name__ == "__main__":
    unittest.main()
