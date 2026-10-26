#!/usr/bin/env python3
"""闸 3 计量驱动：Gemini(REST, 纯标准库) 驱动 ASPIRE 的"生成程序→跑→读工件→修"环。

范围刻意最小：单任务、单开发种子、<=N 轮；每轮 token 用量记入 meter.json。
不属于 skillcomp 包；是 ASPIRE 侧实验脚手架。

用法:
  GEMINI_API_KEY=... python3 aspire_gemini_driver.py \
    --aspire-root /path/ASPIRE --suite libero_goal_swap --task-id 0 --seed 51 \
    --task-language "..." --out /path/gate3 [--model gemini-flash-latest] [--max-rounds 3]
"""
import argparse, ast, json, os, re, subprocess, sys, time, urllib.request
from pathlib import Path

API = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"

RULES = """You are writing ONE Python program for the cap-harness Code-as-Policy runtime.
Rules:
- Use ONLY the public API documented below. No imports. The runtime provides all names.
- The program is plain top-level Python (no functions required), like a script.
- Build a `report = {}` dict and record booleans of each stage.
- Check `.ok` of every call before depending on its result; do not swallow failures silently.
- Positions are metric, frame "robot_base". Grasp from above: reuse the current end-effector
  quaternion for a top-down grasp as shown in the API doc patterns.
- Output ONLY a single ```python code block, nothing else.
"""


def gemini(model: str, key: str, parts: list[str]) -> tuple[str, dict]:
    body = json.dumps({"contents": [{"role": "user", "parts": [{"text": p} for p in parts]}]}).encode()
    req = urllib.request.Request(API.format(model=model, key=key), data=body,
                                 headers={"Content-Type": "application/json"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                d = json.loads(r.read())
            text = d["candidates"][0]["content"]["parts"][0]["text"]
            usage = d.get("usageMetadata", {})
            return text, usage
        except Exception as e:  # noqa: BLE001
            if attempt == 2:
                raise
            time.sleep(15 * (attempt + 1))
    raise RuntimeError("unreachable")


def macro_card(src: str) -> tuple[str, str]:
    """从宏源码提取 (函数名, 目录卡片文本)。卡片=签名+PRE/EFF+返回键，不含实现。"""
    tree = ast.parse(src)
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef))
    args = [a.arg for a in fn.args.args]
    defaults = fn.args.defaults
    for i, d in enumerate(defaults):
        args[len(args) - len(defaults) + i] += "=" + ast.unparse(d)
    doc = ast.get_docstring(fn) or ""
    doc_lines = [l.strip() for l in doc.splitlines()
                 if l.strip().startswith(("PRE:", "EFF:", "NOTE:"))]
    ret_keys: list[str] = []
    for node in ast.walk(fn):
        if isinstance(node, ast.Return) and isinstance(node.value, ast.Dict):
            for k in node.value.keys:
                if isinstance(k, ast.Constant) and k.value not in ret_keys:
                    ret_keys.append(k.value)
    card = (f"def {fn.name}({', '.join(args)})\n  "
            + "\n  ".join(doc_lines)
            + f"\n  returns dict with keys: {ret_keys} — check ['ok'] before proceeding.")
    return fn.name, card


def count_calls(code: str, macro_names: set[str]) -> tuple[int, int]:
    """agent 所写程序文本的决策点：(总调用数, 其中宏调用数)。解析失败记 (-1,-1)。"""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return -1, -1
    total = macro = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            total += 1
            if isinstance(node.func, ast.Name) and node.func.id in macro_names:
                macro += 1
    return total, macro


def extract_code(text: str) -> str:
    m = re.search(r"```python\n(.*?)```", text, re.S)
    if not m:
        raise ValueError("模型输出里没有 python 代码块")
    return m.group(1)


def run_episode(aspire: Path, suite: str, task_id: int, seed: int, program: Path, out: Path,
                osc: bool = False) -> Path:
    env_setup = (
        f'cd {aspire} && source .venv-libero/bin/activate && '
        f'export LIBERO_CONFIG_PATH="$PWD/.libero" TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1 '
        f'MUJOCO_GL=egl PYOPENGL_PLATFORM=egl EGL_PLATFORM=device '
        f'CUDA_VISIBLE_DEVICES=2 MUJOCO_EGL_DEVICE_ID=2 && '
    )
    if osc:
        env_setup += 'export CAP_LIBERO_CONTROLLER=OSC_POSE && '
    cam = ' --camera-width 256 --camera-height 256' if osc else ''
    cmd = (env_setup + f'cap-harness run --benchmark libero-pro --suite {suite} '
           f'--task-id {task_id} --seed {seed} --program {program} '
           f'--no-videos --output-root {out} --flat-run-dir{cam}')
    subprocess.run(["bash", "-c", cmd], check=False, capture_output=True, text=True, timeout=1800)
    runs = sorted((out / f"{seed:04d}").glob("run-*"), key=lambda p: p.name)
    if not runs:
        raise RuntimeError(f"没有产生运行目录: {out}/{seed:04d}")
    return runs[-1]


def failure_digest(run_dir: Path) -> str:
    outcome = json.loads((run_dir / "outcome.json").read_text())
    lines = [f"task_success={outcome['task_success']} termination={outcome['termination_reason']}"]
    for k in ("program_status", "program_error", "error"):
        if outcome.get(k):
            lines.append(f"{k}: {str(outcome[k])[:500]}")
    ev = run_dir / "trace" / "events.jsonl"
    if ev.exists():
        fails, names = [], []
        for line in open(ev):
            d = json.loads(line)
            if d.get("category") == "program" and d.get("parent_id") is None and d.get("event") == "span_end":
                names.append(f"{d['name']}:{'ok' if d['ok'] else 'FAIL'}")
                if not d["ok"]:
                    fails.append(d["name"])
        lines.append("call sequence: " + " -> ".join(names[:40]))
        if fails:
            lines.append("failed calls: " + ", ".join(fails))
        # 为每个失败的顶层调用附上其 output.json(含失败原因)
        n_attached = 0
        for line2 in open(ev):
            d2 = json.loads(line2)
            if (d2.get("category") == "program" and d2.get("parent_id") is None
                    and d2.get("event") == "span_end" and not d2.get("ok") and n_attached < 3):
                num = d2["span_id"].rsplit("-", 1)[-1]
                for m in (run_dir / "trace" / "calls").glob(f"call-{num}-*/output.json"):
                    lines.append(f"failed {d2['name']} output: " + m.read_text()[:400])
                    n_attached += 1
    pub = run_dir / "source" / "public_result.json"
    if pub.exists():
        lines.append("program public result: " + pub.read_text()[:800])
    logs = sorted((run_dir / "logs").glob("*.log")) if (run_dir / "logs").exists() else []
    for lg in logs[:1]:
        tail = lg.read_text()[-800:]
        lines.append(f"log tail ({lg.name}): {tail}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--aspire-root", required=True)
    ap.add_argument("--suite", required=True)
    ap.add_argument("--task-id", type=int, required=True)
    ap.add_argument("--seed", type=int, default=51)
    ap.add_argument("--task-language", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="gemini-flash-latest")
    ap.add_argument("--max-rounds", type=int, default=3)
    ap.add_argument("--example", action="append", default=[],
                    help="成功程序样例文件(别的任务的)，作为 API 用法接地材料，可重复")
    ap.add_argument("--macro", action="append", default=[],
                    help="已验证宏的 .py 文件，可重复。签名+PRE/EFF 进提示目录，"
                         "实现由驱动在执行前拼到程序头部（口1 注入）")
    ap.add_argument("--extra-doc", action="append", default=[],
                    help="附加说明文件（如 vla_act 技能卡片），原文进提示")
    ap.add_argument("--osc", action="store_true",
                    help="OSC_POSE 集：VLA 技能模式（256x256 相机，几何运动 API 不可用）")
    args = ap.parse_args()

    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        print("缺 GEMINI_API_KEY", file=sys.stderr)
        return 2
    aspire = Path(args.aspire_root)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    api_doc = (aspire / "docs" / "api-reference.md").read_text()

    examples = []
    for ex in args.example:
        examples.append("=== WORKING EXAMPLE (a DIFFERENT task; copy its API usage patterns, "
                        "not its goal) ===\n```python\n" + Path(ex).read_text() + "\n```")
    for doc in args.extra_doc:
        examples.append(Path(doc).read_text())

    macro_srcs, macro_cards, macro_names = [], [], set()
    for mp in args.macro:
        src = Path(mp).read_text()
        name, card = macro_card(src)
        macro_srcs.append(src)
        macro_cards.append(card)
        macro_names.add(name)
    catalog = []
    if macro_cards:
        catalog = ["=== VERIFIED SKILL CATALOG ===\n"
                   "The runtime ALSO provides these higher-level skills as predefined "
                   "functions (already loaded; do NOT redefine them). Each was execution-"
                   "verified on this benchmark. Prefer calling them over re-implementing "
                   "their effect with the raw API; fall back to the raw API only for what "
                   "the catalog does not cover.\n\n" + "\n\n".join(macro_cards)]

    meter = {"model": args.model,
             "driver": ("v4-catalog" if macro_cards else ("v3" if examples else "v1")),
             "examples": args.example, "macros": args.macro, "rounds": []}
    digest = None
    t0 = time.time()
    for rnd in range(1, args.max_rounds + 1):
        parts = [RULES, "=== API REFERENCE ===\n" + api_doc, *catalog, *examples,
                 f"=== TASK ===\nBenchmark LIBERO-Pro, suite {args.suite}, task {args.task_id}.\n"
                 f"Task instruction: {args.task_language}\n"
                 f"Cameras available: agentview (scene), robot0_eye_in_hand (wrist)."]
        if digest:
            prev = (out / f"program_r{rnd-1}.py").read_text()
            parts.append("=== PREVIOUS PROGRAM (failed) ===\n```python\n" + prev + "\n```")
            parts.append("=== EXECUTION EVIDENCE ===\n" + digest +
                         "\nRevise the program to fix the first failure. Output the full corrected program.")
        text, usage = gemini(args.model, key, parts)
        meter["rounds"].append({"round": rnd,
                                "prompt_tokens": usage.get("promptTokenCount"),
                                "output_tokens": usage.get("candidatesTokenCount"),
                                "total_tokens": usage.get("totalTokenCount")})
        agent_code = extract_code(text)
        prog = out / f"program_r{rnd}.py"
        prog.write_text(agent_code)
        n_calls, n_macro = count_calls(agent_code, macro_names)
        meter["rounds"][-1].update({"program_calls": n_calls, "macro_calls": n_macro})
        if macro_srcs:
            # 口1 注入：目录给规划者，实现由运行时提供（拼到程序头部）
            exec_prog = out / f"program_r{rnd}_injected.py"
            exec_prog.write_text("\n\n".join(macro_srcs) + "\n\n" + agent_code)
        else:
            exec_prog = prog
        run_dir = run_episode(aspire, args.suite, args.task_id, args.seed, exec_prog, out / "runs",
                              osc=args.osc)
        outcome = json.loads((run_dir / "outcome.json").read_text())
        ok = bool(outcome["task_success"])
        meter["rounds"][-1].update({"run_dir": str(run_dir), "task_success": ok,
                                    "termination": outcome["termination_reason"]})
        print(f"[round {rnd}] success={ok} termination={outcome['termination_reason']} run={run_dir.name}")
        (out / "meter.json").write_text(json.dumps(meter, indent=1))
        if ok:
            break
        digest = failure_digest(run_dir)
        (out / f"digest_r{rnd}.txt").write_text(digest)
    meter["wall_s"] = round(time.time() - t0, 1)
    meter["final_success"] = ok
    (out / "meter.json").write_text(json.dumps(meter, indent=1))
    print(json.dumps(meter, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
