# 精读笔记：GPT-6 Astra 两篇 RoboDojo 评测（2026-10-31）

来源：arXiv 2609.24170（Unexpected Robot Policy）、2609.38537（Systematically
Exploring … as Embodied Policies）。均为预印本、第三方评测；Astra 内部机制
无技术报告，以下全部是接口层观测。

## 一、2609.24170：纯 Astra 当策略（逐轮工具调用，非写程序）

**接口（和 ASPIRE 的 code-as-policy 不同！）**
- 输入：三路 RGB（头部+双腕，仅保留最近两轮图像）、14 维末端状态、只读
  关节角、任务指令 + wiki 任务说明、全部文字历史。**不给深度、不给特权
  位姿**——公制坐标全靠模型从 RGB 估。
- 输出：每轮恰好一次工具调用——`move_eef`（14 维末端目标的任意子集 +
  note 文字）或 `give_up`。非学习后处理做校验→IK→关节路径→25Hz 重采样。
- 预算：每集 ≤100 次模型调用；成功集典型 14–25 次。

**成绩（RoboDojo-Sim，42 任务）**
| 条目 | Score | 平均 SR |
|---|---|---|
| GPT-6 Astra | 28.97 | **22.48%**（40 个公开策略之上） |
| DM0.5（最强学习策略） | 24.90 | 19.34% |
| π0.5 | 11.41 | **6.91%** |
| DeepSeek-Flash / GPT-5.5（同接口） | 2.99 / 1.13 | 1.92% / 0.88% |

- 强项：Open 34.36、Generalization 33.36；弱项：Precision 12.65
  （"large gaps in precision and coordinated manipulation"）。
- **模型差异巨大**：同一接口下 GPT-5.5 几乎为零——能力在模型不在接口。
- **ICL 反而降分**：零样本 22.9% > 图像示范 17.9% > 文字示范 12.9%。
- **真机被中止**：反复发出物理不安全动作并损坏硬件，官方真机协议未完成。
- 扰动：翻转图像 8/8 稳；集内自适应有初步证据（坐标系取反后自我修正），
  作者强调单 seed、每项仅 8 次二元试验。

## 二、2609.38537：Astra + π0.5 混合（逐块审查制）

**机制**：π0.5 每次提出 50 步动作块，**Astra 审查每一块**，二选一：
执行其前 1–15 步，或替换为自己的 1–5 步末端修正。RoboCasa 里还可改写
子任务指令而不动动作。无明确触发规则——每块都过审。预算尽则回退纯 π0.5。

**控制步分配**：RoboDojo 85.6% π0.5 / 14.4% Astra（"intervenes
selectively"）；RoboCasa 44.8% 为 Astra。

**成绩**
| 场景 | Hybrid | 纯 Astra (Direct) | 纯 π0.5 |
|---|---|---|---|
| RoboDojo 10 任务（微调权重） | **48%** | 26% | 15.67% |
| RoboLab 10 任务（零样本权重） | 92% | **98%** | 36% |
| 灵巧操作 Score | **61.6** | 16.6 | 44.2 |
| RoboCasa | 38.7% | 33.3% | 22.7%（p=0.52 不显著） |

**作者结论**（原文）：少量针对性修改可带来明显提升；辅助价值"depends on
how well the learned motion prior fits the task"；辅助也会伤害本已能做的
case（RoboLab 98→92）。

**成本（关键！）**：RoboDojo 50 集 Hybrid 总 token 624.8M——**约 1,250 万
token/集**；Direct 更是 1,132M/50 集。

## 三、对我们论文的五个直接含义

1. **能力圈的教科书案例**：π0.5 在 LIBERO（微调分布内）98% ↔ RoboDojo
   6.91%。"能力 = 训练分布"从没这么直观过；我们的 PRE/能力圈语言正好
   给这件事提供表述和检测机制。
2. **"辅助的符号由先验契合度决定"= 我们"圈内中间层只能减分"的他证**：
   RoboLab 上纯 Astra 98 > Hybrid 92，与我们整句 29/30 > 拆解 2/9 同构。
   两个独立证据指向同一条定理——介入要有条件判断，无条件介入必伤圈内。
3. **成本结构是我们最大的差异化**：他们逐块审查、每集 ~12.5M token、
   **无任何积累**——第 100 次做同一任务和第 1 次一样贵。我们的全部主张
   就是把这笔钱摊销掉：trace→条件/宏/expert，重复任务递减到零 LLM。
   引用他们的 token 数就是我们动机一节最硬的数字。
4. **他们没有库、没有门、没有学习环**：失败不变成训练数据，修正不沉淀
   为技能，介入规则不被学习。我们管线的每个框都恰好是他们缺的那块。
5. **harness 重要性他证**（配合 2609.39018）：同一 Astra，原生 16.0 →
   RoboProbe 34.4；Opus 5.5 + URAI 60%。"价值在模型外面那一层"成立。

## 四、风险与诚实边界

- Astra 闭源无技术报告：污染"unquantified rather than ruled out"（原文）。
- 这两篇已占据"frontier VLM 直接/混合控制"的发表先机；我们的空间在
  **积累与摊销**（他们明确没做），动作要快。
- 真机安全事故提示：任何把 VLM 放进控制环的方案都要写安全章节。

## V. Parameter audit: the 22.48% vs 6.91% headline (added 2026-11-03, verbatim re-read)

Conclusion: the numbers are reported correctly, but the comparison is NOT a
controlled experiment. Key findings, each traceable to paper text:

### Provenance

- All 40 learned-policy rows (incl. Pi-05 11.41 Score / 6.91% SR, DM0.5
  24.90 / 19.34%) are a **2026-09-10 public-leaderboard snapshot**, not runs
  by the authors; cells "were not re-run alongside the LLM-controller
  columns" (App. H). Paper 1 states nothing about who trained the leaderboard
  pi0.5, on what data, or its runtime config (chunk length, replan cadence,
  control Hz, cameras — all absent; presumably in the benchmark paper
  arXiv 2607.04434, which we have not read).
- Paper 2's "pure pi0.5 15.67%" on RoboDojo is **also not a run**: it is the
  published pi0.5 results *reweighted* to their 10-task mixture — a mixture
  deliberately stratified toward pi0.5-weak tasks (6 of 10 from the lowest
  published-SR interval). The benchmark releases task-finetuned pi0.5
  weights; Hybrid uses those.
- RoboLab (Direct 98% vs pi0.5 36%): pi0.5 is zero-shot DROID-trained
  weights; Astra was allowed repeat attempts (two Direct episodes got a
  500-decision budget vs the standard 180) — an Astra-only allowance.

### Known runtime parameters, per side (Paper 1, Direct)

| Parameter | GPT-6 Astra Direct | Pi-05 (leaderboard row) |
|---|---|---|
| Provenance | authors' run: 42 tasks x 50 eps = 2,100 trials, single seed | leaderboard snapshot, not re-run |
| Training | frozen commercial model, zero robot training | unknown (benchmark releases task-finetuned weights per Paper 2) |
| Observation | 3 RGB (head + both wrists; resolution not stated), images kept for last 2 turns only, full text history; 14-dim grasp-point state + 12 read-only joint angles as text; arrival-error feedback | not stated in Paper 1; benchmark spec per Paper 2: head + both wrists 640x480, 14-dim proprioception |
| Extra input | wiki task recipe + process-score ladder (authors concede input asymmetry) | task instruction only |
| Action output | one move_eef per turn: subset of 14 world-frame absolute dims (x,y,z,pitch,roll,yaw,gripper per arm); bounds in App. A | action chunks; Paper 2 shows 50x14 joint-space chunks (as exposed in Hybrid); executed-steps-per-chunk and replan cadence NOT stated in either paper |
| Expansion / control | non-learned: validate -> IK -> joint path -> resample 25 Hz; waypoint count varies with travel | 25 Hz control (benchmark spec) |
| Time | turn-based; env steps consumed in proportion to motion distance; physics pause during deliberation implied (Paper 2 states pausing explicitly for its own settings) | real-time chunked execution |
| Budget | 100 model calls/ep + env-step cap (value unpublished); successful probe episodes 14-25 calls | zero LLM calls |
| Aggregation | Score = mean process reward x 100; headline = unweighted mean over 5 axes (micro: 472/2,100 = 22.48% SR) | 6.91% = same axis-mean convention |

### Per-axis SR (%) — the single number hides reversals

| Axis | Astra | Pi-05 | DM0.5 |
|---|---|---|---|
| Generalization | 30.50 | 8.17 | 10.95 |
| Precision | **4.00** | 5.50 | 16.75 |
| Long-Horizon | **8.25** | 14.67 | 19.50 |
| Memory | 38.67 | 4.56 | 47.44 |
| Open | 31.00 | 1.67 | 2.08 |

- Pi-05 **beats Astra on Precision and Long-Horizon**; Astra's entire lead
  comes from Open / Memory / Generalization.
- DM0.5 beats Astra on 3 of 5 axes (Precision, Long-Horizon, Memory); on the
  40-row leaderboard proper, DM0.5 ranks #1.
- Revised insight: mechanism-2's advantage is concentrated in semantic /
  open-ended / generalization axes, not in motor competence. "Astra wins
  out-of-distribution" must be stated per-axis, never as one number.

### Fairness caveats the authors themselves list (App. H)

Input asymmetry (wiki recipe); stale snapshot baselines; "the per-episode
call budget is a condition, not a neutral setting"; single evaluation seed,
no variance estimates; contamination unquantified; interface as measurement
boundary (move_eef cannot express continuous-contact behaviour; RGB-only may
cap precision; image_horizon=2 confounds the Memory axis).

### Identity of DM0.5 (added 2026-11-04, from HF model cards)

DM0.5 = "DM05", Dexmal's open-source VLA foundation model (successor of DM0;
released 2026-07-09; no arXiv paper, only a tech blog; license: gemma).
Architecture: Gemma 3 4B VLM backbone + 680M action expert (~6B total),
continuous action chunks — structurally the pi0 family (mechanism 5), though
the cards never state flow matching vs diffusion. The leaderboard entry is
DM05-MEM-Robodojo-Sim (2026-08-26): fine-tuned on RoboDojo sim (demo count
unstated), ARX X5 bimanual, 3 RGB cameras, outputs 50-step x 14-dim
**absolute joint-position** chunks, eval adapter executes the first 25 steps
per chunk (N=50, H=25; control Hz unstated). MEM = up to 20 head-camera
history frames at 1 FPS (~20 s of history; media reports of "60 s" are not
on the card). Reading: the board's #1 is not a new mechanism — it is
mechanism 5 plus task finetuning plus an explicit history window, which is
exactly why Astra's Memory-axis lead holds against zero-history pi0.5
(38.67 vs 4.56) but flips against DM0.5-MEM (38.67 vs 47.44). Capability
gaps here trace to harness/input differences (history window), not to the
generation mechanism.

### Implication for our experiment plan

No matched-variable comparison of mechanism-2 vs mechanism-5 exists in
either paper (different inputs, budgets, time conditions, provenance). Our
planned B-arm (Gemini-as-Astra on our harness: same tasks, same seeds, same
executor as the vla_act arm) would be the first controlled version of this
comparison, at Gemini scale.
