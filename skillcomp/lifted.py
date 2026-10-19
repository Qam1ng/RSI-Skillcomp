"""升维挖掘：按技能名（忽略接地参数）找跨集、跨任务反复出现的连续段。

动机（2026-10-19 实测钦定）：25 集、3 任务、2 种作者的真实轨迹里，
技能名层的连续段（localize→get_state→move 等）覆盖 25/25 集，
而接地（带参数）层跨任务命中为 0 —— 复用的结构只存在于名字层。

本模块只负责"合什么"（动机 + 证据 + 参数角色摘要）；
"怎么合成代码"在 synthesize.py（一次性离线蒸馏 + 验证门）。
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from .trace import Trace


@dataclass
class ArgRole:
    """动机中某个调用位置的参数角色摘要（给合成提示用）。"""
    position: int                # 动机内第几个调用
    skill: str
    distinct_args: list[tuple]  # 该位置见过的接地参数（去重，截断）
    role: str                    # "constant" 恒定 | "varies" 跨例变化（候选参数/运行时计算）


@dataclass
class LiftedMotif:
    names: tuple[str, ...]
    episode_coverage: int        # 覆盖多少集（每集至多计一次）
    task_coverage: int           # 覆盖多少个不同任务
    tasks: list[str] = field(default_factory=list)
    occurrences: list[tuple] = field(default_factory=list)  # (trace_idx, start_idx)
    arg_roles: list[ArgRole] = field(default_factory=list)

    def describe(self) -> str:
        return (f"{' -> '.join(self.names)}  "
                f"[覆盖 {self.episode_coverage} 集 / {self.task_coverage} 任务]")


def mine_lifted(
    traces: list[Trace],
    min_len: int = 3,
    max_len: int = 8,
    min_episode_coverage: int = 3,
    min_task_coverage: int = 2,
    require_success_window: bool = True,
) -> list[LiftedMotif]:
    """在成功轨迹里挖技能名层的连续段。

    覆盖口径：每集每个动机至多计一次（防止单集内循环刷支持数）。
    跨任务下限 min_task_coverage 把"只属于一道题"的段滤掉——那种段是缓存不是结构。
    """
    ep_cov: Counter[tuple] = Counter()
    task_cov: dict[tuple, set] = defaultdict(set)
    occ: dict[tuple, list] = defaultdict(list)
    for ti, t in enumerate(traces):
        if not t.success:
            continue
        names = [s.skill for s in t.steps]
        seen_in_ep: set[tuple] = set()
        for L in range(min_len, min(max_len, len(names)) + 1):
            for i in range(len(names) - L + 1):
                if require_success_window and not all(s.success for s in t.steps[i:i + L]):
                    continue
                key = tuple(names[i:i + L])
                occ[key].append((ti, i))
                if key not in seen_in_ep:
                    ep_cov[key] += 1
                    task_cov[key].add(t.task)
                    seen_in_ep.add(key)
    out: list[LiftedMotif] = []
    for key, cov in ep_cov.items():
        if cov < min_episode_coverage or len(task_cov[key]) < min_task_coverage:
            continue
        out.append(LiftedMotif(
            names=key, episode_coverage=cov, task_coverage=len(task_cov[key]),
            tasks=sorted(task_cov[key]), occurrences=occ[key],
            arg_roles=_arg_roles(key, occ[key], traces),
        ))
    # 长的优先，再按覆盖
    out.sort(key=lambda m: (len(m.names), m.episode_coverage, m.task_coverage), reverse=True)
    return _drop_subsumed(out)


def _arg_roles(key: tuple, occurrences: list[tuple], traces: list[Trace],
               max_distinct: int = 4) -> list[ArgRole]:
    roles = []
    for pos in range(len(key)):
        vals = []
        for ti, start in occurrences[:50]:
            vals.append(traces[ti].steps[start + pos].args)
        distinct = list(dict.fromkeys(vals))
        role = "constant" if len(distinct) == 1 else "varies"
        roles.append(ArgRole(position=pos, skill=key[pos],
                             distinct_args=[_short(a) for a in distinct[:max_distinct]],
                             role=role))
    return roles


def _short(args: tuple, limit: int = 60) -> tuple:
    return tuple(a if len(a) <= limit else a[:limit] + "…" for a in args)


def _drop_subsumed(motifs: list[LiftedMotif]) -> list[LiftedMotif]:
    """丢掉"是更长动机的子串且覆盖没有更广"的候选。"""
    kept: list[LiftedMotif] = []
    for m in motifs:
        subsumed = any(
            len(k.names) > len(m.names)
            and _contains(k.names, m.names)
            and k.episode_coverage >= m.episode_coverage
            for k in kept
        )
        if not subsumed:
            kept.append(m)
    return kept


def _contains(big: tuple, small: tuple) -> bool:
    n, m = len(small), len(big)
    return any(big[i:i + n] == small for i in range(m - n + 1))


def motif_report(motifs: list[LiftedMotif], top: int = 10) -> str:
    lines = []
    for m in motifs[:top]:
        lines.append(m.describe())
        for r in m.arg_roles:
            if r.role == "varies":
                lines.append(f"    [{r.position}] {r.skill}: 参数跨例变化, 样本 {r.distinct_args[:2]}")
    return "\n".join(lines)
