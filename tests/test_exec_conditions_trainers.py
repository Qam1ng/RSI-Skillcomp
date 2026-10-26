"""执行模块（注入替身 runner）、条件核查代码生成、训练器任务构造的单测。"""
import ast
import json

import pytest

from skillcomp import conditions, exec_aspire, trainers
from skillcomp.battery import Battery
from skillcomp.skill import SkillCard


BATTERY = Battery(name="pick@goal2", suite="libero_goal_task", task_id=2,
                  seeds=(56, 57, 58, 59, 60))


def test_run_battery_builds_contract_compliant_command_and_parses(tmp_path):
    prog = tmp_path / "prog.py"
    prog.write_text("report = {}\nprint(report)\n")
    calls = []

    def fake_runner(cmd):
        calls.append(cmd)
        if cmd[0] == "scp":
            return ""
        remote = cmd[2]
        if "run-batch" in remote:
            return "batch done"
        if "batch-results.jsonl" in remote:
            rows = [{"seed": s, "task_success": s != 58, "program_ok": True,
                     "termination_reason": "program_completed",
                     "run_dir": f"/data/x/{s:04d}/run-1"} for s in BATTERY.seeds]
            return "\n".join(json.dumps(r) for r in rows)
        if "program-result.json" in remote:
            return json.dumps({"stdout": "{'grasp_ok': True}"})
        raise AssertionError(remote)

    res = exec_aspire.run_battery(str(prog), BATTERY, "unit_out", runner=fake_runner)
    batch_cmd = calls[1][2]
    # 底盘契约：直调 venv 内的 cap-harness、带 LIBERO_CONFIG_PATH、seeded、冻结种子
    assert ".venv-libero/bin/cap-harness run-batch" in batch_cmd
    assert "LIBERO_CONFIG_PATH=" in batch_cmd and "uv run" not in batch_cmd
    assert "--seeds 56-60" in batch_cmd and "--init-mode seeded" in batch_cmd
    assert res.passes == 4 and res.total == 5
    assert res.stdout_reports[56] == "{'grasp_ok': True}"


def test_seed_spec_handles_gaps():
    assert exec_aspire._seed_spec((56, 57, 58)) == "56-58"
    assert exec_aspire._seed_spec((56, 58, 60)) == "56 58 60"


def test_emit_glue_checks_and_sandbox_rules():
    glue = conditions.emit_glue([
        ("pick_object", '"wine bottle"', "grasp"),
        ("place_into", '"bowl", held_below_m=float(grasp.get("below_grasp_m", 0.25))', "placed"),
    ])
    ast.parse(glue)                                  # 语法合法
    assert "import" not in glue                      # 沙箱规则
    # EFF 裕度是连续量，不是布尔
    assert 'report["margin_grasp_below_grasp_m"]' in glue
    assert 'report["margin_placed_release"]' in glue
    # place 的 PRE 引用上一个调用（pick）的承诺效果
    assert 'report.get("check_grasp_eff_grasped"' in glue
    # PRE 不满足时跳过执行而不是硬闯
    assert '"pre_violated"' in glue


def test_checked_program_compiles_with_real_macros():
    srcs = [open("macros/pick_object.py").read(), open("macros/place_into.py").read()]
    prog = conditions.checked_program(srcs, [
        ("pick_object", '"wine bottle"', "grasp"),
        ("place_into", '"bowl", held_below_m=float(grasp.get("below_grasp_m", 0.25))', "placed"),
    ])
    ast.parse(prog)


def _lora_card(version=3):
    return SkillCard(name="pick_object", kind="macro", carrier="lora", version=version,
                     carrier_meta={"backbone_id": "pi05_base",
                                   "adapter_path": "ckpt/pick_v3"})


def test_refine_job_continues_own_adapter():
    job = trainers.refine(_lora_card(), data_group="g7", config_name="CFG")
    assert job.kind == "refine" and job.new_version == 4
    assert "--resume-adapter=ckpt/pick_v3" in job.command
    assert job.parent["version"] == 3


def test_split_requires_new_pre():
    with pytest.raises(ValueError):
        trainers.split(_lora_card(), "pick_flat", "g8", "CFG", new_pre="")
    job = trainers.split(_lora_card(), "pick_flat", "g8", "CFG",
                         new_pre="object is flat; grasp via proposer")
    assert job.kind == "split" and job.new_version == 1
    assert job.parent["from_skill"] == "pick_object"


def test_trainers_reject_code_carrier():
    code_card = SkillCard(name="pick_object", kind="macro", carrier="code")
    with pytest.raises(ValueError):
        trainers.refine(code_card, "g", "CFG")


def test_collect_writes_ledger_and_blames_first_failed_skill(tmp_path):
    from skillcomp import collect
    from skillcomp.exec_aspire import BatchResult, SeedResult
    res = BatchResult(battery="pick@goal2", program="p.py")
    for s, ok in [(56, True), (57, False)]:
        res.results.append(SeedResult(seed=s, task_success=ok, program_ok=True,
                                      termination="x", run_dir=f"/r/{s}"))
    res.stdout_reports[56] = ("{'grasp_ok': True, 'grasp_stage': 'done',"
                              " 'margin_grasp_below_grasp_m': 0.11,"
                              " 'placed_ok': True, 'placed_stage': 'done'}")
    res.stdout_reports[57] = ("{'grasp_ok': True, 'grasp_stage': 'done',"
                              " 'placed_ok': False, 'placed_stage': 'move_place',"
                              " 'check_placed_pre_holding': True}")
    plan = [("pick_object", "a", "grasp"), ("place_into", "b", "placed")]
    out = collect.from_batch(res, BATTERY, plan, {"pick_object": 5, "place_into": 3},
                             str(tmp_path / "l.jsonl"), str(tmp_path / "c.jsonl"))
    assert out == {"entries": 2, "cases": 1}
    from skillcomp import casestore, ledger
    entries = ledger.read(tmp_path / "l.jsonl")
    pick = [e for e in entries if e.skill == "pick_object"][0]
    assert pick.passes == 2 and pick.margins["margin_grasp_below_grasp_m"] == [0.11]
    case = casestore.read(tmp_path / "c.jsonl")[0]
    assert case.skill == "place_into" and case.stage == "move_place"
    assert case.kind == "in_envelope"  # PRE 满足却没兑现效果：技能分内的锅
