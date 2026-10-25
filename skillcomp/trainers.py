"""训练器：三选一裁决的"继续训 / 拆分"原语 → openpi 训练任务。

v1 产出**任务描述**（命令行 + 预期产物路径），不直接执行——训练在
GPU 机上由执行模块发出，且每个任务要走准入门后才可能入库。
openpi 的训练入口是 scripts/train.py <config> --exp-name <名>；
具体 config 名由调用方传（π0.5 的 LIBERO LoRA 配置以 openpi 仓为准，
不在这里写死一个可能错的名字）。
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .skill import SkillCard


@dataclass
class TrainJob:
    kind: str                 # "refine" | "split"
    skill: str
    new_version: int
    command: list[str]        # 在 openpi_root 下执行
    data_group: str           # 本次用的数据组标识
    expected_adapter: str     # 训练产物（新 LoRA）的预期路径
    notes: str = ""
    parent: dict = field(default_factory=dict)  # 出身：从哪个版本/底座分叉


def _train_cmd(config_name: str, exp_name: str, extra: list[str]) -> list[str]:
    return ["uv", "run", "scripts/train.py", config_name,
            f"--exp-name={exp_name}", *extra]


def refine(card: SkillCard, data_group: str, config_name: str,
           extra_args: list[str] | None = None) -> TrainJob:
    """继续训：从该技能当前的 LoRA 续训，产出 vN+1 候选。旧版本不动。"""
    if card.carrier != "lora":
        raise ValueError(f"refine 训练器只管 lora 载体，{card.name} 是 {card.carrier}")
    exp = f"{card.name}_v{card.version + 1}_{data_group}"
    extra = list(extra_args or [])
    if card.carrier_meta.get("adapter_path"):
        extra.append(f"--resume-adapter={card.carrier_meta['adapter_path']}")
    return TrainJob(
        kind="refine", skill=card.name, new_version=card.version + 1,
        command=_train_cmd(config_name, exp, extra), data_group=data_group,
        expected_adapter=f"checkpoints/{config_name}/{exp}",
        parent={"version": card.version,
                "adapter": card.carrier_meta.get("adapter_path", "")})


def split(parent: SkillCard, new_skill: str, data_group: str, config_name: str,
          new_pre: str, extra_args: list[str] | None = None) -> TrainJob:
    """拆分：从父技能的 checkpoint 分叉一块新 LoRA，配新数据组和新的使用条件。"""
    if parent.carrier != "lora":
        raise ValueError(f"split 训练器只管 lora 载体，{parent.name} 是 {parent.carrier}")
    if not new_pre.strip():
        raise ValueError("拆分必须写明新技能的使用条件（PRE）——这是分家的全部意义")
    exp = f"{new_skill}_v1_{data_group}"
    return TrainJob(
        kind="split", skill=new_skill, new_version=1,
        command=_train_cmd(config_name, exp, list(extra_args or [])),
        data_group=data_group,
        expected_adapter=f"checkpoints/{config_name}/{exp}",
        notes=f"new PRE: {new_pre}",
        parent={"from_skill": parent.name, "version": parent.version,
                "adapter": parent.carrier_meta.get("adapter_path", "")})
