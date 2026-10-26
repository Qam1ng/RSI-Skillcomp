"""VLA 评测执行模块：π0.5 在 LIBERO 上的"起服务→发评测→收结果"。

与 exec_aspire 同一纪律：路径与环境变量固化成配置、命令由模块构造、
远端执行可注入替身。跑通过的实配见 doc/active/substrate_contract_openpi.md。
"""
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class OpenpiConfig:
    host: str = "ucla"
    openpi_root: str = "/data/qyan/skillcomp_work/openpi"
    ckpt_dir: str = ("/home/qyan/.cache/openpi/openpi-assets/checkpoints/pi05_libero")
    policy_config: str = "pi05_libero"
    server_gpu: int = 1
    server_port: int = 8000
    client_gpu: int = 2
    libero_config_path: str = "/data/qyan/skillcomp_work/openpi/.libero_client"
    out_root: str = "/data/qyan/skillcomp_work"


def server_command(cfg: OpenpiConfig = OpenpiConfig()) -> str:
    """策略服务端的远端启动命令（阻塞式；调用方自行决定 nohup/监控）。"""
    return (f"cd {cfg.openpi_root} && CUDA_VISIBLE_DEVICES={cfg.server_gpu} "
            f"uv run scripts/serve_policy.py policy:checkpoint "
            f"--policy.config={cfg.policy_config} --policy.dir={cfg.ckpt_dir}")


def eval_command(suite: str, trials_per_task: int, out_name: str,
                 cfg: OpenpiConfig = OpenpiConfig()) -> str:
    """评测客户端的远端命令。LIBERO 配置必须预先写好（契约第 3 条），
    否则首次导入会交互式卡死。"""
    return (
        f"cd {cfg.openpi_root} && "
        f"source examples/libero/.venv/bin/activate && "
        f"export PYTHONPATH=$PWD/third_party/libero && "
        f"export MUJOCO_GL=egl PYOPENGL_PLATFORM=egl EGL_PLATFORM=device && "
        f"export CUDA_VISIBLE_DEVICES={cfg.client_gpu} "
        f"MUJOCO_EGL_DEVICE_ID={cfg.client_gpu} && "
        f"export LIBERO_CONFIG_PATH={cfg.libero_config_path} && "
        f"python examples/libero/main.py "
        f"--args.task-suite-name {suite} "
        f"--args.num-trials-per-task {trials_per_task} "
        f"--args.video-out-path {cfg.out_root}/{out_name}/videos"
    )


@dataclass
class EvalResult:
    suite: str
    successes: int
    total: int
    per_task: dict[str, tuple[int, int]]   # 任务名 -> (成, 回合)

    @property
    def rate(self) -> float:
        return self.successes / self.total if self.total else 0.0


def parse_log(log_text: str, suite: str, trials_per_task: int) -> EvalResult:
    """从评测客户端日志恢复逐任务成败。

    日志形态（openpi examples/libero/main.py）：每个任务开始处打一行
    "Task: <名字>"，每集结束累计打 "# successes: N (xx.x%)"。
    """
    per_task: dict[str, tuple[int, int]] = {}
    task, start_succ, latest = None, 0, 0
    episodes_in_task = 0
    for line in log_text.splitlines():
        m = re.search(r"Task: (.+)$", line)
        if m:
            if task is not None:
                per_task[task] = (latest - start_succ, episodes_in_task)
            task, start_succ, episodes_in_task = m.group(1).strip(), latest, 0
            continue
        m = re.search(r"# successes: (\d+)", line)
        if m:
            latest = int(m.group(1))
            episodes_in_task += 1
    if task is not None:
        per_task[task] = (latest - start_succ, episodes_in_task)
    total = sum(n for _, n in per_task.values())
    return EvalResult(suite=suite, successes=latest, total=total, per_task=per_task)


def run_eval(suite: str, trials_per_task: int, out_name: str,
             cfg: OpenpiConfig = OpenpiConfig(), runner=None) -> EvalResult:
    """阻塞式跑一片评测并解析。长评测（全量 Gate 1）建议由调用方
    把 eval_command 放后台、完后用 parse_log 收账。"""
    def default_runner(cmd: list[str]) -> str:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
        if p.returncode != 0:
            raise RuntimeError(f"远端命令失败 rc={p.returncode}: {p.stderr[-500:]}")
        return p.stdout
    r = runner or default_runner
    log = f"{cfg.out_root}/{out_name}.log"
    r(["ssh", cfg.host,
       f"bash -c '{eval_command(suite, trials_per_task, out_name, cfg)}' > {log} 2>&1; cat {log}"])
    text = r(["ssh", cfg.host, f"cat {log}"])
    return parse_log(text, suite, trials_per_task)
