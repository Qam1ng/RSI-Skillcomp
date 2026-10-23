"""Context Assembly v1：给裁决者组装上下文——Q1 的实验面，策略可插拔。

v1 规则版：按技能过滤 → 最近优先 → 按 (stage, kind) 去重 → 预算内装箱。
进上下文的是"裕度 + 诊断"，不是光秃秃的成败（信号分辨率纪律）。
"""
from __future__ import annotations

from .casestore import Case


def render_case(c: Case) -> str:
    scene = ", ".join(f"{k}={v}" for k, v in sorted(c.scene.items())) or "-"
    fix = f" | fix: {c.fix}" if c.fix else ""
    return (f"[{c.ts}] {c.task} seed{c.seed} {c.skill} v{c.version} "
            f"died@{c.stage} kind={c.kind} scene({scene}) | {c.diagnosis}{fix}")


def assemble(cases: list[Case], skill: str, budget_chars: int = 4000,
             header: str = "") -> str:
    """选最相关的病历装进预算。返回拼好的上下文文本。

    选择规则（v1，预注册）：该技能的案例，最近优先；同 (stage, kind) 只留
    最新一条（代表性覆盖优于数量）；塞满预算即停。
    """
    mine = [c for c in cases if c.skill == skill]
    mine.reverse()  # 最近优先（append 顺序即时间序）
    seen: set[tuple[str, str]] = set()
    picked: list[Case] = []
    for c in mine:
        key = (c.stage, c.kind)
        if key in seen:
            continue
        seen.add(key)
        picked.append(c)
    lines = [header] if header else []
    used = len(header)
    for c in picked:
        line = render_case(c)
        if used + len(line) > budget_chars:
            break
        lines.append(line)
        used += len(line)
    return "\n".join(lines)
