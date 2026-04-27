# Triptych — Trial 1 Research Report

*MNIST/EMNIST trial, April 2026. Written to be picked up cold by any future session — read this alongside `PRD.md` and `ecosystem-scan.md`.*

---

## How to use this document

**If you are a new session starting work from this report:**

1. Read §0 (TL;DR) and §2 (what Trial 1 did NOT exercise) first. They set the honest baseline.
2. §3 (findings) and §6 (recommendations) are the actionable content. Each recommendation in §6 links back to a finding in §3 so you can audit the reasoning before acting.
3. Before starting work on any recommendation, open the specific files it references — this report was written from a code read, but code drifts. Verify current state, then proceed.
4. `ecosystem-scan.md` is the reference catalogue of external Claude Code projects, skills, and tools to consider pulling in. Treat it as a searchable index, not a read-through.
5. `PRD.md` is the north star. If a recommendation in this report conflicts with the PRD, the PRD wins unless you have a considered argument for deviation (and note it in the commit message).

**Status markers used:**
- ✅ Verified from evidence
- ⚠️ Partial / asserted but not directly evidenced by Trial 1
- ❌ Contradicted by evidence or not exercised
- 🔍 Needs investigation before acting

---

## 0. TL;DR

Trial 1 was a useful but narrow test. Quinn ran a 7-stage ML study (MNIST saturated at 99.44%, EMNIST-Balanced at 89.15% EMA) inside a cloned Triptych repo. The agent completed the substantive work, rewrote the research display into a kanban-first layout, built three new display addons, and wired plan tracking into `core/research.py` and `core/verify.py`.

**What Trial 1 exercised well (✅):** plan structure (7 items), dependency graph in `deps.json` (13 nodes, 11 edges), kanban-style research display, new display addons (`optuna.py`, `architecture.py`, `_graph.py`), embedded Optuna Dashboard integration, AST-based architecture visualization.

**What Trial 1 did NOT exercise (❌):** the verification loop. `emit_claim()` was never called. There is no `workspace/research/verification.log` in the mnist repo. The 6 "verified" results were written directly to `deps.json` by `scripts/backfill_mnist_plan.py` via `add_established()` — which sets `status: verified` as a side-effect of adding the node, *without any verifier ever running*. Cross-verification, watcher, invalidation propagation, and exploration mode were also untouched.

This matters because the PRD's central thesis is **verified work via isolated verification**. Trial 1 did not stress that thesis. It stressed the *structural scaffolding* around it (plan, state, graph, displays), which held up well. The verification loop's real-world behavior remains an open question.

Where friction appeared was at the surfaces — display tab flicker, stale output accumulation, no agent awareness of what the human is looking at, no articulated embed-vs-external paradigm, no goal-driven onboarding, no hooks for skill auto-activation. Most of these are additive work on a solid foundation, not rearchitecture.

---

## 1. What Trial 1 Actually Was

Quinn cloned Triptych to `C:/Users/aquin/mnist/` (same initial commit as the base system) and ran an ML study: train a from-scratch CuPy MLP on MNIST, saturate accuracy, then transfer the recipe to EMNIST-Balanced. Full trial spec in `workspace/files/emnist/PLAN.md` (source plan uses coarser numbering up to Stage 8; the agent's own plan in `workspace/research/state.md` breaks this into 7 items).

### What exists in the mnist repo that does not exist in triptych (✅ verified by diff)

**Three new display addons** (`C:/Users/aquin/mnist/displays/`):
- `optuna.py` — embeds Optuna Dashboard as an iframe in a display tab, auto-manages the subprocess via `scripts/optuna_server.py`, clamps iframe `min-width: 1400px` because the dashboard is desktop-optimized
- `architecture.py` — "What the AI has built" visualization; scans `workspace/files/` with Python AST, renders folder-grouped module cards with click-to-focus
- `_graph.py` — shared helper; injects `window.TriptychGraph` with a Sugiyama layered layout used by both `research.py` and `architecture.py`

**One substantially rewritten display** (`displays/research.py`, ~1038 → ~2000 lines): kanban columns (Planned → In-Progress → Verified), header-strip small-multiples (plan gauge, open-question count, verified-claims-over-time sparkline, verification-latency sparkline), dependency graph with depth slider and hover path highlighting, narrative state.md collapsible below fold.

**Core plumbing** (`core/research.py` +157 lines, `core/verify.py` +36 lines):
- `set_plan(items)` / `advance_plan(id)` / `mark_plan_done(id, claim_id)` — plan lifecycle
- `_ensure_plan_section(state_path)` — backfill the Plan section into state.md files that predate the schema extension
- `emit_claim(..., plan_id=...)` / `write_result(...)` gained `plan_id` awareness; `advance_plan` is called on emit, `mark_plan_done` on verify
- ⚠️ **Schema note**: this silently extends the PRD's **seven-field** research state to **eight** (Plan was added after Goal). The mnist `core/research.py` line 10 acknowledges this: `# The eight sections of the research state (Plan added after Goal)`. This is a PRD deviation — either a justified domain-addon promoted to core, or a case the PRD text should be updated to reflect. See §7 open question.

**One new helper module** (`core/optuna_helper.py`, ~120 lines): `TrialHandle` class with curve buffering + auto-publishing of Plotly panels; `single_run()` and `sweep()` context managers; single SQLite DB at `workspace/research/optuna/studies.db`.

**Seven new scripts** (`scripts/`, ~58 KB total):
1. `optuna_server.py` — idempotent start/stop of `optuna-dashboard` subprocess, port picking 8840–8849
2. `optuna_backfill.py` — reconstruct studies from on-disk `runs/stage{N}/seed{K}/metrics.json`
3. `optuna_push_ema_panel.py` — one-off publish of EMA-vs-raw comparison panel
4. `optuna_republish_panels.py` — regenerate unified panels, prefers EMA curves where present, cleans deprecated panel IDs
5. `build_repo_graph.py` — AST extraction to `workspace/output/arch-graph.json` (stdlib-only, ast + re)
6. `backfill_mnist_plan.py` — inserts the 7-stage plan into `state.md` AND writes R1–R6 directly via `add_established()` (see §2.1 below)
7. `particle_demo.py` — unrelated demo

**Docs touched**: `CLAUDE.md` (+1 line adding `/optuna` skill row), `tools.md` (+33 lines documenting research-display kanban, architecture display, Optuna addon and scripts, shared graph helper), `requirements.txt` (+2 lines: `optuna>=3.5`, `optuna-dashboard>=0.19`).

**Workspace output** (`workspace/output/`): 12 files (✅ counted) — 7 HTML tabs (`research.html`, `architecture.html`, `stage6.html`, `stage6_push.html`, `mnist-history.html`, `emnist-history.html`, `optuna_emnist.html`), 1 JSON data file (`arch-graph.json`), 3 logs (`finish_stage6.log`, `republish_loop.log`, `stage7_train.log`), and 1 **misplaced Python source file** (`progress_stage6.py`) that shouldn't be in an output directory at all.

**Uncommitted**. `C:/Users/aquin/mnist/` has zero trial commits — all of the above is untracked in the working tree. Meta-risk: if Quinn's machine dies, Trial 1 evaporates. Process finding: future trials should include a "commit at checkpoint" discipline, or Triptych should auto-snapshot trial state.

### The graph at the end of Trial 1

`deps.json` (✅ read directly): 13 nodes (7 plan items + 6 results), 11 edges. Structure is a linear chain:

```
s1_baseline → R1
              ↓       ← s2_adamw
              R2
              ↓       ← s3_regularize
              R3
              ↓       ← s4a_elastic
              R4
              ↓       ← s4a_emnist
              R5
              ↓       ← s5_ema
              R6
s6_affine (planned, no edges yet)
```

⚠️ **The graph is a chain, not a DAG.** Each result depends only on its predecessor + its plan slot — no branching, no invalidation, no cross-links. The graph's value in Trial 1 was structural/visual (seeing progress at a glance), not logical (no invalidation fired, no alternate paths to compare). The PRD's interesting dependency-graph behaviors (invalidation propagation, cross-verification divergence) remain unexercised.

---

## 2. What Trial 1 Did NOT Exercise

This section exists because the original draft of this report over-claimed. The PRD is mostly about verification, watcher, exploration, and autonomy. Trial 1 did not test most of that.

### 2.1 Verification — ❌ not exercised

`emit_claim()` was never called in Trial 1. `workspace/research/verification.log` does not exist. The 6 "verified" results in `deps.json` came from `scripts/backfill_mnist_plan.py`, which calls `add_established(id, label, depends_on)` directly. `add_established` creates a node with `status: "verified"` as a side-effect of being called — there is no actual verification step. No Sonnet verifier ran, no cross-verifier ran, no CAS tool ran on R1–R6. The numeric metrics (98.16%, 98.59%, 98.83%, 99.44%, 89.06%, 89.15%) were observed from training runs — they are *empirical facts* recorded in `runs/stage{N}/seed{K}/metrics.json` — but they are *not* verified claims in the PRD sense.

**Implication.** The PRD's Huang-et-al-motivated design (isolated verifier, one-line context, async loop, cross-verification at milestones) has zero real-world evidence either way from Trial 1. Claims that the loop "held up in real work" are unsupported. A physics or derivation-heavy trial is needed to exercise the actual verification path.

### 2.2 Cross-verification — ❌ not exercised

No second independent re-derivation was attempted on R4 (MNIST saturation), R5 (EMNIST baseline), or R6 (EMA result). These are the exact kind of milestone results the PRD §Cross-verification section is designed to catch.

### 2.3 Watcher — ❌ not exercised

`/watcher` skill exists but was not run. The human was steering the agent via chat, not working on a whiteboard or annotating a PDF. No human workspace was captured and read by a watching agent. The PRD's "whoever is not doing the work is checking the work" principle was not bidirectional in this trial.

### 2.4 Invalidation propagation — ❌ not exercised

No assumption was ever invalidated. The recursive graph walk for flagging downstream results untouched. The PRD's JSON-graph design is untested against its primary use case.

### 2.5 Exploration mode — ❌ not exercised

The MNIST plan was pre-written in `PLAN.md` before the trial started. The agent went straight into formalization. The PRD's exploration → crystallization → formalization transition was skipped.

### 2.6 Autonomous operation — ❌ not exercised end-to-end

The agent had an explicit human-written plan and checked in frequently. The `/autonomous` skill's loop (work → verify → cross-verify → update state → repeat) was not run unattended.

**Bottom line:** Trial 1 exercised ~30% of the PRD's surface area. What it did exercise (plan, state, graph, displays, an integration) mostly worked. The other 70% is still a hypothesis. The next trial should deliberately target the unexercised paths — a physics derivation is a natural fit for verification + watcher + exploration → formalization.

---

## 3. Findings by Theme

Each finding maps to one of Quinn's feedback points. Each has a recommendation pointer in §6.

### 3.1 Display tab state flicker

**Symptom.** When displays reload, the active tab sometimes jumps back to the first display (usually `Main`/`index.html`) instead of staying put.

**Root cause (✅ read from code):** In `core/default-display.html:228–232`:

```js
let active = files.find(f => f.stem === activeStem);
if (!active) active = files.find(f => f.name === 'index.html') || files[0];
activeStem = active.stem;   // ← bug: overwrites the user's choice
```

When the active file is briefly absent from the pool response — e.g. during an atomic write (`displays/_base.py:atomic_write_text` writes to `.tmp` and renames, and on Windows the rename has a transient window where the file is gone) — `activeStem` doesn't match any current file, falls back to `index.html`, and **the fallback value is written back into `activeStem`**. When the active file reappears on the next poll, `activeStem` has already been corrupted, and the selection is lost permanently.

Server side (`server/index.ts:89–155`) is already stable: it sorts by `firstSeen` (not mtime or birthtime), pins `index.html` and `research.html` to the front, and maintains a `poolFirstSeen` Map that survives rewrites. The bug is purely on the frontend.

**Also note.** `showEmpty()` is called when `files.length === 0` (line 215–218) — it doesn't reset `activeStem` (good), but it does `return` before updating `lastKey`, so the next non-empty poll will always trigger a fresh tab re-evaluation.

**Fix.** Decouple "which tab to render" from "which tab the user wants." Keep `activeStem` sticky on the user's last explicit choice; compute `renderStem` on each poll as "activeStem if present, else index.html fallback." Only overwrite `activeStem` on user click or on a programmatic `focus_display()` request. Drop the line `activeStem = active.stem;` or gate it behind a condition.

### 3.2 Stale display accumulation

**Symptom.** Trial 1 ended with 12 files in `workspace/output/` including misplaced `progress_stage6.py` (a Python *source* file in the output dir — shouldn't be there at all), two history-dashboard tabs (`mnist-history.html`, `emnist-history.html`) that duplicate each other in structure, and two stage-6 tabs (`stage6.html`, `stage6_push.html`) that look like iteration residue.

**Why this happened.**
- `displays/_base.py` already has `clear_display(name)` and `clear()` functions — the primitives exist.
- The agent has no convention about *when* to clean up: no hook, no reminder in CLAUDE.md, no auto-GC.
- The agent has no awareness of what tabs the human is currently looking at (see 3.3), so it can't safely delete.
- Misplaced files like `progress_stage6.py` are a different class: not iteration residue, just confusion about where code lives vs. where output lives.

**Fix.**
- Add `cleanup_displays(keep=[...])` alongside `clear`/`clear_display`, with a convention to call it at end-of-session or when a workflow phase completes.
- Document the output-dir discipline in CLAUDE.md ("no source files in `workspace/output/` — that directory is rendered tabs only").
- Longer-term: tie cleanup to display-awareness (3.3) — don't delete tabs the user has recently viewed.

### 3.3 Agent is blind to the display panel

**Symptom.** The agent can produce displays but cannot see them. Quinn: *"the agent needs awareness of what the person is seeing on the display panel at any given time."*

**Current state (✅ read from code):**

What the agent *can* read today:
- File list in `workspace/output/` (knows what tabs exist)
- `workspace/output/.focus` — this is the **last programmatic focus request**, written by `focus_display()` in Python. The server piggybacks it on `/api/output-pool`. So the agent can see what *it itself* last asked for.

What the agent *cannot* read today:
- Which tab the user is actually viewing (if it differs from the last programmatic focus — which it will, as soon as the user clicks)
- How long the user has been on the current tab
- Whether the rendered content is actually visible (e.g., if an embedded iframe like Optuna Dashboard is empty)
- What the user clicked, scrolled, or dismissed

**Why this matters.** Without a user-focus channel, cleanup is guessing, prioritization is guessing, and "I notice you're on the stage-5 curve — here's the stage-6 comparison" isn't expressible.

**Fix.**
- Add a user-focus channel: frontend POSTs the active tab to `/api/display-state` on every click + tab-switch event; server maintains separate `userFocus` (actual current tab) and `.focus` (last programmatic request) state.
- Add an `active_display()` Python helper that reads `userFocus`; document it in `tools.md`.
- Longer-term, if needed: periodic screenshot of the display iframe written to `workspace/snapshots/display-latest.png`. Start with the lighter state endpoint; add screenshots only if the endpoint isn't enough.

### 3.4 Embed vs. external — no paradigm

**Symptom.** Trial 1 embedded Optuna Dashboard (iframe in display tab) but Quinn disliked the result: *"I embedded optuna, but am not a fan of how it looks so might need to integrate weights and biases instead even though we can't embed that."* Four Optuna scripts + one helper module were needed to make the embed behave (port management, EMA-vs-raw curve reconciliation, panel ID cleanup, disk-metrics backfill). The 1400px iframe min-width clamp is a visible scar.

**Missing paradigm.** There is no Triptych rule for when to embed vs. link out. The heuristic is clear once written down:

| Condition | Default |
|---|---|
| Tool renders well at panel size, has a clean iframe API, same-origin or permissive CORS | Embed |
| Tool is the de-facto standard, users already have accounts, team-collaborative, or full-screen-assuming | External (link + API summary panel) |
| Tool is desktop-only, has complex auth, or its UX fights the panel | External |
| User explicitly prefers one | User wins |

Weights & Biases is the external-done-right target: it's the dominant experiment tracker (W&B Weave is the standard LLM-observability tool as of 2026 — see ecosystem-scan.md §H), researchers already have accounts, iframing it fights auth and wastes its UX. The right move: launch W&B in a browser tab, log the run URL in research state, render a compact in-Triptych summary panel (best metric, loss-curve thumbnail, last-update timestamp) polled from the W&B API.

**Fix.** Build `core/integrations/` with two base classes: `EmbeddedTool` (owns subprocess, exposes iframe) and `ExternalTool` (owns nothing, exposes auth + API-driven summary panel). Migrate Optuna to `EmbeddedTool` as the reference. Ship W&B as the first `ExternalTool`. Research state gets a standard `integrations:` block listing tools-in-use with their run URLs and summary-panel IDs.

### 3.5 No display-design workflow skill

**Symptom.** Quinn: *"The agent needs a way, maybe a skill, for the full workflow of designing displays and testing them."*

**Observation.** `/triptych-displays` exists as a skill (catalog) and the agent can write to `displays/`. But the *workflow* — draft → iterate → decide named-vs-anonymous → register in tools.md — isn't codified. The residue in `workspace/output/` (misplaced `progress_stage6.py`, two stage-6 tabs) is evidence the agent improvises this workflow and leaves drift.

**Fix.** New skill `/display-design-workflow` with checkpointed steps:
1. Scope (what data, update cadence, live vs. one-shot?)
2. Sketch with dummy data, render, iterate on layout
3. Wire real data
4. Test under update pressure (flicker? state survives reload?)
5. Decide named vs. anonymous; register in `tools.md` if named
6. Clean up iteration artifacts

Parallel skill `/integration-design` for the embed-vs-external decision in 3.4.

### 3.6 Onboarding records a goal but doesn't act on it

**Symptom.** Quinn: *"At the beginning, you need an onboarding where you're specifying a goal, and then it can start building anything it needs in the background or pulling in any relevant skills."*

**Current state (✅ read from `.claude/skills/first-boot/SKILL.md`).** `/first-boot` asks domain (Math/Physics, CS/ML, Research/Writing, Other) and experience level, recommends MCP servers and settings, writes `CLAUDE.local.md`. It does NOT:

- Ask what the user is trying to *do* this session (goal-level, not domain-level)
- Call `init_research(goal)` to seed the research state
- Install recommended MCPs (only suggests)
- Spawn any background agent or watcher
- Link stated domain to a default addon pack

**Fix.** Extend `/first-boot` into a two-stage flow:
- Stage 1 (first boot only): domain, experience, MCP install offer — as today.
- Stage 2 (every session or on demand): goal elicitation → classify exploration vs. formalization → seed research state → prime relevant skills → background prep (pre-fetch data, scaffold workspace) → human review → start.

This is closer to Manus's Planner → Execution handoff than the current informational onboarding. It matches the PRD's "good research mentor" framing at the exploration → formalization boundary (PRD §Exploration and Formalization).

### 3.7 No hooks for skill auto-loading

**Symptom.** Quinn: *"I think sometimes the agent doesn't load skills that can help it, so maybe we could have a hook where it looks for some skills and uses those more."*

**Observation.** CLAUDE.md is a guideline the agent may or may not follow; hooks run in the harness and can't be forgotten. The emerging ecosystem convention (see ecosystem-scan.md §E) is:
- `.claude/skills/skill-rules.json` maps intent patterns → skills
- `UserPromptSubmit` hook reads the prompt, matches rules, prepends "use skill X" before Claude sees it
- Claude can't forget because it never had to remember

**Fix.** Ship a starter `.claude/skills/skill-rules.json` with ≤10 rules covering the most common Triptych workflows (train/HPO → triptych-displays + optuna; derive/prove/verify → verifier; circuit/schematic → circuitjs workspace; paper/arxiv → literature-review; design display → display-design-workflow). Add a `SessionStart` hook that injects the list of installed skills as a reminder, and a `PreToolUse` hook that catches writes to `displays/` without having consulted `/triptych-displays` this session. Keep hooks fast — aim for sub-second on `UserPromptSubmit` to avoid perceptible latency on every prompt.

### 3.8 Skill ecosystem pull-in

Quinn: *"Should also think about what skills we want to pull in — maybe point it at trusted repo's like awesome claude code skills or similar. Some skills we should ship it with, especially visualization related stuff."*

See `ecosystem-scan.md` for the full named catalogue. High-signal sources (in priority order):

1. **`anthropics/skills`** — Apache 2.0, official, ~17 top-level skill dirs
2. **`obra/superpowers`** + `obra/superpowers-marketplace` — Jesse Vincent's methodology pack (TDD, four-phase debugging, subagent code review, "TDD for skills"). Distributed via `claude.com/plugins` as an official partner plugin.
3. **`K-Dense-AI/claude-scientific-skills`** — 170+ scientific skills across bio/chem/physics/engineering. Evaluate case-by-case; quality bar may vary.
4. **`VoltAgent/awesome-agent-skills`** + **`VoltAgent/awesome-claude-code-subagents`** — cross-platform (agentskills.io format), good for discovery.
5. **`hesreallyhim/awesome-claude-code`** — canonical but CC BY-NC-ND 4.0, so discovery only (not redistributable).

**Agent Skills standard**: as of Anthropic's December 2025 announcement, the skill format is documented at `agentskills.io` and adopted by OpenAI for Codex CLI. Triptych skills should conform — this is a small engineering cost for cross-platform portability and future-proofing (including against users migrating to OpenCode per 3.11).

Visualization starter skills to evaluate for bundling:
- CircuitJS workspace addon (3.9)
- CadQuery display addon (3.9)
- marimo integration (ecosystem-scan.md §K)
- Mermaid + Excalidraw workspaces

### 3.9 Engineering-specific additions — circuit CAD, and beyond

Quinn: *"One thing we should definitely add is some more engineering specific stuff — I saw a really cool engineering visualization thing, similar to CAD but for circuits."*

**Falstad CircuitJS1** is the clear first target. Public, active, iframe-embeddable:
- `pfalstad/circuitjs1` (upstream)
- `sharpie7/circuitjs1` (active fork, most recent maintenance)
- `MaxPastushkov/KiCad_to_Falstad` (KiCad schematic importer)
- Documented JavaScript postMessage interface (same-origin required)

**Implementation shape.** Drop CircuitJS into `workspaces/circuitjs.html`, wire the postMessage bridge so the agent can read circuit state and write components. Companion display addon renders analysis output (Bode plots, transient response) from CircuitJS data.

**Adjacent tools** (all in ecosystem-scan.md §G):
- **CadQuery + Yet Another CAD Viewer** — Python parametric CAD with browser viewer (STL/STEP/AMF/3MF). Strong fit for mechanical engineering.
- **OpenSCAD.js** — slower pure-web alternative to CadQuery.
- **Three.js** — general 3D; `mysimulator.uk` has hundreds of physics/science sims as a reference (verify latest count via ecosystem-scan.md).
- **Mermaid**, **Excalidraw** — systems diagrams / hand sketches.

**General principle.** Each STEM discipline has one or two canonical embeddable tools. Triptych's addon model already accommodates this. What's missing is curated **starter packs**: physics = Three.js + SymPy + desmos-mcp; circuits = CircuitJS + ngspice bridge; mechanical = CadQuery; ML = Optuna (embed) + W&B (external). `/first-boot` should install the starter pack matching the user's stated domain.

### 3.10 Dual-agent / dashboard-manager

Quinn: *"Might want to look into having dual agents sometimes, one to manage dashboard."*

**Why.** During Trial 1 the agent interleaved ML work with display work. Every new panel or kanban rewire fragmented the main train of thought. The residue (three stage-6-related files, two history tabs, misplaced `progress_stage6.py`) is evidence.

**Precedent.** Anthropic's Agent Teams pattern (shipped as a Claude Code preview — see ecosystem-scan.md §F for current status) is the nearest-fit. Team Lead + Teammates in independent contexts, coordinated through a shared task list with file locking.

**Shape for Triptych.**
- **Main agent** — research, claim emission, state updates.
- **Dashboard agent (new)** — owns `workspace/output/`, handles display design/polish/cleanup.
- **Verifier agent (existing)** — drains claim queue.

Main writes *intent* ("training-curve display, EMA vs. raw, stage 5–6, 30s refresh"); dashboard agent does addon selection, layout, data wiring, cleanup. Main doesn't block.

**Cost guardrail.** Orchestrator-worker architectures have a well-documented context-blowup failure mode (one frequently-cited case reported workflows costing cents in testing ballooning to tens of thousands monthly in production — see ecosystem-scan.md for citation). The fix is aggressive context isolation: dashboard agent receives data + intent only, not the research narrative. Matches the verifier's isolation principle.

**Gate.** Default single-agent. Enable via `triptych dashboard-agent on` flag, or auto-enable when display work exceeds a threshold.

### 3.11 OpenCode as an option

Quinn: *"Lastly, might want to consider making opencode an option?"*

**Summary.** OpenCode is a CLI agent with broad LLM-provider support (see ecosystem-scan.md §J for current star count and spec). Same SKILL.md format via `agentskills.io`. Philosophy: multi-model routing vs. Claude-only. Triptych's server hosts the terminal process via PTY; swapping Claude Code for OpenCode is a process substitution, not a rearchitecture.

**Trade-off.** Broadens reach (users who can't or won't use Claude directly); costs ongoing (two agents to test, skill-format parity, model-specific quality differences on `/verifier`).

**Fix.** Document PTY substitution in `docs/internal/`, test the core skill set under both, ship a `triptych --agent opencode` flag. Do not promise `/verifier` parity — explicitly flag that verification quality depends on model class.

### 3.12 Use-case catalogue with industry-standard integrations

Quinn: *"We should also maybe make a list of use cases, and then try to integrate industry standard technologies for those use cases... is a good chance to steer people towards good workflows."*

First-pass catalogue (to be expanded in `docs/internal/use-cases.md` once drafted):

| Use case | Recommended integration | Default addons | Steering |
|---|---|---|---|
| ML experiment tracking | W&B (external) + Optuna (embed, HPO) | `wandb`, `optuna` displays | Log to W&B, pin URL in research state, summary panel in display |
| Physics derivation | SymPy (MCP), desmos-mcp, manim | `latex`, `research`, `threejs` | Exploration → formalization → `/verifier` |
| Circuit design | CircuitJS (embed) + ngspice | `circuitjs` workspace, `bode-plot` display | Draft → simulate → display |
| Mechanical CAD | CadQuery + YACV (embed) | `cadquery` display | Script → render → iterate |
| Data analysis | marimo (embed) + Plotly | `marimo` workspace, `plotly` display | Reactive DAG in marimo, summary in Triptych |
| Literature review | arxiv-latex-mcp, HF MCP, firecrawl | `research` (literature mode) | `/literature-review` skill |
| Math research | sympy-mcp, Wolfram (future: Lean 4) | `latex`, `research`, `derivation` | Exploration → formalization → `/verifier` |
| Biology / lab notebook | Deferred — under-served (see ecosystem-scan.md) | Extension opportunity | TBD |

Each entry becomes a micro-document with the recommended workflow, why these tools, and the default skill invocations. This is how Triptych *steers* — absence of opinion creates decision fatigue.

---

## 4. Alignment with the PRD Vision

Report card by PRD capability (PRD §The Vision):

| PRD capability | Status | Evidence |
|---|---|---|
| 1. Workspace where human thinks | ✅ Solid | File browser, PDF viewer, editors in daily use |
| 2. Display where AI shows work | ⚠️ Works; awareness + cleanup gaps | 7 useful + 5 residue/misplaced = 12 files in `output/` |
| 3. Terminal where AI operates | ✅ Solid | Session spawn/kill fixed in `b8eccf5` |
| 4. Verification system | 🔍 Untested in Trial 1 | No claim flow ran; backfill path only |
| 5. Proactive watcher | 🔍 Untested in Trial 1 | `/watcher` skill exists; not invoked |
| 6. Research state | ✅ Strong; Trial 1 extended it | Plan kanban, deps.json, 13 nodes |

**The PRD's invisibility constraint** (§Core Principles: *"the researcher should be able to forget the system is running"*) was **partially violated** in two observable ways during Trial 1:
- Tab flicker made the system visible to the user (3.1).
- Stale display accumulation made the system visible to the user (3.2).

There is a **third, much larger invisibility violation** that Trial 1 masks rather than reveals: if the verification loop isn't running but the graph says "verified," the system is *invisibly wrong* — the human can't detect that verification didn't happen. This is more dangerous than a visible flicker. The PRD's "the AI must not make mistakes, whether or not the human is watching" applies, and the backfill path around `add_established()` is an escape hatch that bypasses the principle. Either (a) `add_established()` should refuse to mark `status: verified` without a corresponding verification log entry, or (b) the display should distinguish "empirically observed" from "formally verified."

**The PRD's Core vs. Addons boundary** mostly held: the three new displays and helpers are addons; research/verify extensions are core. One edge case: the Plan schema extension (seven → eight fields) crosses the boundary silently. See §7 open question.

**PRD gaps that Trial 1 didn't touch**, per §2: cross-verification, invalidation propagation, watcher, exploration mode, end-to-end autonomous. The next trial should deliberately target these.

---

## 5. Ecosystem Scan — positioning

Full named catalogue is in `ecosystem-scan.md`. Key positioning takeaways for Triptych:

1. **Three-panel layout is not novel.** Google NotebookLM (Sources / Chat / Studio) and Microsoft Copilot Notebooks both ship three-column workspaces as of 2026. Triptych's form factor is mainstream. *Triptych's distinguishing axis is verification, not layout.* All external comms should lead with the verification thesis.
2. **Closest architectural sibling is Manus** (Planner / Execution / Verification agents, separate contexts). Difference: Manus is cloud-VM-per-session, Triptych is local + filesystem-first.
3. **marimo is the most aligned visualization tool** — reactive DAG, pure-Python, WASM-embeddable, explicit AI-native positioning. If Triptych ever wants a live-code display richer than Plotly HTML, marimo is the obvious bet.
4. **Agent Skills became an open standard in late 2025** (agentskills.io). Cross-platform portability for ~free if Triptych conforms strictly.
5. **The verified-research-environment niche is sparse.** No other project combines (a) local three-panel UI, (b) formal-verification feedback loop, (c) filesystem-as-comm-channel. Under-served STEM domains (physics derivation, lab notebooks, formal verification, live instruments) are where Triptych can land distinctive skills.
6. **Hooks are the standard enforcement layer** in 2026 Claude Code setups. Triptych's absence of hooks is a gap, not a stylistic choice.
7. **Orchestrator context blowup is a real production failure mode** — if Triptych ships a dashboard-manager agent (3.10), context isolation must be ruthless.

---

## 6. Recommendations, Ordered

### Near-term (1–2 weeks, surface fixes)

1. **Fix the tab-state `activeStem` corruption bug** (3.1). Decouple user-intent from rendered-tab: keep `activeStem` sticky, compute `renderStem` per-poll, only update `activeStem` on user click or `focus_display()`. Touch: `core/default-display.html:228–232`.
2. **Add a user-focus channel** (3.3). New `POST /api/display-state` endpoint; frontend reports active tab on click/switch; server maintains `userFocus` separate from `.focus`. Add `active_display()` Python helper reading via the pool endpoint. Document in `tools.md`.
3. **Add `cleanup_displays(keep=[...])` + output-dir discipline note** (3.2). Alongside existing `clear_display(name)` and `clear()` in `displays/_base.py`. Add CLAUDE.md note: "no source files in `workspace/output/`."
4. **Decide on the verification/backfill issue** (§4, §2.1). Either make `add_established()` refuse `status: verified` without a verification log entry, or rename the status to reflect what it actually means (e.g., `status: recorded` for backfilled results). The current behavior is a silent invisibility violation.
5. **Auto-start verifier loop when claims are emitted.** Mechanism: on `emit_claim()`, `core/verify.py` writes a sentinel to `workspace/research/verifier-wanted`. A `UserPromptSubmit` hook (or a polling process in `scripts/`) checks the sentinel each turn and, if present and no loop is running, instructs the main agent to start `/loop 60s /verifier`. A Python function cannot spawn a Claude loop directly; the hook layer is the right place.

### Short-term (2–4 weeks, paradigm articulation)

6. **Build `core/integrations/` with `EmbeddedTool` and `ExternalTool`** (3.4). Migrate Optuna to `EmbeddedTool`. Ship W&B as the reference `ExternalTool` (auth + API summary panel, pins run URL in research state).
7. **New skill `/display-design-workflow`** (3.5). Six checkpointed steps.
8. **New skill `/integration-design`** (3.4). Embed-vs-external decision, under `core/integrations/`.
9. **Goal-driven onboarding** (3.6). Extend `/first-boot` with stage-2 goal elicitation → research state seeding → skill priming → background prep.
10. **Hooks for skill auto-loading** (3.7). `.claude/skills/skill-rules.json` + `UserPromptSubmit` hook. Start with ≤10 rules; add `SessionStart` hook for skill inventory; add `PreToolUse` hook for `displays/` writes.
11. **Resolve the PRD schema extension** (§1 schema note). Either update PRD text to say "seven or more fields, Plan is the first canonical extension," or move Plan out of core into a domain addon. Don't leave the code and the PRD in silent disagreement.

### Medium-term (1–2 months, ecosystem integration)

12. **Use-case catalogue** (`docs/internal/use-cases.md`) (3.12). Target 8–10 entries with default addon packs and recommended integrations.
13. **Dashboard-manager agent (gated)** (3.10). Agent Teams pattern with context isolation. Ship behind a flag.
14. **Engineering starter pack: circuits** (3.9). CircuitJS workspace + postMessage bridge + Bode-plot display + ngspice integration. Reference implementation for an engineering discipline.
15. **Skill ecosystem pull-in** (3.8). Bundle `obra/superpowers` methodology skills. Evaluate `K-Dense-AI/claude-scientific-skills` against Triptych's quality bar and selectively pull. Align all Triptych skills strictly to `agentskills.io` format.

### Longer-term (experimental, not committed)

16. **marimo-backed display addon** (ecosystem-scan.md §K). Prototype; see if reactive DAG unlocks live-code workflows.
17. **End-to-end physics trial** — exercise verification, cross-verification, watcher, invalidation, exploration mode. Measure what Trial 1 couldn't.
18. **Display-iframe screenshot path** (3.3). Only build if the state endpoint (Rec #2) isn't enough.
19. **OpenCode compatibility** (3.11). Process substitution, no verifier-parity promise.

---

## 7. Open Questions

- **Schema extension**: PRD says seven fields; mnist trial silently added Plan as an eighth. Core addition or domain addon? (Touches Rec #11.)
- **Verification integrity**: should `add_established()` refuse to mark `verified` without a log entry? (Touches Rec #4.)
- **Auto-start verifier mechanism**: hook vs. polling script vs. server-side watcher? (Touches Rec #5.)
- **Dashboard-manager default**: gate-by-flag or auto-enable by heuristic? (Touches Rec #13.)
- **Display-awareness depth**: is the state endpoint enough, or do we need screenshots? (Touches Rec #2, #18.)
- **Starter-pack scope**: 80% coverage per discipline is ideal; what does that look like for physics, circuits, ML, biology? (Touches Rec #14, #15, `docs/internal/use-cases.md`.)
- **Cross-verification budget**: not every milestone warrants re-derivation. What fraction does? Physics trial should begin answering.
- **Invisibility instrumentation**: can we measure PRD-constraint violations (tab flicker events, stale-tab count, claim-without-verifier count) automatically?
- **W&B vs. MLflow vs. Neptune** as the default external ML tracker. Strong opinions among users; need an explicit pick.

---

## 8. Where to Look Next Session

**Start here:**
- `docs/internal/PRD.md` — north star, esp. §Verification System and §Exploration and Formalization
- `docs/internal/trial-1-report.md` — this document
- `docs/internal/ecosystem-scan.md` — named catalogue of Claude Code projects / skills / tools to pull in (generated in the same planning cycle as this report)

**Files Rec #1 will touch:**
- `core/default-display.html:228–232` (the bug)
- `server/index.ts:89–155` (pool endpoint — reference only, already correct)

**Files Rec #2 will touch:**
- `server/index.ts` (new endpoint)
- `core/default-display.html` (active-tab POST)
- `displays/_base.py` (new `active_display()` helper)
- `tools.md` (document the new API)

**Files Rec #4 will touch:**
- `core/research.py` (`add_established()` behavior change or status rename)
- `docs/internal/PRD.md` (language update if status semantics change)

**Trial 1 artifacts (for reference, uncommitted — back them up before touching):**
- `C:/Users/aquin/mnist/` — full trial working tree
- Key files: `core/research.py` (+157), `core/verify.py` (+36), `core/optuna_helper.py` (new), `displays/optuna.py`, `displays/architecture.py`, `displays/_graph.py`, `displays/research.py` (rewrite), 7 scripts in `scripts/`

---

## Appendix A: Evidence Trail

| Claim | How verified |
|---|---|
| 6 "verified" results came from backfill, not verifier | Read `scripts/backfill_mnist_plan.py`; no `workspace/research/verification.log` exists in mnist |
| Tab-state bug is in `activeStem = active.stem` | Read `core/default-display.html:228–232` with surrounding context |
| Server sorts by `firstSeen` not mtime | Read `server/index.ts:133–144` |
| 12 output files, incl. misplaced `progress_stage6.py` | `ls C:/Users/aquin/mnist/workspace/output/` |
| Dependency graph is a chain, not DAG | Read `deps.json`: 11 edges, linear topology |
| Schema extension to 8 fields | `core/research.py:10` comment in mnist |
| PRD-stated field count | `docs/internal/PRD.md` §Research State |
| `clear_display` and `clear` exist | `displays/_base.py` |
| `/first-boot` asks domain, not goal | `.claude/skills/first-boot/SKILL.md` |

## Appendix B: Quantitative Metrics from Trial 1 (empirical, not formally verified — see §2.1)

| Stage | Dataset | Recipe | Test accuracy |
|---|---|---|---|
| 1 | MNIST | SGD baseline MLP | 98.16% |
| 2 | MNIST | + AdamW + cosine LR + label smoothing | 98.59% |
| 3 | MNIST | + LayerNorm + GELU + dropout | 98.83% |
| 4a | MNIST | + Elastic distortion (σ=5, α=36) | **99.44%** (saturated) |
| 4a | EMNIST-B | Same recipe, transfer | 89.06% |
| 5 | EMNIST-B | + EMA (d=0.9995, 3 seeds × 100ep) | **89.15% ± 0.05** (EMA) vs 89.07% ± 0.21 (raw) — σ cut ~4× |
| 6 | EMNIST-B | + Affine aug | PLANNED (not executed) |

*Report compiled 2026-04-21, revised after independent review same day. Ecosystem scan in companion doc. Next review: after the physics trial.*
