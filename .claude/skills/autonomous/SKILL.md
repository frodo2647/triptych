---
name: autonomous
description: Autonomous operation — accept a problem, work it independently using the full verification pipeline, maintain research state, produce verified results. Use when handed a problem to solve independently.
---

# Autonomous Operation

You have been given a problem to solve independently. Follow this protocol. It uses the full Triptych v2 infrastructure — research state, verification, and cross-verification.

## The Loop

### 1. Accept problem and initialize

```python
python -c "
import sys; sys.path.insert(0, '.')
from core.research import init_research
init_research('STATE THE GOAL HERE')
"
```

Set the goal to a clear statement of what needs to be shown, found, derived, or understood.

### 2. Exploration phase

Survey approaches before committing to one:
- What methods are available? (Lagrangian, Newtonian, energy methods, etc.)
- What tools are relevant? (SymPy, numerical computation, dimensional analysis)
- What are the key assumptions?
- What prior results or known solutions exist?

Update research state as you explore:
```python
python -c "
import sys; sys.path.insert(0, '.')
from core.research import update_state
update_state('questions', '- What approach should we use?\n- What assumptions are needed?', 'workspace/research')
update_state('assumptions', '- Small angle approximation\n- No friction', 'workspace/research')
"
```

No claims emitted during exploration. No formal verification. You're forming a strategy.

### 3. Crystallize

State a clear research question or hypothesis. Update the goal if needed:
```python
python -c "
import sys; sys.path.insert(0, '.')
from core.research import update_state
update_state('goal', 'Derive the equation of motion for a simple pendulum using the Lagrangian method', 'workspace/research')
"
```

### 4. Formalization phase — derive step by step

Work through the problem. At each significant step, emit a claim:
```python
python -c "
import sys; sys.path.insert(0, '.')
from core.verify import emit_claim
emit_claim('T = (1/2)ml^2 * theta_dot^2', 'kinetic energy in polar coordinates', depends=['A1'], research_dir='workspace/research')
"
```

**When to emit a claim:** new equations, changes in approach, approximations, key intermediate results. Not every mechanical step — use judgment per PRD.

Show your work in the display panel using display addons.

### 5. Between each step — check verification log

```python
python -c "
import sys; sys.path.insert(0, '.')
from core.verify import read_verification_results
results = read_verification_results('workspace/research')
for r in results:
    print(f'{r[\"type\"]}: {r.get(\"status\", r.get(\"kind\", \"\"))} — {r.get(\"detail\", r.get(\"content\", \"\"))}')
"
```

- If flagged: address the issue before continuing. Update attempts if the approach failed.
- If clear: proceed to next step.
- Clear results after reading: `from core.verify import clear_results; clear_results('workspace/research')`

### 6. At milestones — cross-verification

When you've established a significant result (not every claim, but key conclusions):

Spawn the cross-verifier agent:
```
Agent(subagent_type="cross-verifier", prompt="Problem: [problem statement]. Claimed result: [your result]. Verify by solving via a different method.")
```

The cross-verifier independently re-derives the result. If results match, confidence is high. If they diverge, investigate.

### 7. When done — final verification pass

- Start the verifier loop if it isn't already running: `/loop 60s /verifier`. It drains the claim queue via isolated subagents — don't spawn verifiers yourself.
- Wait for `read_verification_results()` to return empty (all claims have results).
- Update research state with final established results
- Update the dependency graph
- Show final results in the display panel with `show_research()`
- Stop the loop: `/loop stop`

```python
python -c "
import sys; sys.path.insert(0, '.')
from displays.research import show_research
show_research()
"
```

## Verification system architecture

The verifier agent (`.claude/agents/verifier.md`) receives only the claims and the original problem statement — never your reasoning. This isolation prevents contamination. For each claim, the verifier decides how to verify:
- Symbolic recomputation via CAS (SymPy MCP, Wolfram Alpha MCP)
- Numerical spot-check (plug in concrete values)
- Dimensional analysis
- Limiting case evaluation
- Comparison against known results
- Independent reasoning

You don't spawn the verifier subagent directly. Instead, start the verifier loop once formal work begins:
```
/loop 60s /verifier
```

The `/verifier` skill drains the queue one claim per tick via isolated subagents. Results land in `workspace/research/verification.log` and flow to research state automatically via `process_result()`:
- **verified** → established results + dependency graph
- **failed** → attempts section only (not in graph)
- **uncertain** → open threads + graph with "unverified" status

If a verification agent fails to return results within a reasonable time, log the failure and proceed with claims marked unverified. Do not block indefinitely on verification.

## Research state reference

Two files in `workspace/research/`, each doing what it's best at:
- **`state.md`** — human-readable narrative with seven sections: Goal, Questions, Assumptions, Attempts, Established Results, Open Threads, Next Step
- **`deps.json`** — machine-parseable dependency graph (nodes + edges with status)

Core operations (`core/research.py`):
```python
import sys; sys.path.insert(0, '.')
from core.research import (
    init_research, read_state, update_state,
    add_attempt, add_established, add_observed,
    add_node, add_edge, invalidate, get_downstream, get_graph,
)
```

- `add_established("R1", "L = T - V", ["A1", "A2"])` — formally verified (requires a verification.log entry); writes to state.md and deps.json with status `verified`
- `add_observed("R2", "accuracy = 99.44%", ["A1"])` — empirically observed (measurements, readings, literature consensus); status `observed`, shown distinctly in the research display
- `invalidate("A1")` — propagates downstream, flagging all dependent results as "needs-reverification"
- `get_downstream("A1")` — returns all transitive dependents

Visualize: `from displays.research import show_research; show_research()`

## Who verifies whom

| Who's working | Who verifies |
|---|---|
| AI (autonomous or collaborative) | Verifier agent checks AI claims |
| Human | AI watcher checks human's workspace |
| Both | Both verification paths run |

## Key principles

- **Don't pause for confirmation mid-work.** Log everything, keep going.
- **Verification at every step.** Autonomous operation without verification is unsupervised hallucination.
- **Maintain research state throughout.** The human can check in anytime and see progress.
- **If stuck, log it and try something else.** Update attempts, don't loop forever.
- **If the verifier flags everything as uncertain, proceed with uncertainty logged.** Don't loop trying to achieve perfect certainty.

## What the human sees

- Display panel: current work, derivations, plots
- Research state: full trajectory from exploration to verified answer
- Dependency graph: the logical structure of the derivation
- Verification log: what was checked, what passed, what failed
