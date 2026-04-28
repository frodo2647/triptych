---
name: check
description: Milestone challenge — push back on a result before it becomes load-bearing. Runs /whats-missing first (surface unstated assumptions and gaps), then /redteam (challenge what's there). Both are calibrated against false positives — empty findings is a valid, encouraged answer when the work is sound. Fourth of five core commands (start → explore → work → check → wrap). Use at major results, before write-up, or when the user says "push back on this" / "challenge this."
---

# /check

The milestone challenge. Pushes back on a conclusion before it becomes load-bearing for downstream work.

`/check` is sequential — whats-missing first (cheap, surfaces gaps), then redteam (challenge what's there) — so findings compound rather than duplicate. Both passes are calibrated to return "nothing substantive" when the work is sound; that's the valuable answer when it's true.

## When to use

- A major result has been established and the rest of the work will build on it.
- About to write up / present / publish — last pass before it leaves your hands.
- The user types "push back," "challenge this," "is this right," "what am I missing."
- The result feels too clean — sometimes worth a check.

Don't run continuously. Milestone cadence keeps the signal calibrated; an agent told to find mistakes constantly will start hallucinating them.

## Step 1: Identify the target

Read research state to find what to check:

```python
import sys; sys.path.insert(0, '.')
from core.research import read_state
state = read_state()
```

Three cases:

- **Args supplied** (`/check <claim ID>` or `/check <description>`) — use that as the target.
- **No args, established results exist** — default to the most recent established result (or the goal conclusion if write-up time).
- **Nothing substantive yet** — say *"Nothing established yet to check. Use `/work` to make progress, or pass an explicit target: `/check <claim>`."* Exit.

## Step 2: Decide the mode

Default: **both** (whats-missing first, then redteam).

Args can scope it:
- `/check missing` — only whats-missing.
- `/check redteam` — only redteam.
- `/check both` — explicit default.
- `/check deep` — both, plus a `cross-verifier` cross-derivation pass via Task. Use sparingly — it's slow and only worth it for top-level conclusions.

## Step 3: Run whats-missing first (if in mode)

```
Task(
  subagent_type="whats-missing",
  prompt=(
    "Analysis to examine: <file path or excerpt or claim>\n"
    "Optional focus: <assumptions / counterfactuals / scope, or all>\n"
    "\n"
    "Return your findings per the output format in your system prompt. "
    "Empty findings is the right answer if the analysis is complete."
  )
)
```

Read the verdict:

- **"analysis is complete"** → log to redteam pass with this context, proceed.
- **"minor gaps only"** or **"important gaps"** → note the gaps, proceed to redteam. Triage all findings together at the end (Step 6) — don't pause mid-`/check` to ask the user how to handle each gap class. Iteration cadence stays uninterrupted.
- **"load-bearing"** or **"blocking gaps"** (where redteam can't sensibly run until the gap is addressed — e.g. the artifact has a hole that makes challenging it pointless) → only here, pause and surface to user: *"whats-missing flagged a blocking gap: `<gap>`. Redteam can't meaningfully challenge until this is addressed — fix first, or proceed anyway?"*

## Step 4: Run redteam (if in mode)

```
Task(
  subagent_type="redteam",
  prompt=(
    "Milestone: <what was just reached>\n"
    "Artifact to challenge: <file path or claim ID or excerpt>\n"
    "Optional axis to focus on: <e.g. 'method', 'overlooked alternative'>\n"
    "\n"
    "Return your verdict and any findings per the output format in your "
    "system prompt. Empty findings is the right answer if the work is sound."
  )
)
```

Read the verdict (one of: nothing-substantive / minor-presentational / issues-worth-addressing / blocking-concerns).

## Step 5: Optionally run cross-verification (`/check deep` only)

If `deep` mode and there's a top-level conclusion worth re-deriving:

```
Task(
  subagent_type="cross-verifier",
  prompt=(
    "Problem: <goal>\n"
    "Claimed result: <result>\n"
    "Method used (so you can choose a different one): <method>\n"
    "\n"
    "Solve the problem independently using a different method. Compare to "
    "the claimed result. Report match / mismatch / unable to verify."
  )
)
```

## Step 6: Triage findings

Aggregate findings from all passes. For each:

- **Empty / no findings** — report cleanly: *"`/check` complete. Nothing substantive flagged across whats-missing + redteam. Result is sound."* This is the most valuable possible outcome — don't pad it.
- **Findings exist** — surface them grouped by severity:
  - `must-address` / `load-bearing` — list these first; the conclusion is in question.
  - `nice-to-have` / `minor` — list briefly; can be applied at user's discretion.
- For each finding, suggest the resolution path: a new `emit_claim`, an explicit `add_node` for an unstated assumption, a `/work` revisit of the questionable step.

## Step 7: Suggest next move

- **No findings** → *"Looks good. Back to `/work`, or ready to `/wrap`?"*
- **Findings to address** → *"`/work` on the open ones, then re-`/check` when resolved."*
- **Blocking concern** → *"This re-opens the analysis — back to `/work` or `/explore` to reframe."*

## Args summary

- `/check` — both passes, default target (most recent established result).
- `/check <claim ID or description>` — scope to a specific target.
- `/check missing` — only whats-missing.
- `/check redteam` — only redteam.
- `/check deep` — both + cross-verification.

## Hard rules

- **Trust empty verdicts.** If both passes return "nothing substantive," don't re-prompt with leading questions to extract findings. The calibration is the feature.
- **Sequential, not parallel.** whats-missing first surfaces context that improves redteam's challenge. Don't run them in parallel.
- **Milestone-only by default.** Don't run `/check` mid-derivation — that's what the verifier loop is for.
- **One axis per redteam spawn.** If multiple angles need challenging (methodology and assumptions, say), spawn redteam twice with different focus — keeps each pass calibrated.
