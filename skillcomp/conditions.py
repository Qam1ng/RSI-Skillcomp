"""判定条件（PRE/EFF）装车：生成在 harness 沙箱内、运行期执行的核查代码。

核查不能事后读日志替代——必须在执行时发生，所以本模块产出的是
**注入程序里的代码片段**：每次技能调用之前核查使用条件（PRE），
之后核查承诺效果（EFF），并把连续裕度写进 report（别把数砍成布尔扔掉）。

片段遵守沙箱规则：无 import、无数组真值判断、只用公开 API。
阈值只用执行验证过的数（松开判定 >0.03 来自实测：松开 0.297 / 闭合 ≈0）。
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CheckSpec:
    """一个技能的核查片段。{ret} 会被替换成该次调用的返回值变量名。"""
    skill: str
    pre_code: str = ""    # 调用前执行；可写 report、可设 pre_ok_flag 门闸
    post_code: str = ""   # 调用后执行；写 check_*/margin_* 进 report


REGISTRY: dict[str, CheckSpec] = {
    "vla_act": CheckSpec(
        skill="vla_act",
        # EFF：episode 被判定器终止 = 任务级完成（terminated 即成功，契约第 6 条）
        post_code=(
            'report["check_{ret}_eff_done"] = bool({ret}.terminated)\n'
            'report["margin_{ret}_steps"] = int({ret}.steps_executed)\n'
        ),
    ),
    "pick_object": CheckSpec(
        skill="pick_object",
        post_code=(
            'report["check_{ret}_eff_grasped"] = bool({ret}.get("ok", False))\n'
            'report["margin_{ret}_below_grasp_m"] = float({ret}.get("below_grasp_m", -1.0))\n'
        ),
    ),
    "place_into": CheckSpec(
        skill="place_into",
        # PRE：必须正握着东西（上一步的承诺效果就是这一步的使用条件，{prev}=上一调用返回名）
        pre_code=(
            'pre_ok_flag = bool(report.get("check_{prev}_eff_grasped", False))\n'
            'report["check_{ret}_pre_holding"] = pre_ok_flag\n'
        ),
        # EFF：松开要用夹爪开度核实（open_gripper 成功也可能报 ok=False，契约第 5 条）
        post_code=(
            'report["check_{ret}_eff_ok"] = bool({ret}.get("ok", False))\n'
            'st_{ret} = get_robot_state()\n'
            'w_{ret} = float(st_{ret}.gripper_positions["primary"])\n'
            'report["margin_{ret}_release"] = w_{ret} - 0.03\n'
            'report["check_{ret}_eff_released"] = w_{ret} > 0.03\n'
        ),
    ),
}


def emit_glue(plan: list[tuple[str, str, str]]) -> str:
    """生成带核查的任务胶水代码。

    plan 的每项是 (技能名, 参数源码, 返回值变量名)，按顺序执行；
    PRE 不满足则跳过该调用并记录，不硬闯（这就是运行期的失败检测）。
    """
    lines = ["report = {}", "pre_ok_flag = True"]
    prev = ""
    for skill, args_src, ret in plan:
        spec = REGISTRY.get(skill)
        if spec and spec.pre_code and prev:
            lines.append(spec.pre_code.format(ret=ret, prev=prev).rstrip())
            lines.append(f"if pre_ok_flag:")
            lines.append(f"    {ret} = {skill}({args_src})")
            lines.append(f"else:")
            lines.append(f'    {ret} = {{"ok": False, "stage": "pre_violated"}}')
        else:
            lines.append(f"{ret} = {skill}({args_src})")
        lines.append(f'report["{ret}_ok"] = bool({ret}.get("ok", False))')
        lines.append(f'report["{ret}_stage"] = {ret}.get("stage", "done")')
        if spec and spec.post_code:
            lines.append(spec.post_code.format(ret=ret).rstrip())
        prev = ret
    lines.append("print(report)")
    return "\n".join(lines) + "\n"


def checked_program(macro_sources: list[str], plan: list[tuple[str, str, str]]) -> str:
    """宏实现 + 带核查的胶水 = 可直接交给执行模块的完整程序。"""
    return "\n\n".join(s.rstrip() for s in macro_sources) + "\n\n\n" + emit_glue(plan)
