---
name: whats-missing
description: Spawn a one-shot subagent that surfaces unstated assumptions, counterfactuals, and out-of-scope gaps in a piece of analysis. Sister to /redteam — redteam challenges what's there, whats-missing points at what isn't. Empty findings is a valid answer when the analysis is complete.
level: below
---

# What's Missing

A one-shot subagent that looks at an analysis or conclusion and asks: what's *not* on the page that should be? Use it when you want a deliberate check for assumptions you may have made silently, or when the work feels too clean and you want a sanity pass before relying on it.

## When to spawn

- **Before a conclusion lands as `add_established`.** The work is about to become a verified result downstream code will rely on. One pass to surface unstated assumptions before it's cemented.
- **After drafting a write-up.** The prose can hide assumptions the steps make explicit. A pass before sending it out.
- **When the user asks "what am I missing?"** — direct mapping to the skill.
- **When something feels too clean.** Not a structured trigger, but a useful one. If the answer came easily, it's worth checking what was assumed away.

Sister to `/redteam`. Spawn redteam to challenge what's *there*; spawn whats-missing to surface what *isn't*. They compose — many milestones benefit from both.

## How to spawn

```
Task(
  subagent_type="whats-missing",
  prompt=(
    "Analysis to examine: <file path or excerpt>\n"
    "Optional focus: <one of 'assumptions', 'counterfactuals', 'scope', or all>\n"
    "\n"
    "Return your findings per the output format in your system prompt. "
    "Empty findings is the right answer if the analysis is complete."
  )
)
```

The subagent reads the analysis and returns a structured list of unstated assumptions, counterfactuals worth checking, and out-of-scope gaps. It does not modify any files.

## Reading the result

The subagent returns one of four statuses:

- **"analysis is complete"** — nothing material is missing. Move on.
- **"minor gaps only"** — small assumptions or scope notes worth adding for honesty, but the conclusion holds.
- **"important gaps"** — assumptions or counterfactuals that should be examined before relying on the conclusion.
- **"load-bearing gaps"** — something missing that, if filled in, could overturn the conclusion. Re-open the analysis.

For findings under `important gaps` or higher, treat them as candidates to either verify (turn into claims) or explicitly add to the Assumptions section of research state.

## Manual invocation

`/whats-missing` runs against whatever the main agent identifies as the current analysis. The user can also pass a target:

```
/whats-missing workspace/research/established.md
/whats-missing "the conclusion that capacity scales linearly with N"
```

## Hard rules

- **Don't conflate with redteam.** Redteam = challenge what's there. Whats-missing = point at what isn't. Spawn the right one for the question.
- **Trust empty results.** If the subagent says nothing is missing, don't re-prompt with leading questions to extract findings.
- **One focus axis per spawn** when the analysis is large. Assumptions, counterfactuals, and scope are different lenses; mixing them dilutes signal.
- **Read-only.** The subagent reports; it doesn't write to research state or any files.
