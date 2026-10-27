#!/usr/bin/env python3
"""Counterfactual flip probe for context assembly (component bench, probe #2).

Build two contexts that differ by exactly ONE precedent (the "needle"), ask the
same frozen judge k times each, and measure how the decision distribution moves.
If adding the decisive memory never flips the decision, the memory is not being
read - assembly quality upstream is moot.

Ground truth is by construction (we plant the needle), so this is a component
bench test, not an experimental claim about tasks.

Usage: GEMINI_API_KEY=... python tools/probe_flip.py [--k 5] [--model gemini-flash-latest]
Writes data/probe_flip.json.
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path

API = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"

JUDGE_PROMPT = """You are the triage judge of a robot skill library.
A skill call failed. Decide ONE action:
- retry: the skill is fine, the planner mis-called it; just re-plan.
- refine: the failure is within the skill's declared scope; continue training THIS skill.
- split: failures cluster on inputs the skill was never meant to handle; fork a NEW
  specialist skill with its own use-conditions.

{context}

=== CURRENT FAILURE ===
{failure}

Answer with exactly one word on the first line: retry, refine, or split.
Then one sentence of justification citing which precedent (if any) you relied on."""

DISTRACTORS = [
    "[precedent P1] place_into v3: failures at release stage, use-conditions satisfied "
    "(in-scope) -> decision: refine -> outcome: 1/5 -> 5/5 after one round. GOOD",
    "[precedent P2] pick_object v5: 3 failures where the planner called it before any "
    "object was visible (planner fault) -> decision: retry -> outcome: re-planning fixed "
    "all 3, no training needed. GOOD",
]

NEEDLE = (
    "[precedent P3] pick_object v5: 5/5 failures clustered on FLAT objects (plate); "
    "use-conditions had admitted them but the grasp recipe cannot handle flat geometry "
    "(out-of-scope input). refine was tried twice and failed -> decision: split -> "
    "outcome: new specialist skill passed the gate 5/5, original skill unaffected. GOOD"
)

FAILURE = (
    "pick_object v5 on task 'put the tray on the shelf': 4/5 seeds failed at the grasp "
    "descend stage. The tray is a FLAT object. Use-conditions (visible and reachable) "
    "were satisfied on every failure. Failure margins cluster tightly (grasp height "
    "below table by 0.01-0.02 m on all flat-object cases; non-flat objects unaffected)."
)


def gemini(model: str, key: str, prompt: str) -> str:
    body = json.dumps({"contents": [{"role": "user", "parts": [{"text": prompt}]}]}).encode()
    req = urllib.request.Request(API.format(model=model, key=key), data=body,
                                 headers={"Content-Type": "application/json"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                d = json.loads(r.read())
            return d["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            if attempt == 2:
                raise
            time.sleep(10 * (attempt + 1))
    raise RuntimeError("unreachable")


def parse_decision(text: str) -> str:
    m = re.search(r"\b(retry|refine|split)\b", text.lower())
    return m.group(1) if m else "unparsed"


def run_arm(name: str, precedents: list[str], k: int, model: str, key: str) -> dict:
    ctx = "=== PRECEDENTS (past failures, decisions, and how they turned out) ===\n" + \
          "\n".join(precedents) if precedents else "(no precedents available)"
    counts = {"retry": 0, "refine": 0, "split": 0, "unparsed": 0}
    cites = 0
    for _ in range(k):
        out = gemini(model, key, JUDGE_PROMPT.format(context=ctx, failure=FAILURE))
        counts[parse_decision(out)] += 1
        if "P3" in out:
            cites += 1
    return {"arm": name, "n": k, "decisions": counts, "cited_needle": cites}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--model", default="gemini-flash-latest")
    args = ap.parse_args()
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        print("missing GEMINI_API_KEY", file=sys.stderr)
        return 2
    arms = [
        run_arm("no_needle", DISTRACTORS, args.k, args.model, key),
        run_arm("with_needle", DISTRACTORS + [NEEDLE], args.k, args.model, key),
        run_arm("empty_context", [], args.k, args.model, key),
    ]
    out = {"probe": "counterfactual_flip", "model": args.model,
           "needle_truth": "split", "failure": FAILURE, "arms": arms}
    Path("data").mkdir(exist_ok=True)
    Path("data/probe_flip.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out["arms"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
