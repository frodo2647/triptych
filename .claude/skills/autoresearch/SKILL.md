---
name: autoresearch
description: Autonomous self-improvement loop after Karpathy — define a metric, iterate, keep what works, revert what doesn't. Use when the user asks to optimize, tune, benchmark, or iteratively improve a system against a measurable metric. Triggers: "optimize", "tune", "benchmark", "improve performance", "self-improve", "auto-tune", "sweep", "beat baseline".
---

# AutoResearch

Adapted from [Karpathy's autoresearch](https://github.com/karpathy/autoresearch). The idea: give an AI agent a setup with a measurable metric and let it experiment autonomously. Modify the code, run the experiment, check if the result improved, keep or discard, repeat. You wake up to a log of experiments and (hopefully) a better system.

> "You're not touching any of the Python files like you normally would as a researcher. Instead, you are programming the `program.md` Markdown files that provide context to the AI agents and set up your autonomous research org." — Karpathy

## Core Philosophy

**Constraint is the enabler.** One file to modify. One metric to optimize. Fixed time budget per experiment. The constraints are the design, not limitations.

**Simplicity wins over cleverness.** All else being equal, simpler is better. A small improvement that adds ugly complexity is not worth it. Removing something and getting equal or better results is a great outcome — that's a simplification win. A 0.001 improvement from deleting code? Definitely keep. A 0.001 improvement that adds 20 lines of hacky code? Probably not worth it.

**Mechanical metric decides everything.** The metric went down or it didn't. No subjective evaluation. No "looks good to me."

**Git is memory.** Every experiment is a commit. Keep improvements by advancing. Discard failures by resetting.

**Never stop.** Once the loop begins, do NOT pause to ask the human if you should continue. Do NOT ask "should I keep going?" The human might be asleep. You are autonomous. If you run out of ideas, think harder — re-read the code for new angles, combine previous near-misses, try more radical changes. The loop runs until the human interrupts you, period.

## When to use this vs /autonomous vs Triptych more broadly

| Use `/autoresearch` | Use `/autonomous` | Use Triptych without either |
|---|---|---|
| Optimizing a metric (accuracy, speed, score) | Deriving a result (equation, proof) | Conceptual work — design calls, exploratory derivations, anything where the right answer isn't obvious from a number |
| Trial-and-error with measurable feedback | Step-by-step logical chain | Back-and-forth thinking with displays + verifier + redteam |
| ML training, algorithm tuning, prompt engineering | Math, physics, formal reasoning | Most real research — the work is figuring out what counts as "right" |

`/autoresearch` and `/autonomous` are the special cases where the problem is well-shaped enough for an AI to drive on its own. Most problems aren't, which is the broader Triptych use case.

## Setup

### 1. Define the constraints

Before starting, establish:
- **The file(s) to modify** — keep scope tight. One file is ideal.
- **The metric** — must be mechanical, scalar, and fast to evaluate.
- **The time budget** — how long each experiment takes to run.
- **The evaluation command** — how to measure the metric.

### 2. Initialize research state

```python
import sys; sys.path.insert(0, '.')
from core.research import init_research
init_research('Optimize [WHAT] — metric: [METRIC], baseline: [VALUE]')
```

### 3. Establish baseline

Run the metric on the current state. Record it.

```python
from core.research import add_observed
# add_observed (not add_established) for empirical baselines — metrics are
# measurements, not verifier-checked claims. add_established is reserved for
# results with a verification.log entry; the autoresearch loop's baseline
# doesn't have one.
add_observed('B1', 'Baseline: [metric] = [value]', depends_on=[])
```

Commit: `git add -A && git commit -m "autoresearch: baseline [metric]=[value]"`

## The Loop

```
LOOP FOREVER:
  1. Look at git state — current branch, recent experiment history
  2. Pick ONE experimental idea based on what worked, what failed, what's untried
  3. Make ONE focused change to the target file(s)
  4. git commit -m "experiment: [description of change]"
  5. Run the experiment
  6. Read the metric
  7. If metric improved → KEEP (advance the branch)
     If metric equal or worse → REVERT (git reset --hard HEAD~1)
     If crashed → read tail of log, fix or skip, revert
  8. Log the result to research state
  9. Repeat — go to 1
```

### Inside each iteration

**Pick a change:**
- Read the current code carefully before modifying
- ONE change per iteration — if you change two things and it improves, you don't know which helped
- Draw from: hyperparameter tweaks, architectural changes, removing unused code, combining near-misses from previous experiments

**Evaluate the simplicity criterion:**
When deciding whether to keep a change, weigh complexity cost against improvement:
- Improvement + simpler code → always keep
- Improvement + same complexity → keep
- Improvement + ugly complexity → keep only if improvement is significant
- No improvement + simpler code → keep (simplification win)
- No improvement or worse → revert

**Log the result:**
```python
from core.research import add_attempt
add_attempt('[description]', outcome='kept' if improved else 'reverted',
            reason=f'[metric]: {old_val} -> {new_val}', research_dir='workspace/research')
```

**Update display every few iterations:**
```python
from displays.research import show_research
show_research()
```

### When stuck

Do NOT stop. Think harder:
- Re-read the target file for angles you missed
- Review which experiments came closest to improving
- Try combining two near-miss ideas
- Try the opposite of what you've been doing
- Try more radical changes — big architectural shifts
- Read comments/docstrings for hints about what could be better

### Periodic review (every 10-20 iterations)

Step back and assess:
- What patterns emerge from kept vs reverted experiments?
- Are we plateauing? Time to try a different direction.
- Is the metric still measuring what we care about?

```python
from core.research import update_state
update_state('threads', '- [N] experiments, [M] kept, plateau at [value]\n- Pattern: [what works]\n- Next direction: [idea]')
```

## Integration with Triptych

This runs on top of Triptych's research state system:

- **Research state** (`workspace/research/`) tracks the full experiment trajectory
- **Display panel** shows progress via `show_research()`
- **Dependency graph** shows which improvements built on which
- **Verification system** can validate the metric itself if needed

The key difference from raw Karpathy: we have structured research state, not just a TSV log. The philosophy is identical — the infrastructure is Triptych's.

## Example domains

| Domain | File to modify | Metric | Time budget |
|--------|---------------|--------|-------------|
| ML training | train.py | val_loss / val_bpb | 5 min |
| Prompt engineering | prompt.md | benchmark score | 30 sec |
| Algorithm tuning | solver.py | runtime (ms) | 10 sec |
| System config | config.yaml | throughput (req/s) | 1 min |
| Code quality | module.py | test pass rate + coverage | 30 sec |
