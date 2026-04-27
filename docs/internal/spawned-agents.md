# Spawned Agents — how Triptych runs parallel work

*2026-04-23.*

Triptych spawns three parallel agents alongside the main one: **verifier** (checks claims), **watcher** (observes the human's workspace), **dashboard** (owns the display pool). All three use the same pattern. There's also a separate class of one-shot subagents (redteam, whats-missing) the main agent spawns directly.

## Two layers — peer and below

Spawned work splits into two layers. The mechanism is the same (`/loop + skill` and the `Task` tool), but the lifecycle and stature differ.

| Layer | Lifecycle | Mechanism | Examples |
|---|---|---|---|
| **Peer** — sibling to main agent | Long-lived. Drains a filesystem queue continuously while a phase of work is active. | `/loop <interval> /<skill>` runs the skill in an isolated context. Some peers also spawn `Task` subagents per queue item for extra isolation. | `verifier`, `watcher`, `dashboard` |
| **Below** — one-shot worker | Short-lived. Spawned for a single bounded task, returns a summary, exits. | `Task(subagent_type="<name>", prompt=...)` from the main agent. Definition lives in `.claude/agents/<name>.md`. | `redteam`, `whats-missing`, the per-claim verifier subagent (spawned *by* the `/verifier` loop — distinct from the loop itself) |

Peer agents are conceptually equal to the main agent — different focus, same stature. They run on their own schedule and communicate only through the queue. Below agents are dispatched by the main agent for a specific question and return a summary; they don't have a persistent role.

The `level: peer | below` field in each `SKILL.md` frontmatter makes this explicit.

## The pattern — `/loop + skill`

```
/loop <interval> /<skill>
```

`/loop` is a built-in Claude Code skill that re-invokes another skill on an interval. The skill's `SKILL.md` lives in `.claude/skills/<name>/`, runs in an isolated subagent context (spawned via the Task tool when appropriate), reads a filesystem queue, and exits silently when the queue is empty.

**Three skills, one pattern:**

| Skill | Interval | Queue file | Owns |
|---|---|---|---|
| `/verifier` | `60s` | `workspace/research/verification.log` | Claim verdicts |
| `/watcher` | `30s` | `workspace/snapshots/latest.{png,json}` | `workspace/research/watcher.log` |
| `/dashboard` | `30s` | `workspace/research/dashboard-queue.json` | `workspace/output/` |

Each skill has a sibling `.claude/agents/<name>.md` definition that declares the isolated subagent character (model, allowed tools, system prompt). The main agent invokes these via the Task tool when isolation matters (`/verifier` always does — fresh eyes on each claim).

## Why not Anthropic's Agent Teams?

Agent Teams is real and experimental (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`, docs at code.claude.com/docs/en/agent-teams). We considered it for this use case and chose not to. Reasons:

1. **Wrong shape.** Agent Teams is designed for inter-agent discussion ("teammates debating hypotheses," "red-team a plan"). Triptych's spawned agents are independent parallel workers draining filesystem queues — no debate, no coordination beyond the queue file. The `/loop + skill` pattern fits this workload exactly; Agent Teams would be overkill.
2. **Token cost.** Agent Teams gives each teammate its own full 1M-token context window. Three live teammates = ~3× the cost of one session. `/loop + skill` spawns only when there's work — verifier is idle between claims, dashboard is idle between requests.
3. **Known gotchas (from the docs + practitioner reports).** Agent Teams has no `/resume` support (session resumption breaks), has task-status lag, supports only one team per session, has file-conflict risk when teammates edit the same file, and requires tmux/iTerm2 for split-pane mode (not Windows Terminal, which Quinn uses).
4. **Experimental.** API may shift. `/loop + skill` is built on stable primitives (skills, Task tool, filesystem).

Agent Teams is the right fit when the workload genuinely involves two agents *talking to each other* — red-team / blue-team debate, planner / critic exchange. When it gets there for Triptych, we'll reopen the decision. Until then, `/loop + skill` is the recommendation.

## Starting and stopping

Each skill has its own start conditions:

- **`/verifier`**: start when the main agent emits the first claim. `/loop 60s /verifier`. The `inject-verifier-hint.mjs` UserPromptSubmit hook nudges automatically.
- **`/watcher`**: start when the human is actively working in the workspace panel. `/loop 30s /watcher`.
- **`/dashboard`**: start when display work begins fragmenting the main thread — often mid-session when the output pool has >5 tabs or the main agent has queued >=2 display requests. `/loop 30s /dashboard`.

Stop each one with `/loop stop` (or `/loop stop /<skill>` for per-loop shutdown).

**Do not auto-start at session start.** These exist to serve specific phases of work. If there's nothing to do, silence.

## Hand-off protocols

The main agent and the spawned skill communicate only through the queue file. Nothing else is shared.

**`/verifier`**:
- Main agent writes: `emit_claim(claim, context, depends)` → appends to `verification.log`
- Skill reads: scan `verification.log`, find claims without matching `result` entries
- Skill writes: `write_result(claim_id, status, method, detail)` → appends to same log, and `process_result(...)` → updates state.md + deps.json

**`/watcher`**:
- Writes by the capture system: `workspace/snapshots/latest.png` and `latest.json` (every 30s)
- Skill reads: both snapshot files
- Skill writes: `log_watcher(content, type, confidence)` → appends to `workspace/research/watcher.log`

**`/dashboard`**:
- Main agent writes: `request_display(intent, data_path)` → appends to `dashboard-queue.json` pending
- Skill reads: `drain_requests()` → atomic empty of pending, returns list
- Skill writes: builds display in `workspace/output/`, calls `mark_done(id, output_path)` → appends to `dashboard-queue.json` completed

## Context isolation

All three skills see only what they need:

- `/verifier` sees: the claim + one-line context + dependency IDs. Never the main agent's reasoning.
- `/watcher` sees: the current snapshot + the goal from state.md. Never the verification log.
- `/dashboard` sees: the intent sentence + the data path. Never the research narrative.

This is the guardrail against **orchestrator context blowup** — the well-documented failure mode where a multi-agent setup's main context balloons because everything gets forwarded to everyone. We don't forward. Each skill has a narrow window.

## What to do when a skill misbehaves

- **Queue not draining**: check if the `/loop` is running (`/loop status`). If not, restart. If yes, tail the skill's log (verifier: `verification.log` tail; watcher: `watcher.log` tail; dashboard: `dashboard-queue.json` completed tail).
- **Skill crashes or hangs**: `/loop stop /<skill>` then inspect. Hook errors land in `workspace/research/hook-errors.log` (see `scripts/hooks/_safe.mjs`).
- **Same skill keeps processing the same item**: inspect the queue file — the skill probably isn't marking items done correctly.

## When to add a fourth

The pattern generalizes. A new spawned agent is worth adding when:

1. There's work that would fragment the main agent's context if inline.
2. That work has a clean filesystem queue (or can be made to have one).
3. The work benefits from a different model, different tools, or different prompt than the main agent.

If all three apply, write a new `.claude/skills/<name>/SKILL.md` and a companion `.claude/agents/<name>.md`, define the queue shape, point at this doc. Don't add coordination machinery beyond the queue file.

## Related

- `.claude/skills/verifier/SKILL.md`
- `.claude/skills/watcher/SKILL.md`
- `.claude/skills/dashboard/SKILL.md`
- `core/verify.py`, `core/research.py` (log_watcher), `core/dashboard_queue.py`
- `docs/internal/architecture.md` (where core stops and addons begin)
