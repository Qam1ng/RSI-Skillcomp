"""执行器：载体 → 怎么跑。

- CodeMacroExecutor：代码技能。实际执行走 harness 内注入（宏源码拼进程序，
  由 exec_aspire 发批），本类负责载体路由校验。
- VLAExecutor：共享 π0.5 底座 + 每技能一块 LoRA。推理走 openpi 的
  policy server（官方 scripts/serve_policy.py 起服务端，websocket 协议：
  送观测字典、收动作块）。本类实现客户端一侧；把动作块喂进环境的
  步进循环属于 harness 适配层（cap-harness 的 step API），单独接。
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
            "代码技能经注入程序在 harness 内执行（exec_aspire.run_battery）；"
            "本地直跑只用于玩具环境")


class VLAExecutor:
    """π0.5 expert 的推理客户端。

    服务端加载 pi05 底座 + 该技能的 LoRA adapter 后起 websocket 服务；
    本类按 openpi-client 协议连过去。观测字典的键随 openpi 的
    LIBERO 配置（图像、机器人状态、语言指令）。
    """
    carrier = "lora"

    def __init__(self, backbone_id: str = "pi05_base",
                 host: str = "127.0.0.1", port: int = 8000) -> None:
        self.backbone_id = backbone_id
        self.host = host
        self.port = port
        self._client = None

    def supports(self, card: SkillCard) -> bool:
        return (card.carrier == "lora"
                and card.carrier_meta.get("backbone_id") == self.backbone_id)

    def _connect(self):
        if self._client is None:
            try:
                from openpi_client import websocket_client_policy
            except ImportError as e:
                raise RuntimeError(
                    "缺 openpi-client 包（openpi 仓库 packages/openpi-client）。"
                    "装好 openpi 环境后本执行器即可用。") from e
            self._client = websocket_client_policy.WebsocketClientPolicy(
                host=self.host, port=self.port)
        return self._client

    def infer(self, observation: dict) -> dict:
        """送一帧观测，收一个动作块。服务端没起会在连接时报错。"""
        return self._connect().infer(observation)

    def run(self, card: SkillCard, args: dict, env) -> dict:
        if not self.supports(card):
            raise ValueError(f"载体不匹配: {card.name} carrier={card.carrier}")
        raise NotImplementedError(
            "动作块→环境步进的循环在 harness 适配层（cap-harness step API）——"
            "推理客户端已就绪（用 infer()），步进接入是 Phase 2 Gate 1 之后的接线")
