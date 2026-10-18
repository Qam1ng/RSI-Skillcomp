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
  skill.py        技能卡 + 技能库（atomic/macro、前置/效果/维持、回退指针=body）
  compose.py      运算法则（declared/observed 两种合成）+ n-gram 挖掘 + 准入门
  runtime.py      运行时垫片：宏执行、条件核对、重试、回退报告、事件标签
  adapters/       harness 适配器接口（ASPIRE/RPent/RoboHarn-Evo 待落地）
  envs/           玩具符号环境 + BFS 占位规划器（真实场景中规划者=LLM）
tests/            9 个单测：代数、挖掘、回退、端到端"决策点下降"
doc/active/       当前有效文档（轨迹格式 v0 等）；过期移 doc/history/
journal/          工作日志
scoreboard.md     已确立的数字（带出处）
```

## 当前状态（2026-10-18）

- v0 骨架完成，9/9 测试过。接地版宏（参数不泛化）；条件两档（declared/observed）。
- 下一步：ASPIRE 复现认证（LIBERO-Pro quickstart）→ ASPIRE 适配器 → 配对测量。
- 底盘与对照班子：ASPIRE（底盘）、RoboHarn-Evo（主 baseline）、RPent（无积累对照）、
  RoboICL（ICL 对照）、SymSkill（谓词来源，合作方向）。
