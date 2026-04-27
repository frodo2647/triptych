---
name: work
description: Formalization mode — actually do the work. Activates the rigor pose — emits claims, runs the verifier loop, keeps research state live, surfaces /think-rigorously patterns silently. Third of five core commands (start → explore → work → check → wrap). Use when committed to a specific problem and ready to derive, prove, compute, or analyze with rigor. Re-runnable mid-session if the rigor pose has slipped.
---

# /work

The default mode for actually solving the problem. Where the verifier runs, claims get emitted, the research state stays live, and the domain mentor surfaces patterns silently.

`/work` is what makes Triptych Triptych. Most session time is spent here.

## When to use

- After `/start` (formalization phase) → straight into `/work`.
- After `/explore` crystallizes into a specific question → `/work <crystallized goal>`.
- Mid-session when rigor has slipped (verifier stopped, claims aren't being emitted) → `/work` re-establishes the pose.
- When the user says "let's derive," "let's compute," "prove this," "let me solve for X."

## Step 1: Check / seed research state

Read session and research state:

```python
import sys; sys.path.insert(0, '.')
from core.session import read_session
from core.research import read_state
s = read_session()
state = read_state()
```

Three cases:

- **No goal in session** — say *"No goal yet. Run `/start` first, or pass one: `/work <goal>`."* Exit unless goal arg was supplied.
- **Phase is exploration** — switch to formalization. Confirm with user briefly: *"Crystallizing on `<goal>`. Switching to formalization mode."* Then `init_research(goal)` to seed state.md + deps.json + session.json with phase=formalization.
- **Phase is formalization, state already seeded** — proceed.

If `/work` was called with args (`/work <sub-goal>`), the args either replace the goal (rare — usually means re-starting) or refine it as a sub-question. Ask the user which they meant if ambiguous.

## Step 2: Activate the rigor pose

Three things have to be live during `/work`:

**1. Research state visible:**
```python
from displays import show_research
show_research()
```
This pins the Research State tab (Alt+2). It auto-updates as `emit_claim`, `add_established`, etc. fire.

**2. Verifier loop running** (only if claims will be emitted):
```
/loop 60s /verifier
```
Start it before the first claim. If it's already running from this session, no-op.

**3. Domain mentor primed.** Read `CLAUDE.local.md` `## Domains`. The relevant mentor (`/physics-in-triptych`, `/math-in-triptych`, `/ml-in-triptych`) is now active by tag — its rigor patterns and pitfall warnings should surface naturally as the work proceeds.

## Step 3: Surface `/think-rigorously` patterns silently

Before the first equation / step / experiment, run a one-minute self-audit on the goal:

1. **Type / dimension check** — what are the symbols, what are their types/units?
2. **Decompose** — is the problem small enough to hold in one screen? If not, name the parts.
3. **Bound-then-refine** — order-of-magnitude envelope before precise computation.
4. **Sanity at limits** — what should the answer reduce to in the trivial cases?
5. **Falsifiability** — what would change my mind?
6. **What's missing?** — what assumption is silently load-bearing?

These are silent during `/work` (mention only when one *changes* a result), audible during `/explore` (use as Socratic prompts).

## Step 4: Emit claims as they become real

Whenever the work produces a non-trivial assertion (a derivation step, a computed result, a key intermediate, a new equation), emit a claim:

```python
from core.verify import emit_claim
emit_claim(
    "<the claim, in plain language or notation>",
    "<one-line context: what operation produced it>",
    depends=["A1", "C2"],  # IDs of upstream assumptions/claims
)
```

The verifier loop drains the queue async — don't block on it. Poll results when a downstream decision depends on a claim:

```python
from core.verify import read_verification_results
new = read_verification_results()  # only entries since last poll
for r in new:
    if r['type'] == 'result':
        process_result(r['claimId'], r['status'], ...)
```

For the load-bearing assumptions in this work, register them so they show up in the dependency graph (and the assumptions display, if used):

```python
from core.research import add_node
add_node('A1', 'assumption', 'Small-angle regime', 'provisional')
```

## Step 5: Surface assumptions and claims-in-flight (when applicable)

If the work has non-trivial assumptions, show them:

```python
from displays import show_assumptions
show_assumptions(from_research=True, subtitle='for the <goal>')
```

If claims are actively in flight, show the verification timeline:

```python
from displays import show_claims_status
show_claims_status(subtitle='for the <goal>')
```

These don't have to be live — but if the work has more than two or three of either, surface them rather than burying them in prose.

## Step 6: Suggest the next move

Don't auto-chain — just surface options as work progresses:

- Major result just established → *"Good time to `/check`?"*
- Stuck for 15+ minutes → *"Want to `/explore` other framings?"*
- Session winding down → *"Ready to `/wrap`?"*

## Args

- `/work` — activates rigor pose for the current goal in session.
- `/work <sub-goal>` — refines on a sub-question; or, if no session goal yet, sets it directly.

## Hard rules

- **Don't start the verifier loop if no claims will be emitted.** Pure analytical writing or design conversation doesn't need it. Use judgment.
- **Don't mention rigor patterns unless one changes a result.** They're silent during formalization; the user doesn't need a checklist read aloud.
- **Re-runnable mid-session is a feature, not a problem.** If rigor has slipped, the user can call `/work` again and the state gets re-pinned.
- **`/work` doesn't drive autonomy.** For autonomous problem-solving without the human, use `/autonomous` directly — that's a different mode.
