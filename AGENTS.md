# skillcomp — 符号技能的合成与抽短（合成层）

一句话：一个独立的夹层包。harness 向它要技能目录（原子技能+合成出的大技能），
跑完把轨迹交回；它把反复跑通的序列按运算法则并成带条件的大技能——
**轨迹随经验变短，跑偏时沿回退指针拆回细粒度**。

## 定位（给任何 agent 的三条）

1. 这是论文代码，不是产品。主张：轨迹随经验变短（决策点下降、成功率不降），
   机制是宏合成，验证方式是"每个底盘自己 vs 自己+本层"的配对比较。
2. 本仓库不 fork 任何 harness。接新 harness = 在 `skillcomp/adapters/` 写一个
   适配器（日志→Trace 翻译 + 目录注入），遵守 `doc/active/trace_format_v0.md`。
3. 玩具环境（`skillcomp/envs/drawer_world.py`）只用于机制验证与单元测试，
   它产生的数字**不得**写进任何对外报告。

## 硬规矩（继承自项目组惯例）

- 先讨论后动手：新实验/新依赖/改评测口径，动手前先获准。
- 数字必须带出处：报任何成功率/步数都注明环境、种子数、协议。
- 评测只用公认口径（LIBERO-PRO 等），不自创尺子。
- 收工写 journal/（一日一文件）；结论进 scoreboard.md。
- 索引→语义的映射从代码导出，不猜。

## 地图

```
skillcomp/
  trace.py        轨迹协议（Step/Trace, JSONL IO）
  skill.py        技能卡 + 技能库（追加式版本化；carrier=code|lora，vN 与 vN+1 并存禁覆盖）
  compose.py      运算法则（declared/observed 两种合成）+ n-gram 挖掘
  lifted.py       技能名层挖掘（跨任务动机）
  synthesize.py   LLM 蒸馏合成 + 静态门（白名单/PRE/EFF 强制）
  runtime.py      运行时垫片：宏执行、条件核对、重试、回退报告
  battery.py      尺子登记册：冻结评测组 + 本底噪声（没噪声线不许读 Δ）
  ledger.py       逐轮台账：每技能分数/裕度/花费序列（库级"梯度"）
  casestore.py    病历档案：失败归因三类（圈内/圈外/planner）+ 场景特征
  context.py      Context Assembly（Q1 实验面）：检索+去重+预算装箱
  triage.py       三选一裁决 retry/refine/split（规则预注册）
  gate.py         准入门裁定记录 + 证据回流轮数预算（≤2 轮硬停）
  executors.py    载体→执行器路由：CodeMacroExecutor / VLAExecutor（openpi 协议客户端）
  trainers.py     继续训/拆分 → openpi 训练任务构造（拆分必须写新 PRE）
  conditions.py   PRE/EFF 核查代码生成（沙箱内运行期执行，裕度进 report）
  exec_aspire.py  执行模块：发批→等待→收逐种子结果（替代手敲 ssh）
  collect.py      自动记录：批结果 → 台账 + 病历
  vla_eval.py     π0.5 原生评测的起服务/发评测/解析（Gate 1 用）
  loop.py         外循环主逻辑：校准/逐轮/停驻待批
  adapters/       harness 适配器（aspire.py 已落地）
  envs/           玩具符号环境（数字不得进对外报告）
run_rsi.py        外循环唯一入口（calibrate / run，无证书拒跑）
tools/            生产线脚本：aspire_gemini_driver（planner 驱动，--osc VLA 模式）、
                  vla_act_card.md（技能卡）、produce_vla.sh、harvest_vla.py、
                  make_macro / make_catalog / run_injected
patches/          ASPIRE 本地补丁三枚（0003 = vla_act：π0.5 作为技能）
data/             traces/（统一格式轨迹）、cases.jsonl（病历）、ledger.jsonl、
                  registry.json（检定证书）
tests/            43 个单测
doc/active/       vla_act_integration、pipeline_v3_alignment、两份底盘契约、口1 预注册
journal/          工作日志
scoreboard.md     已确立的数字（带出处）
```

## 当前状态（2026-10-26）

- **内循环（产 trace 生产线）在转**：任务卡（manifest 导出）→ planner（Gemini
  驱动读 vla_act 技能卡）写程序 → OSC_POSE 集真仿真执行（π0.5 经补丁 #3 成为
  harness 内技能）→ 失败验尸自动回流 → trace/病历自动落库。首跑 9 卡产
  18 条 trace + 7 条病历，2/9 任务 ≤2 轮成。
- **载体级发现**：同策略原生整句评测 29/30，planner 拆成子提示 2/9——端到端
  VLA 吃整句，拆解出分布（task 2/6 单调用成 vs 拆两段败为铁证）。规划层价值
  在能力圈外（长时程/组合/恢复/路由），圈内最优动作是整句转发。
- 外循环（量→记→判）一键可跑（run_rsi.py），代码载体证书已检定（floor=0）。
- 待办：整句单调用对照臂；task 9 补跑；VLA 冻结尺子+噪声线；libero_10
  长时程套件（规划层真正的用武之地）。

## 存档状态（2026-10-23）

- 代码技能双环已在 ASPIRE/LIBERO-Pro 实证：纯宏整任务 5/5（未见种子，基准判定）；
  目录注入试点显示规划 agent 自愿采用大技能（程序 54→6 调用）。
- 重整第 1–5 步落地：版本化库、测量层（尺子/台账/病历）、Context Assembly v1、
  triage 规则版、门记录、执行器接口。33/33 测试过。
- 待办：① ucla 实测本底噪声（尺子登记后首件事）；② 从 port1/verify_* 工件回填
  Case Store；③ Phase 2 = π0.5（官方 pi05_base，JAX 分支才有 LoRA），训练
  codebase 由合作方重整，本仓只接 VLAExecutor/trainers 接口。
- 论文定位（白话版）：给"靠技能库自我改进的机器人系统"做决策机制——
  用四种信号（逐轮分数变化、失败归因分类、执行日志诊断、人工纠正数据）
  决定每轮修哪个技能、是修还是拆分、以及在"评测要花钱"的前提下花多少。
