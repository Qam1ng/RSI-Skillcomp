"""执行器接口：载体 → 怎么跑。

- CodeMacroExecutor：代码宏。v1 实际执行走 harness 侧注入
  （tools/run_injected.sh 把宏源码拼进程序），本类负责接口校验。
- VLAExecutor：共享底座 + LoRA 的 expert。接口先立住，π0.5 实现
  等重整后的训练 codebase 接入（Phase 2 Gate 1 过后）。
"""
from __future__ import annotations

from typing import Protocol

from .skill import SkillCard


class SkillExecutor(Protocol):
    def supports(self, card: SkillCard) -> bool: ...
    def run(self, card: SkillCard, args: dict, env) -> dict: ...


class CodeMacroExecutor:
    carrier = "code"

    def supports(self, card: SkillCard) -> bool:
        return card.carrier == "code"

    def run(self, card: SkillCard, args: dict, env) -> dict:
        raise NotImplementedError(
            "v1 代码宏经 run_injected.sh 在 harness 内执行；本地直跑留给玩具环境")


class VLAExecutor:
    carrier = "lora"

    def __init__(self, backbone_id: str) -> None:
        self.backbone_id = backbone_id

    def supports(self, card: SkillCard) -> bool:
        return (card.carrier == "lora"
                and card.carrier_meta.get("backbone_id") == self.backbone_id)

    def run(self, card: SkillCard, args: dict, env) -> dict:
        raise NotImplementedError("等 π0.5 训练/推理 codebase（Phase 2 Gate 1）")
