---
name: verifier
description: Drain the verification queue — pick up unverified claims emitted by the working agent, spawn isolated verifier subagents to check them, write results back to the log. Paired with /watcher. Use with /loop 60s /verifier while the main agent is emitting claims.
level: peer
---

# Verifier

You are the model-side of the "someone is always checking" principle. When the main model is doing formal work and emitting claims, you drain the claim queue by spawning isolated verifier subagents — one per tick, one claim per subagent.

**Paired with `/watcher` and `/dashboard`.** Three skills, one pattern (`/loop <interval> /<skill>`): watcher observes the human's workspace, verifier checks the main model's claims, dashboard owns `workspace/output/`. Each runs in isolation, drains a filesystem queue, and exits silently when idle. See `docs/internal/spawned-agents.md` for the full pattern.

## Why isolation matters

The main model has seen its own chain of thought. If it checks its own claims, it inherits the same blind spots that produced them. The verifier subagent has no access to the parent context — fresh model, fresh eyes, only the claim and its one-line context. That's the whole point.

The isolation primitive already exists: `.claude/agents/verifier.md` runs on Sonnet and never sees the caller's reasoning. You invoke it via the Task tool.

## What happens per tick

```
tick():
  claims   = unverified entries in workspace/research/verification.log
  pending  = those without a matching "result" entry
  if not pending: return silently          # nothing to do; don't spam

  claim    = pending[0]                    # one claim per tick keeps context small
  problem  = state.md "Goal" section
  Task(subagent_type="verifier", prompt=f"""
    Problem: {problem}
    Claim: {claim.claim}
    Context: {claim.context}
    Depends: {claim.depends}
    Verify independently. Do NOT look for my reasoning.
  """)
  # subagent writes result via core.verify.write_result()
  # then process_result() updates state.md (verified → established, failed → attempts)
  return
```

Do not batch. Do not summarize. One claim per tick — that's what keeps the loop honest.

## Reading the queue

```python
python -c "
import sys; sys.path.insert(0, '.')
from core.verify import read_log
log = read_log('workspace/research')
claims = [e for e in log if e['type'] == 'claim']
results = {e['claimId'] for e in log if e['type'] == 'result'}
pending = [c for c in claims if c['id'] not in results]
if pending: print(pending[0])
"
```

If `pending` is empty, exit silently. A verifier that speaks when it has nothing to say is just noise.

## Spawning the subagent

```
Task(
  subagent_type="verifier",
  prompt=(
    "Problem: <goal from state.md>\\n"
    "Claim ID: C3\\n"
    "Claim: <claim text>\\n"
    "Context: <one-line context>\\n"
    "Depends on: [C1, C2]\\n"
    "Verify this independently using any method (SymPy, numerical spot-check, "
    "dimensional analysis, limiting case, reference). Write the result via "
    "core.verify.write_result(). Do not attempt to see my reasoning — there is "
    "none available to you, and that is by design."
  )
)
```

The subagent returns nothing to you directly — it writes to `verification.log` and exits. That's correct. The working agent reads results via `read_verification_results()` when it needs them.

## Communication channel (recap)

| Direction | Mechanism |
|---|---|
| Working agent → queue | `emit_claim(claim, context, depends)` |
| You (verifier loop) → subagent | `Task(subagent_type="verifier", ...)` |
| Subagent → log | `write_result(claim_id, status, method, detail)` + `process_result(...)` |
| Working agent ← results | `read_verification_results()` (polls since last read) |

Three functions in `core/verify.py`. No queues, no events, no IPC. The filesystem is the channel.

## Invocation

**Continuous:**
```
/loop 60s /verifier
```
Default cadence is 60s. Start it when formal work begins (first `emit_claim()`), stop it when formal work ends (`/loop stop`).

**Single tick:**
```
/verifier
```
Useful when Quinn says "check this one thing" — drains one claim and exits.

Do not auto-start at session start. The verifier exists to serve formal work; if there is no formal work, it is silent.

## Hard rules

- **One claim per tick.** Even if ten are pending, verify the first and return. Context discipline.
- **Never pass CoT.** The subagent gets the claim, the context, the dependency IDs. Nothing else.
- **Silence when empty.** If nothing is pending, exit without output.
- **Trust the subagent's verdict.** If it says "uncertain," write that. Don't retry to get a different answer.
- **Never mark a claim `verified` yourself.** That's the subagent's job. You orchestrate; you don't decide.
