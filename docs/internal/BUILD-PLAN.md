# Triptych v2 — Build Plan

*This plan is executed by one Opus orchestrator with Sonnet subagents. The north star is `PRD.md` — every decision should trace back to it. When in doubt, read the PRD.*

## Build Protocol

Every task follows this loop. No exceptions.

```
1. PLAN        → orchestrator defines the task, references PRD section
2. TEST FIRST  → subagent writes failing tests for the feature
3. IMPLEMENT   → subagent(s) code until tests pass. Stop when tests pass.
4. SIMPLIFY    → fresh subagent (no implementation context) reviews the diff
5. VERIFY      → run full test suite (pytest for Python, vitest for TypeScript)
6. DOCUMENT    → update tools.md / CLAUDE.md / skills only if user-facing
7. CHECKPOINT  → human reviews, /clear, next task
```

### Hard Rules

1. **No architectural decisions in subagents.** Subagents implement the plan. They don't redesign the system. If they think the plan is wrong, they report back.
2. **One file per subagent.** Two agents writing the same file creates race conditions and inconsistency.
3. **Read before write.** Every agent reads the files it will touch AND at least one adjacent file to absorb conventions before writing anything.
4. **Tests define done.** When tests pass, stop. Don't "improve" working code.
5. **Line budget.** v2 should add <2,000 lines to the existing ~3,700 line codebase. If it's heading past that, something is overengineered.
6. **No fix-forward.** If something breaks, diagnose the root cause. Don't wrap it in a try/catch.
7. **Pattern reference.** Every task includes "match the pattern in [existing file]."
8. **No new dependencies** without explicit justification. If the alternative is <50 lines of code, write the code.
9. **The PRD is the north star.** If a task doesn't trace back to the PRD, it shouldn't exist.

### The Simplifier Agent

Runs after every implementation step. Fresh context — no knowledge of the implementation reasoning. Only sees the code.

Mandate:
- If in doubt, remove it
- If a feature added >150 lines, justify each block. If you can't, simplify.
- No new dependencies unless the alternative is >50 lines
- Match existing patterns — if the codebase uses plain functions, don't introduce classes
- Run tests after every simplification — simplification that breaks things isn't simplification
- Check for: unnecessary abstraction, dead code, unused imports, over-engineering, pattern inconsistency, remnant scaffolding

### Agent Architecture

- **Orchestrator (Opus):** reads plan, decomposes tasks, delegates, reviews results, manages checkpoints
- **Implementation subagents (Sonnet):** write tests and code, scoped to specific files
- **Simplifier subagent (Sonnet):** reviews implementation with fresh eyes, simplifies
- **All subagents use `isolation: worktree`** for parallel work where applicable

---

## Language Split

Two languages, clean boundary, each doing what it's best at:

```
TypeScript (server):   HTTP + WebSocket + PTY + file watching
                       ↕ filesystem ↕
Python (intelligence): research state, verification, display addons, CAS tools
```

The server stays TypeScript — node-pty is the only mature PTY solution on Windows, and the server's job (serving files, managing connections) doesn't overlap with the intelligence layer. Python handles everything Claude interacts with: research state operations, verification, display rendering, CAS tools (SymPy). The filesystem is the interface between them.

## Directory Structure (v2)

The existing structure stays. New v2 additions:

```
triptych/
├── core/
│   ├── shell.html           (existing — UI, modified in final stage)
│   ├── shell.js             (existing — UI, modified in final stage)
│   ├── shell.css            (existing — UI, modified in final stage)
│   ├── capture.js           (existing — snapshot system)
│   ├── default-display.html (existing — display loader)
│   ├── __init__.py          [NEW] — makes core/ a Python package (empty)
│   ├── research.py          [NEW] — research state + dependency graph operations
│   └── verify.py            [NEW] — claim emission + verification log operations
├── server/
│   ├── index.ts             (existing — no changes needed)
│   └── server.test.ts       (existing — extended)
├── .claude/
│   ├── agents/
│   │   ├── simplifier.md    [EXISTS] — BUILD TOOL: code simplification agent (not part of product)
│   │   ├── verifier.md      [CHECKPOINT 2] — product agent: claim verification (built in task 2.2)
│   │   └── cross-verifier.md [CHECKPOINT 4] — product agent: cross-verification (built in task 4.2)
│   ├── skills/
│   │   ├── triptych-displays/SKILL.md  (existing)
│   │   ├── triptych-workspaces/SKILL.md (existing)
│   │   ├── study/            (existing)
│   │   └── watcher/          [NEW] — watcher loop skill
│   └── settings.json
├── workspaces/               (existing workspace addons — unchanged in build phase)
├── displays/
│   ├── __init__.py           (existing — add new exports)
│   ├── _base.py              (existing)
│   ├── d3.py                 (existing — used for dependency graph viz)
│   ├── ... (other existing display addons)
│   └── research.py           [NEW] — research state + dependency graph display addon
├── workspace/                (runtime state — gitignored)
│   ├── snapshots/            (existing)
│   ├── output/               (existing)
│   ├── files/                (existing)
│   └── research/             [NEW] — runtime research state
│       ├── state.md          — research state narrative (PRD calls this research-state.md)
│       ├── deps.json         — dependency graph (PRD calls this dependencies.json)
│       ├── verification.log  — verification results (JSONL)
│       └── watcher.log       — watcher observations (append-only)
├── tests/
│   ├── test_research.py      [NEW] — research state + dependency graph tests
│   ├── test_verify.py        [NEW] — verification system tests
│   └── test_watcher.py       [NEW] — watcher behavior tests
├── onboard.md                [NEW] — first-run onboarding questions (deleted after use)
├── PRD.md                    (north star)
├── BUILD-PLAN.md             (this file)
└── CLAUDE.md                 (project instructions — updated throughout)
```

Core Python files (`core/research.py`, `core/verify.py`) are stable infrastructure Claude calls but doesn't edit. Display Python files (`displays/research.py`) are addons Claude can freely modify. The server (TypeScript) serves files and manages connections — it doesn't need to know about research state or verification.

**New files: ~10.** Most v2 behavior lives in agent definitions, skills, and CLAUDE.md instructions — not new code.

---

## Checkpoint 1: Research State Infrastructure

**PRD reference:** "Research State" section — the seven-field structure, dependency graph, two-file architecture (state.md + deps.json).

**Goal:** The working agent can create, read, update, and query the research state. The dependency graph supports node/edge operations and invalidation propagation. Both are just files.

### Tasks

**1.0 — Project scaffolding (prerequisite for all checkpoints)**

Before any implementation:
- Create `core/__init__.py` (empty — makes core/ a Python package so `from core.research import ...` works)
- Create `workspace/research/` directory
- Add `workspace/research/` to `.gitignore` (runtime state, not checked in)
- Create `tests/conftest.py` with shared fixtures (temp workspace directory, cleanup)
- Install pytest if not present: `pip install pytest`
- Verify import path works: `python -c "import sys; sys.path.insert(0, '.'); from core import research"` should import (even if module is empty)

Note on Python imports: the display addons already use `sys.path.insert(0, '.')` to import from the project root. Core Python files follow the same pattern. All agents calling core functions should use this prefix.

**1.1 — Research state file manager (`core/research.py`)**

A small utility that the working agent uses to manage research state files. Plain functions, no classes.

- `init_research(goal)` → creates `workspace/research/state.md` with the seven-field template and `workspace/research/deps.json` with empty graph
- `read_state()` → reads and returns the current state.md content
- `update_state(section, content)` → updates a specific section of state.md (goal, questions, assumptions, attempts, established, threads, next)
- `add_attempt(description, outcome, reason)` → appends to attempts section
- `add_established(id, label, depends_on)` → adds to established results AND adds node + edges to deps.json

Pattern reference: match the style in `displays/_base.py` — simple functions, constants, no classes. Claude calls these via `python -c "from core.research import init_research; init_research('Derive EOM for pendulum')"` or similar.

Tests first:
- state.md created with correct template on init
- Each section updateable independently
- Attempts append correctly
- Established results write to both files simultaneously

**1.2 — Dependency graph operations (`core/research.py`, continued)**

- `add_node(id, type, label, status)` → adds node to deps.json
- `add_edge(from_id, to_id)` → adds edge to deps.json
- `invalidate(node_id)` → sets node status to "invalidated", walks graph downstream, flags all dependents as "needs-reverification"
- `get_downstream(node_id)` → returns all nodes that depend on (directly or transitively) the given node
- `get_graph()` → returns the full graph object

Tests first:
- Nodes and edges persist to deps.json
- Invalidation propagates downstream correctly (A→B→C, invalidate A, B and C flagged)
- Circular dependency detection (should not be possible, but handle gracefully)
- get_downstream returns transitive closure

**1.3 — Research state display addon (`displays/research.py`)**

- `show_research()` → calls `core.research` to read state.md + deps.json, renders a combined view in the display panel
- Narrative section (state.md rendered as formatted HTML)
- Dependency graph section (deps.json rendered as d3 force-directed graph)
- Nodes colored by status: active (green), verified (blue), invalidated (red), needs-reverification (yellow)

Pattern reference: match `displays/d3.py` for the d3 scaffold, match `displays/markdown.py` for the narrative rendering.

Tests first:
- show_research() produces valid HTML
- Graph renders with correct node count and edge count
- Status colors map correctly

**Checkpoint 1 deliverable:** `workspace/research/` directory works. State can be created, updated, queried. Dependency graph supports invalidation propagation. Research state renders in display panel.

---

## Checkpoint 2: Verification System

**PRD reference:** "The Verification System" section — claim emission, verifier agent, verification log, verifier-agent communication.

**Goal:** The working agent can emit claims. A Sonnet verifier agent independently checks them. Results are written to a verification log. The working agent reads the log between steps.

### Tasks

**2.1 — Claim emission + verification log (`core/verify.py`)**

Utilities for the working agent to emit claims and read verification results.

- `emit_claim(claim, context, depends)` → appends structured claim to `workspace/research/verification.log`
- `read_verification_results()` → reads the log, returns any flags/failures since last check
- `clear_results()` → marks all current results as read
- Log format: JSONL (one JSON object per line) — easy to append, easy to parse, no corruption risk

```jsonl
{"type":"claim","id":"C1","claim":"∂L/∂θ = -mgl sin(θ)","context":"partial derivative of L w.r.t. θ","depends":["A1","R1"],"timestamp":1234567890}
{"type":"result","claimId":"C1","status":"verified","method":"sympy","detail":"confirmed via symbolic differentiation","timestamp":1234567891}
{"type":"result","claimId":"C2","status":"failed","method":"numerical","detail":"LHS=3.14, RHS=2.71, mismatch","timestamp":1234567892}
{"type":"flag","kind":"missing-claim","detail":"new equations in display output with no corresponding claim","timestamp":1234567893}
```

Tests first:
- Claims append to log without corrupting existing entries
- Results are correctly associated with claims by ID
- read_verification_results returns only unread results
- JSONL format is valid and parseable line by line

**2.2 — Verifier agent definition (`.claude/agents/verifier.md`)**

A custom Sonnet subagent. This is a markdown file with YAML frontmatter.

```yaml
---
name: verifier
description: Independent verification agent — checks mathematical and scientific claims without seeing the working agent's reasoning
model: sonnet
tools:
  - Bash
  - Read
  - Write
  - Glob
  - Grep
allowedTools: []
---
```

System prompt body defines:
- Role: you are an independent verifier. You receive claims + one-line context + the original problem statement. Never the working agent's reasoning.
- For each claim, decide how to verify: SymPy computation, numerical spot-check, dimensional analysis, limiting case, independent reasoning
- Write results to the verification log using the JSONL format
- Also monitor display output (`workspace/output/`) for new mathematical content with no corresponding claim — flag as "missing-claim"
- Be honest about uncertainty — flag as "uncertain" rather than rubber-stamping

**The verifier agent has access to Bash (for running Python/SymPy checks) and Read/Write (for the verification log and display output). It does NOT have access to the working agent's conversation or reasoning.**

**How the verifier is spawned:** The working agent uses Claude Code's `Agent` tool to spawn the verifier as a subagent: `Agent(subagent_type="verifier", prompt="Verify the following claims against problem statement: [problem]. Claims: [claims from verification.log]")`. The verifier runs in its own context, reads the claims from the log, runs its checks, writes results back to the log, and returns a summary to the working agent. This is a standard Claude Code custom agent invocation — no special infrastructure needed.

Tests first:
- Agent definition file is valid markdown with correct frontmatter
- A mock claim can be processed (spawn the agent with a test claim, verify it writes a result to the log)
- The agent correctly identifies a known-wrong claim (e.g., "derivative of x² is 3x")
- The agent correctly verifies a known-correct claim

**2.3 — Wolfram MCP setup**

Check if Wolfram MCP is available. If not, set it up so the verifier agent can use it for symbolic computation. If setup is complex, SymPy via Python is the fallback — the verifier agent can run `python -c "from sympy import ..."` via Bash.

This is a configuration task, not a coding task. Document what's available in CLAUDE.md.

**2.4 — Wire verification into research state**

When a claim is verified:
- Add it to established results in state.md
- Add it as a node in deps.json with status "verified" and edges from its dependencies

When a claim fails:
- Add it to attempts in state.md (what was tried, why it failed)
- Do NOT add it to deps.json (unverified claims don't enter the graph)

When a claim is uncertain:
- Note it in state.md under open threads
- Add it to deps.json with status "unverified"

Tests first:
- Verified claim flows to both state.md and deps.json
- Failed claim flows to attempts only
- Uncertain claim flows to open threads + deps.json with "unverified" status

**Checkpoint 2 deliverable:** Full verification pipeline works end-to-end. Working agent emits claims → verifier agent processes them independently → results land in the verification log → research state updates accordingly.

---

## Checkpoint 3: Watcher System

**PRD reference:** "The Proactive Watcher" section — snapshot reading, behavior model, exploration vs. formalization modes, watcher preferences.

**Goal:** The main agent can watch the human's workspace via periodic snapshot reading, with behavior that adapts based on the phase (exploration vs. formalization) and user preferences.

### Tasks

**3.1 — Watcher skill (`.claude/skills/watcher/SKILL.md`)**

A skill that defines the watcher's behavior. This is mostly prompt engineering — the watcher is the main Claude agent reading snapshots on a loop, not a separate process.

The skill defines:
- How to read snapshots (`workspace/snapshots/latest.png` + `latest.json`)
- Behavior model from the PRD: obvious errors → speak, possible errors → log, ideas → log silently
- Exploration mode: Socratic, generative, no verification
- Formalization mode: error-checking, claims being verified, full verification system active
- How to detect the transition (equations appearing, formal derivations starting, human says "let's formalize")
- The research question prompt: "Before we dive in, can we state clearly — what exactly are we trying to show?"
- Where to log observations (`workspace/research/watcher.log` — append-only, timestamped)

Pattern reference: match the `/study` skill's format — detailed behavioral instructions in markdown.

Tests:
- Skill file is valid and loadable
- Watcher log is created and appended to correctly
- Snapshot files can be read (test with a mock snapshot)

**3.2 — Onboarding flow (`onboard.md`)**

A markdown file that the agent reads on first conversation with a new user. Contains:
- Brief introduction to Triptych v2
- Questions about working style: what kind of work, how much intervention, error sensitivity
- Questions about domain: what field, what tools they use
- Instruction to save preferences to CLAUDE.md and delete onboard.md when done

This is a one-time file — it self-destructs after first use.

Tests:
- onboard.md exists and is well-formed
- Instructions are clear about saving to CLAUDE.md and self-deletion

**3.3 — Integrate watcher with verification system**

When the watcher is in formalization mode and the AI is working:
- The watcher's observations about the human's work are separate from the verifier's checks on the AI's claims
- But both write to the research state (watcher observations go to a "Watcher Notes" section or similar)

When the watcher detects the exploration → formalization transition:
- Prompt for a research question / hypothesis
- Initialize the research state with the goal
- Begin claim emission and verification

Tests:
- Watcher log entries are correctly timestamped
- Transition detection triggers research state initialization
- Research question prompt appears at transition

**Checkpoint 3 deliverable:** The watcher skill works. The agent can observe the workspace, adapt behavior based on phase, log observations, and transition between exploration and formalization. Onboarding flow works for new users.

---

## Checkpoint 4: Autonomous Operation

**PRD reference:** "Autonomous Operation" section — same system, human not drawing. Also "Exploration and Formalization — Both phases in autonomous operation."

**Goal:** The agent can accept a problem, work it independently using the full verification pipeline, maintain the research state, and produce verified results.

### Tasks

**4.1 — Autonomous work loop**

This is primarily a skill/protocol definition, not new code. The autonomous loop:

1. Accept problem statement → initialize research state with goal
2. Exploration phase: survey approaches, identify relevant tools, form strategy
3. Crystallize: state a clear research question / hypothesis
4. Formalization phase: derive step by step, emit claims
5. Between each step: check verification log, address any flags
6. At milestones: cross-verification (spawn a separate subagent to solve via different method)
7. When done: full verification pass, update research state, present results

The loop uses everything built in checkpoints 1-3:
- Research state (checkpoint 1) for tracking progress
- Verification system (checkpoint 2) for checking claims
- Watcher behavior model (checkpoint 3) for phase transitions

New code should be minimal — mostly wiring the existing pieces together.

Tests:
- Given a simple problem (e.g., "derive the period of a simple pendulum"), the system:
  - Creates research state
  - Emits claims
  - Claims are verified
  - Research state is updated with established results
  - Dependency graph is populated
- Given a problem with a known error (e.g., a prompt that leads to a common mistake), the verifier catches it

**4.2 — Cross-verification agent**

A custom Opus agent definition (`.claude/agents/cross-verifier.md`) — uses Opus for depth since it runs infrequently. It:
- Receives a problem statement and a claimed result
- Solves the problem via a deliberately different method
- Compares its result with the claimed result
- Reports: match, mismatch, or unable to verify

This runs at milestones during autonomous operation — not on every claim.

Tests:
- Cross-verifier produces an independent result for a known problem
- Cross-verifier correctly identifies a mismatch when given a wrong result

**4.3 — Integration test: full autonomous run**

An end-to-end test that runs the full autonomous loop on a real problem:
- Problem: derive the equation of motion for a damped harmonic oscillator
- Expected: correct equation, verified claims, populated research state, dependency graph showing the derivation chain

This test validates that all the pieces (research state, verification, watcher, autonomous loop) work together.

**Checkpoint 4 deliverable:** The system can work independently on a problem, maintaining verified research state throughout. Cross-verification runs at milestones. The full pipeline works end-to-end.

---

## Checkpoint 5: Integration + Hardening

**PRD reference:** All sections — this checkpoint ensures everything works together and handles edge cases.

**Goal:** The complete system works reliably. Edge cases are handled. Documentation is current.

### Tasks

**5.1 — Edge case handling**

Test and handle:
- What happens when the verifier finds an error mid-autonomous-run? (Agent should re-examine, try alternative, update attempts)
- What happens when an assumption is invalidated? (Dependency graph propagates, affected results flagged)
- What happens when the verifier is uncertain about every claim? (Agent should proceed with uncertainty logged, not loop forever)
- What happens when the workspace has no snapshots? (Watcher should handle gracefully)
- What happens when research state files don't exist yet? (All code should handle first-run gracefully)

**5.2 — CLAUDE.md rewrite**

Update CLAUDE.md to reflect the v2 system:
- Verification system: how to emit claims, how the verifier works
- Research state: where it lives, how to read/update it
- Watcher: how it behaves, how preferences work
- Exploration vs. formalization: what changes between phases
- Autonomous operation: how to start, what to expect
- Keep it concise (<300 lines per best practices)

**5.3 — tools.md update**

Add new core features and any new addons to the tools reference.

**5.4 — Final test suite run**

Run all tests. Everything passes. No flaky tests.

**Checkpoint 5 deliverable:** The system is complete, documented, and tested. All edge cases handled. CLAUDE.md reflects v2. Ready for UI work.

---

## Final Stage: UI Design + Browser Testing

**This stage happens AFTER all 5 checkpoints, with human input on design.**

**PRD reference:** "The system must be invisible when working correctly" — UI should surface verification status and research state without being noisy.

### Tasks

**6.1 — UI design discussion with human**

Before any code:
- Discuss what the UI should look like for verification status, research state, dependency graph
- Discuss whether existing UI patterns work or need changes
- Discuss notification model for errors
- Mock up / wireframe before implementing

**6.2 — UI implementation**

Implement the agreed design. This may touch:
- `core/shell.html` / `core/shell.js` / `core/shell.css` — layout changes
- `core/default-display.html` — how research state / verification status appears
- New or modified display addons

**6.3 — Browser testing**

Using Chrome automation tools:
- Open localhost:3000
- Navigate between workspaces
- Trigger verification (have the agent work a problem)
- Verify research state renders correctly
- Verify dependency graph visualization works
- Check that verification is invisible when things pass
- Check that errors surface appropriately
- Test the onboarding flow
- Record a GIF of the full workflow

**6.4 — Final simplifier pass**

One last review of the entire v2 diff:
- Remove any dead code
- Consolidate any duplication
- Verify pattern consistency
- Check line budget
- Tests still pass

---

## Summary

| Checkpoint | Focus | Key Files | PRD Section |
|---|---|---|---|
| 1 | Research State | `core/research.py`, `displays/research.py` | "Research State", "Logical dependency graph" |
| 2 | Verification | `core/verify.py`, `.claude/agents/verifier.md` | "The Verification System" |
| 3 | Watcher | `.claude/skills/watcher/`, `onboard.md` | "The Proactive Watcher", "Exploration and Formalization" |
| 4 | Autonomous | `.claude/agents/cross-verifier.md` | "Autonomous Operation" |
| 5 | Integration | CLAUDE.md, tools.md, edge cases | All sections |
| Final | UI | `core/shell.*`, display addons | "The system must be invisible" |

**Estimated new code: <2,000 lines across ~10 new files.**
**Estimated new tests: ~500 lines across 3-4 test files (pytest for Python, vitest for existing TS tests).**
**Much of v2 is behavioral (agent definitions, skills, CLAUDE.md) rather than code.**

**Test runners:**
- Python tests: `pytest tests/` — covers core/research.py, core/verify.py, watcher, integration
- TypeScript tests: `npx vitest run` — covers server (existing) and any TS additions

---

## v2 Build Status (as of 2026-04-05)

**Checkpoints 1-5: COMPLETE.** Final Stage (UI): COMPLETE.

### What's built and working

| Component | Files | Tests | Status |
|---|---|---|---|
| Research state (7-field + deps graph) | `core/research.py` | 20 tests | Done |
| Verification system (claims, log, wiring) | `core/verify.py` | 13 tests | Done |
| Watcher log + utilities | `core/research.py` (log_watcher) | 5 tests | Done |
| Edge cases | tests/run_tests.py | 7 tests | Done |
| Research display addon | `displays/research.py` | 4 tests | Done, browser-tested |
| Verifier agent definition | `.claude/agents/verifier.md` | — | Done |
| Cross-verifier agent definition | `.claude/agents/cross-verifier.md` | — | Done |
| Watcher skill | `.claude/skills/watcher/SKILL.md` | — | Done |
| Autonomous skill | `.claude/skills/autonomous/SKILL.md` | — | Done |
| Onboarding flow | `onboard.md` | — | Done |
| Shared theme system | `core/theme.css` | — | Done, all workspaces updated |
| Documentation | CLAUDE.md, tools.md | — | Done |

**49 tests, 0 failures. 559 lines of new code (budget was 2,000).**

### What's left: behavioral tuning and real-world testing

The infrastructure is built. What remains is **prompting quality** and **real-world iteration** — things that can only be refined through actual use sessions, not pre-built.

#### Ready to use now (just invoke it)
- **Verifier agent**: spawn via `Agent(subagent_type="verifier", ...)` — this is Claude Code's built-in subagent mechanism, no custom code needed
- **Cross-verifier agent**: spawn via `Agent(subagent_type="cross-verifier", ...)`  
- **Watcher**: run via `/loop 30s /watcher` — `/loop` is a built-in Claude Code skill
- **Autonomous mode**: invoke via `/autonomous` with a problem statement
- **Research display**: call `show_research()` from Python

#### Needs real-world testing and iteration
1. **Verifier prompt quality** — Does the verifier.md system prompt actually produce good verification in practice? Does it catch real errors? Does it rubber-stamp? Needs testing on actual math/physics problems to calibrate.

2. **Watcher phase detection** — The watcher skill describes transition signals (equations appearing, formal derivations starting). Does the AI actually detect these from snapshots? Needs testing with real workspace screenshots.

3. **Autonomous loop flow** — The autonomous skill defines the protocol but hasn't been run end-to-end on a real problem. Does the claim→verify→continue loop work smoothly? Where does it get stuck?

4. **Onboarding flow** — `onboard.md` exists but hasn't been run with a real user. The preference-saving-to-CLAUDE.md flow needs to be tested once.

5. **Preference integration** — After onboarding saves preferences to CLAUDE.md, does the watcher actually read and respect them? CLAUDE.md is loaded into context automatically, so the AI should see them — but this needs validation.

#### Things that look like gaps but aren't
- **"/loop command"** — This is a built-in Claude Code skill, not something we need to build
- **"Subagent spawning"** — Claude Code's `Agent()` tool handles this natively; the agent .md files define behavior
- **"Async verification"** — The verifier runs as a subagent within Claude Code; "async" means the working agent spawns it and continues, which is how `Agent()` works
- **"Preference parsing"** — CLAUDE.md is loaded into every conversation; the AI reads preferences from it naturally, no parser needed
- **"Phase state machine"** — The AI maintains phase awareness in its own context; no persistent state file needed since the watcher runs within the same session

#### Genuine future work (not blocking v2 launch)
1. **Display output monitoring** — The verifier should check `workspace/output/` for equations with no corresponding claims. This could be a small addition to the verifier prompt or a utility function. Low priority since the working agent should be emitting claims.

2. **process_result() dependency wiring** — Currently `process_result()` requires the caller to pass `depends` explicitly. It could auto-read the claim's depends from the verification log by claim ID. Small code improvement.

3. **Benchmarking** — PRD mentions measuring verification coverage: "run N problems, compare verified vs. unverified solve rates." This is future work after the system is running.

4. **Domain-specific addons** — Math addon (SymPy integration), biology addon, etc. The addon architecture exists but no domain-specific examples beyond the research display.

5. **Light theme** — `core/theme.css` uses CSS variables, ready for a light theme swap. Not built yet.

---

*The PRD is the north star. When implementation decisions arise that this plan doesn't cover, read the PRD. When the PRD and this plan conflict, the PRD wins.*
