"""尺子登记册 v1：每技能一组冻结评测案例 + 该尺子的本底噪声。

规矩（预注册）：
- 尺子一旦登记即冻结：种子不换、不拿去训练；换尺子 = 新名字。
- Δ 必须配噪声线读：没有 NoiseFloor 的尺子，台账拒绝判显著。
- 噪声线来自同配置重复测量（floor = max-min），不许拍脑袋。
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path


@dataclass(frozen=True)
class Battery:
    name: str                      # 尺子名，如 "pick_object@goal2"
    suite: str                     # 如 "libero_goal_task"
    task_id: int
    seeds: tuple[int, ...]         # 冻结种子，永不训练
    benchmark: str = "libero-pro"
    notes: str = ""


@dataclass
class NoiseFloor:
    battery: str
    scores: list[int]              # 同配置重复测量的通过数
    total: int                     # 每次测量的案例数
    measured_at: str = ""          # 日期
    provenance: str = ""           # 工件路径
    floor: int = field(init=False)

    def __post_init__(self) -> None:
        if len(self.scores) < 2:
            raise ValueError("噪声线至少需要 2 次重复测量")
        self.floor = max(self.scores) - min(self.scores)


class Registry:
    """登记册：尺子 + 噪声线。文件即单一事实来源。"""

    def __init__(self) -> None:
        self.batteries: dict[str, Battery] = {}
        self.floors: dict[str, NoiseFloor] = {}

    def register(self, b: Battery) -> None:
        if b.name in self.batteries and self.batteries[b.name] != b:
            raise ValueError(f"尺子 {b.name} 已登记且内容不同——尺子冻结，换尺子请换名字")
        self.batteries[b.name] = b

    def set_floor(self, nf: NoiseFloor) -> None:
        if nf.battery not in self.batteries:
            raise KeyError(f"未登记的尺子: {nf.battery}")
        self.floors[nf.battery] = nf

    def require_floor(self, battery: str) -> int:
        if battery not in self.floors:
            raise KeyError(f"尺子 {battery} 没有本底噪声记录——先测噪声线再读 Δ")
        return self.floors[battery].floor

    # ---------- 持久化 ----------
    def save(self, path: str | Path) -> None:
        d = {
            "batteries": [asdict(b) | {"seeds": list(b.seeds)} for b in self.batteries.values()],
            "floors": [asdict(f) for f in self.floors.values()],
        }
        Path(path).write_text(json.dumps(d, ensure_ascii=False, indent=1))

    @staticmethod
    def load(path: str | Path) -> "Registry":
        reg = Registry()
        d = json.loads(Path(path).read_text())
        for b in d.get("batteries", []):
            b["seeds"] = tuple(b["seeds"])
            reg.register(Battery(**b))
        for f in d.get("floors", []):
            f.pop("floor", None)
            reg.set_floor(NoiseFloor(**f))
        return reg
