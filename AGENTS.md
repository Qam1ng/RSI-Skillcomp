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
  triage.py       店长规则版：三叉裁决 retry/refine/split（规则预注册）
  gate.py         准入门裁定记录 + 证据回流轮数预算（≤2 轮硬停）
  executors.py    载体→执行器路由：CodeMacroExecutor / VLAExecutor（π0.5 待接）
  adapters/       harness 适配器（aspire.py 已落地）
  envs/           玩具符号环境（数字不得进对外报告）
tests/            33 个单测，含三叉裁决验收案例（盘子→split）
doc/active/       pipeline_v3_alignment（实施中）、口1 预注册、轨迹格式 v0
journal/          工作日志
scoreboard.md     已确立的数字（带出处）
```

## 当前状态（2026-10-23）

- 代码技能双环已在 ASPIRE/LIBERO-Pro 实证：纯宏整任务 5/5（未见种子，基准判定）；
  口1 试点显示目录被自愿采用（程序 54→6 调用）。
- 重整第 1–5 步落地：版本化库、测量层（尺子/台账/病历）、Context Assembly v1、
  triage 规则版、门记录、执行器接口。33/33 测试过。
- 待办：① ucla 实测本底噪声（尺子登记后首件事）；② 从 port1/verify_* 工件回填
  Case Store；③ Phase 2 = π0.5（官方 pi05_base，JAX 分支才有 LoRA），训练
  codebase 由合作方重整，本仓只接 VLAExecutor/trainers 接口。
- 定位语（给论文）：库式 RSI 的优化器——四层信号（Δ台账/断点分类/飞行记录/
  稠密纠正），三叉裁决含结构动作，评估计费下的预算分配。
