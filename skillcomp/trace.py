"""轨迹协议 v0。

一条轨迹 = 一次任务执行；一步 = 一次技能调用。
谓词用接地字符串表示，如 "drawer_open" / "in_drawer(cup)"。
这份格式同时是：harness 适配器的输出规范、测量打点格式、合成器的输入。
字段定义见 doc/active/trace_format_v0.md。
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Step:
    skill: str
    args: tuple[str, ...] = ()
    pre_snapshot: frozenset[str] = frozenset()
    post_snapshot: frozenset[str] = frozenset()
    success: bool = True
    duration_s: float = 0.0
    llm_calls: int = 0  # 这一步消耗的大模型调用数（harness 侧填写）

    def key(self) -> tuple:
        """挖掘重复子序列时的身份：技能名 + 参数。"""
        return (self.skill, self.args)


@dataclass
class Trace:
    task: str
    steps: list[Step] = field(default_factory=list)
    success: bool = False
    meta: dict = field(default_factory=dict)  # 来源 harness、episode 编号、seed 等

    def key_seq(self) -> tuple[tuple, ...]:
        return tuple(s.key() for s in self.steps)

    # ---------- 序列化 ----------
    def to_dict(self) -> dict:
        d = asdict(self)
        for s in d["steps"]:
            s["args"] = list(s["args"])
            s["pre_snapshot"] = sorted(s["pre_snapshot"])
            s["post_snapshot"] = sorted(s["post_snapshot"])
        return d

    @staticmethod
    def from_dict(d: dict) -> "Trace":
        steps = [
            Step(
                skill=s["skill"],
                args=tuple(s["args"]),
                pre_snapshot=frozenset(s["pre_snapshot"]),
                post_snapshot=frozenset(s["post_snapshot"]),
                success=s["success"],
                duration_s=s.get("duration_s", 0.0),
                llm_calls=s.get("llm_calls", 0),
            )
            for s in d["steps"]
        ]
        return Trace(task=d["task"], steps=steps, success=d["success"], meta=d.get("meta", {}))


def save_jsonl(traces: Iterable[Trace], path: str | Path) -> None:
    with open(path, "w") as f:
        for t in traces:
            f.write(json.dumps(t.to_dict(), ensure_ascii=False) + "\n")


def load_jsonl(path: str | Path) -> list[Trace]:
    out = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(Trace.from_dict(json.loads(line)))
    return out
