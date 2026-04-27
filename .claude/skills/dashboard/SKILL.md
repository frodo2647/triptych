---
name: dashboard
description: Dashboard agent — drain the display-request queue, build/update displays, clean up stale tabs. Spawned by `/loop 30s /dashboard` when display work is fragmenting the main agent's context. Third skill in the /loop + skill pattern alongside /verifier and /watcher.
level: peer
---

# Dashboard

You own `workspace/output/`. When the main agent wants a display built (or rebuilt, or polished) without interrupting its main thread, it writes intent to `workspace/research/dashboard-queue.json`. You drain the queue.

**Paired with `/verifier` and `/watcher`.** Three skills, one pattern: each spawned on an interval via `/loop`, each draining a filesystem queue, each running in an isolated subagent context so it can't pollute the main thread.

| Skill | Queue | Owns |
|---|---|---|
| `/verifier` | `workspace/research/verification.log` | Claim verdicts |
| `/watcher` | `workspace/snapshots/latest.{png,json}` | Watcher log |
| `/dashboard` | `workspace/research/dashboard-queue.json` | `workspace/output/` |

## Why isolation matters

Display design — picking chart types, laying out panels, polishing CSS, cleaning up stale tabs — is distinctive enough to fragment the main agent's context if interleaved with research. By handing off to a skill running in a fresh subagent context, the main agent stays focused on the problem and the display work happens in parallel.

You receive **data + intent only** — never the research narrative. That's the guardrail against orchestrator context blowup (well-documented failure mode in multi-agent setups).

## What happens per tick

```
tick():
  pending = drain_requests()  # one call — atomic empty of the queue
  if not pending: return silently

  for req in pending:
    - read req.intent + req.data_path
    - pick the right display helper (show_plotly, show_html, show_latex, ...)
    - build / update the display; write to workspace/output/
    - mark_done(req.id, output_path)

  optionally: cleanup_displays(keep=[...]) when output pool is cluttered
  return
```

Batch-ok for this loop (unlike `/verifier` which is one-claim-per-tick): display work is cheap enough that draining everything at once is fine and keeps the queue short.

## Reading the queue

```python
python -c "
import sys; sys.path.insert(0, '.')
from core.dashboard_queue import drain_requests
requests = drain_requests()
for r in requests:
    print(r['id'], '->', r['intent'])
"
```

If `requests` is empty, exit silently. Same discipline as `/verifier` — a dashboard that speaks when it has nothing to do is noise.

## Handling a request

Each `req` has `id`, `intent`, optional `data_path`, `ts`.

1. **Parse intent.** Short sentence from the main agent: *"training-curve, EMA vs raw, stages 5-6, 30s refresh"*. Break out chart type, data series, refresh cadence.
2. **Pick the helper.** Reach for the most specific existing display addon first:
   - Time-series → `show_plotly` with a line chart
   - Kanban / state → `show_research`
   - Live progress → `show_progress`
   - Math notation → `show_latex`
   - Raw HTML when nothing fits → `show_html`
   - Check `/triptych-displays` catalog if unsure.
3. **Wire data.** If `data_path` is set, read from there. Otherwise read from where the intent implies (e.g. `workspace/research/attempts.jsonl` for autoresearch).
4. **Build the display.** Stem should be descriptive — `training-curve.html`, not `d1234.html`.
5. **Mark done.**

```python
from core.dashboard_queue import mark_done
mark_done(req['id'], f"workspace/output/{stem}.html")
```

## Cleanup

After draining, decide whether to clean `workspace/output/`:

- Count the files. If >8 and multiple look like iteration residue (same topic, different stems), call `cleanup_displays(keep=[...])` with the stems that should survive.
- Never delete `research.html`, `index.html`, or anything actively being updated.
- If unsure, don't delete. Drift is recoverable; deleted work isn't.

```python
python -c "
import sys; sys.path.insert(0, '.')
from displays import cleanup_displays
cleanup_displays(keep=['research', 'training-curve', 'architecture'])
"
```

## Invocation

**Continuous:**
```
/loop 30s /dashboard
```
Start it when display work begins fragmenting the main thread (often mid-session as displays pile up). Stop it when the session ends.

**Single tick:**
```
/dashboard
```
Useful after a batch of display intent has been queued and you want to drain once.

Do not auto-start at session start. The dashboard exists to serve display-heavy phases; if there's nothing queued, it's silent.

## How the main agent uses you

Main agent, mid-thought:
```python
from core.dashboard_queue import request_display
request_display("training-curve, EMA vs raw, stages 5-6, refresh 30s",
                data_path="workspace/research/attempts.jsonl")
# keeps working on the problem — the display will appear when you drain
```

The main agent does not block. When the rendered display lands in `workspace/output/`, the watcher / display-pool tab list shows it.

## Hard rules

- **Context isolation.** You receive data + intent. Never the research narrative. If a request carries more than a one-sentence intent and a data path, treat the extra context as noise and ignore.
- **Silence when empty.** No pending requests → exit without output.
- **Descriptive stems.** `training-curve.html`, not `d4f2a1b8.html`. The display pool is a human-readable tab list.
- **Don't fight existing displays.** If `research.html` is live, don't rebuild it — the main agent owns it. Only touch what's in the queue or obvious residue.
- **Clean up only with a `keep=` list.** Never `cleanup_displays()` without arguments.
