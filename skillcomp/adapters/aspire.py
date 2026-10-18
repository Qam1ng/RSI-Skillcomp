"""ASPIRE 适配器。

输入：cap-harness 的运行目录（ASPIRE docs/run-artifacts.md，schema 1.0，
字段映射对照真实工件核定于 2026-10-18，样本见 tests/fixtures/aspire_run）：

  run.json             benchmark / suite / task_id / task_name / seed / status
  outcome.json         task_success / termination_reason / wall_duration_s / timing
  trace/events.jsonl   span 流。顶层 program span（parent_id 为空）= 一次技能调用：
                         span_start 给 name；span_end 给 ok 与 duration_s
  trace/calls/call-NNNNNN-<slug>/input.json
                       与 span-NNNNNN 同号，含 args 与 kwargs
  trace/model/turns.jsonl
                       大模型回合（录制示例程序为 0 行；agent 驱动的运行>0）

输出：trace_format_v0 的 Trace（observed 模式：谓词快照为空——ASPIRE 不产谓词）。

纪律：字段缺失一律 fail loudly，不静默兜底。
"""
from __future__ import annotations

import json
from pathlib import Path

from ..trace import Trace, Step


class AspireRunDir:
    """一个 cap-harness 运行目录的只读视图。"""

    def __init__(self, run_dir: str | Path):
        self.root = Path(run_dir)
        self.run = json.loads((self.root / "run.json").read_text())
        self.outcome = json.loads((self.root / "outcome.json").read_text())
        if self.run["status"] != "finalized":
            raise ValueError(f"运行未定稿: status={self.run['status']!r}（不消费半成品）")

    @property
    def task_success(self) -> bool:
        return bool(self.outcome["task_success"])

    @property
    def termination_reason(self) -> str:
        return self.outcome["termination_reason"]

    def iter_events(self):
        with open(self.root / "trace" / "events.jsonl") as f:
            for line in f:
                line = line.strip()
                if line:
                    yield json.loads(line)

    def llm_turns(self) -> int:
        p = self.root / "trace" / "model" / "turns.jsonl"
        if not p.exists():
            return 0
        with open(p) as f:
            return sum(1 for line in f if line.strip())

    def call_args(self, span_id: str) -> tuple[str, ...]:
        """span-NNNNNN → trace/calls/call-NNNNNN-*/input.json → 接地参数串。"""
        num = span_id.rsplit("-", 1)[-1]
        matches = list((self.root / "trace" / "calls").glob(f"call-{num}-*/input.json"))
        if not matches:
            raise FileNotFoundError(f"span {span_id} 没有对应的 call input.json")
        d = json.loads(matches[0].read_text())
        out: list[str] = []
        for a in d.get("args", []):
            out.append(a if isinstance(a, str) else json.dumps(a, sort_keys=True))
        for k in sorted(d.get("kwargs", {})):
            v = d["kwargs"][k]
            out.append(f"{k}={v if isinstance(v, str) else json.dumps(v, sort_keys=True)}")
        return tuple(out)


def export_trace(run_dir: str | Path) -> Trace:
    """运行目录 → Trace。

    Step = 顶层 program span（parent_id 为空）。provider 子调用（sam3/curobo 等）
    不成为 Step——它们是技能内部的实现细节，决策点只数程序层调用。
    """
    rd = AspireRunDir(run_dir)
    open_spans: dict[str, dict] = {}
    steps: list[Step] = []
    for ev in rd.iter_events():
        if ev.get("category") != "program" or ev.get("parent_id") is not None:
            continue
        sid = ev["span_id"]
        if ev["event"] == "span_start":
            if sid in open_spans:
                raise ValueError(f"span 重复开始: {sid}")
            open_spans[sid] = ev
        elif ev["event"] == "span_end":
            start = open_spans.pop(sid, None)
            if start is None:
                raise ValueError(f"span_end 无对应 start: {sid}")
            steps.append(
                Step(
                    skill=ev["name"],
                    args=rd.call_args(sid),
                    pre_snapshot=frozenset(),   # ASPIRE 不产谓词 → observed 模式
                    post_snapshot=frozenset(),
                    success=bool(ev["ok"]),
                    duration_s=float(ev.get("duration_s", 0.0)),
                    llm_calls=0,  # 程序层调用不含大模型；整次运行的回合数在 meta
                )
            )
    if open_spans:
        raise ValueError(f"存在未闭合的 span: {sorted(open_spans)}")
    return Trace(
        task=f'{rd.run["suite"]}/{rd.run["task_id"]}',
        steps=steps,
        success=rd.task_success,
        meta={
            "harness": "aspire",
            "benchmark": rd.run["benchmark"],
            "suite": rd.run["suite"],
            "task_id": rd.run["task_id"],
            "task_name": rd.run["task_name"],
            "seed": rd.run["seed"],
            "run_id": rd.run["run_id"],
            "termination_reason": rd.termination_reason,
            "wall_duration_s": rd.outcome.get("wall_duration_s"),
            "llm_turns": rd.llm_turns(),
            "predicate_source": "none(observed-mode)",
        },
    )
