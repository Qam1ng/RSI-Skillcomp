"""ASPIRE 适配器（骨架）。

输入：cap-harness 的运行目录（见 ASPIRE docs/run-artifacts.md）：
  run.json       身份/任务/种子/采集设置
  outcome.json   task_success、termination_reason、timing 分桶、wall_duration_s
  trace/events.jsonl  程序与 provider 的 span（父子链接、类型化 I/O）——技能调用层
  episode/steps.jsonl 逐仿真 tick 记录（太细，不作为 Step 来源）

输出：trace_format_v0 的 Trace。
谓词快照 ASPIRE 不提供 → 本适配器产 observed 模式轨迹（快照留空），
条件由合成器的 observed 档近似，或后续从 episode 记录离线推导。

状态：骨架。span→Step 的字段级映射等第一份真实工件（闸 2）落地后对表填写，
不预先猜字段名（规矩：索引→语义映射从代码/数据导出）。
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

    @property
    def task_success(self) -> bool:
        return bool(self.outcome["task_success"])

    @property
    def termination_reason(self) -> str:
        return self.outcome["termination_reason"]

    def iter_events(self):
        p = self.root / "trace" / "events.jsonl"
        with open(p) as f:
            for line in f:
                line = line.strip()
                if line:
                    yield json.loads(line)


def export_trace(run_dir: str | Path) -> Trace:
    """运行目录 → Trace（observed 模式：谓词快照为空）。

    TODO(闸2后): 从 trace/events.jsonl 的程序 span 提取
      - 技能名/参数（span 的类型化输入）
      - 每个调用的成败与耗时（span_end）
      - llm_calls（agent 驱动的运行里来自 model-trace span；录制示例程序为 0）
    字段名以真实工件为准，缺字段必须 fail loudly，不静默兜底。
    """
    rd = AspireRunDir(run_dir)
    raise NotImplementedError(
        "span→Step 映射待第一份真实工件对表后填写；"
        f"目录已可读: task_success={rd.task_success}, "
        f"termination={rd.termination_reason}"
    )
