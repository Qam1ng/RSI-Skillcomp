"""宏合成（一次性离线蒸馏 + 静态验证门）。

流程：升维动机（lifted.py 的证据）+ 若干已验证成功的源程序 → 一次 LLM 调用 →
一个可复用的 Python 函数（宏）→ 静态验证（语法、无 import、只用白名单 API、
带条件 docstring）→ 之后的执行验证在底盘上做（准入的最后一道门）。

成本定位：合成是一次性开销，可跨任务摊销；库和运行期复用零模型调用。
LLM 以可调用形式注入（tests 用桩），本模块不绑任何供应商。
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Callable

from .lifted import LiftedMotif

# cap-harness 程序层公共 API（来自 api-reference 与真实轨迹；合成的宏只准用这些名字）
ASPIRE_API_WHITELIST = {
    "open_gripper", "close_gripper", "get_robot_state", "localize_object",
    "move_to_pose", "segment_text", "generate_grasps", "select_grasp",
    "plan_motion", "Pose", "MotionStrategy",
    # 2026-10-19 探针实测：沙箱支持异常机制（此前"无异常机制"系本门误伤）；hasattr 确认被禁
    "ValueError", "RuntimeError", "Exception",
}

PROMPT_TEMPLATE = """You are distilling a reusable robot SKILL FUNCTION from verified programs.

Below are {n_sources} programs that each COMPLETED their task on a robot benchmark
(verified by execution). Across {episodes} successful episodes spanning {tasks} different
tasks, the following call pattern recurred in every one of them:

    {motif}

Argument analysis per position:
{roles}

Write ONE reusable Python function that implements this recurring pattern.

Requirements:
- Signature: def {fn_name}({params}): ...
- The function must RE-COMPUTE all geometry at call time (call localize_object itself;
  derive poses from its fresh point cloud). Never hard-code coordinates.
- Use ONLY these provided runtime names (no imports, they exist in the runtime):
  {whitelist}
- Check `.ok` after every call; on failure return a dict with "ok": False and a "stage" key.
- On success return {{"ok": True, ...}} with useful fields.
- Docstring MUST contain two lines:
  PRE: <when this skill is applicable>
  EFF: <what is true after it succeeds>
- Mirror the geometric techniques used in the verified programs (quantile-based grasp
  points, pre-approach above target, staged descent, verified grasp via gripper state).
- Output ONLY one ```python code block containing the single function.

=== VERIFIED PROGRAM 1 ===
```python
{src1}
```
=== VERIFIED PROGRAM 2 ===
```python
{src2}
```
"""


@dataclass
class MacroCode:
    name: str
    params: list[str]
    code: str
    pre_line: str
    eff_line: str


class MacroValidationError(Exception):
    pass


def build_prompt(motif: LiftedMotif, sources: list[str], fn_name: str, params: list[str]) -> str:
    roles = []
    for r in motif.arg_roles:
        tag = "恒定" if r.role == "constant" else "跨例变化(需参数化或运行时重算)"
        roles.append(f"  [{r.position}] {r.skill}: {tag}; examples: {r.distinct_args[:2]}")
    return PROMPT_TEMPLATE.format(
        n_sources=len(sources), episodes=motif.episode_coverage, tasks=motif.task_coverage,
        motif=" -> ".join(motif.names), roles="\n".join(roles),
        fn_name=fn_name, params=", ".join(params),
        whitelist=", ".join(sorted(ASPIRE_API_WHITELIST)),
        src1=sources[0], src2=sources[1] if len(sources) > 1 else "(none)",
    )


def validate_macro(code: str, fn_name: str) -> MacroCode:
    """静态验证门：语法 / 单函数 / 无 import / 只用白名单外部名 / 带 PRE/EFF。"""
    tree = ast.parse(code)
    fns = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
    if len(tree.body) != len(fns) or len(fns) != 1:
        raise MacroValidationError("必须恰好一个函数定义，别无他物")
    fn = fns[0]
    if fn.name != fn_name:
        raise MacroValidationError(f"函数名应为 {fn_name}，得到 {fn.name}")
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            raise MacroValidationError("禁止 import")
    params = [a.arg for a in fn.args.args]
    # 外部名检查：载入的名字 - 本地绑定 - 参数 - 内置常用
    bound = set(params)
    for node in ast.walk(fn):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            bound.add(node.id)
        if isinstance(node, (ast.For,)) and isinstance(node.target, ast.Name):
            bound.add(node.target.id)
    allowed_builtins = {"len", "sorted", "float", "int", "range", "min", "max", "abs",
                        "list", "dict", "True", "False", "None", "enumerate", "sum", "str"}
    for node in ast.walk(fn):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            if node.id not in bound and node.id not in allowed_builtins \
                    and node.id not in ASPIRE_API_WHITELIST:
                raise MacroValidationError(f"用了白名单外的名字: {node.id}")
    doc = ast.get_docstring(fn) or ""
    pre = next((l.strip() for l in doc.splitlines() if l.strip().startswith("PRE:")), "")
    eff = next((l.strip() for l in doc.splitlines() if l.strip().startswith("EFF:")), "")
    if not pre or not eff:
        raise MacroValidationError("docstring 缺 PRE:/EFF: 条件行")
    return MacroCode(name=fn.name, params=params, code=code, pre_line=pre, eff_line=eff)


def synthesize_macro(
    motif: LiftedMotif,
    sources: list[str],
    fn_name: str,
    params: list[str],
    llm: Callable[[str], str],
    max_attempts: int = 2,
) -> MacroCode:
    """蒸馏 + 验证。验证失败把错误喂回去重试一次。"""
    import re
    prompt = build_prompt(motif, sources, fn_name, params)
    last_err = None
    for _ in range(max_attempts):
        text = llm(prompt if last_err is None else prompt +
                   f"\n\nYour previous output failed validation: {last_err}. Fix and resend.")
        m = re.search(r"```python\n(.*?)```", text, re.S)
        if not m:
            last_err = "no python code block"
            continue
        try:
            return validate_macro(m.group(1), fn_name)
        except (MacroValidationError, SyntaxError) as e:
            last_err = str(e)
    raise MacroValidationError(f"合成未过验证门: {last_err}")
