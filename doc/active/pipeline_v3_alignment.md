# Pipeline v3 对齐方案（2026-10-21 起草；2026-10-23 获批执行，第 1–5 步已落地）

依据：SkillComp Pipeline 图（RSI 环 v3，2026-10-20 通话版，claude.ai/artifact/5ncGNKy7asS9WF64ZanE82）。
原则照图：**换载体，不换管线**——技能从"代码宏"变成"共享 VLA 底座 + 每技能一个 LoRA"，
PRE/EFF、准入门、追加入库、口 2 回流全部保留。

## 图中每个框 ↔ 代码现状 ↔ 要改什么

| 图中框 | 现状（v0） | 改动 |
|---|---|---|
| Skill Library | `skill.py` SkillCard 只有 kind=atomic/macro，body=调用序列 | 加 `carrier` 字段：`code`（现有）/ `lora`（backbone_id, adapter_path, version, parent_version, data_group）。Library 改为**追加且带版本**，vN 与 vN+1 并存，禁覆盖 |
| VLM Planner（冻结） | ASPIRE 的 LLM + `tools/aspire_gemini_driver.py` | 不动。目录卡片的渲染（`tools/make_catalog.py`）要能渲染 lora 技能 |
| Execute Skills（VLA expert，无底层规划器） | `runtime.py` Executor 协议只跑符号调用；真实执行靠 ASPIRE 的 move_to_pose 几何管线 | 新增 `executors/`：`CodeMacroExecutor`（现状）、`VLAExecutor`（加载 backbone+LoRA，按 skill 的 prompt 出 action chunk，直接 step 环境，不经 move_to_pose）。**π0.5 实现等 Eric 的重整 codebase，这里只定接口与假执行器** |
| Condition Checks | `runtime.run_skill` 已做 PRE 前查 / EFF 后查 | 保留；条件谓词来源从"代码宏自报"扩到"感知谓词"（SymSkill 档） |
| Skill failed → de-chunk | `runtime.py` 回退指针 | 保留；失败时额外产出一条 **Case**（见下） |
| Case Store（追加） | 无。失败证据散在各 run 目录 | 新模块 `casestore.py`：JSONL 追加；字段 scene/skill/version/stage/cause/trace_ref/fix |
| Context Assembly（Q1） | 无 | 新模块 `context.py`：按 skill + 失败聚类检索，预算（token 数）内装箱；策略可插拔，这是实验面 |
| Agent Triage（冻结 VLM） | 无。现在的证据回流是人工/脚本决定修 | 新模块 `triage.py`：输入组装好的上下文，输出 retry / refine / split 之一 + 理由；先给规则版（失败率阈值、圈内/圈外判定）再给 VLM 版 |
| Train Candidate（唯一有梯度处） | 现在是 `synthesize.py` 让 LLM 写代码 | 新接口 `trainers/`：`refine(entry, new_data) -> candidate`、`split(entry, groups) -> [candidate]`。代码载体下 refine=最小差分改码（现有）；LoRA 载体下接训练脚本（Astra waypoint / RL），实现随 Eric 的 codebase |
| Admission Gate | `synthesize.validate_macro` 静态门 + 手工执行验证（verify_*） | 合成一个 `gate.py`：静态检查 + 未见 seed 执行验证（用基准自带判定），证据回流 ≤2 轮 |
| Admitted / append only | `Library.admit` 是覆盖式 | 改追加式；写 provenance |

## 不做（照图 v1 范围）
multi-agent、LoRA merge、planner 后训。

## 实施顺序（每步可独立验收）
1. SkillCard 加 carrier + 版本化 Library（测试：旧 JSON 可读、追加不覆盖）
2. casestore + 从 ASPIRE run 目录抽 Case（用 port1 的双失败做样本）
3. context assembly（规则检索 + 预算）+ triage 规则版（用 port1 盘子案例应判 split，goal2 应判 refine）
4. executors/ 接口 + CodeMacroExecutor 跑通现有 5/5；VLAExecutor 假实现过接口测试
5. gate.py 把现有静态门 + 执行验证合并，接 admitted → append
6. 等 Eric 的 π0.5 codebase 到位，接 VLAExecutor 与 trainers

## 未决（需拍板）
- π0.5 执行器与训练器是等 Eric 的 codebase，还是本仓自己先接 openpi？
  本机与 ucla 当前都没有 openpi；ucla 有 Roboverse_train_smolvla 可参考训练脚手架。
