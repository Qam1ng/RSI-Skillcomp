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
    subgraph H["Harness (unmodified: ASPIRE / RPent / RoboHarn-Evo)"]
        P["Planner<br/>(the harness's own LLM)"]
        E["Executor<br/>(skill calls → robot / simulator)"]
        P -->|plan| E
    end

    subgraph L["RSI-Skillcomp layer (this repo)"]
        CAT["Skill catalog<br/>atomic skills + composed macros"]
        RT["Runtime shim — runtime.py<br/>runs macros, checks conditions, retries"]
        AD["Adapters — adapters/<br/>harness logs → unified Trace format"]
        MINE["Composer — compose.py<br/>mine recurring sequences → compose → admission gates"]
        LIB[("Skill library — skill.py<br/>pre/effect conditions, provenance, fallback pointer")]
    end

    CAT -->|"1 · serve the catalog (more macros = shorter plans)"| P
    E -->|"2 · macros execute through the shim, checked step by step"| RT
    RT -->|"condition broken: fall back to fine-grained steps; unrecoverable: ask planner to replan"| P
    E -->|"3 · collect execution logs"| AD
    AD -->|"Trace (JSONL)"| MINE
    MINE -->|"4 · recurring verified sequences become new macros"| LIB
    LIB --> CAT
```

Each round of experience closes the loop 1→2→3→4 once: more macros → shorter plans →
fewer decisions and fewer LLM calls. The measured object is this speedup curve
(success rate must not drop). Paired experiment = the same harness with this loop
disconnected vs. connected.

- 入口与规矩：[AGENTS.md](AGENTS.md)
- 轨迹协议：[doc/active/trace_format_v0.md](doc/active/trace_format_v0.md)
- 机制演示：`python3 examples/demo_curve.py`
- 测试：`python3 -m unittest discover -s tests`

## v0 范围声明（诚实版）

- 宏是接地的（绑定具体参数），参数泛化是 v1 的研究内容；
- 条件两档：declared（环境/算子自带）与 observed（从快照统计，近似）；
- 自带玩具环境只用于机制验证，其数字不构成任何实验主张；
- harness 适配器（ASPIRE / RPent / RoboHarn-Evo）尚未落地，接口见 `skillcomp/adapters/base.py`。
