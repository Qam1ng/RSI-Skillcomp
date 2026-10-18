"""合成器：把验证过的连续技能序列并成一个大技能（宏）。

运算法则（经典宏算子的顺序合成，接地版）：
  对序列 o1..on，各带 (pre_i, add_i, del_i)：
  - 新前置 = 第一步的前置 ∪ 后面各步需要、但之前没被造出来的条件；
  - 新效果 = 整段跑完的净增/净删；
  - 若某步的前置被更早一步删掉且未重建 → 序列不可合成（IncompatibleComposition）。

挖掘：在成功轨迹里数反复出现的连续子序列（n-gram），过三道准入门：
  支持数 ≥ min_support、所有出现全程成功、合成在代数上合法。
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass

from .skill import SkillCard, Library, Call
from .trace import Trace


class IncompatibleComposition(Exception):
    pass


def compose_declared(cards: list[SkillCard], name: str) -> SkillCard:
    """按声明的条件合成宏。条件不兼容时抛 IncompatibleComposition。"""
    if len(cards) < 2:
        raise ValueError("合成至少需要两步")
    pre: set[str] = set(cards[0].pre)
    established: set[str] = set(cards[0].add)   # 到目前为止净新增
    destroyed: set[str] = set(cards[0].delete)  # 到目前为止净删除
    for c in cards[1:]:
        # 这一步需要、但之前既没新增也不属于已承诺前置的条件 → 上提为宏前置
        for p in c.pre:
            if p in destroyed:
                raise IncompatibleComposition(
                    f"{c.name}{c.args} 的前置 {p!r} 已被更早一步删除且未重建")
            if p not in established:
                pre.add(p)
        destroyed -= c.add
        established -= c.delete
        established |= c.add
        destroyed |= c.delete
    # 宏的前置里被整段净删除的条件不冲突（先用后删是合法的）
    maintain = frozenset().union(*(c.maintain for c in cards)) if cards else frozenset()
    return SkillCard(
        name=name,
        args=(),
        pre=frozenset(pre),
        add=frozenset(established),
        delete=frozenset(destroyed),
        maintain=maintain,
        kind="macro",
        body=tuple(c.call_key() for c in cards),
        origin="declared",
    )


def compose_observed(occurrences: list[list], name: str, body: tuple[Call, ...]) -> SkillCard:
    """从轨迹快照近似合成（真实 harness 适配用）。

    occurrences: 每次出现对应的 Step 列表。
    前置 = 各次出现第一步 pre 快照的交集；
    净增 = 各次出现 (末步 post − 首步 pre) 的交集；净删同理。
    """
    pres, adds, dels = [], [], []
    for steps in occurrences:
        first_pre = steps[0].pre_snapshot
        last_post = steps[-1].post_snapshot
        pres.append(set(first_pre))
        adds.append(set(last_post) - set(first_pre))
        dels.append(set(first_pre) - set(last_post))
    inter = lambda sets: frozenset(set.intersection(*sets)) if sets else frozenset()
    return SkillCard(
        name=name, args=(),
        pre=inter(pres), add=inter(adds), delete=inter(dels),
        kind="macro", body=body, origin="observed",
        provenance={"support": len(occurrences)},
    )


# ---------------- 挖掘 ----------------

@dataclass
class MacroCandidate:
    seq: tuple[Call, ...]
    support: int
    occurrences: list[list]  # 每次出现的 Step 列表


def mine_candidates(
    traces: list[Trace],
    min_len: int = 2,
    max_len: int = 5,
    min_support: int = 3,
) -> list[MacroCandidate]:
    """在成功轨迹里挖反复出现、全程成功的连续子序列。"""
    counts: Counter[tuple] = Counter()
    occ: dict[tuple, list] = defaultdict(list)
    for t in traces:
        if not t.success:
            continue
        steps = t.steps
        n = len(steps)
        for L in range(min_len, min(max_len, n) + 1):
            for i in range(n - L + 1):
                window = steps[i : i + L]
                if not all(s.success for s in window):
                    continue
                key = tuple(s.key() for s in window)
                counts[key] += 1
                occ[key].append(list(window))
    out = [
        MacroCandidate(seq=k, support=c, occurrences=occ[k])
        for k, c in counts.items()
        if c >= min_support
    ]
    # 长的优先、支持数高的优先
    out.sort(key=lambda m: (len(m.seq), m.support), reverse=True)
    return out


def _macro_name(seq: tuple[Call, ...]) -> str:
    parts = []
    for skill, args in seq:
        parts.append(skill if not args else f"{skill}[{','.join(args)}]")
    return "macro__" + "__".join(parts)


def propose_macros(
    traces: list[Trace],
    library: Library,
    min_len: int = 2,
    max_len: int = 5,
    min_support: int = 3,
    max_new: int = 3,
) -> list[SkillCard]:
    """挖掘 → 合成 → 准入。返回本轮新收进库的宏。

    贪心不重叠：收下一个长宏后，跳过它的子串候选。
    """
    admitted: list[SkillCard] = []
    covered: set[tuple] = set()
    for cand in mine_candidates(traces, min_len, max_len, min_support):
        if len(admitted) >= max_new:
            break
        name = _macro_name(cand.seq)
        if library.has(name):
            continue
        # 是已收宏的子串则跳过
        if any(_is_subseq(cand.seq, big) for big in covered):
            continue
        try:
            cards = [library.get(s, a) for s, a in cand.seq]
        except KeyError:
            continue  # 序列里有库外技能（例如嵌套宏展开前的旧名），跳过
        if all(c.origin == "declared" for c in cards):
            try:
                card = compose_declared(cards, name)
            except IncompatibleComposition:
                continue
        else:
            card = compose_observed(cand.occurrences, name, cand.seq)
        card.provenance.update({"support": cand.support, "n_steps": len(cand.seq)})
        library.admit(card)
        admitted.append(card)
        covered.add(cand.seq)
    return admitted


def _is_subseq(small: tuple, big: tuple) -> bool:
    n, m = len(small), len(big)
    if n > m:
        return False
    return any(big[i : i + n] == small for i in range(m - n + 1))
