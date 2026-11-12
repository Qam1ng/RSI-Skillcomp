# Baseline survey: LIBERO-Pro and RoboDojo — who scores what, with which model, and who executes (rewritten 2026-11-12)

Purpose: fix the baseline set after the pivot toward "VLM planner + VLA
executor". This rewrite replaces the 2026-11-12 morning version. Every row
was read from the paper full text, the official leaderboard data, or the
adapter README, unless the row says otherwise.

Reading rules:

- Scores under different protocols are NOT comparable. Always quote the
  protocol next to the score.
- "Learns where" matters as much as the score: zero-shot (no experience),
  same-task experience (other seeds or layouts of the tested task), or
  transfer (experience from other tasks or another benchmark).
- Coverage is bounded by what was found by 2026-11-12. Boards are live.
  This document does not claim that any combination is unoccupied.

## 0. Retractions

Three earlier claims in this file were wrong and are withdrawn:

1. "No VLM-planner + VLA-executor system reports on LIBERO-Pro." At least
   thirteen do (Section 2).
2. "Nobody combines between-episode harness growth with VLA execution."
   Zetta, DynaHarness, EmbodiedRSI, HarnessPAI and RoboACE do; on RoboDojo
   PhysicalRSI and WorldScape-R2SI do.
3. "RoboDojo-Sim has no VLM + VLA entry." The official board has an
   "Agent + VLA" track (PhysicalRSI) and two "Agent + WAM" entries.

## 1. Protocols

| Tag | Definition | Used by |
|---|---|---|
| 8-cell | Spatial/Object/Goal/LIBERO-10 x Task/Swap, 10 tasks x 10 seeds = 800 episodes (defined by Harness VLA) | Harness VLA, ChunkAct, EmbodiedRSI, OpenRUA, ORA, Astra+ICL, OmniBrain-0, HexaShell (subset) |
| 6-cell | Spatial/Object/Goal x Task/Swap, 60 tasks x 50 seeds (CaP-Gym; defined by ASPIRE's use) | ASPIRE, HarnessPAI, AMP1, OpenRUA, RoboAuto, WAA, SPARK, Pigey, RHO, RATS, Robo-Harness K1 |
| 4-cell | Goal + LIBERO-10 x Task/Swap, 20 seeds per task = 800 episodes | Zetta, DynaHarness |
| Long zero-shot | LIBERO-Pro Long with a skill library built only on LIBERO-90 | Skill2Real, ASPIRE |
| Own panels | PyRUA-Lean 40 tasks x 5 seeds; RoboACE 200 conditions; RoboRSI 120 tasks x 5; RAX position-only; HexaShell 156 tasks x 10 | as named |
| Policy boards | LIBERO-PRO v1 (arXiv:2510.03827) and LIBERO-Pro2.0 (arXiv:2610.24587; 17 policies, no agent entries) | flat policies only |
| RoboDojo-Sim official | 42 bimanual tasks, 50 hidden layouts per task; Average = mean of five dimension values; Score (partial credit) and SR% | robodojo-benchmark.com |

## 2. LIBERO-Pro

Executor column: **VLA** = a frozen VLA performs contact phases; **no VLA** =
the model's code or direct end-effector targets drive IK / motion planning.

### 2a. 8-cell (800 episodes)

| System | Upper model | Executor | Learns where | Score | Source |
|---|---|---|---|---|---|
| GPT-6 Astra + ICL (SenseNova) | GPT-6 Astra | no VLA (direct control) | same task (RPent seed-0 memory as examples) | 98.25 (786/800) | arXiv:2610.22471v2 |
| HexaShell + task skills (HexaFuture) | GPT-6 Astra | no VLA (Python over 14 geometry tools + SAM 3) | same task (dev states 0-19, test 20-29) | 97.4; without skills 79.0 | arXiv:2610.23479v3 |
| Harness VLA / RPent (Tsinghua) | GPT-6 Astra low (Codex) | **VLA** (frozen pi0.5-SFT "piRLinf") + 6 analytic primitives | same task (seed-0 exploration memory) | 92.63; Opus 4.7 82.40; GPT-5.5 75.13; Qwen3.6-27B 70.63 | arXiv:2607.08448v5; rpent.readthedocs.io leaderboard |
| OpenRUA (UCL/CMU) | Claude Opus 5 (Claude Code) | no VLA (code over ROS 2) | none | 87.0 | arXiv:2610.02459 |
| EmbodiedRSI (Columbia/Princeton) | not identified in our read | **VLA-class** frozen robot foundation model | same task (10 evolve seeds, 10 disjoint test seeds) | 86.8 | arXiv:2610.10498 |
| ChunkAct (USC/UCF) | GPT-5.6-sol high | **VLA** (piRLinf) + chunks compiled offline from memory | same task (inherits Harness VLA memory) | 83.8 (own Harness VLA rerun 78.8) | arXiv:2610.18874 |
| ORA (UCSD blog) | DeepSeek-V4.1-Flash | no VLA (code) | none | 81.4 (651/800) | haoailab.com/blogs/ora |
| OmniBrain-0 RSI (Xiaomi) | own 9B model distilled from GPT-5.6-Sol | skills incl. **VLA** skills | distillation + experience library | 69.3; teacher GPT-5.6-Sol few-shot 78.3; pi0.5 43.8 in the same table | arXiv:2610.36013 Table 1 |
| References on the RPent board | — | — | — | piRLinf alone 50.0; pi0.5 11.0; ASPIRE listed 61.36 | RPent leaderboard |

Harness VLA without memory (Claude Code, Goal suite only): 31.0 Swap / 79.0
Task. Its "motor only" setting (no VLA) on Long Task: 38.

### 2b. 6-cell (60 tasks x 50 seeds)

| System | Upper model | Executor | Learns where | Score | Source |
|---|---|---|---|---|---|
| ASPIRE, per-task debugging (NVIDIA) | Opus 5.5 / GPT-6 Astra | no VLA (code + IK/cuRobo) | same task (seeds 51-65, test 1-50) | 98.9 / 97.8; original Opus 4.6 72.0 | arXiv:2607.00272v2 |
| HexaShell + task skills | GPT-6 Astra | no VLA | same task | 98.0; without skills 83.3 | arXiv:2610.23479v3 |
| HarnessPAI (Darwin Agent Team) | GPT-5.6-sol writes the program, Gemini-3.5-Flash diagnoses rollout video | **VLA** (frozen pi0.5-LIBERO as primitive inside a fixed program) | same task (program evolved on seeds 0-14; the 50 test seeds include those 15) | 96.5 | arXiv:2609.29166v2 Table 7 |
| AMP1 (Apple) | Gemini 4 Argon | no VLA (model writes Python in the control loop; depth + calibration given) | none | 95.2 | arXiv:2611.09892 |
| OpenRUA | Opus 5 | no VLA | none | 91.8 | arXiv:2610.02459 |
| RoboAuto (WashU) | Opus 4.6 | no VLA (code) | same task (15 training scenes) | 89.1 | arXiv:2610.36533 |
| Robo-Harness K1 | Gemini 3.7 Flash + K1 perception tools | no VLA | none (abstract-level read) | 77.8 (77.2 on the 6 cells per HexaShell) | arXiv:2609.29389 |
| WAA | Gemini 3.7 Flash | no VLA (IK/cuRobo) | transfer (skills evolved on LIBERO-90, frozen) | 75.6; zero-shot 28.9 | arXiv:2609.29964 |
| SPARK | Qwen3.8-27B (local) | no VLA | none | 75.1 | arXiv:2606.30613v5 |
| Pigey (Princeton/Together AI) | Opus 4.7 | **VLA** (frozen pi0.5-LIBERO) + TAMP skills | none | 53.3 | arXiv:2607.21725 |
| References | — | — | — | RHO 45.0; RATS 43.8; CaP-Agent0 18.2; pi0.5 12.8 (public) / 34.9 (LIBERO-finetuned, HarnessPAI's run) | respective papers |

HarnessPAI's Table 7 also quotes Harness VLA on these six cells: Claude Code
87.7, Codex 79.3 (10 seeds per task).

### 2c. 4-cell (Goal + LIBERO-10, 800 episodes)

| System | Upper model | Executor | Learns where | Score | Source |
|---|---|---|---|---|---|
| DynaHarness (NTU) | Qwen3-VL-4B | **VLA** (frozen public pi0.5) + analytic recovery skills | offline failure attribution, paired validation, registry admission | 74.25 | arXiv:2609.40306 |
| Zetta (Tsinghua AIR) | GPT-5.6-sol | **VLA** (frozen pi0.5) + critics + recovery playbook | same task (50 dev seeds) | 71.13 (baseline 32.00) | arXiv:2608.16590 |
| Harness VLA as rerun by DynaHarness | Opus 4.7 / GPT-5.5 / Qwen3-VL-4B | **VLA** | same task | 76.8 / 60.5 / 6.0 | arXiv:2609.40306 Table 1 |

### 2d. Long zero-shot, and own panels

| System | Upper model | Executor | Learns where | Score | Source |
|---|---|---|---|---|---|
| Skill2Real (Long zero-shot) | GPT-6 Astra (Opus 5: 49.0) | no VLA (code/API) | transfer from LIBERO-90 | 56.3 | arXiv:2610.02788 |
| ASPIRE (Long zero-shot) | Opus 4.6 | no VLA | transfer from LIBERO-90 | 30.5 | arXiv:2607.00272 Table 8 |
| PyRUA-Lean (PKU/NUS/NVIDIA), 40 tasks x 5 seeds | GPT-6 Astra high | **VLA** (frozen pi0.5) + RPent primitives + SAM 3 | none | 94.0 with Python cells; 83.0 with tool calling; 80.5 with the VLA removed | arXiv:2610.01939v2 |
| RoboACE (MMLab@SIAT), 200 conditions | GPT-6.1 Terra high | **VLA** (official pi0.5) + SAM 3 | transfer (harness evolved on LIBERO only, deployed frozen) | 74.0 (before evolution 59.0; pi0.5 alone 60.5; RPent without target experience 32.5) | arXiv:2611.13034 |
| RAX (Harvard/NVIDIA et al.), position perturbation only | Opus 5.5 xhigh (Claude Code) | no VLA (code) | explores up to 20 episodes on unperturbed layouts | 76.0; 84.4 with up to 5 adaptation episodes | arXiv:2610.22496 |
| RoboRSI (SJTU), 120 tasks x 5 | GPT-5.6-sol | no VLA | self-improving | 49.5 | arXiv:2610.12424 |
| S2, LIBERO-PRO v1 axes | Kimi K2.5 rewrites the instruction | **VLA** (fine-tuned pi0.5) | none | Position 46.4 / Task 40.75 | arXiv:2606.02735 |
| LIBERO-Pro2.0 policy board | — | flat policies | training | MolmoAct2 71.2; Cosmos Policy 70.8; pi0.5 66.7 | arXiv:2610.24587 |

## 3. RoboDojo

### 3a. Official RoboDojo-Sim board (site data, last update 2026-11-03)

| Rank | Entry (track tag) | Upper model | Executor | Learns where | Score / SR% | Source |
|---|---|---|---|---|---|---|
| 1 | Q0-Preview (Agent) | Opus 5.5 by default config; GPT-6 Astra as alternative config | no VLA (model outputs spatial points from 3 RGB views; CuRobo) | none at run time; ships per-task guidance files | 74.20 / 68.87 | board; XPolicyLab Q0_Preview adapter |
| 2 | GO-3 Nano Preview (Agent + WAM) | not disclosed | world-action model (GE-Act 2.0 family, fine-tuned) | training | 61.90 / 56.42 | board; adapter README; arXiv:2609.05588 |
| 3 | PyRUA-Lean (Agent) | GPT-6 Astra high | no VLA (own geometric primitives + SAM 3) | none | 55.26 / 50.35 (paper's own run 58.20 / 51.62) | board; arXiv:2610.01939v2 |
| 4 | HexaShell-Preview (Agent) | GPT-6 Astra (Codex) | no VLA (per-task tools) | same task (tools repaired after failures on the first 10 layouts of seed 0) | 53.18 / 46.85 | board; arXiv:2610.23479v3 |
| 5 | WorldScape-R2SI (Agent + WAM) | not disclosed | code tools, or world-action model takeover | outer loop: reflection, paired validation, version activation | 46.58 / 39.35 | board; github.com/manifoldai-research/R2SI |
| 6 | EmbodiedEvo (Agent) | GPT-6 Astra xhigh | no VLA (code) | same task (one Playground scene per task) | 45.08 / 38.95 | board; arXiv:2610.18867 |
| 7-8 | WALL-OSS-1.0-lite (VLA); VPP2 (WAM) | — | flat policies | training | 42.59 / 34.97; 39.26 / 32.26 | board |
| 9 | PhysicalRSI (Agent + VLA; HKU MMLab & KAI) | not disclosed | **VLA**: the agent picks one composition per episode from pi0.5, pi0.5 with sparse memory, or code programs | frozen task-aware memory; outer loop rewrites the harness between rollouts | 36.27 / 31.38 | board; XPolicyLab PhysicalRSI adapter; project page |
| 18 | GPT-6 Astra direct (RoboDojo team) | GPT-6 Astra medium | no VLA (direct end-effector targets) | none | 28.97 / 22.48 | board; arXiv:2609.24170 |
| — | pi0.5 | — | flat VLA | training | 11.44 / 6.93 | board |

The boundary between the "Agent + X" and "VLM + X" tags is undefined
(RoboDojo GitHub issue #75, open, no reply).

### 3b. Self-reported RoboDojo results (not on the official board)

| System | Upper model | Executor | Learns where | Result | Source |
|---|---|---|---|---|---|
| AMP1+ (Apple) | model not confirmed in the sections read (the paper's main model is Gemini 4 Argon) | no VLA (code; RGB only) | same task (up to 48 practice episodes on seed 0, tested on seed 2) / continual single pass over 42 tasks | SR 26.4 zero-shot -> 84.1 per-task practice; 57.6 continual | arXiv:2611.09892 |
| HexaShell, own evaluation | GPT-6 Astra xhigh | no VLA | same task (layouts 0-9, tested on 10-19) | SR 69.92 without skills -> 85.00 with skills | arXiv:2610.23479v3 |
| Fable 5.2 launch page | Fable 5.2 | one shared harness, run internally; executor not described | none stated | 64.9; Opus 5.5 39.4; Gemini 4 Argon 34.2; GPT-6 Astra 29.8; Fable 5.1 27.6 | anthropic.com/claude-fable-and-mythos-5-2 |
| Astra paper ablation (SenseNova) | GPT-6 Astra | **VLA** in closed loop + in-context examples | same-task examples | 54.17 (Astra alone 15.56; + VLA closed loop 23.61; + examples 29.67; VLA alone 6.91) | arXiv:2610.22471v2 |
| RoboDawn (Tsinghua) | GPT-6 Astra | no VLA (discrete motion commands) | one in-context demonstration | SR 35.67 zero-shot -> 47.17 one-shot (42 tasks, 5 runs) | arXiv:2609.22966 Table 4 |
| GPT-as-Policy, 10 tasks x 5 | GPT-6 Astra | Hybrid: **VLA** (task-finetuned pi0.5 proposes chunks, Astra reviews and corrects) | none | Hybrid SR 48 / Score 62.60; Direct SR 26 / 37.81 | arXiv:2609.38537 Table 14 |
| FastHarness (SJTU/ZJU), 4 tasks | GPT-6 Astra as reviewer | **VLA** (frozen pi0.5) | same task (persistent per-task memory) | mean 97.19 | arXiv:2610.31427 |
| RAX, 7 tasks | Opus 5.5 | no VLA (code) | exploration episodes | average Score 78.3 (VPP2 24.9) | arXiv:2610.22496 |

## 4. What the evidence supports

1. VLM planning + frozen VLA execution is common on LIBERO-Pro (Harness VLA,
   PyRUA-Lean, ChunkAct, EmbodiedRSI, Zetta, DynaHarness, RoboACE, HarnessPAI,
   OmniBrain-0, Pigey, S2) and present on RoboDojo (PhysicalRSI on the board;
   GPT-as-Policy, FastHarness and the Astra-paper ablation off the board).
2. A frozen VLA wrapped in a harness that grows from failures with gated
   admission is published several times (Zetta, DynaHarness, EmbodiedRSI,
   HarnessPAI on same-task seeds; RoboACE with LIBERO -> LIBERO-Pro transfer;
   PhysicalRSI and WorldScape-R2SI on RoboDojo).
3. Frontier models are used with VLA executors (Astra in Harness VLA and
   PyRUA-Lean; GPT-6.1 Terra in RoboACE), but the strongest recent results
   do not use a VLA: AMP1 95.2 zero-shot, OpenRUA 91.8 zero-shot,
   HexaShell 98.0 and Astra+ICL 98.25 with same-task experience. PyRUA-Lean
   measures the VLA's contribution at +13.5 points on LIBERO-Pro (80.5 ->
   94.0) and drops the VLA on RoboDojo. The top of the RoboDojo board is
   agents without a VLA or with a world-action model; the one Agent + VLA
   entry (36.27) is below the best flat policies (42.59).
4. Saturated: LIBERO-Pro 6-cell and 8-cell (zero-shot 87-95; with same-task
   experience 96-98). Not saturated: Long zero-shot from LIBERO-90 (best
   56.3), RoboACE's LIBERO-X panel (30.5), the official RoboDojo board (best
   74.20; self-reported 84-85 with per-task practice).

## 5. Known discrepancies and unread parts

- Harness VLA with GPT-5.5: 72.1 (paper) / 75.13 (board) / 78.8 (ChunkAct's
  rerun with GPT-5.6-sol).
- ASPIRE Opus 4.6 on LIBERO-Pro: 72.0 (own) / 71.7 (HarnessPAI) / 61.36
  (RPent board, 8-cell) / 63.2 (RAX, position only).
- pi0.5 on LIBERO-Pro ranges from 11.0 to 60.5 depending on checkpoint and
  panel; never quote it without both.
- GPT-6 Astra direct on RoboDojo: 22.48 official; 15.56, 26, 29.8, 35.67 in
  other harnesses.
- PyRUA-Lean and EmbodiedEvo official-board numbers differ from their papers.
- Not read first-hand: Robo-Harness K1 beyond the abstract; EmbodiedRSI's
  planner model; which model AMP1+ used on RoboDojo; the agent side of GO-3
  Nano and the model behind PhysicalRSI and R2SI (not disclosed).
- The decision on our baseline set and target benchmark is open and belongs
  to the project leads; this file only records the evidence.
