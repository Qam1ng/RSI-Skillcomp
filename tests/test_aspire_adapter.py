import unittest
from pathlib import Path

from skillcomp.adapters.aspire import export_trace

FIXTURE = Path(__file__).parent / "fixtures" / "aspire_run"


class TestAspireAdapter(unittest.TestCase):
    def test_export_real_artifact(self):
        tr = export_trace(FIXTURE)
        # 任务级
        self.assertTrue(tr.success)
        self.assertEqual(tr.meta["harness"], "aspire")
        self.assertEqual(tr.meta["termination_reason"], "task_succeeded")
        self.assertEqual(tr.meta["llm_turns"], 0)  # 录制示例程序，零大模型回合
        self.assertEqual(tr.task, "libero_object_swap/0")
        # 步级：顶层程序调用（这份工件里：open_gripper / localize_object / move_to_pose ...）
        self.assertGreater(len(tr.steps), 5)
        names = [s.skill for s in tr.steps]
        self.assertIn("open_gripper", names)
        self.assertIn("localize_object", names)
        self.assertIn("move_to_pose", names)
        # provider 子调用不得混入步级
        self.assertNotIn("sam3-segment-text", names)
        # 参数来自 call input.json
        loc = next(s for s in tr.steps if s.skill == "localize_object")
        self.assertIn("blue soup can", loc.args)
        self.assertIn("camera_name=agentview", loc.args)
        # 真实质感：任务成功，但存在步级失败（松爪与收尾撤离报 ok=false）——
        # 适配器必须如实转译，不得把任务级成功涂抹到步级
        self.assertEqual(len(tr.steps), 27)
        failed = [i for i, s in enumerate(tr.steps) if not s.success]
        self.assertEqual(failed, [24, 26])
        # observed 模式：快照为空
        self.assertTrue(all(not s.pre_snapshot and not s.post_snapshot for s in tr.steps))

    def test_roundtrip_jsonl(self):
        from skillcomp.trace import save_jsonl, load_jsonl
        import tempfile, os
        tr = export_trace(FIXTURE)
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, "t.jsonl")
            save_jsonl([tr], p)
            back = load_jsonl(p)[0]
            self.assertEqual(back.key_seq(), tr.key_seq())
            self.assertEqual(back.success, tr.success)


if __name__ == "__main__":
    unittest.main()
