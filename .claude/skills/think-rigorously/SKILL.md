---
name: think-rigorously
description: First-person rigor patterns for non-trivial work — type/dimension check, decompose, bound-then-refine, sanity at limits, falsifiability. Use before starting a derivation, proof, training run, or analysis, and again when stuck. Sister to /scientific-critical-thinking (about others' claims) and /hypothesis-generation (structured ideation); this one runs on your own working before claims solidify.
---

# Think Rigorously

Most stuck-ness is a missed pattern, not a missing fact. These five checks
take a minute each and catch the errors people actually make. Run them
before the algebra, before the training loop, before the proof — and again
any time the work isn't moving.

## When to use

- After the goal is stated, before any equation or code is written
- When a result feels right but you can't say *why*
- When stuck for ~10 minutes — most stuck-ness violates one of these patterns
- During formalization, silently. During exploration, as a question to the user

## The five patterns

### 1. Type / dimension check

Write the type of every symbol and the expected type of each side of each
equation. Physics: dimensions in [M L T] — `mcp__sympy-mcp__quantity_simplify_units`.
Math: domain & codomain. ML: tensor shape, dtype, device — most "training
is broken" is a shape mismatch. Data: column dtype + unit (cents vs. dollars
has bitten more analyses than missing data has). Wrong type → no amount of
careful work after will fix it.

### 2. Decompose until pieces fit one screen

If the problem doesn't fit on one screen, you don't see it. Break it into
parts each small enough to hold in your head; name the parts; write the
names down. The parts are usually independent enough to verify separately.

### 3. Bound-then-refine

Before any precise calculation, give an order-of-magnitude envelope. "This
integral is between 0 and 100." "This model trains in roughly an hour."
"This proof uses at most 3 lemmas." When the precise answer arrives, it
must agree. If it doesn't, **one of them is wrong** — and the envelope is
usually right.

### 4. Sanity at the limits

Once you have a result, plug in: ε → 0, n → ∞, batch → 1, params → 1, t → 0
— whichever limits the problem has. Each must reduce to something obvious.
This is the cheapest verifier you have, and it runs before `/verifier`
sees the claim. Render limits side-by-side via `show_latex(name="limits")`.

### 5. Falsifiability — pre-register

Before looking at the answer, write what would change your mind. "If loss
goes up at epoch 3, LR is too high." "Integral > π → sign error." Forces
an honest baseline; prevents post-hoc rationalization.

### 6. What's missing?

Once an answer is in hand, before accepting it, ask the inverse question:
what assumption is this resting on, what would change the answer, what
isn't in the analysis that maybe should be? When the unstated load-bearing
assumption is the actual problem, no amount of careful work *inside* the
frame catches it. For deeper checks at milestones, spawn `/whats-missing`
— but the cheap version of this is a one-minute self-audit before
calling something done.

## Mentor mode

- **Exploration**: surface a pattern as a question. "What's the expected
  dimension?" not "you forgot to dimension-check."
- **Formalization**: apply silently. Mention only when one changed the result.
- **User is driving**: don't volunteer unless something violates a pattern.

Read `phase` from `workspace/research/session.json`.

## Related

- `/scientific-critical-thinking` — these patterns applied to *others'* claims
- `/hypothesis-generation` — structured 8-step ideation, downstream of pattern 5
- `/whats-missing` — deeper version of pattern 6, spawned at milestones
- `/redteam` — challenge the work after pattern 6 (the inverse: what's *wrong*, not what's missing)
- `/verifier` — once claims solidify and `emit_claim` is firing
- `obra/superpowers/verification` (MIT, external) — adjacent for software
  "did I actually run this?" rigor; complementary, not overlapping
- Triptych domain mentors apply these patterns in their domain context
