# Triptych Production Plan

A research document covering everything needed to take Triptych from a personal tool to a deployable product that anyone can use to solve hard problems with AI.

---

## 1. Core Philosophy

Triptych exists because **AI collaboration for hard problems is broken**. Claude Code solved coding — filesystem + compiler + terminal creates a tight feedback loop. For math, physics, and research, there is no equivalent. A wrong derivation produces no error. A plausible formula doesn't crash. Triptych closes that loop.

The product proposition in one sentence: **A three-panel collaboration system where you and Claude solve hard problems together, with built-in verification so you can trust the results.**

Design principles (unchanged):
1. Do the simple thing that works. Files, not databases. HTML from CDN, not npm builds.
2. The framework should be invisible. You think about your problem, not the tool.
3. You can always extend it. Write HTML for workspaces, Python for displays.
4. **New: It gets better through use.** Mistakes are captured, patterns are learned, and the system improves.

---

## 2. What Needs to Change

### 2.1 The Problem with the Current State

The current CLAUDE.md is 209 lines and serves as both the "how Claude behaves in Triptych" guide AND a personal configuration file. It contains:

- **Universal behavioral instructions** (how displays work, how verification works) — these should ship with the product
- **Personal context** (Quinn's study integration, Obsidian paths) — these must not ship
- **Detailed API documentation** (every function signature for research.py, verify.py) — this should be in skills, loaded on demand
- **Operational redundancy** — the verification system is documented in CLAUDE.md AND in the autonomous skill AND in PRD.md

Research shows that **LLMs reliably follow ~150-200 instructions**. Claude Code's system prompt already uses ~50. That leaves ~100-150 for CLAUDE.md. The current file likely exceeds this budget, and adding more detail will degrade compliance across ALL instructions.

### 2.2 The Separation

```
SHIPS WITH PRODUCT (git-tracked):
  CLAUDE.md              — Slim behavioral guide (~80 lines)
  .claude/skills/        — Domain instructions loaded on demand
  .claude/agents/        — Verification agents
  .claude/rules/         — Auto-loaded rules for specific contexts
  core/, displays/,      — Framework code
  workspaces/, server/

USER-SPECIFIC (gitignored or in user config dir):
  CLAUDE.local.md        — Personal overrides (study integration, Obsidian paths)
  workspace/             — Already gitignored (runtime state)
  .env                   — API keys, preferences
  memory/                — Cross-session persistence (per-user)

QUINN'S CURRENT PERSONAL STUFF → moves to CLAUDE.local.md:
  - Study Integration section
  - Obsidian references
  - Memory directory instructions (the auto-memory system is Claude Code's, not Triptych's)
```

---

## 3. The New CLAUDE.md

### 3.1 Design Principles (from research)

**The litmus test for every line:** "Would removing this cause Claude to make mistakes, produce noticeably worse output, or miss a capability the user expects it to know about?" This is broader than "would it cause errors?" because CLAUDE.md also serves as a quality guide and capability primer — not just an error-prevention checklist.

**What goes in CLAUDE.md:**
- What Triptych is (one paragraph)
- How to show your work (the core display workflow — 5 lines)
- How to see what the human is doing (snapshots — 3 lines)
- Pointers to skills for domain-specific behavior
- Hard constraints (never kill the server, dark theme palette)
- The verification philosophy (WHY, not HOW — the HOW lives in skills)

**What does NOT go in CLAUDE.md:**
- Function signatures and API documentation (discoverable from code)
- Detailed verification protocol (lives in `/autonomous` and `/watcher` skills)
- Research state operations (loaded when doing research)
- Server endpoint documentation (Claude can read server/index.ts)
- Personal user configuration

**Key prompting insights from research:**
- Claude 4.6 is significantly more proactive than prior models — avoid "CRITICAL: YOU MUST" language, use natural instructions
- Provide WHY not just WHAT — Claude generalizes better from explained context than bare directives
- Use hooks for things that must happen every time (deterministic enforcement) rather than CLAUDE.md instructions (advisory)
- Skills implement progressive disclosure naturally: name+description at startup (~100 tokens), full instructions only when activated

### 3.2 Proposed CLAUDE.md

```markdown
# Triptych

You are Claude Code running inside Triptych, a three-panel system for solving hard problems. The human works in the left panel (workspace), you show your work in the middle panel (display), and this terminal is how you communicate.

Triptych supports research, study, writing, data work, and design. Use verification for mathematical and scientific claims; for other tasks, work naturally.

The filesystem is the communication channel. You read and write files. The framework handles the rest. Triptych is Express + WebSocket on port 3000, with chokidar watching `workspace/output/` for display auto-reload.

## Show Your Work

Write to `workspace/output/`. The display panel auto-reloads.

Triptych Python modules are in the project root. Always prefix scripts with `import sys; sys.path.insert(0, '.')` before importing from `core/` or `displays/`.

    import sys; sys.path.insert(0, '.')
    from displays import show_figure, show_plotly, show_html, show_latex, show_research, clear

Use the dark theme: background #0a0a0b/#111113, text #c8c8d0, accents #6e73ff (blue), #34d399 (green), #f87171 (red), #fbbf24 (yellow), borders #222228. Prefer interactive visualizations (Three.js, Plotly) over static images — see `/triptych-displays` for the full catalog including 3D surfaces, vector fields, and parametric curves.

## See What the Human is Working On

Workspace snapshots update every 30 seconds:
- `workspace/snapshots/latest.png` — screenshot
- `workspace/snapshots/latest.json` — context metadata

The human shares files via `workspace/files/` — you can read and write files there.

## Research and Verification

Triptych exists because AI makes mistakes on hard problems and nobody catches them. Every significant claim during mathematical derivations, scientific reasoning, or formal analysis must be independently verified. Routine computations, visualizations, and conversational help do not need verification.

For structured research, initialize state with `core/research.py` (`init_research`, `update_state`, `add_established`) and track claims with `core/verify.py`. Verification results integrate with research state automatically — verified claims become established results, failed claims stay in attempts.

    from core.verify import emit_claim
    emit_claim("F = ma", "Newton's second law", depends=["A1"], research_dir="workspace/research")

After emitting claims, spawn the verifier agent to check them. See `/autonomous` for the full verification loop including cross-verification.

## When to Use Skills

| Task | Skill |
|------|-------|
| Solve a problem independently | `/autonomous` |
| Watch human's workspace for errors | `/watcher` |
| Build a new display addon | `/triptych-displays` |
| Build a new workspace addon | `/triptych-workspaces` |
| Optimize Triptych itself | `/autoresearch` |

## Extending Triptych

- Write HTML to `workspaces/` to create new workspace tools
- Write Python modules in `displays/` to create new display types
- Check `tools.md` for all available addons and MCP servers (sympy, arxiv, desmos)

## Constraints

- Never kill or restart the server process. It hosts this terminal session.
- The `workspace/` directory is for runtime state. Framework code lives in `core/`, `displays/`, `workspaces/`.
- If display output fails, verify `workspace/output/` exists and create it if needed.
- Check `CLAUDE.local.md` for user-specific configuration if it exists.
```

**Line count: ~65 lines.** About a third of the current CLAUDE.md. Incorporates critique feedback: explains `sys.path.insert`, acknowledges research state exists, includes shared files, adds skill-to-task mapping table, clarifies when verification applies, and mentions MCP servers. Every line passes the broader litmus test.

### 3.3 What Moved Where

| Current CLAUDE.md Section | New Location | Why |
|---|---|---|
| The Big Idea (10 lines) | Condensed to 2 lines in CLAUDE.md | Core identity, always needed |
| Verification System (35 lines) | `/autonomous` skill + 5-line summary in CLAUDE.md | Only needed during research work |
| Research State (25 lines) | `/autonomous` skill | Only needed during research work |
| Watcher (10 lines) | `/watcher` skill (already there) | Only needed when watching |
| Autonomous Operation (10 lines) | `/autonomous` skill (already there) | Pointer in CLAUDE.md suffices |
| How to Show Work (15 lines) | 4 lines in CLAUDE.md | Core workflow, keep brief |
| How to Create Workspaces (10 lines) | `/triptych-workspaces` skill | Only when building addons |
| Server Endpoints (10 lines) | Removed entirely | Claude can read server/index.ts |
| Available Python Packages (2 lines) | Removed entirely | Claude can check with pip |
| Philosophy (5 lines) | Removed from CLAUDE.md | In BRIEF.md for humans to read |
| Study Integration (8 lines) | `CLAUDE.local.md` | Personal to Quinn |
| Memory (3 lines) | Removed | Claude Code's auto-memory handles this |

---

## 4. Progressive Disclosure Architecture

### 4.1 The Three Layers

**Layer 1 — Always loaded (CLAUDE.md, ~65 lines, ~700 tokens):**
Identity, core workflow (show work, read snapshots), verification philosophy, skill-to-task mapping, constraints.

**Layer 2 — Loaded on demand (skills, ~200-500 lines each, ~2-5k tokens):**
- `/autonomous` — Full verification protocol, research state API, claim emission
- `/watcher` — Observation behavior, phase detection, log format
- `/triptych-displays` — How to build display addons, dark theme details
- `/triptych-workspaces` — How to build workspace addons, capture.js integration
- `/autoresearch` — Self-improvement loop protocol

**Layer 3 — Discoverable from code (0 tokens until needed):**
- Function signatures → `read displays/__init__.py`
- Server endpoints → `read server/index.ts`
- Research state operations → `read core/research.py`
- Available packages → `pip list`

### 4.2 The `/learn` Pattern for Self-Improvement

When Claude makes a mistake or discovers a non-obvious pattern, it should record the lesson where it will be seen before repeating the mistake. The question is: where?

**Options evaluated:**

| Approach | Pros | Cons |
|---|---|---|
| CLAUDE.md | Always loaded | Bloats the always-on context |
| `.claude/rules/*.md` | Auto-loaded, scoped | Still always-on, adds to the ~150 instruction budget |
| Skill files | Loaded on demand | Only seen when skill is activated |
| Memory files | Persistent across sessions | Not loaded by default, must be explicitly accessed |
| Comments in code | Seen when reading the code | Only helps when reading that specific file |

**Recommended approach: Tiered lesson storage**

1. **Critical lessons that prevent data loss or broken sessions** → `.claude/rules/safety.md` (always loaded, but kept very short — <10 rules)
2. **Domain-specific lessons** (e.g., "Three.js arrows: use setDirection/setLength, don't remove+recreate") → append to the relevant skill file (loaded when doing that kind of work)
3. **User-specific preferences** → `CLAUDE.local.md` or memory files

**The key insight:** Lessons go where they'll be seen at the right time. A Three.js rendering lesson should be in the displays skill, not in CLAUDE.md. A "don't kill the server" lesson belongs in `.claude/rules/safety.md` because it applies to all sessions.

### 4.3 Implementation

Create `.claude/rules/safety.md`:
```markdown
# Safety Rules
- Never kill, restart, or replace the server process. It hosts Claude's terminal session — killing it kills this conversation.
- Never force-push to main.
- Never delete workspace/research/ state without asking.
```

Move domain lessons into their respective skill files:
- Display workflow lessons → `.claude/skills/triptych-displays/SKILL.md`
- Research protocol lessons → `.claude/skills/autonomous/SKILL.md`

---

## 5. Self-Improvement Loop

### 5.1 The Goal

Triptych should get better through use. When Claude makes a mistake, the correction should be captured such that the same mistake cannot happen again. But context window space is finite, so lessons must be stored efficiently.

### 5.2 The Mechanism

**Immediate correction (current session):**
When an error is caught (by the human, the verifier, or Claude itself), fix the immediate problem. No special infrastructure needed.

**Persistent correction (future sessions):**
After fixing, determine if the lesson is generalizable:
- Is this specific to the current problem? → Don't persist. The fix is in the code/research state.
- Could this happen again in a different problem? → Persist to the appropriate tier (see 4.2).

**Format for persistent lessons:**
```markdown
## Lesson: [short title]
**What went wrong:** [one line]
**Fix:** [one line]
**When this applies:** [trigger condition]
```

### 5.3 Learning from Other Instances (Multi-User Future)

Currently, lessons are per-instance. Each Triptych installation learns from its own mistakes. Quinn manually promotes good lessons into the shipped product's skill files. Future multi-user sharing will be via curated GitHub PRs (human-reviewed for quality and privacy) if/when a user community develops.

### 5.4 Avoiding Context Overload

The danger of self-improvement is that the lesson store grows unboundedly. Mitigations:

1. **Budget per tier:** Safety rules: max 10. Skill-specific lessons: max 10 per skill. If a skill accumulates >10 lessons, consolidate or graduate patterns into code changes.
2. **Consolidation:** When multiple lessons point to the same underlying issue, merge them into one principle. "Don't remove+recreate arrows" and "Don't remove+recreate lights" → "In Three.js, update objects in place rather than removing and recreating."
3. **Graduation:** When a lesson applies universally, it should become a code change (default behavior) rather than an instruction. If Claude always needs to set a specific Three.js parameter, the `threejs.py` module should set it by default.
4. **Periodic review:** Use the `/autoresearch` skill to periodically audit lesson files for staleness, redundancy, and consolidation opportunities.

---

## 6. Deployment Strategy

### 6.1 Prerequisites

Users need:
- Node.js 18+ (for the server)
- Python 3.10+ (for display addons)
- C++ build tools (for node-pty compilation — Visual Studio Build Tools on Windows, Xcode CLT on Mac, build-essential on Linux)
- Claude Code CLI (authenticated with an API key)

### 6.2 Installation

**Target experience:**

```bash
git clone https://github.com/[user]/triptych.git
cd triptych
npm install                           # installs Node deps (including native node-pty)
pip install -r requirements.txt       # installs Python deps
npm run dev                           # starts on http://localhost:3000
```

The Python step is explicit and separate because it's the most likely to fail and the error messages from `pip` are much more actionable than a postinstall hook that silently checks and prints. Users who use conda, venv, or pyenv know what to do. Users who don't need a clear command they can Google if it fails.

### 6.3 The node-pty Problem

`node-pty` is a native module requiring C++ compilation. This is the biggest barrier to "download and run."

**Concrete failure rates by platform:**
- **Windows without Visual Studio Build Tools:** ~70% of non-developers. Error is a wall of C++ compilation errors. Fix: `npm install -g windows-build-tools` or install VS Build Tools.
- **Mac without Xcode CLT:** Fixable with `xcode-select --install` (one command, clear error message).
- **Linux without build-essential:** Fixable with `sudo apt install build-essential` or equivalent.

**Decision: Ship with `node-pty-prebuilt-multiarch` as the default dependency.** It ships pre-compiled binaries for Windows x64, macOS arm64/x64, and Linux x64. Falls back to compilation only when no prebuilt binary exists. This eliminates the problem for 95%+ of users with a one-line change to `package.json`. If prebuilt binaries prove unreliable, we can revert to standard `node-pty` with clear build tool documentation.

### 6.4 Configuration

**No `.env` file.** The server currently reads from `process.env` directly, and there are only two configurable values (`PORT`, `LOG_LEVEL`). Users who want a different port run `PORT=3001 npm run dev`. Adding `.env`, `dotenv`, `.env.example`, and copy-on-first-run infrastructure for two rarely-changed settings is over-engineering.

If configuration grows beyond 4 settings in the future, introduce `.env` at that point.

**`CLAUDE.local.md` (user-created, gitignored):**
Personal instructions, study integration, custom preferences. Mentioned in README as optional.

### 6.5 First-Run Setup

Create `requirements.txt`:
```
matplotlib
numpy
scipy
sympy
plotly
pandas
```

Create `scripts/preflight.js` — a standalone script users run BEFORE `npm install` if they want prerequisite validation. NOT a postinstall hook (because postinstall runs after `npm install`, which is too late if node-pty compilation fails).

```bash
node scripts/preflight.js   # optional: checks Node version, Python, build tools
npm install
pip install -r requirements.txt
npm run dev
```

The preflight script:
1. Checks Node.js version ≥18
2. Checks Python availability (`python` vs `python3` vs `py`, platform-aware)
3. Checks for C++ build tools as a soft warning ("only needed if prebuilt node-pty binaries fail for your platform")
4. Lists missing Python packages from requirements.txt
5. Prints clear, platform-specific fix instructions for anything missing
6. Creates `workspace/` directory structure if missing

This is optional — `npm install && pip install -r requirements.txt && npm run dev` works without it. The preflight script is for users who want diagnostics when something fails.

### 6.6 package.json Changes

```json
{
  "engines": {
    "node": ">=18.0.0"
  },
  "scripts": {
    "dev": "tsx server/index.ts",
    "preflight": "node scripts/preflight.js",
    "test": "vitest run",
    "test:watch": "vitest"
  }
}
```

---

## 7. Dogfooding Strategy — Iterating Within Triptych

### 7.1 The Constraint

The Triptych server hosts Claude Code's PTY session. Killing the server kills the conversation.

### 7.2 What Can Change Without Restart

Most of Triptych is hot-swappable by design:
- **Display addons** (Python files in `displays/`) — chokidar auto-reloads the display panel
- **Workspace addons** (HTML files in `workspaces/`) — chokidar notifies clients of new addons
- **Skill files** (`.claude/skills/`) — take effect on next Claude interaction
- **CLAUDE.md** — takes effect on next Claude interaction
- **Rules** (`.claude/rules/`) — take effect on next Claude interaction

These are the majority of changes. Edit the file and go.

### 7.3 What Requires Server Restart

Changes to `server/index.ts` or `core/shell.*` require restarting the server. This ends the current Claude session. The cost is: you lose conversation context (Claude Code's in-memory state), but all filesystem state persists (research, outputs, displays, memory).

**Workflow for server changes:**
1. Make the code change
2. Restart the server (`npm run dev`)
3. Claude Code respawns automatically in the new terminal session
4. Resume work — all file state is intact

This is simpler and more honest than a dual-instance setup. Server changes are infrequent compared to addon/skill changes.

**Advanced option: Dual-instance.** For testing server changes without interrupting a long session, run a second instance on a different port with a separate workspace: `PORT=3001 PROJECT_ROOT=/tmp/triptych-test npm run dev`. But this is rarely needed.

### 7.4 Git Strategy

```
main        — always deployable, what you run day-to-day
feature/*   — individual changes, merged to main after testing
```

Tag releases (`v0.2.0`, `v0.3.0`) for rollback points.

---

## 8. Security Model

### 8.1 Current Threat Surface

Triptych runs locally. The server binds to localhost. The primary security concerns are:

1. **Path traversal** — Already handled. Server validates all file paths.
2. **Claude Code permissions** — Currently runs with `--dangerously-skip-permissions`. For production, this should be configurable. Users should be able to run with standard permission prompts.
3. **Addon code execution** — Display addons run Python. Workspace addons run in browser iframes. A malicious addon could do anything Python/JS can do. For now, this is acceptable — users install addons they trust (same model as VS Code extensions).

### 8.2 The `--dangerously-skip-permissions` Question

Currently hardcoded in `server/index.ts`. This is a deliberate design choice, not a hack.

**Why it's needed:** Triptych's `/autonomous` skill and verification system are designed around Claude operating without human intervention. Permission prompts (which appear as interactive terminal prompts in the xterm.js panel) would block autonomous workflows. If Claude is running an autonomous research loop and hits a permission prompt, it blocks silently. The user might not notice for minutes. This defeats the core product value.

**The security model is "trusted local tool"** — the same model as VS Code with extensions. Triptych runs on localhost. The user installed it. The addons are part of the project. Claude Code has the same filesystem access the user has.

**Decision: Keep `--dangerously-skip-permissions` as the default.** Document it clearly in the README:
- Explain what it means (Claude can read/write files and run commands without asking)
- Explain why it's needed (autonomous operation, verification pipeline)
- Explain the security model (localhost, single-user, same trust as your shell)
- Tell users who want to change it how to edit the spawn args in `server/index.ts`

Making it configurable via env var adds complexity for a setting that almost no one will change, and the "safe" default would break the core workflow. This is the wrong place to add optionality.

### 8.3 Multi-User Considerations (Future)

If Triptych ever supports multiple users on a shared server:
- Each user gets an isolated `workspace/` directory
- Memory files are per-user
- No shared state between users
- Addon code is reviewed before installation (like an app store model)

This is future work. For now, Triptych is single-user, localhost-only.

---

## 9. File Changes Required

### 9.1 Files to Modify

| File | Change |
|---|---|
| `CLAUDE.md` | Replace with slim ~75-line version (section 16) |
| `.gitignore` | Add `CLAUDE.local.md`, `memory/` |
| `package.json` | Add `engines`, `node-pty-prebuilt-multiarch`, preflight script |
| `.claude/skills/autonomous/SKILL.md` | Absorb verification protocol details from CLAUDE.md |
| `server/index.ts` | Ensure `workspace/` subdirs are created on startup (mkdirp output, files, snapshots, research) |

### 9.2 Files to Create

| File | Purpose |
|---|---|
| `requirements.txt` | Python dependencies (matplotlib, numpy, scipy, sympy, plotly, pandas) |
| `CLAUDE.local.md` | Quinn's personal config (study integration, Obsidian) — gitignored |
| `.claude/rules/safety.md` | Always-loaded safety rules (<10 lines) |
| `scripts/preflight.js` | Optional prerequisite checker (run before npm install) |
| `LICENSE` | MIT license |
| `README.md` | Public-facing project description, install instructions, contributing section |
| `.github/workflows/ci.yml` | Automated test pipeline (see 9.5) |

### 9.3 Internal Docs → `docs/internal/`

Move BRIEF.md, PRD.md, BUILD-PLAN.md, UI-PLAN.md, and PRODUCTION-PLAN.md to `docs/internal/`. Keep them in git — they contain architectural decisions and design rationale that contributors need. They cost nothing (small text files) and provide valuable context for understanding why Triptych is built the way it is. Users who clone can simply ignore the `docs/` directory.

The `simplifier` agent (`.claude/agents/simplifier.md`) is a build tool, not a product feature — move to `docs/internal/` or remove.

The `bench/` directory is evaluation infrastructure. Keep it in git but document it as "for development, not end users" in CONTRIBUTING.md.

### 9.4 Directory Structure After Changes

```
triptych/
  CLAUDE.md               — Slim behavioral guide (~65 lines)
  CLAUDE.local.md          — Personal overrides (gitignored)
  README.md                — Public-facing docs
  CONTRIBUTING.md          — How to contribute
  LICENSE                  — MIT
  requirements.txt         — Python dependencies
  package.json             — With engines and node-pty-prebuilt
  tools.md                 — Addon reference
  
  .claude/
    rules/
      safety.md            — Always-loaded safety rules
    skills/
      autonomous/SKILL.md  — Full verification protocol
      watcher/SKILL.md     — Observation behavior
      triptych-displays/   — Display addon instructions
      triptych-workspaces/ — Workspace addon instructions
    agents/
      verifier.md          — Claim verification agent
      cross-verifier.md    — Independent re-derivation agent
  
  .github/
    workflows/ci.yml       — Test pipeline
  
  core/                    — Framework code (unchanged)
  displays/                — Display addons (unchanged)
  workspaces/              — Workspace addons (unchanged)
  server/                  — Server code
  scripts/
    preflight.js           — Optional prerequisite checker
  tests/                   — Test suite
  docs/
    internal/              — Design docs (BRIEF, PRD, BUILD-PLAN, etc.)
    addon-build-plan.md    — Already exists
  bench/                   — Evaluation infrastructure (dev use)
  
  workspace/               — Runtime state (gitignored, created on first run)
  memory/                  — Per-user persistence (gitignored)
  logs/                    — Server logs (gitignored)
```

### 9.5 CI/CD

Add `.github/workflows/ci.yml` that:
1. Runs TypeScript tests (`npm test`) on push/PR — need to mock node-pty in CI to avoid native compilation, or use a matrix with build tools installed
2. Runs Python tests (`python -m pytest tests/` or `python tests/run_tests.py`)
3. Runs TypeScript type-checking (`npx tsc --noEmit`)
4. Matrix: Ubuntu (primary), macOS, Windows

**Linting/formatting:** Add incrementally. Start with `ruff` for Python (fast, opinionated, zero-config) and ESLint + Prettier for TypeScript. These can be added in a follow-up PR after the core production changes land.

**Test runnability note:** The server tests import `server/index.ts`, which has module-level side effects (creates directories). Tests that register a `terminal` WebSocket role may try to spawn Claude Code. These need to be mocked or skipped in CI where Claude Code is not installed. This is a prerequisite for CI working at all.

---

## 10. Implementation Order

### Phase 1: Separate and Slim Down
1. Write the new slim CLAUDE.md (~65 lines)
2. Create CLAUDE.local.md with Quinn's personal config (study integration, Obsidian)
3. Move verification protocol details into `/autonomous` skill
4. Create `.claude/rules/safety.md`
5. Update `.gitignore` (add CLAUDE.local.md, memory/)
6. Move design docs to `docs/internal/`

### Phase 2: Dependencies and Setup
7. Create `requirements.txt`
8. Switch `node-pty` to `node-pty-prebuilt-multiarch` in package.json
9. Add `engines` field to package.json
10. Create `scripts/preflight.js`
11. Add `LICENSE` (MIT)

### Phase 3: Documentation
12. Write `README.md` with platform-specific install instructions, including a "Contributing" section (a full `CONTRIBUTING.md` is premature with one user — add it when contributors arrive)

### Phase 4: CI and Testing
13. Add `.github/workflows/ci.yml`
14. Mock node-pty and Claude Code spawning in test environment
15. Verify tests pass in CI

### Phase 5: Validate
16. Clone the repo to a fresh directory (or have someone else try)
17. Run through the setup process as a new user on a clean machine
18. Verify Claude Code works correctly with the new slim CLAUDE.md
19. Fix issues found
20. Tag v0.2.0

---

## 11. Resolved Questions

1. **`tools.md`** — Keep as a standalone file. It serves both humans (quick reference) and Claude (CLAUDE.md points to it). Making it a skill adds activation friction for something that's useful to browse. The CLAUDE.md now mentions key MCP servers directly.

2. **`bench/` directory** — Keep in git. Document in CONTRIBUTING.md as development/evaluation infrastructure.

3. **`.claude/agents/`** — Ship verifier and cross-verifier (integral to verification). Remove simplifier (build tool, not product feature).

4. **`docs/`** — Move design docs (BRIEF, PRD, BUILD-PLAN, UI-PLAN) to `docs/internal/`. Keep in git for contributor context.

---

## 12. Prompting Philosophy — What Makes Triptych Special

The key insight from the research: **the best prompts give context, not commands.** Instead of "ALWAYS verify your work," explain why: "This is a research collaboration tool. Unverified claims waste the human's time and erode trust. The verification system exists because humans can't catch math errors at the speed AI generates them."

Claude generalizes from explained context. If it understands WHY verification matters, it will verify even in edge cases the instructions didn't anticipate. If it only knows the rule, it follows the rule mechanically and misses the spirit.

The proposed CLAUDE.md embodies this: it explains what Triptych is and why verification matters, then points to skills for the how. The skills contain the operational details. The rules contain the hard constraints. Everything else is discoverable from code.

This is progressive disclosure applied to prompting: the right information at the right time, in the right amount. The context window is a scarce resource. Treat it like one.

---

## 13. Agent Behavioral Design — The Good Colleague

This is the most important section. Everything else in this plan is infrastructure. This is what makes Triptych actually good.

### 13.1 The Core Insight from Research

Anthropic's official guidance says Claude should be like **"a brilliant friend who also has the knowledge of a doctor, lawyer, and financial advisor"** — someone who provides "real information based on our specific situation" rather than generic hedged advice. This is exactly the Triptych philosophy: not an assistant that follows instructions, but a colleague that thinks alongside you.

The research on human-AI collaboration (CHI 2025, 398 interventions analyzed) found that **proactive AI increases efficiency but risks disruption**. The key is calibration:
- **53% of proactive interventions** led to effective engagement
- **62% of mid-task interruptions** were dismissed
- **Interrupting at task boundaries** (commit, test, phase transition) achieved 53-73% engagement
- **Detecting pauses as "stuck"** backfired — people think during pauses

The MIT meta-analysis (106 studies) found that human-AI combinations only outperform solo performers **when each party does what they do better**: AI leads on recall-intensive tasks, computation, and generating alternatives; humans lead on aesthetic judgment, novel problem framing, and contextual understanding.

### 13.2 Phase-Based Behavior

The agent's behavior should change based on what phase of work it detects. This is already outlined in the PRD's "Exploration and Formalization" section, but the research adds concrete guidance:

**Exploration Phase** (brainstorming, reading, sketching, "what should we even ask?"):
- **Be Socratic.** Ask questions that deepen engagement: "What constraints does this system have?" "Have you considered the limit where X → 0?" "This reminds me of [concept] — does that connection seem useful?"
- **Draw connections.** Multi-persona brainstorming (connecting ideas from different domains) rated significantly higher than single-perspective responses. Surface unexpected links.
- **Generate alternatives.** Divergent thinking is the goal. Offer multiple framings, not one answer.
- **Stay quiet during pauses.** Pauses ≠ stuck. The human is thinking.
- **No verification.** There are no formal claims to verify yet.
- **No interruptions during active thinking.** Only speak at natural breaks.

**Formalization Phase** (derivation, computation, formal analysis):
- **Be verificatory.** Emit claims, run the verification pipeline. This is where the "compiler for hard problems" activates.
- **Catch errors proactively.** Flag algebra mistakes, dimensional inconsistencies, and dropped signs without being asked. These are obvious errors — speak up immediately.
- **Check work at step boundaries.** After completing a derivation step, verify before proceeding. Don't interrupt mid-step.
- **Suggest limiting cases and sanity checks.** "Does this reduce to the right answer when θ → 0?" "Do the units check out?"
- **Log concerns that aren't certain.** If something looks wrong but you're not sure, log it. Surface only if the human asks or the concern is confirmed.

**Review/Iteration Phase** (testing, comparing approaches, refining):
- **Try alternatives proactively.** "What if we approached this using energy methods instead?" Run the alternative and compare.
- **Test edge cases.** Push the solution to its limits — extreme values, boundary conditions, degenerate cases.
- **Show side-by-side comparisons.** Display the original approach and the alternative together.
- **Be concrete about what's different.** Not "this approach might work better" but "this approach gives θ̈ = -(g/l)sinθ via Lagrangian vs. θ̈ = -(g/l)sinθ via Newton — they agree, confirming the result."

### 13.3 The CLAUDE.md as Identity Document

The CLAUDE.md should not just tell Claude what to do. It should help Claude understand **what it is** in this context and **why that matters**. From Anthropic's prompting guide:

> "Add context/motivation for instructions. Instead of bare commands, explain why. Claude generalizes from explained context better than from bare directives."

The proposed CLAUDE.md already does this for verification ("Triptych exists because AI makes mistakes on hard problems and nobody catches them"). But it should also convey the colleague framing:

**Add to the top of the proposed CLAUDE.md:**
```
You are a research colleague, not an assistant following instructions. During
brainstorming, draw connections and ask questions that deepen understanding.
During formalization, check work proactively and suggest sanity checks. Adapt
to what the human needs in the moment — sometimes that's generating ideas,
sometimes that's catching errors, sometimes that's working independently.
```

This is behavioral context, not an instruction. It tells Claude what it IS, and Claude generalizes from there.

### 13.4 Self-Improvement: The Agent Improves Itself

The agent should actively seek to get better. From the research:

**Karpathy's autoresearch loop** (the model for `/autoresearch`): The key insight is **binary evaluation**. "The moment you introduce a 1-7 rating, the agent starts producing outputs that technically score a 5 but read like garbage." Binary pass/fail is the only scoring that works for unsupervised optimization.

**Hermes Agent's self-improvement mechanisms:**
1. When the agent completes a complex task, it creates a reusable skill document
2. At set intervals, it evaluates what from the session is worth persisting to long-term memory
3. Skills are refined each time they're applied

**For Triptych, the agent should:**
- After a research session, reflect: "What went well? What went wrong? Is there a lesson here that applies to future sessions?" If yes, record it in the appropriate tier (safety rules / skill lessons / memory).
- When it encounters a task it doesn't have a skill for, it should build one — write a SKILL.md, test it, and offer to keep it. This is Claude's existing ability to "extend the system on the fly."
- When a display addon or workspace doesn't exist for what it needs, it should build it — write the Python or HTML, test it, and add it to the system.
- Periodically (at session end, or when prompted), consolidate lessons: merge duplicates, graduate patterns into code, delete stale entries.

**The key principle from Anthropic:** "Give Claude a way to verify its work." The agent's self-improvement is only reliable when improvements are measured against binary criteria. Did the new skill work? Did the lesson prevent the same error? Binary, not subjective.

### 13.5 Claude 4.6-Specific Behavioral Notes

From Anthropic's official guidance on Claude 4.6:

- **Dial back aggressive prompting.** Where you might have written "CRITICAL: YOU MUST use this tool," write "Use this tool when..." Claude 4.6 is more responsive to system prompts and will overtrigger on aggressive language.
- **Don't encourage extra thoroughness.** Claude 4.6 already does significantly more upfront exploration than previous models. Prompts that previously encouraged thoroughness should be tuned down.
- **Anti-overengineering instructions.** Claude 4.6 tends to create extra files, add unnecessary abstractions, and build in flexibility that wasn't requested. The CLAUDE.md should say "only make changes that are directly requested or clearly necessary."
- **Expect concise communication.** Claude 4.6 is more direct and less verbose. Don't require summaries after every action — it's already concise.

---

## 14. What Ships: Addons, Skills, and MCP Servers

### 14.1 Workspaces (Ship Current Set — 7)

The current workspace set is already strong. No additions needed for v0.2.0.

| Workspace | Purpose | Status |
|-----------|---------|--------|
| File browser | Navigate and manage files in `workspace/files/` | Ship |
| tldraw canvas | Freeform drawing and whiteboarding | Ship |
| Code editor (CodeMirror 6) | Code editing with syntax highlighting | Ship |
| Markdown editor (Milkdown) | WYSIWYG writing with KaTeX math | Ship |
| Spreadsheet (jspreadsheet) | Grid data with formulas | Ship |
| PDF viewer | Read PDFs | Ship |
| Settings | Configure Triptych settings | Ship |

**Future additions (not v0.2.0):** Graphing calculator (embeddable Desmos/Function Plot), mind map (markmap), study dashboard.

### 14.2 Displays (Ship Current Set + 1 New — 15 total)

Add `show_derivation()` — a step-by-step mathematical derivation display. This is the single highest-value addition for the core use case.

| Display | Purpose | Status |
|---------|---------|--------|
| matplotlib | Static plots (PNG) | Ship |
| plotly | Interactive charts | Ship |
| latex/KaTeX | Math equations | Ship |
| markdown | Rich text with math | Ship |
| html | Pass-through HTML | Ship |
| image | Image viewer | Ship |
| pdf | PDF rendering | Ship |
| code | Syntax-highlighted code + diffs | Ship |
| table | Data tables (lists, dicts, DataFrames) | Ship |
| d3 | D3.js scaffold generator | Ship |
| threejs | 3D graphics (surfaces, vectors, curves) | Ship |
| research | Research state + dependency graph | Ship |
| autoresearch | Self-improvement dashboard | Ship |
| **derivation** | **Step-by-step math derivation with KaTeX** | **New** |

**`show_derivation()` specification:**
```python
show_derivation(steps=[
    ("T = \\frac{1}{2}ml^2\\dot{\\theta}^2", "Kinetic energy in polar coordinates"),
    ("V = -mgl\\cos\\theta", "Potential energy with θ measured from vertical"),
    ("L = T - V = \\frac{1}{2}ml^2\\dot{\\theta}^2 + mgl\\cos\\theta", "Lagrangian"),
], title="Lagrangian Derivation")
```
Generates HTML with numbered steps, KaTeX-rendered equations, annotations, and optional "what changed" highlighting between steps.

**Future additions (not v0.2.0):** Animated simulation (p5.js/Canvas), side-by-side comparison, flashcard/quiz.

### 14.3 Skills (Ship Current Set + 1 New — 7 total)

Add `/literature-review` — the most universal research workflow.

| Skill | Purpose | Status |
|-------|---------|--------|
| `/autonomous` | Solve problems independently with verification | Ship |
| `/watcher` | Observe workspace, catch errors | Ship |
| `/autoresearch` | Self-improvement loop | Ship |
| `/triptych-displays` | How to build display addons | Ship |
| `/triptych-workspaces` | How to build workspace addons | Ship |
| `/study` | Study session management | Ship (if not Quinn-specific) |
| **`/literature-review`** | **Structured paper search and synthesis** | **New** |

**`/literature-review` specification:**
Accept a topic or research question. Search via arXiv MCP + PapersFlow. Retrieve key papers. Extract claims and methods. Build structured summary with citations. Identify gaps. Update research state. Output: annotated bibliography in research state format.

**Future additions (not v0.2.0):** /data-analysis, /explain, /debug (for research problems, not code).

### 14.4 MCP Servers (Ship Current + 2 New)

Add Wolfram Alpha and PapersFlow.

| MCP Server | Purpose | Status |
|------------|---------|--------|
| sympy-mcp | Symbolic math | Ship |
| arxiv-latex-mcp | Paper lookup and LaTeX extraction | Ship |
| desmos-mcp | Interactive graphing | Ship |
| firecrawl | Web scraping and search | Ship |
| context7 | Library documentation | Ship |
| Hugging Face | Model/dataset search | Ship |
| **Wolfram Alpha** | **Numerical computation, constants, units, step-by-step** | **New** |
| **PapersFlow** | **474M papers, citation graphs, related papers** | **New** |

**Wolfram Alpha** fills the gap between Claude's native computation and SymPy's symbolic math. It handles unit conversion, physical constants, numerical integration, data lookup, and natural language math queries. Requires a free API key (2000 queries/month on free tier).

**PapersFlow** searches 474M+ academic papers across OpenAlex (not just arXiv). Free, no API key. One-command install: `claude mcp add papersflow --transport streamable-http https://doxa.papersflow.ai/mcp`.

### 14.5 What NOT to Ship

- **Jupyter notebook workspace**: Over-engineered. Claude IS the compute kernel. The terminal handles what Jupyter would.
- **LaTeX editor (Overleaf clone)**: The markdown editor handles KaTeX. A full LaTeX editor is massive build for marginal gain.
- **Kanban / Gantt / project management**: Triptych solves hard problems, not project management.
- **Molecule viewer / circuit diagrams**: Niche domain-specific tools. Build when needed, don't ship as defaults.
- **More than ~10 MCP servers**: Each server is cognitive overhead for the agent. Ship the essential set, let users add more.

---

## 15. Deployment — Updated Strategy

### 15.1 Three Deployment Paths

Research shows that no single deployment method works for everyone. The winning strategy is to provide three paths that share the same underlying configuration:

**Path 1: GitHub Codespaces (zero install, one click)**
For users who want to try Triptych immediately. Click "Open in Codespaces" in the README. A fully configured cloud environment spins up in 2-3 minutes. Set your Anthropic API key as a Codespaces secret. Open port 3000. Done.

Cost: Free for 60 hours/month (2-core). Sufficient for casual use.

**Path 2: Docker Compose (local, requires only Docker)**
For users who want to run locally without managing Node/Python/build tools.

```bash
git clone https://github.com/[user]/triptych.git
cd triptych
echo "ANTHROPIC_API_KEY=your-key-here" > .env
docker compose up
```

Opens at `http://localhost:3000`. Everything (Node, Python, scientific packages, node-pty) is inside the container.

**Path 3: Native install (for developers and contributors)**
For users who want to modify Triptych or prefer native performance.

```bash
git clone https://github.com/[user]/triptych.git
cd triptych
npm install                           # Node deps + node-pty
pip install -r requirements.txt       # Python deps
npm run dev                           # http://localhost:3000
```

Requires Node 18+, Python 3.10+, and C++ build tools (for node-pty).

### 15.2 Shared Infrastructure

All three paths share:
- The same `Dockerfile` (used by both Codespaces and Docker Compose)
- The same `devcontainer.json` (used by Codespaces and VS Code Remote)
- The same `requirements.txt` (used by Docker and native install)
- The same `package.json` (used by Docker and native install)

One Dockerfile, three deployment paths. Maintenance is one file.

### 15.3 The Dockerfile

```dockerfile
FROM node:20
RUN apt-get update && apt-get install -y python3 python3-pip python3-venv build-essential
RUN pip3 install --break-system-packages matplotlib numpy scipy sympy plotly pandas
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm install -g @anthropic-ai/claude-code@latest
# Create workspace directories (server expects them to exist)
RUN mkdir -p workspace/output workspace/files workspace/snapshots workspace/research
EXPOSE 3000
CMD ["npx", "tsx", "server/index.ts"]
```

### 15.3.1 Authentication in Docker and Codespaces

Claude Code CLI authenticates via the `ANTHROPIC_API_KEY` environment variable. The paths:

**Docker Compose:** The `.env` file contains the API key. The `docker-compose.yml` passes it:
```yaml
services:
  triptych:
    build: .
    ports:
      - "3000:3000"
    volumes:
      - ./workspace:/app/workspace
    env_file: .env
    stdin_open: true
    tty: true
```
The `env_file: .env` directive passes all variables from `.env` into the container. Claude Code picks up `ANTHROPIC_API_KEY` from the environment automatically. The server passes the container's environment to the spawned Claude Code process via `node-pty`'s env option.

**Codespaces:** Set `ANTHROPIC_API_KEY` as a Codespaces secret (Settings → Codespaces → Secrets). Map it in `.devcontainer/devcontainer.json`:
```json
{
  "name": "Triptych",
  "build": { "dockerfile": "../Dockerfile" },
  "forwardPorts": [3000],
  "secrets": {
    "ANTHROPIC_API_KEY": {
      "description": "Your Anthropic API key for Claude Code"
    }
  }
}
```
Codespaces secrets are automatically available as environment variables in the container.

**Implementation note:** The server's `getOrSpawnPty()` function in `server/index.ts` must pass `process.env` to the spawned Claude Code process. Verify this is the case (it likely already inherits the environment, but confirm).

### 15.4 Files to Create for Deployment

| File | Purpose |
|------|---------|
| `Dockerfile` | Shared container definition |
| `docker-compose.yml` | One-command local Docker setup |
| `.devcontainer/devcontainer.json` | Codespaces + VS Code Remote config |
| `requirements.txt` | Python dependencies |
| `.env.example` | Template for Docker Compose API key |

### 15.5 Updated Implementation Order

Replace Phase 2 in Section 10 with:

**Phase 2: Deployment Infrastructure**
7. Create `requirements.txt`
8. Create `Dockerfile`
9. Create `docker-compose.yml`
10. Create `.devcontainer/devcontainer.json`
11. Create `.env.example` (for Docker path only — API key)
12. Add "Open in Codespaces" badge to README
13. Switch `node-pty` to `node-pty-prebuilt-multiarch` in package.json (for native path)
14. Add `engines` field to package.json
15. Add `LICENSE` (MIT)

---

## 16. The Revised CLAUDE.md (Final Version)

Incorporating all research — Anthropic prompting guide, collaboration patterns, agent behavior, progressive disclosure:

```markdown
# Triptych

You are a research colleague working inside Triptych, a three-panel system for solving hard problems. The human works in the left panel (workspace), you show your work in the middle panel (display), and this terminal is how you communicate.

During brainstorming, draw connections and ask questions that deepen understanding. During formalization, check work proactively and suggest sanity checks. Adapt to what the human needs — sometimes generating ideas, sometimes catching errors, sometimes working independently. Be honest about uncertainty — say what you know and what you don't.

Triptych supports research, study, writing, data analysis, and design. Verification is for formal derivations and scientific claims, not conversation — be direct and confident in normal discussion, rigorous and verified in formal work.

The filesystem is the communication channel. You read and write files. The framework handles the rest. Triptych is Express + WebSocket on port 3000, with chokidar watching `workspace/output/` for display auto-reload.

## Show Your Work

Write to `workspace/output/`. The display panel auto-reloads.

Triptych Python modules are in the project root. Always prefix scripts with `import sys; sys.path.insert(0, '.')` before importing from `core/` or `displays/`.

    import sys; sys.path.insert(0, '.')
    from displays import show_figure, show_plotly, show_html, show_latex, show_research, clear

Use the dark theme: background #0a0a0b/#111113, text #c8c8d0, accents #6e73ff (blue), #34d399 (green), #f87171 (red), #fbbf24 (yellow), borders #222228. Prefer interactive visualizations (Three.js, Plotly) over static images — see `/triptych-displays` for the full catalog including 3D surfaces, vector fields, and parametric curves.

## See What the Human is Working On

Workspace snapshots update every 30 seconds:
- `workspace/snapshots/latest.png` — screenshot
- `workspace/snapshots/latest.json` — context metadata

The human shares files via `workspace/files/` — you can read and write files there.

## Research and Verification

Triptych exists because AI makes mistakes on hard problems and nobody catches them. Every significant claim during mathematical derivations, scientific reasoning, or formal analysis must be independently verified. Routine computations, visualizations, and conversational help do not need verification.

For structured research, initialize state with `core/research.py` (`init_research`, `update_state`, `add_established`) and track claims with `core/verify.py`. Verification results integrate with research state automatically — verified claims become established results, failed claims stay in attempts.

    from core.verify import emit_claim
    emit_claim("F = ma", "Newton's second law", depends=["A1"], research_dir="workspace/research")

After emitting claims, spawn the verifier agent to check them. See `/autonomous` for the full verification loop including cross-verification.

## When to Use Skills

| Task | Skill |
|------|-------|
| Solve a problem independently | `/autonomous` |
| Watch human's workspace for errors | `/watcher` |
| Build a new display addon | `/triptych-displays` |
| Build a new workspace addon | `/triptych-workspaces` |
| Optimize Triptych itself | `/autoresearch` |
| Search and synthesize papers | `/literature-review` |

## Extending Triptych

- Write HTML to `workspaces/` to create new workspace tools
- Write Python modules in `displays/` to create new display types
- Check `tools.md` for all available addons and MCP servers (sympy, arxiv, desmos, wolfram, papersflow)
- If a tool you need doesn't exist, build it — that's what Triptych is for

## Constraints

- Never kill or restart the server process. It hosts this terminal session.
- The `workspace/` directory is for runtime state. Framework code lives in `core/`, `displays/`, `workspaces/`.
- If display output fails, verify `workspace/output/` exists and create it if needed.
- Check `CLAUDE.local.md` for user-specific configuration if it exists.
```

**Changes from the previous draft:**
- Added the "colleague" framing at the top (3 lines — behavioral context, not instructions)
- Added "When uncertain, say so honestly" (from Anthropic's constitution on calibrated honesty)
- Added `/literature-review` to the skill table
- Added "If a tool you need doesn't exist, build it" (self-extension principle)
- Added wolfram and papersflow to MCP server mentions
- Total: ~75 lines. Still under 1/3 of the original 209-line CLAUDE.md.

---

## 17. Critique Log

This plan went through multiple rounds of independent critique. Key findings that changed the plan:

### Round 1: Prompting Design Critique

**Finding:** The original 45-line CLAUDE.md was too slim. It removed critical context about `sys.path.insert(0, '.')`, research state existence, shared files (`workspace/files/`), and the architecture mental model. Claude wouldn't know these things existed without reading code files it has no reason to read.

**Action:** Expanded to ~65 lines. Added: sys.path explanation, research state awareness (without full API), shared files line, architecture one-liner, skill-to-task mapping table, MCP server mention, verification scope clarification.

**Finding:** The litmus test "would removing this cause mistakes?" was too narrow. Some instructions prevent quality degradation (dark theme, visualization preferences) or capability blindness (MCP servers, Three.js displays) without strictly preventing errors.

**Action:** Broadened litmus test to include quality and capability awareness.

**Finding:** There's an "activation gap" — Claude needs to know when to activate skills, but the triggers are often ambiguous. The plan assumed Claude would naturally match "let's work through this problem" to the `/autonomous` skill, but in practice the user might be collaborative, not autonomous.

**Action:** Added a task-to-skill mapping table directly in CLAUDE.md. Added awareness of research state to bridge collaborative and autonomous modes.

**Finding:** Multi-user learning Phase 3 (structured JSON aggregation) was premature abstraction occupying mental budget.

**Action:** Collapsed to two sentences.

### Round 2: Engineering Critique

**Finding:** Python dependencies are completely unmanaged. No `requirements.txt`, no `pyproject.toml`. The "3 commands" installation promise was false — users would need to figure out `pip install matplotlib numpy scipy sympy plotly pandas` on their own.

**Action:** Added `requirements.txt` to the plan. Made `pip install -r requirements.txt` an explicit installation step.

**Finding:** `node-pty` compilation will fail for 60-70% of non-developer Windows users. "Accept it and document" is insufficient for a tool targeting "anyone."

**Action:** Changed recommendation to `node-pty-prebuilt-multiarch` as default dependency.

**Finding:** `postinstall` hook runs AFTER `npm install`. If `npm install` fails (because node-pty can't compile), the prerequisite checker never runs. Wrong lifecycle hook.

**Action:** Changed to standalone `scripts/preflight.js` run before `npm install`.

**Finding:** `.env` file for two settings (PORT, LOG_LEVEL) is over-engineering. Users who want a different port can use env vars directly.

**Action:** Dropped `.env` pattern entirely.

**Finding:** Dual-instance dogfooding is more complex than needed. Most changes (addons, skills, CLAUDE.md) are hot-swappable. For server changes, just restart.

**Action:** Simplified to "edit files for hot-swap changes, restart server for server changes."

**Finding:** `--dangerously-skip-permissions` removal would break autonomous operation (permission prompts block in the terminal panel). Triptych's security model is "trusted local tool," not "untrusted remote service."

**Action:** Changed to "keep as default, document clearly" instead of "make configurable, default to safe."

**Finding:** Design docs (BRIEF.md, PRD.md, etc.) contain valuable architectural context. Gitignoring them destroys history that contributors need.

**Action:** Changed to moving them to `docs/internal/`, keeping them in git.

**Finding:** No CI/CD, no linting, no formatting. Tests may not be runnable in CI due to node-pty and Claude Code dependencies.

**Action:** Added CI section with GitHub Actions workflow, noted need to mock native dependencies in CI.

### Round 3: Behavioral Design and Deployment Research

**Finding (Anthropic prompting guide):** Claude 4.6 is more proactive than previous models. The plan's CLAUDE.md used neutral language, but should explicitly set the "colleague" framing. Anthropic says: "Add context/motivation for instructions — Claude generalizes from explained context better than bare directives." The agent needs to understand what it IS, not just what to DO.

**Action:** Added the colleague framing paragraph to the top of CLAUDE.md. Added "When uncertain, say so honestly rather than hedging" (from Anthropic's calibrated honesty principle).

**Finding (collaboration research):** CHI 2025 study of 398 proactive AI interventions found that interrupting at task boundaries (53-73% engagement) works, but mid-task interruptions are dismissed 62% of the time. Detecting pauses as "stuck" backfires — people think during pauses.

**Action:** Added detailed phase-based behavior guidance (Section 13.2) — specific instructions for exploration, formalization, and review phases, with concrete "do this" and "don't do this" for each.

**Finding (deployment research):** No single deployment method works for everyone. Docker + Codespaces share a Dockerfile and eliminate all dependency management. GitHub Codespaces provides zero-install, one-click access for free (60 hrs/month). Docker Compose requires only Docker. Both solve the node-pty and Python dependency problems completely.

**Action:** Added three deployment paths (Section 15) sharing one Dockerfile: Codespaces (zero install), Docker Compose (local), and native (for developers).

**Finding (addons research):** The current workspace set is already strong. The highest-value display addition is `show_derivation()` — step-by-step math with KaTeX. The highest-value MCP additions are Wolfram Alpha (numerical computation/constants) and PapersFlow (474M papers, free). The highest-value skill addition is `/literature-review`.

**Action:** Added Section 14 specifying exactly what ships, what's future, and what never ships. Applied the "simpler is better" principle — no Jupyter, no LaTeX editor, no project management tools.

**Finding (self-improvement research):** Karpathy's autoresearch proves that binary evaluation is essential — subjective 1-7 scales produce garbage optimization. Hermes Agent's self-improvement works by creating skill documents after complex tasks and periodically evaluating what to persist.

**Action:** Added self-improvement guidance to Section 13.4. The agent should build skills when it needs them, record lessons in the right tier, and consolidate at session end.

### Round 4: Final Holistic Review

**Finding:** Section 4.1 said "~45 lines, ~500 tokens" but the CLAUDE.md was actually 65 lines.

**Action:** Updated to "~65 lines, ~700 tokens."

**Finding:** The preflight script checked for C++ build tools even though node-pty-prebuilt was supposed to eliminate that need.

**Action:** Made build tool check a soft warning: "only needed if prebuilt binaries fail."

**Finding:** A fresh Claude wouldn't know CLAUDE.local.md exists or to look for it.

**Action:** Added "Check CLAUDE.local.md for user-specific configuration if it exists" to constraints.

**Finding:** CONTRIBUTING.md is premature with one user.

**Action:** Dropped it, added a Contributing section to README instead.

---

## 18. First-Boot Protocol

When a new user clones Triptych and runs `npm run dev` for the first time, Claude Code starts in a fresh project with no context about the user. The first-boot protocol gets Claude oriented and the user configured.

### 18.1 The Problem

Claude Code has several features that Triptych depends on but which may not be enabled:
- **Auto-memory** (`autoMemoryEnabled`) — must be on for Triptych's learning loop
- **Sandbox mode** — should be enabled for security (see Section 19)
- **Permission mode** — needs to be set appropriately
- **MCP servers** — sympy-mcp, arxiv-latex-mcp, desmos-mcp should be configured

Additionally, Claude needs to know:
- Who is the user? (Researcher, student, engineer — affects communication style)
- What kind of problems will they work on? (Math, physics, data science, general)
- Any preferences? (Verbosity, proactiveness, verification rigor)

### 18.2 Implementation: `.claude/rules/first-boot.md`

Create a path-scoped rule that fires on first interaction. This is an auto-loaded rule file (NOT a skill — it should run without explicit activation).

```markdown
---
description: First-boot setup — runs when Triptych detects no user configuration
---

# First-Boot Protocol

On your very first interaction in a new Triptych installation, check if setup is needed:

1. Check if `CLAUDE.local.md` exists. If not, this is a first boot.

2. If first boot, greet the user and run through setup:

   a. **User profile**: Ask what they primarily work on (math, physics, engineering, data science, general research) and their experience level. This shapes how you communicate — a physics PhD gets different explanations than an undergrad.

   b. **Settings check**: Verify Claude Code settings are configured for Triptych:
      - Auto-memory should be enabled (check settings, suggest enabling if off)
      - Recommend sandbox mode for security (see below)
      - Suggest useful MCP servers based on their domain

   c. **Create CLAUDE.local.md**: Based on their answers, generate a personal config file with their preferences. Template:
      ```
      ## User Profile
      [Domain, experience level, communication preferences]

      ## Custom Instructions
      [Any personal overrides or additions]
      ```

   d. **Quick tour**: Show the three-panel layout, demonstrate a display (`show_latex`), explain how files work.

3. After setup, do NOT run this protocol again. The existence of `CLAUDE.local.md` is the flag.
```

### 18.3 Why a Rule, Not a Skill

A skill requires explicit activation (`/first-boot`) or semantic matching. A rule in `.claude/rules/` loads automatically every session.

**Overhead concern:** The full rule text (~30 lines) loads every session, not just the gate check. To minimize this, keep the rule body short — just the gate logic and a pointer to a `/first-boot` skill for the actual onboarding flow. The rule becomes 5 lines ("if no CLAUDE.local.md, run `/first-boot`"), and the skill's full instructions only load when triggered.

**Settings check limitation:** There is no `claude config get` command. Claude cannot programmatically verify settings. The first-boot protocol should recommend settings and tell the user how to check/change them manually (e.g., "open `~/.claude/settings.json` and verify `autoMemoryEnabled` is true"). Be honest about this limitation.

### 18.4 Settings to Recommend

| Setting | Where | Value | Why |
|---------|-------|-------|-----|
| `autoMemoryEnabled` | `~/.claude/settings.json` | `true` | Triptych's learning loop depends on memory |
| `sandbox.enabled` | `.claude/settings.json` | `true` | Security without breaking autonomous operation |
| `autoCompactPercent` | `~/.claude/settings.json` | `60` | Triptych sessions can be long; compact early |
| `permissions.defaultMode` | `.claude/settings.json` | See Section 19 | Depends on sandbox availability |

### 18.5 MCP Server Recommendations by Domain

| Domain | Recommended MCP Servers |
|--------|------------------------|
| Math/Physics | sympy-mcp, desmos-mcp, wolfram-alpha |
| CS/ML | context7, hugging-face |
| General Research | arxiv-latex-mcp, papersflow, firecrawl |
| All users | firecrawl (web search/scraping) |

The first-boot protocol should suggest but never auto-install MCP servers. Installation requires running `claude mcp add ...` which the user should do themselves.

---

## 19. Security Model — Revised with Native Sandbox

### 19.1 The Discovery: Claude Code Has a Native Sandbox

Claude Code has built-in OS-level sandboxing that restricts filesystem and network access for bash commands. This changes the security story significantly.

**How it works:**
- **macOS**: Uses Apple's Seatbelt (sandbox-exec) — works out of the box
- **Linux/WSL2**: Uses bubblewrap + socat — requires `sudo apt install bubblewrap socat`
- **Native Windows**: Not yet supported (planned). WSL2 works via Linux path.

**What it does:**
- OS-level filesystem restrictions (cannot be bypassed by prompt injection)
- Network domain allowlists
- Configurable read/write path allow/deny lists

### 19.2 The Revised Permission Strategy — Two Layers

**Layer 1: Permission allowlists (all platforms, shipped in `.claude/settings.json`):**

```json
{
  "permissions": {
    "allow": ["Bash(python *)", "Bash(git *)", "Bash(npm *)", "Read", "Edit", "Write", ...],
    "deny": ["Bash(rm -rf /)", "Bash(curl * | bash)", "Bash(wget * | bash)"]
  }
}
```

This is Claude Code's prompt-level permission system. It works on all platforms (Windows, Mac, Linux). It auto-approves common operations and blocks dangerous patterns. Combined with `--dangerously-skip-permissions` in the server, this means Claude operates autonomously but the deny list still prevents catastrophic commands.

**Layer 2: OS-level sandbox (macOS/Linux only, opt-in via `.claude/settings.local.json`):**

Provided as `.claude/sandbox.example.json`. Users copy the sandbox config into their local settings. This adds filesystem write restrictions, network domain allowlists, and OS-level enforcement that cannot be bypassed by prompt injection.

**What this gives us:**
- All platforms: permission allow/deny lists provide tool-level safety
- macOS/Linux: optional sandbox adds OS-level isolation on top
- Windows: permissions-only protection (sandbox planned by Anthropic)
- No Windows-specific bugs from forced sandbox config (known issues with anthropics/claude-code#28880)

### 19.3 Platform-Specific Notes

**Windows (native, no WSL2):** Sandbox is not yet supported. Fall back to `--dangerously-skip-permissions` with clear documentation. This is Quinn's current platform.

**Windows (WSL2):** Full sandbox support. Recommend WSL2 for security-conscious Windows users.

**macOS/Linux:** Full sandbox support out of the box (Mac) or with one package install (Linux).

### 19.4 Updated server/index.ts

Remove `--dangerously-skip-permissions` from the hardcoded spawn args. Instead:

```typescript
// The sandbox configuration in .claude/settings.json handles permissions.
// On platforms without sandbox support (native Windows), users can add
// --dangerously-skip-permissions to their CLAUDE_FLAGS env var.
const claudeArgs = ['--dangerously-skip-permissions'];
// TODO: When sandbox support is confirmed working, remove this flag
// and rely on .claude/settings.json sandbox config instead.
```

**Pragmatic decision:** Ship with `--dangerously-skip-permissions` for now (it works everywhere), but also ship the sandbox configuration in `.claude/settings.json`. On platforms that support sandbox mode, the sandbox provides the real security layer. On Windows native, the flag is the fallback. Document both paths in README.

**Interaction between the two:** When both `--dangerously-skip-permissions` AND sandbox config are active, the sandbox still enforces OS-level restrictions. The flag skips Claude Code's *prompt-level* permission checks (the "allow this tool call?" dialogs), but the sandbox operates at the OS level and cannot be bypassed. This means: even with the flag, a sandboxed bash command cannot write outside allowed directories or reach disallowed network domains. The flag and sandbox are complementary, not contradictory.

**The migration path:** Once native Windows sandbox support ships, remove `--dangerously-skip-permissions` from the spawn args and rely entirely on sandbox + permission allowlists. Until then, the flag is necessary for Windows users and harmless on sandboxed platforms.

### 19.5 The Permission Modes Explained

Claude Code has six permission modes. The right one for Triptych depends on context:

| Mode | Use Case for Triptych |
|------|----------------------|
| `default` | First-time cautious users — prompts for everything |
| `acceptEdits` | Normal collaborative work — auto-approves file edits |
| `plan` | Read-only exploration — good for reviewing research state |
| `auto` | Best for autonomous work (Team/Enterprise/API plan only) — classifier evaluates each action |
| `bypassPermissions` | Full autonomous operation without sandbox — current default |

**Recommendation for shipped `.claude/settings.json`:** Don't set a default mode in the project settings. Let users choose via Shift+Tab cycling in the terminal. The sandbox settings (Section 19.2) provide the safety net regardless of permission mode.

---

## 20. Skills Architecture and Safety

### 20.1 The Skill/Tool/MCP Distinction

This must be crystal clear in both documentation and CLAUDE.md:

| Concept | What It Is | When to Use | Where It Lives |
|---------|-----------|-------------|----------------|
| **Skill** | Instructions Claude follows | Repeatable workflows, domain knowledge | `.claude/skills/*/SKILL.md` |
| **Tool** | A function Claude calls | Specific action (read file, run command) | Built into Claude Code |
| **MCP Server** | External process exposing tools | External system integration (CAS, APIs, search) | `.mcp.json` or `~/.claude.json` |
| **Agent** | Isolated Claude instance | Parallel work, context isolation, verification | `.claude/agents/*.md` |

**The composability pattern:** A skill orchestrates, MCP tools execute, and agents isolate. Example: the `/autonomous` skill tells Claude how to do research. During research, Claude calls sympy-mcp for computation. At verification checkpoints, Claude spawns the verifier agent.

### 20.2 tools.md — The Comprehensive Reference

`tools.md` is the single source of truth for what's available. Claude should read it at the start of every session where it needs to use tools.

**Updated CLAUDE.md reference:**
```
Always read `tools.md` before using display addons, workspace commands, or MCP servers you haven't used this session.
```

**tools.md structure:**

```markdown
# Triptych Tools Reference

## Display Addons
| Function | What it does | Quick example |
| `show_figure(fig)` | Matplotlib plot | `show_figure(plt.gcf())` |
| `show_plotly(fig)` | Interactive Plotly | `show_plotly(fig)` |
| ... | ... | ... |

For full display addon development: use `/triptych-displays` skill.

## Workspace Addons
| Workspace | Purpose | File |
| ... | ... | ... |

For full workspace development: use `/triptych-workspaces` skill.

## MCP Servers
| Server | What it provides | Example usage |
| sympy-mcp | Symbolic math | `mcp__sympy-mcp__simplify_expression(...)` |
| ... | ... | ... |

## Tool Lessons
Recurring issues and fixes. Read before using the tool.

### sympy-mcp
- [lesson if any]

### Three.js displays
- Update arrows in place (setDirection/setLength) — don't remove and recreate, causes flicker

### General
- Always `import sys; sys.path.insert(0, '.')` before importing Triptych modules
```

### 20.3 Tool Lessons in tools.md

**Where tool lessons go:**

| Lesson type | Where |
|-------------|-------|
| Recurring tool issue (>1 occurrence) | `tools.md` under "Tool Lessons" for that tool |
| One-time fix | Don't persist — the fix is in the code |
| Safety-critical | `.claude/rules/safety.md` |
| Skill-specific workflow lesson | The relevant skill's SKILL.md |
| General project insight | Auto-memory (Claude Code's built-in system) |

**The flow:**
1. Claude encounters a tool issue
2. First occurrence: fix it, don't persist
3. Second occurrence of the same pattern: add a note to `tools.md` under that tool's lesson section
4. If it's skill-related: add to the skill's SKILL.md instead
5. If it's safety-critical: add to `.claude/rules/safety.md`

**Why tools.md and not a separate file:** Claude already reads tools.md when using tools. Adding lessons to the same file means Claude sees the lesson right before using the tool — perfect progressive disclosure timing. No extra file to remember to check.

**Preventing bloat:** Cap the Tool Lessons section at 20 lines total. If it grows beyond that, consolidate (merge similar lessons) or graduate lessons into code changes. The consolidation instruction should be in `tools.md` itself: "If this section exceeds 20 lines, consolidate related lessons before adding new ones."

### 20.4 Finding and Vetting Skills Online

**Reputable sources (trust, but still review SKILL.md before installing):**
- `anthropics/skills` — Anthropic's official repo
- `anthropics/knowledge-work-plugins` — Anthropic's knowledge worker plugins
- `travisvn/awesome-claude-skills` — curated community list
- `VoltAgent/awesome-agent-skills` — large collection from verified publishers (Trail of Bits, Sentry, Vercel, etc.)

**Red flags when evaluating a skill:**
1. Shell commands (`bash`, `curl`, `wget`) that download or execute remote code
2. Instructions to read `.env`, `~/.ssh/`, credentials, or API keys
3. Network requests to unknown domains
4. "Ignore previous instructions" or other prompt injection attempts
5. Hidden characters (zero-width Unicode) in the SKILL.md
6. New/unverified GitHub accounts with no history
7. Skills that ask to modify `.claude/settings.json` or other config files

**The rule:** Always read the entire SKILL.md before installing. It's just markdown — you can read it in 30 seconds. If it contains anything you don't understand, don't install it.

**36% of skills scraped from an unvetted public registry (ClaWHub) contained prompt injection** in a 2026 Snyk study of ~4000 skills. Curated lists (like the ones recommended above) are significantly safer, but you should still review every SKILL.md before installing.

**One more red flag the checklist misses:** Skills that write to `.claude/rules/` or `.claude/agents/`. A skill creating a new auto-loading rule is a persistence mechanism — it can inject instructions that load every future session.

### 20.5 Creating New Skills

When Claude needs a workflow it doesn't have a skill for, it should build one:

1. Identify the repeatable pattern
2. Write a SKILL.md with clear name, description (including trigger phrases), and instructions
3. Place in `.claude/skills/[name]/SKILL.md`
4. Test it works — invoke via `/name` and verify behavior
5. If it's Triptych-generic (not user-specific), keep it in the project. If it's personal, put it in `~/.claude/skills/`.

**Skill quality checklist:**
- Description includes both what it does AND when to trigger (<1024 chars)
- Body under 500 lines
- Code examples for every key operation
- References to supporting files/docs rather than inlining them
- No secrets, paths, or personal data in the skill

---

## 21. Updated CLAUDE.md (Final with tools.md and first-boot)

Add these lines to the proposed CLAUDE.md from Section 16:

After "## Extending Triptych":
```markdown
## Tools Reference

Always read `tools.md` before using display addons, workspace commands, or MCP servers you haven't used this session. It includes usage examples and known issues for each tool.

## Installing Skills from External Sources

Only install skills from trusted sources (Anthropic official repos, verified publishers). Always read the entire SKILL.md before installing — 36% of community skills contained malicious instructions in a 2026 security audit. If you need a workflow that doesn't exist, build the skill yourself.
```

This adds ~8 lines, bringing the total CLAUDE.md to ~83 lines.

### 21.1 Total Always-On Instruction Budget

| Source | Lines | Approx Tokens |
|--------|-------|---------------|
| CLAUDE.md | ~83 | ~900 |
| `.claude/rules/safety.md` | ~5 | ~60 |
| `.claude/rules/first-boot.md` | ~5 (gate only) | ~60 |
| Auto-memory MEMORY.md | ~15 (index) | ~200 |
| Claude Code system prompt | ~50 instructions | ~5000 |
| **Total always-on** | **~158 lines** | **~6200 tokens** |

This is comfortably under the ~150-200 instruction budget for LLMs. The key is that skills, tool lessons, and detailed protocols only load when activated — they don't count against the always-on budget.

---

## 22. Updated Implementation Order

Add to Phase 1:
- Create `.claude/rules/first-boot.md`
- Create `.claude/settings.json` with sandbox config and permission allowlists

Add to Phase 2:
- Update `tools.md` with "Tool Lessons" section structure
- Update CLAUDE.md with tools.md reference and skill safety guidance

---

## Research Sources (New)

### Sandboxing and Permissions
- [Claude Code Sandboxing - Official Docs](https://code.claude.com/docs/en/sandboxing)
- [Claude Code Permission Modes - Official Docs](https://code.claude.com/docs/en/permission-modes)
- [Configure Permissions - Official Docs](https://code.claude.com/docs/en/permissions)
- [Claude Code Auto Mode (Anthropic Engineering)](https://www.anthropic.com/engineering/claude-code-auto-mode)
- [sandbox-runtime (GitHub)](https://github.com/anthropic-experimental/sandbox-runtime)
- [Docker Sandboxes for Claude Code](https://www.docker.com/blog/docker-sandboxes-run-claude-code-and-other-coding-agents-unsupervised-but-safely/)

### Skills and Security
- [Agent Skills Specification (agentskills.io)](https://agentskills.io/specification)
- [Equipping Agents with Skills (Anthropic Engineering)](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)
- [Snyk ToxicSkills Study (2026)](https://snyk.io/blog/toxicskills-malicious-ai-agent-skills-clawhub/)
- [Claude Code Skill Security Audit Guide (Repello AI)](https://repello.ai/blog/claude-code-skill-security)
- [anthropics/skills (GitHub)](https://github.com/anthropics/skills)
- [Trail of Bits Security Skills](https://github.com/trailofbits/skills)

### Settings and Configuration
- [Claude Code Settings - Official Docs](https://code.claude.com/docs/en/settings)
- [Claude Code Memory - Official Docs](https://code.claude.com/docs/en/memory)
- [Claude Code Skills - Official Docs](https://code.claude.com/docs/en/skills)
- [Anatomy of the .claude/ Folder (Avi Chawla)](https://blog.dailydoseofds.com/p/anatomy-of-the-claude-folder)

---

## Research Sources

### Anthropic Official
- [Prompting best practices (Claude 4.6)](https://platform.claude.com/docs/en/docs/build-with-claude/prompt-engineering/claude-4-best-practices)
- [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Building effective agents](https://www.anthropic.com/research/building-effective-agents)
- [Claude's character](https://www.anthropic.com/research/claude-character)
- [Claude's constitution](https://www.anthropic.com/constitution)
- [The assistant axis](https://www.anthropic.com/research/assistant-axis)
- [The "think" tool](https://www.anthropic.com/engineering/claude-think-tool)
- [Claude Code best practices](https://code.claude.com/docs/en/best-practices)
- [Building multi-agent research systems](https://www.anthropic.com/engineering/multi-agent-research-system)
- [Vision documentation](https://platform.claude.com/docs/en/build-with-claude/vision)
- [Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)

### CLAUDE.md and Prompting
- [Writing a Good CLAUDE.md (HumanLayer)](https://www.humanlayer.dev/blog/writing-a-good-claude-md)
- [How to Write a Good CLAUDE.md (Builder.io)](https://www.builder.io/blog/claude-md-guide)
- [Stop Bloating Your CLAUDE.md (alexop.dev)](https://alexop.dev/posts/stop-bloating-your-claude-md-progressive-disclosure-ai-coding-tools/)
- [Progressive Disclosure for AI Agents (honra.io)](https://www.honra.io/articles/progressive-disclosure-for-ai-agents)
- [Maximising Claude Code (Maxitect)](https://www.maxitect.blog/posts/maximising-claude-code-building-an-effective-claudemd)

### Human-AI Collaboration
- [CHI 2025: Assistance or Disruption? Proactive AI](https://arxiv.org/html/2502.18658v4)
- [MIT: When Humans and AI Work Best Together](https://mitsloan.mit.edu/ideas-made-to-matter/when-humans-and-ai-work-best-together-and-when-each-better-alone)
- [Developer Interaction Patterns with Proactive AI (Five-Day Field Study)](https://arxiv.org/html/2601.10253)
- [AI as Colleagues in Ideation (ACM)](https://arxiv.org/html/2510.23904v2)
- [Collaborating with AI Agents: A Field Experiment](https://arxiv.org/html/2503.18238v2)
- [Google PAIR Guidebook](https://pair.withgoogle.com/guidebook/)

### Self-Improvement
- [Karpathy's Autoresearch](https://github.com/karpathy/autoresearch)
- [Hermes Agent Self-Improving Framework](https://hermes-agent.nousresearch.com/docs/)
- [Self-Improving Coding Agents (Addy Osmani)](https://addyosmani.com/blog/self-improving-agents/)

### Deployment
- [Docker Dev Environments](https://docs.docker.com/desktop/features/dev-environments/)
- [GitHub Codespaces](https://docs.github.com/en/codespaces)
- [pixi (prefix.dev)](https://pixi.sh)
- [node-pty-prebuilt](https://github.com/daviwil/node-pty-prebuilt)

### Configuration and Open Source
- [.cursorrules vs CLAUDE.md vs AGENTS.md (The Prompt Shelf)](https://thepromptshelf.dev/blog/cursorrules-vs-claude-md/)
- [env-paths (Sindre Sorhus)](https://github.com/sindresorhus/env-paths)
- [Choose a License](https://choosealicense.com/licenses/)
