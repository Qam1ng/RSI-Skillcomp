"""逐轮台账 v1：每技能在冻结尺子上的分数序列——"梯度"的库级那一层。

现状之前是"量完就扔"；台账把每次测量留成 JSONL，一行一次测量。
读 Δ 的唯一入口是 delta()：强制配噪声线，低于噪声线的差一律判 flat。
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import date
from pathlib import Path


@dataclass
class Entry:
    skill: str
    version: int
    battery: str
    passes: int
    total: int
    ts: str = field(default_factory=lambda: date.today().isoformat())
    margins: dict = field(default_factory=dict)   # 谓词裕度，连续量（别阈值化扔掉）
    cost: dict = field(default_factory=dict)      # {"rollouts": n, "gpu_s": x, "api_tokens": n}
    note: str = ""


def append(path: str | Path, e: Entry) -> None:
    with open(path, "a") as f:
        f.write(json.dumps(asdict(e), ensure_ascii=False) + "\n")


def read(path: str | Path) -> list[Entry]:
    p = Path(path)
    if not p.exists():
        return []
    return [Entry(**json.loads(line)) for line in p.read_text().splitlines() if line.strip()]


def series(entries: list[Entry], skill: str, battery: str | None = None) -> list[Entry]:
    """某技能的测量序列，按记录顺序。"""
    return [e for e in entries
            if e.skill == skill and (battery is None or e.battery == battery)]


def delta(entries: list[Entry], skill: str, floor: int, battery: str | None = None
          ) -> tuple[str, int]:
    """最近两次测量的变化：("up"|"down"|"flat", 原始差值)。

    floor 来自 Registry.require_floor()——没有噪声线不许调用本函数。
    |差| <= floor 一律 flat：低于噪声底的 Δ 不是信号（AXIS ±3 纪律）。
    """
    s = series(entries, skill, battery)
    if len(s) < 2:
        return ("flat", 0)
    raw = s[-1].passes - s[-2].passes
    if abs(raw) <= floor:
        return ("flat", raw)
    return ("up" if raw > 0 else "down", raw)


def spent(entries: list[Entry], skill: str | None = None) -> dict:
    """累计花费（预算分配的依据）。"""
    out: dict[str, float] = {}
    for e in entries:
        if skill is None or e.skill == skill:
            for k, v in e.cost.items():
                out[k] = out.get(k, 0) + v
    return out
