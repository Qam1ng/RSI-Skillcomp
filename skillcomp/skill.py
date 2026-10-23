"""技能卡 v0。

每条技能一张卡：名字、条件（前置/新增效果/删除效果/维持）、身体、出身。
- atomic：身体为空，执行时直接交给 harness 的执行器；
- macro：身体 = 成分调用序列（即回退指针——条件破了沿它拆回细粒度）。

v0 为接地版：宏绑定具体参数，不做参数泛化（泛化留给 v1，见 README 范围声明）。
条件来源两档：
- declared：卡上直接写明（玩具环境、SymSkill 式算子）；
- observed：从轨迹快照统计出来（真实 harness 适配时的近似），卡上标 origin="observed"。
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path


Call = tuple[str, tuple[str, ...]]  # (skill_name, args)


@dataclass
class SkillCard:
    name: str
    args: tuple[str, ...] = ()
    pre: frozenset[str] = frozenset()
    add: frozenset[str] = frozenset()
    delete: frozenset[str] = frozenset()
    maintain: frozenset[str] = frozenset()  # 执行全程必须保持为真的条件
    kind: str = "atomic"  # "atomic" | "macro"
    body: tuple[Call, ...] = ()  # macro 的成分序列；atomic 为空
    origin: str = "declared"  # "declared" | "observed"
    provenance: dict = field(default_factory=dict)  # 支持数、来源轨迹、成功统计
    carrier: str = "code"  # "code" | "lora"（共享底座+LoRA 的 VLA expert）
    carrier_meta: dict = field(default_factory=dict)  # lora: backbone_id/adapter_path/data_group/parent_version
    version: int = 1  # 追加式版本号；vN 与 vN+1 并存，禁覆盖

    def call_key(self) -> Call:
        return (self.name, self.args)

    # ---------- 序列化 ----------
    def to_dict(self) -> dict:
        d = asdict(self)
        d["args"] = list(self.args)
        for k in ("pre", "add", "delete", "maintain"):
            d[k] = sorted(d[k])
        d["body"] = [[n, list(a)] for n, a in self.body]
        return d

    @staticmethod
    def from_dict(d: dict) -> "SkillCard":
        return SkillCard(
            name=d["name"],
            args=tuple(d.get("args", ())),
            pre=frozenset(d["pre"]),
            add=frozenset(d["add"]),
            delete=frozenset(d["delete"]),
            maintain=frozenset(d.get("maintain", [])),
            kind=d["kind"],
            body=tuple((n, tuple(a)) for n, a in d.get("body", [])),
            origin=d.get("origin", "declared"),
            provenance=d.get("provenance", {}),
            carrier=d.get("carrier", "code"),
            carrier_meta=d.get("carrier_meta", {}),
            version=d.get("version", 1),
        )


class Library:
    """技能库：atomic + macro 的统一目录，**追加式版本化**。

    防遗忘是架构性质：admit 只追加，vN 与 vN+1 并存，禁止覆盖同版本。
    harness 的规划者只看 catalog()（每技能最新版）；回滚 = 指回旧版本。
    """

    def __init__(self) -> None:
        self._versions: dict[Call, list[SkillCard]] = {}

    def admit(self, card: SkillCard) -> None:
        chain = self._versions.setdefault(card.call_key(), [])
        if any(c.version == card.version for c in chain):
            raise ValueError(
                f"禁止覆盖：{card.name} v{card.version} 已在库中（追加请用新版本号）")
        if chain and card.version <= max(c.version for c in chain):
            raise ValueError(
                f"版本必须递增：{card.name} 已有 v{max(c.version for c in chain)}")
        chain.append(card)

    def get(self, name: str, args: tuple[str, ...] = ()) -> SkillCard:
        return self._versions[(name, args)][-1]

    def get_version(self, name: str, args: tuple[str, ...], version: int) -> SkillCard:
        for c in self._versions[(name, args)]:
            if c.version == version:
                return c
        raise KeyError(f"{name} v{version} 不在库中")

    def history(self, name: str, args: tuple[str, ...] = ()) -> list[SkillCard]:
        return list(self._versions.get((name, args), []))

    def has(self, name: str, args: tuple[str, ...] = ()) -> bool:
        return (name, args) in self._versions

    def catalog(self) -> list[SkillCard]:
        return [chain[-1] for chain in self._versions.values()]

    def macros(self) -> list[SkillCard]:
        return [c for c in self.catalog() if c.kind == "macro"]

    # ---------- 持久化 ----------
    def save(self, path: str | Path) -> None:
        cards = [c for chain in self._versions.values() for c in chain]
        with open(path, "w") as f:
            json.dump([c.to_dict() for c in cards], f, ensure_ascii=False, indent=1)

    @staticmethod
    def load(path: str | Path) -> "Library":
        lib = Library()
        with open(path) as f:
            for d in json.load(f):
                lib.admit(SkillCard.from_dict(d))
        return lib
