"""测量层 + 店长的单测。验收标准来自 doc/active/pipeline_v3_alignment.md 第 3 步：
port1 的盘子案例应判 split，goal2 式圈内失败应判 refine，planner 失误应判 retry。
"""
import pytest

from skillcomp import battery, casestore, context, gate, ledger, triage
from skillcomp.casestore import Case


def _case(skill, kind, stage="grasp", seed=56, scene=None, **kw):
    pre_ok, eff_ok = {"in_envelope": (True, False),
                      "out_of_envelope": (False, False),
                      "planner": (True, True)}[kind]
    if kind == "planner":
        pre_ok, eff_ok = True, False  # planner 类也以失败收场，只是锅不在技能
    return Case(task="libero_goal_task/1", seed=seed, skill=skill, version=3,
                stage=stage, pre_ok=pre_ok, eff_ok=eff_ok, kind=kind,
                scene=scene or {}, **kw)


# ---------- battery ----------

def test_registry_freezes_batteries_and_requires_floor(tmp_path):
    reg = battery.Registry()
    b = battery.Battery(name="pick@goal2", suite="libero_goal_task", task_id=2,
                        seeds=(56, 57, 58, 59, 60))
    reg.register(b)
    reg.register(b)  # 重复登记同内容无害
    with pytest.raises(ValueError):  # 改种子 = 换尺子，必须换名
        reg.register(battery.Battery(name="pick@goal2", suite="libero_goal_task",
                                     task_id=2, seeds=(1, 2, 3)))
    with pytest.raises(KeyError):
        reg.require_floor("pick@goal2")  # 没测噪声线不许读 Δ
    reg.set_floor(battery.NoiseFloor(battery="pick@goal2", scores=[5, 4, 5], total=5))
    assert reg.require_floor("pick@goal2") == 1
    p = tmp_path / "reg.json"
    reg.save(p)
    assert battery.Registry.load(p).require_floor("pick@goal2") == 1


# ---------- ledger ----------

def test_ledger_delta_respects_noise_floor(tmp_path):
    p = tmp_path / "ledger.jsonl"
    for passes in (3, 4):
        ledger.append(p, ledger.Entry(skill="place_into", version=2, battery="place@goal2",
                                      passes=passes, total=5, cost={"rollouts": 5}))
    entries = ledger.read(p)
    assert ledger.delta(entries, "place_into", floor=1)[0] == "flat"   # +1 在噪声里
    assert ledger.delta(entries, "place_into", floor=0)[0] == "up"
    ledger.append(p, ledger.Entry(skill="place_into", version=3, battery="place@goal2",
                                  passes=1, total=5, cost={"rollouts": 5}))
    entries = ledger.read(p)
    assert ledger.delta(entries, "place_into", floor=1) == ("down", -3)
    assert ledger.spent(entries, "place_into") == {"rollouts": 15}


# ---------- casestore ----------

def test_classify_encodes_blame_stopping_rule():
    assert casestore.classify(pre_ok=True, eff_ok=False) == "in_envelope"
    assert casestore.classify(pre_ok=False, eff_ok=False) == "out_of_envelope"
    assert casestore.classify(True, True, planner_fault=True) == "planner"
    with pytest.raises(ValueError):
        casestore.classify(pre_ok=True, eff_ok=True)


def test_casestore_roundtrip_and_query(tmp_path):
    p = tmp_path / "cases.jsonl"
    casestore.append(p, _case("pick_object", "out_of_envelope",
                              scene={"object": "plate", "flat": True},
                              diagnosis="descend target below table"))
    casestore.append(p, _case("pick_object", "in_envelope", stage="lift"))
    cases = casestore.read(p)
    assert len(casestore.query(cases, skill="pick_object", kind="out_of_envelope")) == 1
    assert casestore.counts(cases, "pick_object")["in_envelope"] == 1


# ---------- triage：验收案例 ----------

def test_plate_failures_trigger_split():
    """port1 盘子战役：失败全部聚在扁平物（PRE 本不该放行）→ split。"""
    cases = [_case("pick_object", "out_of_envelope", seed=s,
                   scene={"object": "plate", "flat": True},
                   diagnosis="grasp z below table") for s in range(56, 61)]
    d = triage.decide("pick_object", cases)
    assert d.action == "split"
    assert d.evidence["cases"]["out_of_envelope"] == 5


def test_in_envelope_failures_trigger_refine():
    """goal2 式：PRE 满足却 EFF 崩（如缺 return 分支）→ refine。"""
    cases = [_case("place_into", "in_envelope", seed=s, stage="release")
             for s in (56, 57, 59)]
    assert triage.decide("place_into", cases).action == "refine"


def test_planner_faults_trigger_retry():
    cases = [_case("pick_object", "planner", seed=s) for s in (1, 2, 3)]
    assert triage.decide("pick_object", cases).action == "retry"


def test_insufficient_evidence_holds():
    cases = [_case("pour", "in_envelope")]
    assert triage.decide("pour", cases).action == "hold"
    assert triage.decide("ghost_skill", []).action == "hold"


def test_meeting_target_holds():
    cases = [_case("pick_object", "in_envelope", seed=s) for s in (1, 2, 3)]
    entries = [ledger.Entry(skill="pick_object", version=5, battery="pick@goal2",
                            passes=5, total=5)]
    d = triage.decide("pick_object", cases, entries=entries, target=5)
    assert d.action == "hold" and "R3" in d.reason


# ---------- context assembly ----------

def test_context_budget_and_dedup():
    cases = ([_case("pick_object", "out_of_envelope", seed=s,
                    scene={"object": "plate"}, diagnosis="below table")
              for s in range(56, 61)]
             + [_case("pick_object", "in_envelope", stage="lift", diagnosis="slip")])
    text = context.assemble(cases, "pick_object", budget_chars=4000)
    # 同 (stage, kind) 去重：5 条盘子案例只留最新 1 条，lift 案例保留
    assert text.count("below table") == 1 and "slip" in text
    tiny = context.assemble(cases, "pick_object", budget_chars=10)
    assert tiny == ""  # 预算装不下就不装，不截断半条


# ---------- gate ----------

def test_gate_record_and_evidence_budget():
    r = gate.GateRecord(skill="pick_object", version=6, battery="pick@goal2",
                        static_ok=True, exec_passes=5, exec_total=5)
    assert r.admitted
    assert not gate.GateRecord("x", 1, "b", True, 4, 5).admitted
    budget = gate.EvidenceBudget(max_rounds=2)
    budget.spend(); budget.spend()
    with pytest.raises(RuntimeError):
        budget.spend()
