"""执行模块：把"发一批评测、等它跑完、收回结果"做成管线部件。

此前批跑靠人在终端手敲 ssh——违反运行纪律（运行期环里只许有系统自己）。
本模块把底盘契约里的路径与环境变量固化成配置，通过 ssh 调 cap-harness，
阻塞等待后收回逐种子结果。远端执行可注入替身（runner），零 GPU 即可单测。
"""
from __future__ import annotations

import json
import shlex
import subprocess
from dataclasses import dataclass, field

from .battery import Battery


@dataclass(frozen=True)
class SubstrateConfig:
    """底盘怎么够得着。默认值 = 我们的 ucla 部署（见 macros/substrate_contract_aspire.md）。"""
    host: str = "ucla"
    aspire_root: str = "/data/qyan/skillcomp_work/ASPIRE"
    workdir: str = "/data/qyan/skillcomp_work"
    harness_bin: str = ".venv-libero/bin/cap-harness"   # 直调，不走 uv run（契约第 10 条）
    workers: int = 2
    env_prefix: str = "LIBERO_CONFIG_PATH={root}/.libero"  # 契约第 11 条


@dataclass
class SeedResult:
    seed: int
    task_success: bool
    program_ok: bool
    termination: str
    run_dir: str


@dataclass
class BatchResult:
    battery: str
    program: str
    results: list[SeedResult] = field(default_factory=list)
    stdout_reports: dict[int, str] = field(default_factory=dict)  # seed -> print(report) 原文

    @property
    def passes(self) -> int:
        return sum(r.task_success for r in self.results)

    @property
    def total(self) -> int:
        return len(self.results)


def _run(cmd: list[str]) -> str:
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
    if p.returncode != 0:
        raise RuntimeError(f"远端命令失败 rc={p.returncode}: {p.stderr[-500:]}")
    return p.stdout


def _seed_spec(seeds: tuple[int, ...]) -> str:
    s = sorted(seeds)
    if s == list(range(s[0], s[-1] + 1)):
        return f"{s[0]}-{s[-1]}"
    return " ".join(str(x) for x in s)


def load_batch(out_name: str, battery: Battery,
               cfg: SubstrateConfig = SubstrateConfig(), runner=_run) -> BatchResult:
    """重读一个已经跑完的批次（不执行任何东西），供事后落账。"""
    return _collect_results(f"{cfg.workdir}/{out_name}", battery, out_name, cfg, runner)


def run_battery(program_local: str, battery: Battery, out_name: str,
                cfg: SubstrateConfig = SubstrateConfig(), runner=_run) -> BatchResult:
    """把本地程序发上底盘，在该评测组的全部冻结种子上跑一批，收回结果。"""
    remote_prog = f"{cfg.workdir}/{out_name}.py"
    runner(["scp", "-q", program_local, f"{cfg.host}:{remote_prog}"])

    out_root = f"{cfg.workdir}/{out_name}"
    env = cfg.env_prefix.format(root=cfg.aspire_root)
    remote = (
        f"cd {cfg.aspire_root} && {env} {cfg.harness_bin} run-batch"
        f" --benchmark {battery.benchmark} --suite {battery.suite}"
        f" --task-id {battery.task_id} --seeds {_seed_spec(battery.seeds)}"
        f" --program {remote_prog} --output-root {out_root}"
        f" --init-mode seeded --no-videos --workers {cfg.workers}"
        f" --summary {out_root}/summary.json"
    )
    runner(["ssh", cfg.host, remote])
    return _collect_results(out_root, battery, program_local, cfg, runner)


def _collect_results(out_root: str, battery: Battery, program: str,
                     cfg: SubstrateConfig, runner) -> BatchResult:
    raw = runner(["ssh", cfg.host, f"cat {shlex.quote(out_root)}/batch-results.jsonl"])
    res = BatchResult(battery=battery.name, program=program)
    for line in raw.splitlines():
        if not line.strip():
            continue
        d = json.loads(line)
        res.results.append(SeedResult(
            seed=d["seed"], task_success=bool(d["task_success"]),
            program_ok=bool(d.get("program_ok", False)),
            termination=d.get("termination_reason", ""), run_dir=d["run_dir"]))
    res.results.sort(key=lambda r: r.seed)

    # 程序里 print(report) 的原文（条件核查的裕度就在这里面）
    for r in res.results:
        try:
            out = runner(["ssh", cfg.host,
                          f"cat {shlex.quote(r.run_dir)}/source/program-result.json"])
            res.stdout_reports[r.seed] = json.loads(out).get("stdout", "")
        except (RuntimeError, json.JSONDecodeError):
            res.stdout_reports[r.seed] = ""
    return res
