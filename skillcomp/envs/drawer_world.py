"""玩具符号环境：抽屉-台面世界。端到端测试与演示用，不代表真实机器人。

谓词：drawer_open / drawer_closed / in_drawer(x) / on_counter(x) / holding(x) / hand_empty
原子技能（声明式条件）：
  open_drawer, close_drawer, pick_from_drawer(x), pick_from_counter(x),
  place_on_counter(x), place_in_drawer(x)
可注入故障：每技能独立失败率（失败=状态不变）；也可注入"抽屉自己关上"的结构意外。
"""
from __future__ import annotations

import random

from ..skill import SkillCard, Library
from ..trace import Step


def atomic_cards(items: list[str]) -> list[SkillCard]:
    cards = [
        SkillCard("open_drawer", (), frozenset({"drawer_closed"}),
                  frozenset({"drawer_open"}), frozenset({"drawer_closed"})),
        SkillCard("close_drawer", (), frozenset({"drawer_open"}),
                  frozenset({"drawer_closed"}), frozenset({"drawer_open"})),
    ]
    for x in items:
        cards += [
            SkillCard("pick_from_drawer", (x,),
                      frozenset({"drawer_open", f"in_drawer({x})", "hand_empty"}),
                      frozenset({f"holding({x})"}),
                      frozenset({f"in_drawer({x})", "hand_empty"})),
            SkillCard("pick_from_counter", (x,),
                      frozenset({f"on_counter({x})", "hand_empty"}),
                      frozenset({f"holding({x})"}),
                      frozenset({f"on_counter({x})", "hand_empty"})),
            SkillCard("place_on_counter", (x,),
                      frozenset({f"holding({x})"}),
                      frozenset({f"on_counter({x})", "hand_empty"}),
                      frozenset({f"holding({x})"})),
            SkillCard("place_in_drawer", (x,),
                      frozenset({f"holding({x})", "drawer_open"}),
                      frozenset({f"in_drawer({x})", "hand_empty"}),
                      frozenset({f"holding({x})"})),
        ]
    return cards


class DrawerWorld:
    """实现 runtime.Executor 协议。"""

    def __init__(self, items: list[str], fail_rate: float = 0.0, seed: int = 0):
        self.items = items
        self.fail_rate = fail_rate
        self.rng = random.Random(seed)
        self.lib = Library()
        for c in atomic_cards(items):
            self.lib.admit(c)
        self.mischief: list[str] = []  # 预排的结构意外队列，如 "close_drawer"
        self.reset()

    def reset(self) -> None:
        self._state: set[str] = {"drawer_closed", "hand_empty"}
        for x in self.items:
            self._state.add(f"in_drawer({x})")

    def state(self) -> frozenset[str]:
        return frozenset(self._state)

    def run(self, skill: str, args: tuple[str, ...]) -> Step:
        pre = self.state()
        card = self.lib.get(skill, args)
        applicable = card.pre <= pre
        fails = self.rng.random() < self.fail_rate
        ok = applicable and not fails
        if ok:
            self._state -= set(card.delete)
            self._state |= set(card.add)
        # 结构意外：本步执行后世界自己变
        if self.mischief:
            event = self.mischief.pop(0)
            if event == "close_drawer" and "drawer_open" in self._state:
                self._state.discard("drawer_open")
                self._state.add("drawer_closed")
        return Step(skill=skill, args=args, pre_snapshot=pre,
                    post_snapshot=self.state(), success=ok, llm_calls=0)


def plan_bfs(lib: Library, state: frozenset[str], goal: frozenset[str],
             max_depth: int = 12) -> list[tuple[str, tuple[str, ...]]] | None:
    """最小 BFS 规划器：把目录里的卡（含宏）当算子，返回最短计划。

    计划长度 = 决策点数。库里有宏时计划自然变短——这就是测量对象。
    规划器本身是研究无关的占位件：真实 harness 里这个角色由 LLM 扮演。
    """
    from collections import deque

    cards = lib.catalog()
    start = frozenset(state)
    if goal <= start:
        return []
    seen = {start}
    q: deque = deque([(start, [])])
    while q:
        st, plan = q.popleft()
        if len(plan) >= max_depth:
            continue
        for c in cards:
            if not c.pre <= st:
                continue
            nxt = frozenset((st - c.delete) | c.add)
            if nxt in seen:
                continue
            nplan = plan + [c.call_key()]
            if goal <= nxt:
                return nplan
            seen.add(nxt)
            q.append((nxt, nplan))
    return None
