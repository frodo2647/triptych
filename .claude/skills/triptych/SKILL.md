---
name: triptych
description: Orientation and setup-check — read where the user is in the work, ask about their goals, identify their position in the start → explore → work → check → wrap arc, surface a concrete recommended next step, and optionally check that Triptych is set up well for their use case. Use when the user types `/triptych`, `/?`, `/help`, asks "what should I do next?", "what commands do I have?", "where are we?", or seems lost mid-session.
---

# /triptych — orientation

`/triptych` doesn't automate decisions. It reads where you are, asks you what you're trying to do, and recommends a next move — leaving the choice with you. Use it whenever you're unsure what to do next, want a sanity check on setup, or just want to see the arc.

The skill has three modes; default is the full interactive flow.

- `/triptych` — interactive orientation (default).
- `/triptych setup` — readiness check only (config + skills + MCPs for the user's use case).
- `/triptych help` — static cheatsheet only, no interaction.

## Interactive flow (default)

### 1. Read state silently

Before saying anything, gather context:

```python
import sys; sys.path.insert(0, '.')
from core.session import read_session
from core.research import read_state, get_graph
from displays import OUTPUT_DIR
import json
from pathlib import Path

session = read_session()
state = read_state()
try:
    graph = get_graph()
except Exception:
    graph = {'nodes': {}, 'edges': []}

local_md = Path('CLAUDE.local.md').read_text() if Path('CLAUDE.local.md').exists() else ''
output_files = [f.name for f in OUTPUT_DIR.iterdir() if f.is_file() and not f.name.startswith('.')]
```

Build a one-paragraph snapshot of where they are:

- Goal (verbatim from session, or "no goal set yet")
- Phase (exploration / formalization / no session)
- Counts: claims emitted, established results, attempts, open threads
- Loops running (verifier? watcher? dashboard?)
- Display pool — anything live worth referencing
- Domains from CLAUDE.local.md
- Time since last activity

### 2. Show the snapshot

Open with the snapshot, briefly. Example shapes:

> *"Looks like you're mid-work on `<goal>` (formalization). 3 claims emitted, 2 verified, 1 still pending. `show_research` is live; verifier loop is running. Last activity ~12 minutes ago."*

> *"No active session — clean slate. `CLAUDE.local.md` lists physics + math as your domains."*

> *"You started `<goal>` 2 hours ago, set phase to exploration, then went quiet. No claims, no established results yet. Display pool has a `<topic>.html` from earlier."*

Don't moralize — just describe what the state looks like.

### 3. Ask about their intent

Open the conversation with the right question for the situation:

- **No session** → *"What are you trying to do? Pick something to work on, or just talk through what's on your mind."*
- **Active session, recent activity** → *"Still on `<goal>`, or want to shift?"*
- **Stale session (> 4h since lastActive)** → *"You were on `<goal>` last time. Picking that up, or starting something new?"*
- **Active session but stuck-looking** (work phase, no claims emitted in last 20 min) → *"How's the work going? Stuck somewhere, or just thinking?"*

One question. Wait for the answer.

### 4. Identify position in the arc

Based on the state + their answer, locate them in the five-step arc and surface it visually:

```
   start    →   explore    →   [WORK]    →   check    →   wrap
                                  ▲
                          (you are here — 3 claims emitted, 1 unverified)
```

If the position is ambiguous (between two stages), say so and ask which fits better.

### 5. Recommend a concrete next move

Based on position + state + their stated intent, suggest one specific next move with reasoning. Examples:

- *"Two results just landed and you haven't `/check`-ed yet. Now's a good time — empty findings is the most valuable answer when the work is sound."*
- *"You said you're stuck on the linear-algebra step. Worth `/explore`-ing alternative decompositions for 10 minutes, then back to `/work`?"*
- *"You've been here 2 hours and you're winding down — `/wrap` saves the state for tomorrow. Takes 30 seconds."*
- *"No goal yet. `/start` takes a minute and seeds the research state so the verifier has something to check against."*

Always frame it as a suggestion the user can accept, modify, or override. Don't auto-invoke.

### 6. Offer a setup tweak (only if useful)

Run a quick readiness check. Surface only the items that are *actually* off — don't lecture if everything's fine.

| Check | Surface if |
|---|---|
| Domain in `CLAUDE.local.md` | The current goal touches a domain not in the user's profile (offer to add) |
| MCP servers | Working in physics / math / ml but `sympy-mcp` / `desmos-mcp` not listed — point to `/skill-finder` or `claude mcp add` |
| Verifier loop | They're emitting claims but `/loop /verifier` isn't running |
| Watcher | They're actively working in the workspace panel but `/watcher` isn't running and they haven't declined it |
| Display pool | More than 8 stale tabs (offer `cleanup_displays`) |
| Research state | They're in formalization but no `init_research` ran (offer `/work` to seed it) |

Surface at most two — don't overwhelm. Each as one line: *"Heads up: you're emitting claims but the verifier loop isn't running. Want me to start it?"*

### 7. End with the cheatsheet

After orientation, show the five. This is the "if you want to do something specific, here's the menu":

```
/start    Begin a session — set the goal, pick mode (explore vs work)
/explore  Generate ideas, survey, hypothesize — for "what should I ask?"
/work     Do the work — derive, prove, compute, analyze (verifier on)
/check    Push back at a milestone — challenge assumptions and conclusions
/wrap     Close out — summarize, persist for next session, clean up
```

*Plain-language phrasing also works — "let's derive X" → /work, "I'm done for today" → /wrap. You can always `/triptych` again to re-orient.*

## `/triptych setup` — readiness check only

Skip the goal conversation. Run the full readiness check from step 6 and report:

- ✓ items that are good (one line each, dim)
- ⚠ items that could be better (one line each, with the fix as a suggestion)

If everything's fine, just say so cleanly: *"Setup looks good for `<domains from local config>`. No changes recommended."*

## `/triptych help` — static cheatsheet only

The old behavior — no interaction. Just the five-command block plus a one-line description per command, plus the power-user direct skills list. Useful when the user explicitly wants the menu without a conversation.

## Power-user direct skills

(Surface this section in `help` mode, or on request — not by default.)

The five wrap most common needs. If you know exactly what you want, the underlying skills are still callable:

- `/verifier`, `/watcher`, `/dashboard`, `/redteam`, `/whats-missing` — the spawned agents directly
- `/scientific-method`, `/think-rigorously`, `/hypothesis-generation`, `/literature-review` — methodology
- `/autonomous`, `/autoresearch` — special operating modes
- `/physics-in-triptych`, `/math-in-triptych`, `/ml-in-triptych` — domain mentors
- `/triptych-displays`, `/triptych-workspaces` — addon catalogs
- `/skill-finder` — fetch skills from PRPM / K-Dense for sub-domains we don't bundle
- `/field-report` — user-controlled feedback to the maintainer
- Plus eight bundled K-Dense skills (`/scientific-writing`, `/sympy`, etc.)

## Hard rules

- **Don't automate the decision.** `/triptych` *recommends*, never *executes* `/start` / `/work` / `/check` / `/wrap` automatically. The user picks.
- **Read state before speaking.** Always show the snapshot first so the user knows what `/triptych` is reasoning from.
- **One question at a time.** Don't interrogate.
- **Surface setup gaps only when they matter.** No checklist read-aloud if everything's fine.
- **Empty state is fine.** A new user typing `/triptych` immediately should get a clean orientation, not an error about missing session.
