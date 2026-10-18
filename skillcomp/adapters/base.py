"""harness 适配器接口。

接一个新 harness 只需要实现两件事：
1. export_traces：把它的执行日志翻译成 trace.Trace（谓词快照允许为空集，
   此时合成走 observed 模式，条件由快照统计近似）;
2. inject_catalog：把我们的目录（含宏）注入它的技能可见面
   （提示词里的技能清单 / 符号规划器的算子集 / API 注册表）。

v0 只有接口与玩具实现；ASPIRE / RPent / RoboHarn-Evo 适配器随复现工作各自落地。
"""
from __future__ import annotations

from typing import Protocol

from ..skill import Library
from ..trace import Trace


class HarnessAdapter(Protocol):
    name: str

    def export_traces(self, raw_log_path: str) -> list[Trace]: ...
    def inject_catalog(self, lib: Library) -> None: ...
