# 2026-10-23：codebase 重整——测量层 + 三叉裁决落地

按 doc/active/pipeline_v3_alignment.md（本日获批）完成第 1–5 步，全部本地代码，
零 API、零 GPU。33/33 测试过（老 9 + 新 24）。

## 落了什么

1. **版本化技能库**（skill.py）：carrier 字段（code|lora）+ 追加式版本——
   admit 禁覆盖禁倒退，vN/vN+1 并存，旧 JSON 兼容。防遗忘自此是架构性质。
2. **测量层三件**（对应"四层信号"的前两层采集）：
   - battery.py 尺子登记册：评测组冻结（改种子必须换名）；**没测噪声线的尺子
     拒绝出 Δ**（require_floor 硬卡）。
   - ledger.py 台账：分数/裕度/花费逐轮 JSONL；delta() 低于噪声线一律 flat。
   - casestore.py 病历：三类归因（圈内/圈外/planner）编码了条件链反扫的
     停止规则；场景特征必填习惯（盘子教训）。
3. **Context Assembly v1**（context.py）：按技能检索→(stage,kind) 去重→
   字符预算装箱。策略可插拔——这是 Q1 的实验面，v1 只是规则基线。
4. **店长规则版**（triage.py）：六条预注册规则，输出带证据的可审计 Decision。
   验收测试照实施方案写死：盘子型圈外聚集 → split；圈内为主 → refine；
   planner 过半 → retry；样本 <3 或已达标 → hold。
5. **门与执行器**：gate.py（准入裁定记录 + 证据回流 ≤2 轮硬停）；
   executors.py（载体路由接口，VLAExecutor 占位等 π0.5）。

## 选型钉死（本日确认）

- VLA 底座 = **官方 pi05_base**（openpi）。π0.6 无官方权重（第三方复刻不用，
  出处风险）；朋友处实践交叉确认 π0.5。LoRA 必须走 openpi 的 JAX 分支
  （PyTorch 移植不支持），显存 22.5GB+，A6000 可跑。
- 重训底座：不做。Phase 2 Gate 1 = checkpoint 在 LIBERO 上复现评测数字。

## 下一步（顺序预注册）

1. ucla 实测本底噪声：pick/place/纯宏三把尺子，同配置重复批（零 API）。
2. 从 port1 / verify_* 工件回填 Case Store（盘子战役做首批真实病历）。
3. 规则版 triage 对真实病历出首批裁决，和人工判断对账。
