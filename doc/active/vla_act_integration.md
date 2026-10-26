# vla_act：把 π0.5 作为技能接进 ASPIRE（内循环 = 产 trace 的执行环）

2026-10-26 立项。目标：**在 ASPIRE 基础上**建起"VLM Planner → 调技能
（含 VLA）→ 条件核查 → 步级 trace"的执行环。不另起炉灶——planner
（LLM 写程序）、每调用自动记 span、条件注入、批量/种子/判定器全部复用。

## 侦察结论（全部读自 ucla 源码，2026-10-26）

1. 程序沙箱无网络，π0.5 调用必须在 **harness 侧**实现 → 新 API `vla_act`。
2. 扩展机制（LiberoRuntimeExtensions）只开放元数据 → `vla_act` 走**本地补丁 #3**
   （api.py 加方法 + 注册进 approved 清单；与前两枚补丁同纪律，提上游 issue）。
3. **控制器硬约束**：LiberoAdapter 只认 JOINT_POSITION（不符直接 raise）；
   π0.5 训练于 OSC_POSE（7 维末端增量）。robosuite 控制器建环时二选一。
4. 观测拼法照抄 openpi 客户端：两路相机图像上下左右翻转 → resize_with_pad 224
   → uint8；状态 8 维 = EE 位置 3 + 四元数转轴角 3 + 夹爪 2；
   每次推理取动作块前 replan_steps 步执行再重规划。
5. 相机：adapter 的 CAMERA_NAMES 已含 agentview 与 robot0_eye_in_hand。

## 设计（v1）

- **两种集，分而治之**：
  - JOINT_POSITION 集：现状不变，跑代码宏。
  - **OSC_POSE 集（新）**：补丁放行 `controller="OSC_POSE"`；该模式下
    几何运动 API（move_to_pose/plan_motion/execute_trajectory）返回
    UNSUPPORTED，只许 `vla_act` + 感知/状态读取。混载体同集留到 v2。
- **`vla_act(prompt, max_steps=...)`**（harness 侧，按 openpi 协议连策略服务端）：
  抓当前双相机帧+8 维状态 → infer 得 (10,7) 动作块 → 原生 env.step 执行
  前 replan_steps 步 → 循环，直到 max_steps 或环境终止；返回
  ExecutionResult 形结果（steps_executed、终止原因、诊断）。
  每次 vla_act 自动成为 trace 里的一个 span = 一次技能调用。
- **Planner**：复用 Gemini 计量驱动——程序即规划决策记录；目录卡片里
  VLA 技能以 `vla_act("<子任务指令>")` 形式给出，PRE/EFF 照旧由
  conditions.py 注入（谓词从 get_robot_state/localize 算，这些读取类
  API 在 OSC 集保持可用）。
- **步级 trace**：免费——cap-harness 的 events.jsonl/calls 机制原样工作，
  adapters/aspire.py 现有映射直接可读。

## 验收标准（跑一集即检）

产出一个符合 trace_format_v0 的文件：含 planner 决策（程序文本 + 驱动
计量）、每次 vla_act 的起止/参数/步数、每道 PRE/EFF 裕度、基准判定成败。

## 施工顺序

1. 补丁 #3a：adapter 放行 OSC_POSE（建环参数透传 + 几何 API 禁用门）。
2. 补丁 #3b：api.vla_act（观测拼装 + 策略客户端 + 步进循环）+ 注册。
3. 冒烟：固定程序单集（"pick up the wine bottle..."）→ 验收标准过检。
4. 配目录卡片 + conditions 注入 → Gemini 驱动写程序 → 首条完整 trace。
5. exec_aspire/run_rsi 加 OSC 集开关 → VLA 尺子校准（随机策略，floor 预计 >0）。
