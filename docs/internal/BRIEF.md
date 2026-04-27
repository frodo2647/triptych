# Triptych v2 — Project Brief

## The Thesis

Claude Code is the best AI framework for coding. It works because of a tight feedback loop: filesystem + compiler + terminal. The compiler provides instant, binary, external verification — the AI writes code, the compiler says yes or no, the AI iterates.

There is no equivalent for hard problems — math, physics, research. A wrong derivation produces no error message. A plausible formula doesn't crash. Every physicist and mathematician using AI today is stuck in a chat window, copy-pasting between Claude and their actual work. The feedback loop is broken.

There's a second axis worth naming: most AI surfaces today are designed for one-shot consumption. You ask, you get an answer, you accept. Hybrid-intelligence research suggests this mode actively atrophies the human — the people who get sharper from AI are the ones who push back, demand evidence, and ask the AI to argue against itself. Triptych is shaped for the second mode: visible verification, surfaced assumptions, milestone red-team passes. The workspace makes the back-and-forth structural rather than something the user has to remember to do.

Triptych is *not* trying to compete with autoresearch (Karpathy) or other metric-driven optimization tools — those are well-served when the problem is shaped right for them. Triptych is for the much larger class of problems where there is no single number going down: derivations, conceptual work, design decisions, anything where the work is partly figuring out what counts as the right answer.

Triptych v1 built the foundation: three panels (workspace, display, terminal), filesystem as message bus, extensible addons. ~500 lines of framework code. It works. But it's still a passive system — Claude only acts when asked.

**v2 adds the intelligence layer that closes the loop.**

## What v2 Adds

### 1. Proactive Watcher

The predecessor to Triptych (the "Research Interface," March 2026) had this working:

- Claude watches snapshots automatically, builds a mental model of what you're working on
- Phase-based behavior: observe silently (phase 1) -> proactively spawn background workers for sims, paper searches, derivation checks (phase 2) -> respond immediately to voice/text triggers, referencing work already done (phase 3) -> speak unprompted only for errors, dead-end warnings, or important findings (phase 4)
- Background workers write to the display panel — results appear without interrupting the human

This needs to be rebuilt for Triptych's architecture (filesystem-based, not WebSocket-based).

### 2. Verification Hooks

The "compiler for hard problems" isn't one tool — it's a pattern of pluggable verification:

- **Wolfram MCP** ($5/mo service, already exists): symbolic computation, dimensional analysis, numerical checks. When Claude derives something, Wolfram verifies the math.
- **SymPy/NumPy**: local computation for quick checks
- **Cross-verification**: Claude checks its own work by approaching the problem differently, or by checking limiting cases / dimensional analysis / known results
- **Future hooks (not v2 scope)**: Lean for formal proofs, simulation runners for physics, Monte Carlo checks

The watcher should automatically trigger verification on derivation steps it observes in the workspace.

### 3. Autonomous Mode

Triptych v1 is collaborative-only (human draws, Claude watches). v2 adds autonomous mode:

- Feed a problem via prompt or file, Triptych works independently
- Same watcher + verification loop, just without a human in the workspace
- Enables benchmarking: run N problems, measure solve rate vs. Claude alone
- This is how we test and demonstrate the system's value quantitatively

### 4. Research State Persistence

The Research Interface had session memory files (research-context.md, explored-directions.md, session-mode.md). Triptych v2 formalizes this:

- Track what's been tried, what worked, what failed, and why
- Persist across sessions so Claude picks up where it left off
- This is the seed of what could become a "Research State Graph" — but keep it simple for now (markdown files, not a database)

## Competitive Landscape

$3B+ in VC is chasing pieces of this problem:

- **Harmonic** ($1.45B): Math-only, Lean proofs, chatbot interface. No physics, no workspace, no visual reasoning.
- **Axiom** ($1.6B): Math prover + code verifier, Lean/Rocq. No physics, not publicly available.
- **DeepMind AlphaProof**: Research-only, no public tool or API.
- **Wolfram MCP**: Computation layer, not a workspace or reasoning tool.

Nobody is building the workspace — the environment where a human and AI actually work together on hard problems with visual reasoning, pluggable verification, and proactive assistance. That's Triptych.

## Design Philosophy (Unchanged from v1)

1. **Do the simple thing that works.** Files, not APIs. HTML from CDN, not npm packages. If it can be a file write, it should be.
2. **The framework should be invisible.** Human draws, Claude sees. Claude computes, human sees. The plumbing disappears.
3. **Claude can always extend it.** Need a new workspace? Write HTML. Need a new display? Write Python. Need a verification hook? Write a module. No restart, no plugin registry.
4. **Anyone can build their own addons.** The value proposition is the pattern (filesystem + verification + proactive watching), not any specific addon. A Lean user writes Lean addons. A chemist writes molecule viewers. The framework serves all of them.

## Target Outcomes

By end of sprint:
- Proactive watcher working in Triptych (phase-based, background workers)
- Wolfram MCP integrated as verification hook
- Autonomous mode that can accept and solve problems without human input
- Benchmark results: solve rate on graduate-level physics/math problems, Triptych+verification vs. Claude alone
- README rewritten for public launch (architecture description, not GIFs yet — those come in summer when Quinn records collaborative demos)

## What Already Exists (v1)

- Express + WebSocket server (506 lines): `server/index.ts`
- Three-panel shell with resizable dividers: `core/shell.html`, `core/shell.js` (582 lines)
- Capture system (30s snapshots): `core/capture.js`
- 6 workspace addons: tldraw, editor, markdown, spreadsheet, pdf, welcome
- 10 display addons: matplotlib, plotly, latex, html, image, pdf, markdown, code, table, d3
- 26 passing tests
- Dark theme, file sidebar, drag-drop, auto-reload

Read CLAUDE.md and tools.md for full operational details.

## Platform

- Windows 11 (native, NOT WSL)
- Shell: bash (Git Bash)
- Node.js + TypeScript for server
- Python for display addons and computation
- Wolfram MCP: external service, $5/mo subscription
