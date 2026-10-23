"""追加式版本化技能库 + 载体字段的单测（防遗忘是架构性质，不是训练技巧）。"""
import pytest

from skillcomp.skill import Library, SkillCard
from skillcomp.executors import CodeMacroExecutor, VLAExecutor


def _card(version, carrier="code", **kw):
    return SkillCard(name="pick_object", kind="macro", version=version,
                     carrier=carrier, **kw)


def test_append_only_versions(tmp_path):
    lib = Library()
    lib.admit(_card(1))
    lib.admit(_card(2))
    with pytest.raises(ValueError):
        lib.admit(_card(2))        # 禁覆盖
    with pytest.raises(ValueError):
        lib.admit(_card(1))        # 禁倒退
    assert lib.get("pick_object").version == 2          # catalog 看最新
    assert lib.get_version("pick_object", (), 1).version == 1  # 旧版可回滚
    assert [c.version for c in lib.history("pick_object")] == [1, 2]
    assert len(lib.catalog()) == 1  # 目录按技能去重，只露最新
    p = tmp_path / "lib.json"
    lib.save(p)
    lib2 = Library.load(p)
    assert [c.version for c in lib2.history("pick_object")] == [1, 2]


def test_old_json_without_version_loads_as_v1(tmp_path):
    lib = Library()
    card = SkillCard(name="legacy", kind="macro")
    d = card.to_dict()
    d.pop("version"); d.pop("carrier"); d.pop("carrier_meta")
    import json
    p = tmp_path / "old.json"
    p.write_text(json.dumps([d]))
    loaded = Library.load(p)
    got = loaded.get("legacy")
    assert got.version == 1 and got.carrier == "code"


def test_executors_route_by_carrier():
    code_card = _card(1)
    lora_card = _card(1, carrier="lora",
                      carrier_meta={"backbone_id": "pi05_base", "adapter_path": "x"})
    assert CodeMacroExecutor().supports(code_card)
    assert not CodeMacroExecutor().supports(lora_card)
    vla = VLAExecutor(backbone_id="pi05_base")
    assert vla.supports(lora_card) and not vla.supports(code_card)
    with pytest.raises(NotImplementedError):
        vla.run(lora_card, {}, env=None)
