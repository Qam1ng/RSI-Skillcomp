import unittest

from skillcomp.trace import Trace, Step
from skillcomp.lifted import mine_lifted
from skillcomp.synthesize import synthesize_macro, validate_macro, MacroValidationError


def mk_trace(task, names_args, success=True):
    steps = [Step(n, a, frozenset(), frozenset(), True) for n, a in names_args]
    return Trace(task=task, steps=steps, success=success)


PICK = [("localize_object", ("X",)), ("get_robot_state", ()),
        ("move_to_pose", ("P1",)), ("move_to_pose", ("P2",)), ("close_gripper", ())]


class TestLiftedMining(unittest.TestCase):
    def _corpus(self):
        out = []
        for task, obj in (("A/0", "can"), ("B/2", "bowl"), ("C/2", "bottle")):
            for ep in range(3):
                seq = [("open_gripper", ())] + [
                    (n, tuple(x.replace("X", obj).replace("P", f"pose{ep}") for x in a))
                    for n, a in PICK]
                out.append(mk_trace(task, seq))
        return out

    def test_cross_task_motif_found(self):
        motifs = mine_lifted(self._corpus(), min_len=3, max_len=6,
                             min_episode_coverage=5, min_task_coverage=3)
        self.assertTrue(motifs)
        top = motifs[0]
        self.assertEqual(top.task_coverage, 3)
        self.assertEqual(top.episode_coverage, 9)
        self.assertIn("close_gripper", top.names)
        # 参数角色：localize 的参数跨例变化
        loc = next(r for r in top.arg_roles if r.skill == "localize_object")
        self.assertEqual(loc.role, "varies")

    def test_single_task_pattern_filtered(self):
        # 只出现在一个任务里的段：跨任务下限应滤掉
        traces = [mk_trace("A/0", [("open_gripper", ()), ("segment_text", ("x",)),
                                   ("close_gripper", ())]) for _ in range(5)]
        motifs = mine_lifted(traces, min_len=3, max_len=3,
                             min_episode_coverage=3, min_task_coverage=2)
        self.assertEqual(motifs, [])

    def test_per_episode_coverage_counted_once(self):
        # 单集内重复出现不得刷覆盖数
        seq = PICK + PICK
        traces = [mk_trace(t, seq) for t in ("A/0", "B/0", "C/0")]
        motifs = mine_lifted(traces, min_len=5, max_len=5,
                             min_episode_coverage=3, min_task_coverage=3)
        top = next(m for m in motifs if m.names == tuple(n for n, _ in PICK))
        self.assertEqual(top.episode_coverage, 3)
        self.assertGreaterEqual(len(top.occurrences), 6)


GOOD_MACRO = '''def pick_object(object_name):
    """Pick a rigid object with a top-down grasp.

    PRE: gripper empty; object visible from agentview
    EFF: object held in gripper
    """
    opened = open_gripper()
    if not opened.ok:
        return {"ok": False, "stage": "open_gripper"}
    target = localize_object(object_name, camera_name="agentview")
    if not target.ok:
        return {"ok": False, "stage": "localize"}
    pts = target.point_cloud.points
    zs = sorted([float(p[2]) for p in pts])
    state = get_robot_state()
    quat = state.end_effector_poses["primary"].quaternion_wxyz
    xs = sorted([float(p[0]) for p in pts]); ys = sorted([float(p[1]) for p in pts])
    cx, cy, cz = xs[len(pts) // 2], ys[len(pts) // 2], zs[int(len(pts) * 0.9)] - 0.02
    pre = Pose(position=(cx, cy, cz + 0.2), quaternion_wxyz=quat, frame="robot_base")
    if not move_to_pose(pre, tolerance=0.025, max_steps=450).ok:
        return {"ok": False, "stage": "pre_approach"}
    g = Pose(position=(cx, cy, cz), quaternion_wxyz=quat, frame="robot_base")
    if not move_to_pose(g, tolerance=0.02, max_steps=350).ok:
        return {"ok": False, "stage": "descend"}
    closed = close_gripper()
    if not closed.ok:
        return {"ok": False, "stage": "close"}
    return {"ok": True, "grasp": (cx, cy, cz)}
'''


class TestSynthesize(unittest.TestCase):
    def _motif(self):
        return mine_lifted([mk_trace(t, PICK) for t in ("A/0", "B/0", "C/0")],
                           min_len=5, max_len=5,
                           min_episode_coverage=3, min_task_coverage=3)[0]

    def test_valid_macro_passes(self):
        mc = synthesize_macro(self._motif(), ["src1", "src2"], "pick_object",
                              ["object_name"], llm=lambda p: f"```python\n{GOOD_MACRO}```")
        self.assertEqual(mc.name, "pick_object")
        self.assertIn("PRE:", mc.pre_line)
        self.assertIn("EFF:", mc.eff_line)

    def test_import_rejected_then_fixed(self):
        bad = "import os\n" + GOOD_MACRO
        calls = {"n": 0}
        def llm(p):
            calls["n"] += 1
            return f"```python\n{bad}```" if calls["n"] == 1 else f"```python\n{GOOD_MACRO}```"
        mc = synthesize_macro(self._motif(), ["s"], "pick_object", ["object_name"], llm=llm)
        self.assertEqual(calls["n"], 2)
        self.assertEqual(mc.name, "pick_object")

    def test_nonwhitelist_name_rejected(self):
        evil = GOOD_MACRO.replace("close_gripper()", "os_system()")
        with self.assertRaises(MacroValidationError):
            validate_macro(evil, "pick_object")

    def test_missing_conditions_rejected(self):
        noline = GOOD_MACRO.replace("PRE: gripper empty; object visible from agentview", "")
        with self.assertRaises(MacroValidationError):
            validate_macro(noline, "pick_object")


if __name__ == "__main__":
    unittest.main()
