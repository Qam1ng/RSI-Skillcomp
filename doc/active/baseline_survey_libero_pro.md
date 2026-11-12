# Baseline survey: who scores what on LIBERO-Pro, and how (researched 2026-11-12)

Purpose: the project pivoted to "VLM planner + VLA executor + growing skill
library". This document redefines the baseline set with sourced numbers.
Every number below carries its source; items the search could not verify are
marked UNVERIFIED. Four parallel deep searches (ASPIRE, LIBERO-Pro protocols,
hierarchical VLM+VLA systems, self-improving harnesses) feed this file.

## 1. "LIBERO-Pro" is three incompatible protocol families

Numbers are NOT comparable across these. Always name the protocol next to a
score.

1. **LIBERO-PRO v1** (arXiv:2510.03827, 2025-10; github.com/Zxy-MLlab/LIBERO-PRO).
   4 suites (Goal/Spatial/Object/LIBERO-10) x 5 perturbation axes
   (Object/Position/Semantic/Task/Environment), 50 episodes per task, success
   judged by LIBERO's built-in binary goal predicate. Headline: models above
   90% on vanilla LIBERO collapse to ~0.0 on Position/Task axes (Object and
   Semantic axes barely drop).
2. **The agentic protocol on v1** (defined by ASPIRE, arXiv:2607.00272):
   position+task perturbations, "160 tasks, each evaluated on 50 held-out
   seeds" (project page); learn on seeds 51-65, evaluate on seeds 1-50
   (Table 5 caption). WAA and RATS report against this family. The success
   judge is NOT stated in the ASPIRE paper (searched full HTML) — open
   question before we adopt the protocol verbatim.
3. **LIBERO-Pro2.0** (arXiv:2610.24587, 2026-10-17;
   github.com/LIBERO-Pro-Team/LIBERO-Pro2.0): 42 perturbation types (22
   static + 20 runtime), 1,646 valid task-perturbation instances, 32 train /
   8 held-out tasks, fixed checkpoints, 17-policy leaderboard. Episodes per
   variant not stated in the paper (repo examples use seeds 142-144).
   Separately, **Harness VLA** (arXiv:2607.08448) defined its own 800-episode
   Task/Swap protocol (10 tasks x 10 fixed initial states x 8 cells).

## 2. The standings

### 2a. Agentic systems, v1 agentic protocol (overall average)

| System | Score | Source |
|---|---|---|
| **WAA** (World Action Agent) | **75.6** | arXiv:2609.29964 Table 1 ("WAA with skills evolved only from LIBERO-90 reaches a state-of-the-art 75.6% average success") |
| **ASPIRE** (Claude Opus 4.6) | 72.0 | arXiv:2607.00272 Table 5 |
| ASPIRE (Claude Opus 5.5) | ~99 ("nearly saturates", abstract) | same paper, abstract + Table 18 (99.2% at $18.29/task; Sonnet 5.5 98.8% at $12.11) |
| RATS (Playful) | 43.8 | WAA Table 1 (RATS' own claim: +20.6pp over CaP-Agent0, arXiv:2606.19419) |
| CaP-Agent0 | 18.0-23.2 | ASPIRE Table 5 (18.0); WAA Table 1 (18.2 CaP-X / 23.2 Playful) |
| pi0.5 (flat VLA) | 12.8-13.0 | ASPIRE Table 5 (13.0); WAA Table 1 (12.8) |
| Show-Harness | 6.7 | WAA Table 1 |
| OpenVLA, pi0 (flat VLA) | 0.0 | ASPIRE Table 5 (full-row zeros) |

### 2b. LIBERO-Pro **Long, zero-shot transfer** (library built on LIBERO-90) — the unsaturated battlefield

| System | Score | Source |
|---|---|---|
| **Skill2Real** | **56.3** (from 2.0) | arXiv:2610.02788 abstract ("raises LIBERO-Pro Long success from 2.0% to 56.3%"; GPT-5.6 Sol learns, GPT-6 Astra evaluates frozen; ablations: -17.3pp without Verifier, -13.3pp without Governor) |
| ASPIRE (N=90 source tasks) | 30.5 overall (22.6 Pos / 38.3 Task) | arXiv:2607.00272 Table 8 |
| pi0.5 | 5.0 | same Table 8 |
| CaP-Agent0 | 3.8 | same Table 8 |
| OpenVLA, pi0 | 0.0 | same Table 8 |

ASPIRE's Opus 5.5 config also does NOT saturate Long the same way its main
suites do (97.9% on Long is with full learning, not zero-shot transfer —
S3.8). Zero-shot Long transfer is where headroom lives.

### 2c. Pure-VLA leaderboard, LIBERO-Pro2.0 (17 policies, mean success % on 8 held-out tasks)

Top-5 static: MolmoAct2 71.2, Cosmos Policy 70.8, LingBot-VA 68.7,
**pi0.5 66.7**, X-VLA 61.2. Top-5 runtime: LingBot-VA 81.8, MolmoAct2 76.9,
**pi0.5 73.8**, Cosmos Policy 72.2, FastWAM 70.1. (arXiv:2610.24587 Tables
1-2.) Note: under Pro2.0's milder/held-out protocol pure VLAs are far from
dead — the "VLAs collapse to zero" story is specific to v1's Position/Task
axes and the agentic protocol.

### 2d. VLM-planner + VLA-executor entries on LIBERO-Pro (adversarial
re-check 2026-11-12: THE SLOT IS OCCUPIED — full texts fetched)

- **S2** ("See Less, Specify More: Visual Evidence Budgets for Generalizable
  VLAs", arXiv:2606.02735) — the CLEAN counterexample. "an off-the-shelf VLM
  provides local subtask guidance" (S3.3); "The planner never outputs robot
  actions directly" (App B.1); "all experiments instantiate S2 with a
  pi0.5-based executor" (S4.1). Planners: Kimi K2.5 (default), GPT-5.4 nano.
  Full LIBERO-PRO perturbation breakdown (Table 1), e.g. libero_spatial
  Obj/Pos/Sem/Task = 99.0/55.0/90.5/54.5 (Kimi K2.5).
- **Harness VLA** (arXiv:2607.08448v5) — hybrid executor, full text fetched:
  "For contact-rich phases, it invokes a frozen VLA through a single learned
  primitive, vla_act" (S1); "the agentic planner selects structured calls
  from a fixed primitive library rather than emitting low-level actions
  directly" (Fig 1); analytic primitives move_to / rotate_wrist /
  set_gripper / release; frozen VLA = RLinf "pi05_libero130_fullshot"
  pi0.5-SFT checkpoint (piRLinf). Planners: Codex GPT-5.5 72.1, Claude Code
  Opus-4.7 82.4, **GPT-6 Astra 92.63 (741/800, Table 21)** on the
  800-episode Task/Swap protocol (8 cells x 10 tasks x 10 seeds, App C.2).
  Flat baselines same protocol (Table 3): OpenVLA 0.0, pi0 0.3, pi0.5 11.0,
  MolmoAct 1.5, X-VLA 3.8, piRLinf 50.0. (The mirror-board 98.25 belongs to
  a different paper, 2610.22471 — still unverified.)
- **ChunkAct** (arXiv:2610.18874) — same hybrid pattern, confirmed from full
  text: "An agentic system solves a manipulation task with an LLM planner"
  (S3.1); "delegating contact-rich stages such as grasping or fixture
  actuation to the VLA policy" (S3.2); "The VLA primitive is piRLinf"
  (S4.1). Planner GPT-5.6-sol high reasoning. LIBERO-Pro 83.8 overall TSR
  vs Harness VLA 78.8 (Table 1); LIBERO-Plus zero-shot 83.9 vs 72.9
  strongest flat VLA (Table 3). Call-efficiency axis occupied: 2.9x fewer
  LLM calls, 4.4x/2.3x fewer input/output tokens — our dispatch-amortization
  claim must compare against this.
- **HiRoC** (arXiv:2608.05999, LIBERO-Plus): fine-tuned Qwen2.5-VL-3B
  planner (LoRA) + OpenVLA-OFT executor; "best generalization across all
  perturbation types" on LIBERO-Plus (numbers in Figure 3 only); vanilla
  LIBERO 93.5 avg / Long 98.0.
- **RPG** (arXiv:2610.02204): own 22-task suite (not LIBERO-Pro): 95.0% after
  15 practice rounds vs ASPIRE 75.5% and CaP-Agent0 60.0% on the same suite.
  Only other system with a direct head-to-head vs ASPIRE.

## 3. Pipelines of the systems that matter (one paragraph each)

- **ASPIRE** (NVIDIA GEAR; arXiv:2607.00272; github.com/NVlabs/ASPIRE):
  closed-loop execution engine recording per-primitive multimodal traces +
  growing skill library ("skills are induced from validated repairs",
  admission requires verifier-reproduced success, stored as in-context
  guidance) + evolutionary program search (population of K candidates,
  conditioned on best programs + remaining failures; triggered on tasks below
  90%). Perception/geometry/motion exposed as robot programming APIs
  (cap_localize_object from calibrated RGB-D; Mink IK; cuRobo planning).
  NOTE: the paper's prose never describes the SAM-3 + depth-backprojection
  stack; SAM3 appears only as gated weights in the README quick start.
  Engine ablation: 14% -> 62% (execution engine) -> 72% (+evolutionary
  search). Run-to-run std 3.4% (Table 25). Code public.
- **WAA** (arXiv:2609.29964, "working in progress", no code): VLM
  (Gemini 3.7 Flash) acts through a "visual action workspace" with
  auto-selected contact views; "action rehearsal" previews and revises
  proposals before execution; "in-view correction" trims residual offsets;
  skill library seeded by Codex (GPT-5.5) from the harness API + one expert
  trajectory per LIBERO-90 task, evolved by three GPT-5.5 roles
  (Learner/Editor/Reviewer), frozen before evaluation. **No VLA executor** —
  execution is through the harness API. Also: fine-tuning Qwen3.5-9B on
  harness traces lifts out-of-domain 1.7% -> 43.3%.
- **Skill2Real** (arXiv:2610.02788, no code found): skills learned on
  LIBERO-90 by GPT-5.6 Sol, evaluated frozen on Pro Long by GPT-6 Astra;
  has a Verifier and a Governor whose removal costs 17.3/13.3pp. Deep read
  required: carrier type (code? weights?) and executor unknown from abstract.
- **Harness VLA / ChunkAct**: deep reads required (abstract-level only).
- **VLAs-as-Tools** (arXiv:2605.13119, code "will be released"): VLM planner
  (Gemini 3 Flash / GPT 5.4 / Qwen3.5) emits tool-family label + grounded
  instruction; VLA (pi0.5 / OpenVLA-OFT) executes with per-family residual
  adapters; 2Hz joint action+progress prediction; runtime monitor with
  completion threshold 0.90 and stagnation replanning. LIBERO-Long: pi0.5
  92.4 standalone -> **80.4 naive planner loop** -> 97.2 full method. The
  -12pp naive-loop result is direct literature support for our verbatim
  forwarding / in-envelope discipline.
- **Hi-VLA orchestration study** (arXiv:2606.10267): flat 43.3 -> naive
  hierarchy 70.0 -> best hierarchy 83.8 on LIBERO-Object-adapted tasks
  (150 trials/task); factor study of planner/controller/switching/memory.
- **RoboCerebra** (arXiv:2506.06677): LIBERO-asset long-horizon benchmark
  with ready-made hierarchical baselines: GPT-4o+OpenVLA 16.04,
  GPT-4o+pi0-fast 15.15, GT-plan+OpenVLA 25.16.
- Related-work-only (no code or no benchmark): Hi Robot (real-robot only,
  20 trials/task, no weights), RT-H (proprietary), Helix (vendor blog,
  latent interface), RoboCat/SIRIUS/YAY (historical), PLD (weight-updating
  self-improvement, LIBERO 91.8->99.2 w/ OpenVLA), RoboMonkey (test-time
  sample-N, LIBERO-Long 49.8->56.5).

## 4. The open slot (corrected 2026-11-12) and the redefined baseline set

RETRACTION: the earlier claim "no hierarchical VLM planner + VLA executor
system reports LIBERO-Pro numbers" is FALSE — S2, Harness VLA and ChunkAct
all do (Section 2d). What still holds, verified:

- LIBERO-Pro2.0's own 17-policy leaderboard contains no hierarchical
  system (all flat policies; the only LLM use is demo generation).
- RoboDojo-Sim has no confirmed VLM-planner + VLA-executor entry
  (leaderboard snapshot lists only flat policies; one GPT-6 Astra rumor via
  ChunkAct's intro could not be located).
- Frontier planners HAVE been paired with VLA executors: Harness VLA runs
  GPT-6 Astra (92.63) and Claude Opus 4.7 (82.4) over vla_act. The
  "frontier models only drive IK/code" reading is therefore also dead.
- The genuinely open slot is now narrower and sharper: **a GROWING skill
  library over a VLA-included carrier set, grown by execution-failure
  attribution**. Harness VLA's library is explicitly FIXED ("a fixed
  primitive library"); ChunkAct optimizes calls, no library growth; S2 has
  no library; Skill2Real GROWS a library but its executor is pure code/API
  ("learns executable skills through a shared application programming
  interface (API)" — no VLA anywhere in the paper); WAA grows a library,
  no VLA; ASPIRE grows a library, code executor. Nobody combines
  between-episode library growth with VLA execution, and nobody applies
  refine/split verdicts from failure clustering to a VLA-carrier skill.

Redefined baseline table (rows we must report against):

1. pi0.5 flat — 12.8/13.0 (v1 agentic), 5.0 (Long zero-shot), 66.7/73.8
   (Pro2.0) — the executor-alone control arm; runnable (openpi public).
2. CaP-Agent0 — 18.0-23.2 — the code-agent control arm.
3. ASPIRE — 72.0 (Opus 4.6) / ~99 (Opus 5.5); 30.5 Long zero-shot — the
   explicit-perception self-improving harness; code public, re-runnable.
4. WAA — 75.6 — current main-suite SOTA; cite (no code).
5. Skill2Real — 56.3 Long zero-shot — the number to beat on the live
   battlefield; deep read pending.
6. **Harness VLA — 92.63 w/ GPT-6 Astra on Task/Swap-800** — the fixed
   -library hybrid our growing library must beat like-for-like; it is also
   the published validation that planner + vla_act works.
7. ChunkAct — 83.8 LIBERO-Pro / 83.9 LIBERO-Plus — the call-efficiency
   comparator for our amortization claim.
8. S2 — the no-library VLM->pi0.5 subtask-guidance arm (clean LIBERO-Pro
   per-axis numbers to cite).
9. Naive VLM+VLA loop (our own ablation arm) — justified by the -12pp
   result in VLAs-as-Tools.

Strategic readings:
- Main suites under frontier models are closed (ASPIRE 99 / Sonnet 5.5
  98.8). Headline battlefield = **LIBERO-Pro Long zero-shot transfer**
  (best known 56.3), which is exactly the skill-library amortization story.
- Cost axes are now contested: $/task (ASPIRE Pareto: Sonnet 5.5 $12.11)
  and calls/tokens (ChunkAct). Our falling-cost-with-library-growth curve
  must be reported against both.
- ASPIRE's role changes from substrate to strongest published baseline;
  WAA already cross-reports its numbers, so citing is standard practice.

## 5. Verification debts before any number enters a manuscript

- ASPIRE: success judge unstated; abstract "80 tasks" vs project page "160
  tasks"; abstract 72% vs Table 6 92% on two_arm_handover — check PDF.
- Harness VLA absolute SRs; ChunkAct 78.8/83.8; GPT-6-Astra 98.25 on the
  mirror board — all UNVERIFIED.
- Deep reads owed: WAA, Skill2Real, ChunkAct, Harness VLA, RATS, RPG.
- LIBERO-PRO v1 paper reports no seeds; Pro2.0 episodes-per-variant
  unstated. Protocol details must be pinned from code before we adopt one.
