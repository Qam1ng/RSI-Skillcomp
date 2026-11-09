# Related work: MoE and expert libraries in robotics (surveyed 2026-11-09)

Two layers of "mixture of experts" exist in current robot-manipulation work.
Both must be cited; neither occupies our slot. Source: web survey 2026-11-09;
read the papers before quoting numbers in the manuscript.

## Layer 1 — MoE inside the VLA architecture (orthogonal to us)

- AdaMoE (arXiv 2510.14300, 2025-10): replaces the feedforward layers of
  pi0's action expert with sparse MoE layers; decouples expert selection
  from contribution scaling. Reported: LIBERO 94.2 -> 96.0, RoboTwin +9.3.
  Ablations: top-k=1 best, 4 experts beat 8; even collapsed-to-one-expert
  MoE beats dense. Orthogonal: our library could carry an AdaMoE-ized
  backbone as a carrier without touching the pipeline.
- DiTEA (AAAI): MoE inside a diffusion action head, with a task-instruction
  gate for multi-task weight conflicts.

## Layer 2 — LoRA-expert libraries with routing (our close neighbors)

- MoIRA (arXiv 2507.01843, Neurocomputing 2026): frozen text router +
  one LoRA per expert, on GR00T-N1 and pi0. "Planner as router" exists.
- CORAL (arXiv 2603.09298, 2026-03): one LoRA expert PER TASK, runtime
  swap by instruction. Note: per-task experts are exactly our
  pre-registered example of a BAD split (one expert per cup type).
- DMPEL (arXiv 2506.05985, 2025-06): a GROWING library of low-rank
  experts + lightweight router, lifelong learning on LIBERO; forgetting
  handled by coefficient replay at the router. Closest single paper to us.
- LAR-MoE (arXiv 2605.06175, 2026-03): routes manipulation primitives
  (reach/grasp/insert) to experts; pretrains routing separately to avoid
  expert imbalance.
- CoRDE (ICML 2026): concept-prior routed diffusion experts; argues pure
  data-driven MoE routing collapses.
- VLA-GSE (2026): always-active generalized expert + top-k routed
  specialists on the VLM side.

## What this changes in our positioning

"Shared backbone + LoRA expert library + router" and even "growing library
with anti-forgetting" are NO LONGER open slots (DMPEL touches both). Our
novelty must rest on the decision mechanism, not on the library's
existence. Still absent from every paper above:

1. Failure attribution + the three-way verdict. Their experts are assigned
   per task a priori (CORAL) or added on a lifelong curriculum schedule
   (DMPEL). None decides refine-vs-split from the clustering structure of
   execution failures.
2. Explicit applicability conditions (PRE/EFF). Routing is text similarity
   or a learned gate; no checkable clauses, hence no in-envelope
   leave-it-alone rule.
3. Admission gates and evaluation budgets. No frozen batteries, noise
   floors, or bounded evidence rounds; anti-forgetting is a training trick
   (replay), not a structural property of the store.
4. Carrier heterogeneity. All LoRA-only; nobody runs code skills and
   weight skills in one library under one verdict mechanism.

One-line answer for reviewers: "Our boundary with robot MoE/expert-library
work is not whether a library exists but HOW it grows: theirs by human or
curriculum assignment, ours by execution-failure attribution and a gated
three-way verdict — and CORAL's per-task experts are precisely the
degenerate split our mechanism is designed to refuse."
