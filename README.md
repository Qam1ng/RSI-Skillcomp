# RSI-Skillcomp

Symbolic skill composition layer for LLM robot harnesses: verified step
sequences are merged into bigger skills with pre/effect conditions, so
execution traces get shorter with experience; condition violations de-chunk
back to fine-grained steps.

合成层：把 harness 反复跑通的技能序列按运算法则并成带条件的大技能——
轨迹随经验变短；条件破了沿回退指针拆回细粒度。

## Pipeline

```mermaid
flowchart TB
    subgraph H["harness（原封不动：ASPIRE / RPent / RoboHarn-Evo）"]
        P["规划者（harness 的 LLM）"]
        E["执行器（技能调用 → 机器人/仿真）"]
        P -->|计划| E
    end

    subgraph L["RSI-Skillcomp 合成层（本仓库）"]
        CAT["技能目录<br/>原子技能 + 合成宏"]
        RT["运行时垫片 runtime.py<br/>宏执行 · 条件核对 · 原地重试"]
        AD["适配器 adapters/<br/>harness 日志 → Trace（统一轨迹协议）"]
        MINE["合成器 compose.py<br/>n-gram 挖掘 → 运算法则合成 → 准入门"]
        LIB[("技能库 skill.py<br/>前置/效果/维持条件 · 出身 · 回退指针")]
    end

    CAT -->|"① 供货：目录注入（宏越多，计划越短）"| P
    E -->|"② 执行走垫片：宏=成分序列+逐段核对"| RT
    RT -->|"条件破 → 沿回退指针拆回细粒度重试；救不回 → 上报重规划"| P
    E -->|"③ 回收：执行日志"| AD
    AD -->|"Trace (JSONL)"| MINE
    MINE -->|"④ 反复跑通的序列 → 新宏"| LIB
    LIB --> CAT
```

闭环含义：每多跑一轮，②③④①转一圈——**宏变多 → 计划变短 → 决策点和大模型调用变少**；
测量对象就是这条"越跑越快"曲线（成功率不得下降）。配对实验 = 同一 harness 断开/接通此环。

- 入口与规矩：[AGENTS.md](AGENTS.md)
- 轨迹协议：[doc/active/trace_format_v0.md](doc/active/trace_format_v0.md)
- 机制演示：`python3 examples/demo_curve.py`
- 测试：`python3 -m unittest discover -s tests`

## v0 范围声明（诚实版）

- 宏是接地的（绑定具体参数），参数泛化是 v1 的研究内容；
- 条件两档：declared（环境/算子自带）与 observed（从快照统计，近似）；
- 自带玩具环境只用于机制验证，其数字不构成任何实验主张；
- harness 适配器（ASPIRE / RPent / RoboHarn-Evo）尚未落地，接口见 `skillcomp/adapters/base.py`。
