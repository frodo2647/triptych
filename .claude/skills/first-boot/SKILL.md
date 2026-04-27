---
name: first-boot
description: First-time Triptych setup — creates user config, recommends settings, gives a quick tour. Also handles stage-2 goal elicitation on every new session (seed research state, prime skills, offer background prep). Triggered automatically when CLAUDE.local.md doesn't exist; stage 2 can be invoked on demand at any time.
disable-model-invocation: true
---

# First-Boot Setup

Two stages:
- **Stage 1 — One-time setup.** Runs when `CLAUDE.local.md` doesn't exist. Creates user config, recommends settings, gives a quick tour.
- **Stage 2 — Per-session goal elicitation.** Runs at the start of any session if the user opts in. Asks what they want to do, seeds the research state, primes relevant skills, offers to do background prep while they review.

If this is a first boot (no `CLAUDE.local.md`), run Stage 1 followed by Stage 2. If `CLAUDE.local.md` exists and the user invokes `/first-boot` manually, skip straight to Stage 2.

---

## Stage 1 — One-time setup

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

This is **not optional** — it's how Triptych grows into the user's
specific sub-domain on first contact. If the user wants to skip,
they say so once and you move on.

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
