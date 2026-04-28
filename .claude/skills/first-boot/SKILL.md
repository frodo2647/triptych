---
name: first-boot
description: First-time Triptych setup — creates user config, recommends settings, gives a quick tour. Also handles stage-2 goal elicitation on every new session (seed research state, prime skills, offer background prep). Triggered automatically when CLAUDE.local.md doesn't exist; stage 2 can be invoked on demand at any time.
disable-model-invocation: true
---

# First-Boot Setup

Three branches:
- **Stage 0 — Fast-path.** If the user's first message is a substantive task (they came in to *work*, not to be onboarded), spawn a setup subagent in the background and stay engaged with the task on the main thread.
- **Stage 1 — Slow-path.** If the user came in cold (greeting, "what is this," vague intent), run the full guided setup ceremony.
- **Stage 2 — Per-session goal elicitation.** Runs at the start of any session. Asks what they want to do, seeds the research state, primes relevant skills, offers to do background prep while they review.

On first boot (no `CLAUDE.local.md`): pick Stage 0 or Stage 1 based on the rule below, then proceed to Stage 2. On subsequent sessions, only Stage 2 runs (or `/first-boot` invokes Stage 2 manually).

---

## Stage 0 — Fast-path (substantive first message)

### When to use

Use Stage 0 when **all** of these are true:
- `CLAUDE.local.md` does not exist (this is genuinely a first boot).
- The user's first message contains a substantive task — describes a problem, a domain, a goal, or asks for actual work. Heuristic: longer than ~20 words AND contains at least one domain noun (physics, math, ML, paper, derivation, prove, train, design, plan, etc.) OR a clear verb-of-action ("help me", "let's", "I want to", "build", "figure out").
- The first message is *not* a greeting, "what is this", "how do I get started", or similar onboarding prompt.

If any are false, fall through to Stage 1.

### Behavior

The user came here to work. Don't make them sit through ceremony. Two parallel tracks:

**Track A — Main thread (you):** Engage with the user's task immediately. Ask any clarifying questions you'd ask normally. Do the work. **Do not** mention setup is happening unless the user asks.

**Track B — Setup subagent (delegated):** Spawn a single Agent call to do all of Stage 1's setup work in the background. Use the `general-purpose` subagent type. The subagent prompt is below.

When the subagent returns (typically 30-90s later), surface a one-line summary to the user, naturally — *"(set up Triptych for math + physics in the background; pulled `/sympy` and `/paper-lookup`. Carrying on.)"* — without breaking conversation flow. If the subagent failed or had to ask a question, fall back gracefully (mention it took a one-line note for `CLAUDE.local.md`, ask the user the minimum needed to unblock).

### Subagent prompt (template)

```
Run Triptych first-boot setup non-interactively. The user came in with a working task — they're being helped by the main agent right now and you do all setup in the background.

User's first message: <verbatim copy>
Project root: <absolute path>
Auto-memory user profile (if any): <one-line summary or "none">

Tasks (do all of them, no clarifying questions back to the user):

1. Infer 1-2 primary domains from the first message and any user-profile memory. Pick from {physics, math, ml, infrastructure-or-decision, writing, data, design, other}. If unclear, pick "other" — don't ask.

2. Write CLAUDE.local.md to project root with:
   - ## User Profile (Experience: inferred or "unspecified")
   - ## Domains (the inferred 1-2)
   - ## Preferences (leave a one-line placeholder)

3. Invoke /skill-finder for each picked domain. **This is mandatory** — it's how Triptych grows into the user's specific sub-domain. Use the per-domain recommended-packages list in docs/internal/skill-sources.md as the trust gate. Install matches non-interactively. Skip ones that need explicit user consent — note them in the summary instead.

4. Compile an MCP-server recommendation list for the inferred domains (sympy-mcp, desmos-mcp, manim-mcp for math/physics; context7 for CS/ML; arxiv-latex-mcp, firecrawl for research). DO NOT auto-install MCPs (requires user-side `claude mcp add`). Just list them in the summary so the main agent can mention them when there's a natural pause.

5. If the user is on macOS or Linux, note in the summary that the sandbox config can be enabled by copying .claude/sandbox.example.json into .claude/settings.local.json. Don't do it automatically.

Return a single-paragraph summary in this format:

  Set up: domains=<x,y>; CLAUDE.local.md written; skills installed=<list or "none">; MCPs to suggest=<list>; notes=<anything that needed user attention>.

Do not ask the user questions. Do not interrupt the main thread. If a step genuinely fails, report it in the notes field of the summary and continue with the rest.
```

### After the subagent returns

- **Success path:** in your next natural turn, drop the one-line summary the subagent returned. Don't make a ceremony of it.
- **Notes field has items:** mention the relevant ones (e.g. "by the way, you'd benefit from `claude mcp add sympy-mcp --scope user` when you have a sec") at a natural pause — not mid-derivation.
- **Failure path:** treat as if Stage 1's CLAUDE.local.md write failed. Write a minimal CLAUDE.local.md yourself with `## Domains` set to "other" and continue. Don't let setup gaps block the user's task.

### What Stage 0 does NOT do

- The 7-step tour (panels, displays, five core commands). The user will discover these by using them; if they ask "what's this panel for," answer then.
- Settings recommendations beyond writing CLAUDE.local.md. Don't open `~/.claude/settings.json` discussions during a working session.
- Stage 2 goal elicitation. The user already stated the goal in their first message — that *is* the goal. Treat the working session as already started.

---

## Stage 1 — Slow-path (cold-start setup)

### 1. Greet and Explain

Tell the user what Triptych is (three-panel workspace for hard problems with AI — a workspace where you actually push back on the AI rather than just take its answer) and that you'll walk through a quick setup. Keep it brief — 2-3 sentences.

### 2. Ask About Their Work

Ask which domain(s) they work in (multi-select):

- **physics** — derivations, mechanics, EM, QM
- **math** — proofs, computation, analysis
- **ml** — training models, datasets, hyperparameters
- **other** — describe

Triptych ships mentor skills for physics / math / ml in v1. "Other" is
fine — `/skill-finder` will pull tactical skills from PRPM as needed.

Also ask about experience level — this shapes how you communicate. A
physics PhD gets different explanations than an undergrad.

### 3. Recommend Settings

Tell the user to verify these settings in `~/.claude/settings.json`:

| Setting | Recommended | Why |
|---------|-------------|-----|
| `autoMemoryEnabled` | `true` | Triptych learns from sessions |
| `autoCompactPercent` | `60` | Research sessions can be long |

The user can open the file manually or use Claude Code's settings UI. You cannot programmatically check or change these settings.

   **Sandbox (macOS/Linux only):** If the user is on macOS or Linux, recommend enabling the sandbox for additional security. Tell them to copy the sandbox config from `.claude/sandbox.example.json` into `.claude/settings.local.json`. On native Windows, sandbox is not yet supported — the permission allowlists in `.claude/settings.json` provide the security layer instead.

### 4. Recommend MCP Servers

Based on their domain, suggest relevant MCP servers:

| Domain | Servers |
|--------|---------|
| Math/Physics | `sympy-mcp`, `desmos-mcp` |
| CS/ML | `context7` |
| Research | `arxiv-latex-mcp`, `firecrawl` |
| All users | `firecrawl` (web search) |

Tell them to install with: `claude mcp add <name> --scope user`

Do NOT auto-install. Just recommend and explain what each does.

### 5. Create CLAUDE.local.md

Based on their answers, create a `CLAUDE.local.md` file in the project root:

```markdown
## User Profile
- Experience: [their answer]

## Domains
- physics
- math
- ml

## Preferences
[Any preferences they mentioned, or leave blank for them to fill in later]
```

The `## Domains` section drives Stage 2 skill priming. Future sessions
read it without re-asking.

### 5b. Surface domain mentor skills

For each picked domain that ships a mentor skill, name it once:

- physics → `/physics-in-triptych` is now active
- math → `/math-in-triptych`
- ml → `/ml-in-triptych`

Don't lecture about contents — the user can explore via the skill itself.

### 5c. Auto-invoke /skill-finder for tactical skills

For each picked domain, run `/skill-finder` against the per-domain
recommended-packages list in `docs/internal/skill-sources.md`. The
trust gate is the recommendation list; user can decline individual
fetches but the offer happens for each one.

**This step is mandatory and must actually fire.** The first trial
run of `/first-boot` skipped this step entirely — that's the failure
mode to avoid. Before moving to step 6, verify at least one
`/skill-finder` invocation has happened (or the user has explicitly
said "skip skills" — and even then, write that decision into
`CLAUDE.local.md` so future sessions don't keep asking).

If you find yourself about to advance to step 6 without having run
`/skill-finder` at all, stop and run it now. Domain mentor skills
(physics-in-triptych etc.) are necessary but not sufficient — the
tactical skill packages in `docs/internal/skill-sources.md` are
where Triptych adapts to the user's actual sub-domain.

### 6. Quick Tour

Show them the three panels work:
1. Run a quick display to show the display panel works:
   ```python
   python -c "
   import sys; sys.path.insert(0, '.')
   from displays import show_latex
   show_latex(r'E = mc^2', title='Welcome to Triptych')
   "
   ```
2. Explain: "The left panel is your workspace (files, drawing, writing). The middle shows my work. This terminal is how we talk."
3. Mention: "Drop files in `workspace/files/` to share them with me."

### 7. Teach the five core commands

Show them the canonical command set, briefly:

> Triptych has five commands shaped like the arc of doing research. You don't need to remember anything else — every other skill activates automatically when relevant or stays available for power users.
>
> ```
> /start    Begin a session — set the goal, pick mode (explore vs work)
> /explore  Generate ideas, survey, hypothesize — for "what should I ask?"
> /work     Do the work — derive, prove, compute, analyze (verifier on)
> /check    Push back at a milestone — challenge assumptions and conclusions
> /wrap     Close out — summarize, persist for next session
> ```
>
> Mnemonic: start → explore → work → check → wrap. If you're ever unsure where you are or what to do next, type `/triptych` — it reads where you are, asks what you're trying to do, and recommends a next move (without auto-deciding for you).

Don't lecture about what's inside each — they'll learn by using them.

### 8. Handoff to /start

Tell them they're set up and offer: *"Want to /start a session now? Or just dive in — natural-language phrasing works too ('let's derive X' picks up /work, 'I'm done for today' picks up /wrap)."*

If they say yes, invoke `/start`. If no, they can run it any time.

Do not repeat Stage 1 in future sessions. The existence of `CLAUDE.local.md` prevents re-triggering.

---

## Stage 2 — Per-session goal elicitation

Run this at the start of a session if the user opts in. Goal: go from "cold start" to "research state seeded + relevant skills primed + any cheap prep already running in the background" in under two minutes.

### 1. Ask the goal

Ask plainly: *"What are you trying to do this session? One sentence."*

Don't interrogate. You want the goal stated in the user's own words, not a multi-question interview. If they're vague ("explore some physics"), ask one follow-up to crystallize: *"What's the specific question or problem you want to get traction on?"*

Write their answer down verbatim — you'll pass it to `init_research()` in step 3.

### 2. Classify: exploration vs formalization

Based on the goal, pick one:

- **Exploration** — they're looking for direction, generating ideas, surveying a landscape, or deciding what to work on. Cues: "explore," "survey," "get oriented," "figure out what to," "just poke at."
- **Formalization** — they're committed to a specific problem and want to derive / prove / compute with rigor. Cues: "derive," "prove," "compute," "verify," "solve for," "saturate accuracy on."

If unclear, ask: *"Are we generating ideas, or working on a specific thing you've already picked?"*

This classification decides whether to seed the research state now (formalization) or wait (exploration — the PRD's "crystallize first" rule, CLAUDE.md §Research and Verification).

### 3. Seed the research state (formalization) or just the session (exploration)

If **formalization**, call `init_research(goal)` — it creates state.md + deps.json AND writes session.json with phase=formalization:

```python
import sys; sys.path.insert(0, '.')
from core.research import init_research
from displays.research import show_research
init_research("<their goal verbatim>")
show_research()
```

Confirm with the user: "I've seeded the research state with '<goal>' — visible in the display as 'Research State' (Alt+2)."

If **exploration**, skip init_research but still write the session so the SessionStart hook can surface the goal in future sessions:

```python
import sys; sys.path.insert(0, '.')
from core.session import write_session
write_session("<their goal verbatim>", phase="exploration")
```

The research state gets seeded later when the work crystallizes — that boundary is the agent's job to recognize, not to pre-commit.

### 4. Prime relevant skills

Read `CLAUDE.local.md` `## Domains`. For each picked domain that ships
a mentor skill, surface it first. Then add 2–4 task-relevant skills:

| Goal pattern | Skills to surface |
|---|---|
| Physics derivation | `/physics-in-triptych` first, then `/verifier` (when claims emit), `/think-rigorously` |
| Math proof / computation | `/math-in-triptych` first, then `/verifier`, `/think-rigorously` |
| ML training / sweep | `/ml-in-triptych` first, then `/autoresearch`, `/integration-design` |
| Formal investigation across any domain | `/scientific-method` orchestrates the loop |
| Literature survey | `/literature-review`, `/paper-lookup` |
| UI / design work | `/impeccable`, `/critique`, `/polish`; for displays add `/display-craft` |
| Engineering / CAD / circuits | `/integration-design` (for tool choice) |
| Anything with claims | `/verifier`, `/watcher` |

One-liner per skill. Don't repeat skill descriptions — the harness
already surfaces them.

### 5. Offer background prep

If there's anything cheap and obviously useful to do while the user reviews, offer it:

- **Data known and local?** Offer to read + profile it (`/data:explore-data` if the skill is installed, or just read + summarize).
- **Referenced papers?** Offer to pull abstracts via arxiv-latex-mcp.
- **Known dataset / dependency?** Offer to check it's installed / accessible.
- **Literature territory?** Offer to run a quick search and drop candidate papers in `workspace/files/`.

If nothing obvious, skip. Don't invent busy-work.

Ask before doing: *"Want me to [X] while you [review/think/get coffee]?"*

### 6. Human review checkpoint

Pause. Summarize what you've done + what you've queued up:

- "Goal: <verbatim>"
- "Mode: exploration / formalization"
- "Research state: seeded / deferred"
- "Skills I might use: X, Y, Z"
- "Background prep: running / none"

Ask: *"Ready to start, or adjust anything?"*

Don't proceed until they confirm. The point of the stage-2 flow is getting the goal right before committing — steamrolling past a misunderstood goal burns more time than the setup saved.

### 7. Start

When the user confirms, start the work. The phase determines default posture:

- **Exploration** — generate, compare, draw connections, surface questions. Don't verify. Don't seed research state yet. Do use `show_progress` to keep a live "what I'm doing" display.
- **Formalization** — emit claims for significant results, expect the verifier hook to nudge you to start `/loop 60s /verifier`, keep `show_research` live as the primary display.

Session state was persisted in step 3 (either by `init_research` for formalization or `write_session` directly for exploration). The next session's SessionStart hook will surface the goal + phase + staleness automatically — nothing more to do here.
