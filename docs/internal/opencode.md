# OpenCode compatibility

*2026-04-23. Docs only — no code changes required or planned.*

OpenCode is an open-source terminal coding agent (`anomalyco/opencode` on GitHub, ~147k stars as of this writing) with broad LLM-provider support. Some users may prefer it over Claude Code — multi-model routing, open-source license, cost profile, policy reasons. This doc covers how to run OpenCode inside Triptych and what to expect.

## Short answer

Triptych's server hosts a PTY. Any interactive terminal binary works inside it. To try OpenCode:

```bash
# inside the Triptych shell (the terminal panel on the right)
opencode
```

No Triptych config change. No flag. The filesystem-is-the-channel model is provider-agnostic: OpenCode reads/writes the same `workspace/`, runs the same Python modules, sees the same displays auto-reload.

## What works

- **Skills.** Triptych's bundled skills conform to the `agentskills.io` open spec. OpenCode adopts the same format, so `/scientific-writing`, `/paper-lookup`, `/literature-review`, etc. work without change.
- **Research state.** `core/research.py`, `core/verify.py`, `core/session.py` are plain Python — any shell-spawning agent can call them. The main commands (`init_research`, `emit_claim`, `add_observed`, etc.) don't care which agent invokes them.
- **Displays.** Writing to `workspace/output/` triggers auto-reload via chokidar. Provider-agnostic.
- **Integrations.** `integrations/` is just Python; same story.

## What's different / caveats

- **Verifier quality depends on model class.** `/verifier` spawns an isolated subagent to re-derive a claim independently. Its reliability is a function of the model running that subagent. Claude Opus gives stronger mathematical verification than cheaper routers OpenCode might use. If verification is load-bearing (physics derivations, formal proofs), stay on Claude Code or configure OpenCode to route verifier subagents to a strong model.
- **Hooks are Claude Code-specific.** The UserPromptSubmit / SessionStart / Stop hooks in `.claude/settings.json` run only under Claude Code. OpenCode's hook system (if/when it has one) would need separate config files. The downstream effect: context injection from `inject-session-context.mjs`, `inject-skill-hints.mjs`, etc., does not fire under OpenCode. The agent sees less session context on startup.
- **Subagent invocation mechanism may differ.** Claude Code's Task tool spawns subagents from `.claude/agents/`. OpenCode's subagent model (if any) may need a different directory or invocation syntax — verify before relying on `/verifier` or `/dashboard` under OpenCode.
- **`/loop` skill behavior.** `/loop 60s /verifier` is a Claude Code skill. OpenCode has its own loop / scheduling primitives; the pattern is the same but the command isn't portable.

## How to try it

1. Install OpenCode per its README.
2. Open the Triptych terminal panel (right pane).
3. Run `opencode` inside. It takes over the pane.
4. Point it at the same project directory. It'll see `CLAUDE.md` — OpenCode reads CLAUDE.md as project context.
5. Exercise a light task first (render a simple display, read a file). Before anything load-bearing like verifier work, check that your chosen model handles it.

If you want to switch back to Claude Code, exit OpenCode (`/exit` or `Ctrl+D`) and re-launch Claude Code from the same shell.

## Not planned

- `triptych --agent opencode` flag — not needed; PTY substitution covers it.
- Parity claims for `/verifier` across providers — model quality matters too much.
- A Triptych-native wrapper that abstracts over both — more machinery than the problem warrants.

## Related

- `docs/internal/ecosystem-scan.md` §J (alternative agents / CLIs — OpenCode entry)
- `agentskills.io` — open spec for SKILL.md portability
