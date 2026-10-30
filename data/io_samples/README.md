# 两种技能载体的真实 I/O 样本

全部是真实运行记录的原文（底盘自动留痕），非手写示例。

## code_as_policy/（普通代码技能，JOINT_POSITION 集）

出处：libero_object_swap/0 seed 51 获胜程序一集（harvest，2026-10-18）。

- localize-object：输入 = 物体名 + 相机名；输出 = LocalizationResult
  （几何：中心位姿、三维尺寸、点数 1471）
- get-robot-state：无输入；输出 = 末端位姿 + 夹爪开度（标量）
- move-to-pose：输入 = Pose（位置/四元数/坐标系）+ 容差 + 步数上限；
  输出 = ExecutionResult（ok、执行步数、末端误差）
- execute-trajectory：输入 = 关节轨迹（dt 0.05 s 的逐点序列）——
  底层 8 维关节目标形态的实录

## vla/（VLA 技能，OSC_POSE 集）

出处：vla_act 冒烟成功集（libero_goal_task/2 seed 56，2026-10-26，76 步完成）。

- vla_act：输入 = 一句任务指令 + max_steps/replan_steps；
  输出 = ExecutionResult（steps_executed=76、terminated=true、
  status="terminated"——按契约"成功即截断、终止不得自称 ok"，
  程序以 terminated 为成功信号）
- 模型级 I/O（观测四键 → (10,7) 增量动作块）不在调用记录里——
  规范见 doc/active/substrate_contract_openpi.md 第 7 条与动作语义证据链

## logs/

同一冒烟成功集的三件原始日志：outcome.json（基准判定 task_success=true）、
run.json（环境配置：OSC_POSE、256×256 相机、seed）、
vla_smoke_program_result.json（程序 stdout 报告原文）。
