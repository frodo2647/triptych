---
name: scientific-method
description: Run a formal investigation in Triptych — observe → question → hypothesize → predict → test → analyze → conclude → revise. Use when the work shifts from "I'm exploring" to "I want to know whether X is true," when a result needs to be defensible, or when stakes warrant the discipline. Orchestrates /hypothesis-generation, /literature-review, /verifier, and /autonomous; not a replacement for any of them.
---

# Scientific Method

The classical loop, applied to research work in Triptych. Use when results
need to be defensible, not just interesting. The point isn't following
eight steps — it's making each prediction falsifiable *before* a test
runs, so a post-hoc story can't paper over a null result.

## When to use

- The conversation crystallizes from exploration to formalization
- A result will be cited, shipped, or written up
- The user asks "why does X happen?" and wants the answer to hold up
- A previous investigation got the wrong answer; tighten the loop

If the work is throwaway exploration, skip this — `/think-rigorously` is enough.

## The eight steps in Triptych

### 1. Observe

State what you've actually seen, in `state.md` under "Observations". No
explanations yet — just data points: measurements, training curves,
anomalies. Cite if external.

### 2. Question

Promote the most concrete observation to a falsifiable question. "Why
does accuracy drop on classes 3 and 8?" beats "why is the model bad?"
The question goes in `init_research(goal=...)` and pins to the Research
State tab.

### 3. Hypothesize

Use `/hypothesis-generation` for structured ideation — produces 3-5
competing hypotheses with mechanisms. Don't pick yet.

### 4. Predict

For each hypothesis, write **what would change your mind**. The
prediction must be checkable before you look. "If A is true, classes 3
and 8 should also fail at lower learning rates." Predictions diverging
across hypotheses is what makes a test discriminating.

**CRITICAL: every prediction must be falsifiable before testing.** If
you can't say what result would refute it, it's a vibe, not a prediction.

### 5. Test

Run it. Computational: `/autonomous` to execute, `/verifier` to check
claims. Analytical: `emit_claim()` each step and let the verifier loop
run. Literature: `/literature-review` finds whether the result already
exists. Log result in `state.md` under "Tests".

### 6. Analyze

Compare result to each hypothesis's prediction, using the falsifiability
criterion you wrote in step 4 — not a re-interpretation after seeing the
answer. Match → winner. Match none → return to step 3.

### 7. Conclude

Write the conclusion in `state.md` under "Established": which hypothesis
held, which were ruled out, what the test wouldn't have caught, what's
next. **Remember: a null result is a result.**

Before the conclusion lands as load-bearing for downstream work, spawn
`/redteam` against it (calibrated against false positives — empty findings
is the right answer when the work is sound) and `/whats-missing` to
surface unstated assumptions. One pass each at this milestone is cheap
insurance.

### 8. Revise

Update assumptions. If a long-standing belief was wrong, flag it.
Follow-up questions promote to step 2 of the next loop.

## Mentor mode

Surface the loop *as a frame*, not a checklist. Don't interrupt steps
that are going well. If the user jumps from observation to conclusion
(skipping prediction), that's where to ask "what would have changed
your mind?"

## Related

- `/hypothesis-generation` — structured 8-step ideation, plugs into step 3
- `/literature-review` — for step 5 when the test is "has this been done?"
- `/autonomous`, `/verifier` — for step 5 when the test is computational
- `/think-rigorously` — upstream patterns the loop's predictions rely on
- `obra/superpowers/scientific-method` (MIT, external) — the
  software-debugging variant; complementary
