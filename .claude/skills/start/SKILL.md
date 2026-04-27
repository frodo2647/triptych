---
name: start
description: Begin a session. Reads any existing session, asks the goal if there isn't one, sets phase (exploration vs formalization), seeds research state, primes the right domain mentor, optionally activates the watcher. The first of five core commands — start → explore → work → check → wrap. Use at the beginning of a session, or when the user wants to (re)set the goal.
---

# /start

The opening move. Goal of this skill: in under two minutes, go from cold start to "research state seeded, phase set, domain mentor primed, ready to do the work."

If `CLAUDE.local.md` doesn't exist, this is a first boot — defer to `/first-boot` Stage 1 (one-time setup), then continue here.

## Step 1: Read existing session state

```python
import sys; sys.path.insert(0, '.')
from core.session import read_session
s = read_session()
```

Three cases:

- **No session yet** — proceed to Step 2.
- **Active session, recent (< 4h since `lastActive`)** — offer to resume: *"Picking up `<goal>` (phase: `<phase>`). Continue, or set a new goal?"* If continue: skip to Step 5. If new: clear and proceed to Step 2.
- **Stale session (> 4h)** — surface the previous goal as context and ask if today's work continues it: *"Last session was on `<goal>`. Continuing that, or starting something new?"*

## Step 2: Get the goal

If args were passed (`/start <goal text>`), use them verbatim and skip the question.

Otherwise ask plainly: *"What are you trying to do this session? One sentence."*

If vague, ask one follow-up: *"What's the specific question or problem you want to get traction on?"* Don't interrogate — one follow-up max.

Write the goal verbatim. You'll pass it to `init_research` or `write_session` in Step 4.

## Step 3: Classify exploration vs formalization

Read the goal. Pick:

- **Exploration** — generating ideas, surveying a landscape, deciding what to work on. Cues: "explore," "survey," "figure out what to," "get oriented."
- **Formalization** — committed to a specific problem, deriving / proving / computing with rigor. Cues: "derive," "prove," "compute," "verify," "solve for."

Unclear? Ask: *"Are we generating ideas, or working on a specific thing you've already picked?"*

## Step 4: Seed state

If **formalization**:

```python
import sys; sys.path.insert(0, '.')
from core.research import init_research
from displays import show_research
init_research("<goal verbatim>")
show_research()
```

Confirm: *"Research state seeded — visible in the display panel as 'Research State' (Alt+2)."*

If **exploration**:

```python
import sys; sys.path.insert(0, '.')
from core.session import write_session
write_session("<goal verbatim>", phase="exploration")
```

(Research state is seeded later when work crystallizes — the agent should recognize that boundary, not pre-commit.)

## Step 5: Prime the domain mentor

Read `CLAUDE.local.md` `## Domains`. For each picked domain that ships a mentor skill, name it once and let it activate:

- `physics` → `/physics-in-triptych`
- `math` → `/math-in-triptych`
- `ml` → `/ml-in-triptych`

If the goal touches a domain not in the user's profile, mention it but don't auto-add — the user can update their config later.

## Step 6: Offer to start the watcher

If the user is going to be working in the workspace panel during this session (drawing, writing, sketching), offer:

*"Want me watching your workspace this session? `/watcher` runs every 30s — catches obvious errors silently, asks questions when relevant."*

If yes: start `/loop 30s /watcher`. If no: skip.

## Step 7: Hand off

Summarize and suggest the next move:

- **Exploration** → *"Set up. Try `/explore` to start brainstorming, or just dive in — I'll surface patterns as we go."*
- **Formalization** → *"Set up. Try `/work` to start the formal pass — I'll emit claims and the verifier will catch errors as they happen."*

Don't proceed to actually doing the work in this skill — let the user choose. The next `/work` or `/explore` invocation activates the rigor.

## Args

- `/start` — interactive flow above.
- `/start <goal text>` — uses the text as the goal verbatim, skips the question.

## Hard rules

- **One question max for follow-ups.** Don't interrogate the user before they've started.
- **Always read existing session first.** If there's a recent active session, offer resume — don't silently overwrite.
- **Don't seed research state for exploration.** That's a deliberate boundary; the work crystallizes when the user knows what they're answering.
