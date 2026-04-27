---
name: wrap
description: Close a session — summarize what was done, persist state for the next session, clean up the display pool, stop running loops, write to memory if there's a learning worth keeping. Fifth of five core commands (start → explore → work → check → wrap). Use when the user says they're done for now, wrapping up, taking a break, or it's getting late.
---

# /wrap

The closing move. Goal: leave the workspace in a state where the next `/start` can resume warmly without rebuilding context.

## When to use

- User says "I'm done for now," "let's wrap up," "good for today," "taking a break."
- End of a productive stretch — even mid-day, useful to checkpoint.
- About to close the laptop. The session.json + research state should reflect today's work.

## Step 1: Read what just happened

```python
import sys; sys.path.insert(0, '.')
from core.session import read_session
from core.research import read_state, get_graph
s = read_session()
state = read_state()
graph = get_graph()
```

Inventory:
- Goal in session.
- Phase (exploration / formalization).
- Established results count, claims emitted count, attempts count, open threads.
- Anything in `workspace/output/` worth surfacing.

## Step 2: Write a session summary

A short markdown summary to `workspace/research/session-log/<YYYY-MM-DD>.md` (cumulative log; append if the file exists). Format:

```markdown
## <session date> — <hh:mm> to <hh:mm>

**Goal:** <verbatim>
**Phase:** <exploration | formalization>

**Done:**
- <what was actually accomplished — established results, decisions made, hypotheses ruled in/out>

**Open:**
- <what's still in flight — open threads, candidate questions, unresolved claims>

**Next time:**
- <one or two concrete suggestions for the next session>

<optional one-line user note from /wrap arg>
```

Keep it short — three to six bullets per section, max. The point is warm-resume, not a full report.

## Step 3: Update Next Step in research state

Set the "Next Step" field of state.md to the most actionable open thread, so the next `/start` resume sees it immediately:

```python
from core.research import update_state
update_state('next_step', '<one-sentence concrete next action>')
```

If there are multiple open threads, pick the one most likely to unstick the goal. Don't list them all.

## Step 4: Persist to Obsidian (if configured)

Read `CLAUDE.local.md` for an Obsidian path. Quinn's local config (per memory) maps Triptych sessions to Obsidian's `Projects/Study Plan — Physics & Math.md`. If a path is configured:

- Append the session summary to the configured Obsidian file.
- Use the same heading format so it merges cleanly.

If no Obsidian path is configured, skip — the session-log/ markdown is enough.

## Step 5: Memory check

Was there a *learning* in this session that future sessions should know about? Examples:

- A user preference newly observed ("Quinn prefers 3D viz over 2D" — feedback memory).
- A project-level fact that won't change ("the dataset lives at /path/X" — reference memory).
- A surprising methodological finding worth keeping.

If yes, write a memory file using the auto-memory format (see `~/.claude/CLAUDE.md`). If nothing surprising came up, skip — the session log carries the rest.

## Step 6: Clean up the display pool

Run `cleanup_displays` with the stems worth keeping live across sessions:

```python
from displays import cleanup_displays
cleanup_displays(keep=['research', 'index', 'progress', 'assumptions', 'claims'])
```

The default `keep` already preserves `research` and `index`; the call above adds the cyborg-mode defaults if they're being used. Iteration residue (intermediate plots, scratch displays) gets removed.

## Step 7: Stop running loops

If `/loop /verifier`, `/loop /watcher`, or `/loop /dashboard` are running, stop them:

```
/loop stop
```

(Or `/loop stop /verifier`, etc., for selective shutdown.) Loops should not survive the session — they're activated per phase, deactivated at wrap.

## Step 8: Final report

Confirm to the user:

```
Wrapped — <date>.

  Goal: <goal>
  Done: <N established results, M open threads>
  Logged: <session-log path>, <obsidian path if used>
  Next time: <one-line>
```

That's the whole exit. Nothing dramatic — just acknowledged that today's work is checkpointed and tomorrow's `/start` will pick up cleanly.

## Args

- `/wrap` — full close-out flow.
- `/wrap "<note>"` — adds a free-text user note to the session summary (e.g. "felt stuck on the linear algebra step — try a different decomposition tomorrow").

## Hard rules

- **Idempotent.** Running `/wrap` twice in a row should not produce two log entries — check for an existing entry from today's session ID and update rather than append.
- **Don't wrap empty sessions.** If the user invoked `/start` and never did real work, just persist the session and stop loops — skip the summary write. No need to log "did nothing today."
- **Don't lose state.** `/wrap` is a checkpoint, not a reset. Goal, established results, open threads all persist for the next session.
- **Stop loops.** Leaving `/loop /verifier` running between sessions burns tokens for nothing.
