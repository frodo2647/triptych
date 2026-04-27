# Triptych v2 — Product Requirements Document

*North star vision. Not implementation specs — the ideal we're building toward.*

## The Problem

Claude Code works because compilers close the feedback loop. The AI writes code, runs it, sees errors, iterates. This loop is why AI coding tools are years ahead of AI tools for everything else.

Hard problems — math, physics, engineering, research — have no compiler. A wrong derivation looks exactly like a right one. A plausible formula doesn't crash. Today, every researcher using AI is flying blind: they generate work, eyeball it, hope for the best. The AI itself has no way to know if it's wrong.

The data confirms this matters. On graduate-level STEM problems (GPQA Diamond), frontier models get 17-40% of questions wrong depending on the model. On research-level problems, error rates reach 75-95%. Worse: as difficulty increases, errors shift from computational mistakes (which are easy to catch) to conceptual ones (wrong approach, misapplied theorem, flawed reasoning). On hard problems, ~60-70% of errors are strategic — the AI set up the wrong problem entirely.

And the research is clear on one more thing: **asking an AI to "check its own work" does not reliably help.** It rubber-stamps wrong answers and "corrects" right ones at similar rates (Huang et al., 2023). Self-verification without external grounding is theater.

There's a second piece, less about correctness and more about the human side. Recent research on hybrid intelligence ([WSJ piece on the cyborg study](https://www.wsj.com/tech/ai/is-ai-smarter-than-humans-cyborg-956e0f0e); MIT cognitive-offloading work) suggests roughly 5–10% of human-AI teams actively get sharper from collaboration — the ones who push back, demand evidence, ask the AI to argue against itself. The rest atrophy: the AI eliminates friction, and learning gets eliminated with it. Most chat-style AI surfaces are designed for the second mode (one prompt, one fluent answer, accept). Triptych is shaped for the first — visible verification, surfaced assumptions, a workspace where the human stays in the loop visibly rather than nominally.

Triptych v2 closes the loop on both axes — correctness and engagement.

## The Vision

Triptych is the environment where humans and AI collaborate on hard problems. It provides:

1. **A workspace** where the human thinks — drawing, annotating, reading, writing
2. **A display** where the AI shows its work — derivations, plots, simulations, verified results, surfaced assumptions, claim-verification timelines
3. **A terminal** where the AI operates — Claude Code with full filesystem access
4. **A verification system** that catches errors before anyone relies on them, with per-claim verification (continuous), cross-verification (milestones), red-team challenge (milestones), and assumption-surfacing (`whats-missing`, milestones)
5. **A proactive watcher** that observes, assists, and intervenes with judgment
6. **A research state** that tracks what's been tried, what's established, and what's next
7. **A mentor layer** that surfaces best-practice methodology in domains the agent has skills for — not just executing requests, but framing rigor patterns, calling out canonical pitfalls, and steering toward the right tools for the work

The human and AI work like good colleagues. Sometimes they collaborate in real time. Sometimes one works while the other watches. Sometimes the AI works independently and reports back. The system adapts to whatever the moment requires.

### Triptych vs autoresearch

Triptych is shaped for problems where there is no single number going down — derivations, conceptual work, design decisions, anything where the work is partly figuring out what counts as the right answer. Karpathy's autoresearch is the right fit for the inverse case (clear metric, fast eval loop, one file to optimize); Triptych ships an `/autoresearch` skill that can run inside it for metric-shaped subproblems. The two compose; they don't compete.

### Push-back as a first-class mode

Beyond correctness, Triptych is shaped to encourage the *kind* of human-AI interaction that actually makes the human sharper. Hybrid-intelligence research ([WSJ piece on the cyborg study](https://www.wsj.com/tech/ai/is-ai-smarter-than-humans-cyborg-956e0f0e); MIT cognitive-offloading work) suggests roughly 5–10% of human-AI teams actively get sharper through collaboration — the ones who push back on the AI, demand evidence, ask it to argue against itself. The rest atrophy: the AI eliminates friction and learning gets eliminated with it. Most chat-style AI surfaces are designed for the second mode (one prompt, one fluent answer, accept). Triptych is shaped for the first — visible verification, surfaced assumptions, milestone red-team passes, a workspace where the back-and-forth is structural rather than something the user has to remember to do.

## Core Principles

### The AI must not make mistakes, whether or not the human is watching.

This is the central design constraint. A brilliant colleague who is unreliable is worse than a mediocre one who is careful. Every claim the AI makes must be checked — not by the AI re-reading its own reasoning, but by an independent process that can't be contaminated by the same flawed logic.

### The framework is domain-agnostic. Addons are domain-specific.

The core system — verification architecture, watcher, research state — knows nothing about physics or mathematics. It knows about *claims*, *evidence*, *assumptions*, and *verification*. A math addon knows about SymPy and dimensional analysis. A biology addon knows about sequence alignment and statistical tests. A circuit design addon knows about SPICE simulations. The core serves all of them.

The whole system is oriented toward STEM, but no single discipline is privileged in the architecture.

### The system must be invisible when working correctly.

The researcher should be able to forget the system is running. Verification happens in the background. The watcher observes silently. Results appear without interruption. If the human is ever aware of verification overhead — latency, UI clutter, background noise — something is broken.

v2 introduces a lot of AI activity: continuous verification, periodic workspace watching, cross-verification passes, research state maintenance. None of this should be perceptible during normal operation. The system surfaces information only when something is wrong or when the human asks. Everything else is silent. This is a hard constraint, not a nice-to-have — it's the difference between a colleague and an interruption.

### Do the simple thing that works.

Files, not databases. Markdown, not schemas. HTML from CDN, not npm builds. If it can be a file write, it should be. This is what made v1 work and what makes the system extensible — Claude can build new tools on the fly because the tools are just files.

### Lessons from autoresearch.

Karpathy's autoresearch succeeded by constraining the search space (one file, one metric, fixed time budget), making evaluation immutable (the agent cannot modify the thing measuring it), and designing for unsupervised continuous operation. These principles directly inform our verification and autonomous operation design.

## The Verification System

### Why this architecture

A CAS (Wolfram, SymPy) catches roughly one-third of LLM math errors — the computational ones. That's necessary but not sufficient. Cross-verification (solving a problem multiple ways) adds another layer. But neither works if the verifier is contaminated by the working agent's reasoning.

The key insight comes from Claude Code's auto-mode: the oversight agent sees only tool calls and user messages, never the model's internal reasoning. This prevents the overseer from being persuaded by the same logic it's supposed to check. We apply the same principle to mathematical verification. Critically, this also prevents the verifier from being primed by the same flawed logic — if you send the full derivation, a convincing-but-wrong argument biases the verifier toward "yes." Isolating claims forces independent evaluation.

### Who verifies whom

Verification always happens. Who does it depends on who's working:

| Who's working | Who verifies | How |
|---|---|---|
| **AI working (autonomous)** | Verifier agent | Async in real time as claims are emitted, plus full verification pass at end |
| **AI working (collaborative)** | Verifier agent | Same — the human should NOT have to catch AI mistakes |
| **Human working** | The AI (watcher) | Reads workspace snapshots, catches errors the same way the verifier checks the AI |
| **Both working simultaneously** | Both verification paths run | Verifier agent checks AI claims; watcher checks the human's workspace. Each side is independently verified. |

The principle: **whoever is not doing the work is checking the work.** The human never has to be the verifier for the AI. The AI watches the human. A separate agent watches the AI. Nobody works unchecked.

### How it works

**The working agent** solves problems normally, showing its work in the display panel. As it works, it emits structured **claims** — the key mathematical or scientific assertions it's making:

```
CLAIM: ∂L/∂θ = -mgl sin(θ)
CONTEXT: partial derivative of L = ½ml²θ̇² - mgl cos(θ) with respect to θ
DEPENDS: [Lagrangian derivation, no-friction assumption]
```

The claim is the assertion. The context is one line describing what operation produced it — enough for the verifier to know *how* to check it, without enough narrative to be persuasive. This is the "what was done," not "why it's right." The dependencies list what prior claims or assumptions this claim rests on — forming a logical chain that enables invalidation propagation (see Research State below).

Why one line of context and not zero? Without any context, the verifier would have to re-derive from scratch every time to know if a claim is correct — slow and defeats the purpose. But too much reasoning and you're back to the contamination problem. One line is the sweet spot: it tells the verifier *what kind of step this is* so it knows *how* to check it (a routing hint), without providing enough narrative to be persuasive.

**The verifier agent** (Sonnet, by default) receives only the claims and the original problem statement. Never the working agent's full reasoning. For each claim, it decides how to verify:

- Symbolic recomputation via CAS (SymPy, Wolfram)
- Numerical spot-check (plug in concrete values)
- Dimensional analysis
- Limiting case evaluation
- Comparison against known results
- Or simply reasoning about it independently, when computation isn't appropriate

The verifier has access to computational tools but is not made of them. It uses judgment about which checks are appropriate for each claim. A symbolic differentiation gets verified by SymPy. A symmetry argument gets evaluated conceptually. A numerical estimate gets a sanity check.

**If everything passes** — the human never knows verification ran. The system is silent when things are correct.

**If something fails** — the issue is surfaced back to the working agent, which re-examines and corrects. The human can see verification status via the terminal/chat interface if they want, and critical errors (e.g., algebra mistakes) can be pushed as notifications even when the human isn't actively watching.

**If the verifier is uncertain** — the claim is flagged as unverified rather than passed or failed. The working agent can decide whether to proceed (logging the uncertainty in the research state) or pause to investigate. Uncertainty is not failure — some claims are genuinely hard to verify, and the system should be honest about that rather than forcing a binary.

**Cross-verification** runs on final results or key conclusions — both end-of-derivation results and important intermediate results that the rest of the work will build on. A second pass independently re-derives the result via a different method. If both approaches converge, confidence is high. If they diverge, both approaches are presented with their reasoning. Cross-verification requires the result to exist before an alternate approach can be attempted, so it naturally runs at milestones rather than on every claim.

**Red-team challenge** runs at milestones too, but answers a different question than verifier and cross-verification. Verifier asks "is this claim true?" — cross-verification asks "does an independent derivation agree?" — red-team asks "is there a substantive case against this conclusion?" An isolated `redteam` subagent reads the work and produces a structured report with one of four verdicts: nothing-substantive / minor-presentational / issues-worth-addressing / blocking-concerns. The subagent is calibrated against false positives — empty findings is the right answer when the work is sound, and the prompt repeatedly names "inventing issues to look thorough" as the failure mode. An agent that always finds problems is just as useless as one that never does; the calibration is structural, not nominal.

**Whats-missing** is the sister pass to red-team. Where red-team challenges what's *there*, whats-missing surfaces what *isn't* — unstated load-bearing assumptions, counterfactuals that would change the answer, out-of-scope gaps the analysis silently elided. Hard problems often fail at the assumption layer rather than the algebra layer; whats-missing is the structural counterpart to that observation. Same calibration discipline as red-team: empty findings is a valid, encouraged answer.

### Verification timing

During autonomous operation, verification runs **async in real time** — the verifier agent (Sonnet) processes claims as the working agent emits them, running in parallel rather than blocking. Cross-verification runs at milestones — when a significant result is established, not on every step.

During collaborative work (the AI's turn), the same pattern applies. The human doesn't wait for verification and doesn't have to perform it — that's the verifier's job.

### Verifier-agent communication

Communication is file-based, consistent with the system's filesystem philosophy. The verifier writes results to a verification log. The working agent checks the log between steps — the way you'd glance at a colleague's feedback between paragraphs.

The working agent's step loop:
1. Do work, emit claims
2. Check verification log for flags from previous claims
3. If flagged: address the issue before continuing
4. If clear: proceed to next step

The verifier also monitors the working agent's display output — not the reasoning, just the visible results. If new mathematical content appears in the display with no corresponding claim emitted, the verifier flags it. This doesn't require understanding the chain of thought — it's a volume check: "new equations appeared but no claims were filed." This catches the failure mode where the working agent quietly stops emitting claims and the verifier has nothing to check.

Worst case, the working agent is one step ahead of the verifier when an error is caught. That's acceptable — one step of wasted work is cheap compared to an entire unchecked derivation.

### Design constraints

- The verifier never sees the working agent's chain of thought
- The verifier cannot modify the problem statement or success criteria (immutable evaluation, per autoresearch)
- Speed matters more than cost — Sonnet is chosen for the continuous layer because it's fast, not because it's cheap
- The verifier is an intelligent agent with CAS tools, not a rigid pipeline — it decides how to check each claim based on what kind of claim it is

## The Proactive Watcher

### What it does

The main agent periodically reads snapshots of the human's workspace — screenshots and context metadata (selected text, annotations, page numbers, canvas state). From these, it builds an understanding of what the human is working on.

The watcher runs via a `/loop` command at a user-configured interval. The human controls how active it is — from silent observation to active intervention.

### Behavior model

The watcher uses judgment, calibrated by the human's preferences:

- **Obvious errors** (algebra mistake, dropped sign, unit mismatch): speak up immediately, regardless of preference. If you're 100% sure, say so.
- **Possible errors or concerns**: log them. Surface only if the human wants active intervention.
- **Ideas and observations** ("this looks like it might connect to conservation of angular momentum"): log silently. Surface only if the human asks or wants proactive suggestions.
- **Background work**: when the watcher has a hunch, it can run checks, search for references, or test limiting cases in the background. Results are logged, not surfaced, unless the human wants them.

The human communicates preferences naturally — "be more active," "shut up for a while," "tell me if you see anything wrong." The AI remembers these across sessions.

On first use, the system runs a brief onboarding conversation: what kind of work the human does, how much intervention they want, whether they prefer to be told about possible errors or only certain ones. This establishes a baseline that natural-language adjustments refine over time.

### Watching the human's errors too

The verification system checks the AI's work. The watcher checks the human's. Same principles apply — when the watcher sees the human make a sign error on a whiteboard or set up an integral incorrectly, it should flag it (or log it, depending on preferences). The AI is a colleague, not just a tool — colleagues catch each other's mistakes.

An honest caveat: catching errors in the human's work is harder than checking the AI's claims. Handwriting recognition at the precision needed to catch a dropped negative sign is at the edge of what vision models can do reliably today. The system's accuracy will vary by workspace type — typed text in a code editor or PDF annotations are much more readable than freehand whiteboard sketches. The system should build on what existing models can do and improve as vision capabilities improve, rather than promising perfection from day one. The principle is sound; the reliability will be workspace-dependent.

### Watcher preferences

Preferences are stored in the project's CLAUDE.md file — the same place all project-level AI instructions live. This means they're version-controlled, human-readable, and naturally scoped to the project.

Researchers have nuanced needs beyond "be more active." Real preferences look like: "flag anything about boundary conditions but not algebra," "only interrupt me if you're very confident," "I'm in exploratory mode right now." The onboarding conversation establishes a baseline, and the AI refines its understanding over time from natural-language adjustments. Each project gets its own agent (clone the repo per project), so preferences are project-scoped.

## Exploration and Formalization

### Two phases of research

Most PRDs for research tools assume the human arrives with a well-formed problem. In reality, the hardest part of research is often figuring out *what to ask*. The system must support both phases:

**Exploration** — the problem isn't yet defined. The human is sketching, reading, circling things, thinking out loud. There are no formal claims to verify. The goal is to find the right question.

**Formalization** — the problem is defined. The human (or AI) is deriving, computing, proving. Claims are being made and need verification. The goal is to answer the question rigorously.

These are analogous to plan mode vs. coding mode in Claude Code. The system behaves differently in each, but the transition is gradual, not a hard switch.

### Exploration mode behavior

- The watcher is **Socratic, not verificatory**. It asks questions, suggests framings, connects ideas. The formal verification system doesn't run (no claims to verify). But basic error-catching still applies — if the human writes 2+2=5, the watcher says so. The distinction is between formal verification (off during exploration) and common-sense error catching (always on).
- The AI suggests related problems, analogies, alternative approaches. Background work is generative — searching for connections, relevant results, related prior work — not verificatory.
- No claims are emitted. No verification runs. No dependency tracking. There's nothing formal to verify yet.
- The research state tracks: questions being explored, framings considered, connections found, relevant references.

### Formalization mode behavior

- The watcher shifts to error-checking. Claims are emitted and verified.
- The full verification system activates: Sonnet verifier, CAS tools, cross-verification at milestones.
- The research state tracks the seven fields: goal, questions, assumptions, attempts, established results, open threads, next step.
- Dependency tracking at the milestone level.

### The transition

The transition from exploration to formalization is a **crystallization** — the exploratory work becomes the foundation for formal work. The AI acts like a good research mentor at this boundary: "Before we dive into the derivation, can we state clearly — what exactly are we trying to show?"

This prompt for a clear research question or hypothesis is not the system *requiring* formality — it's the AI encouraging best practices. A well-stated research question seeds the Goal field of the research state and gives the verification system something to evaluate against. The questions and framings from exploration become the Assumptions and sub-Questions of the formal investigation.

The transition happens gradually. As the work gets more formal — equations appear, derivations begin — verification starts activating. The human can also make it explicit: "I'm still exploring, don't verify yet" or "let's formalize this." But the system should mostly detect the shift naturally rather than requiring a mode switch.

### Both phases in autonomous operation

When the AI works autonomously, it follows the same two phases. Given an open-ended problem, it explores first — surveying approaches, identifying relevant tools and results, forming a strategy. Then it crystallizes into a research question and formalizes. The research state captures the full trajectory from "what should we even ask?" to "here's the verified answer."

## Autonomous Operation

### Not a separate mode

Autonomous operation is the same system with the human not actively drawing. Like a good colleague who can work independently when you hand them a problem and step away.

The working agent takes a problem, uses the same verification system, maintains the same research state, and produces verified results. The human can check in anytime — the display shows current progress, the research state shows what's been tried.

### What makes autonomy work

From autoresearch: autonomous operation succeeds when the scope is constrained and evaluation is clear. "Derive the equation of motion for this system" has a verifiable end state. "Explore quantum mechanics" does not.

The system should:
- Accept a concrete problem statement
- Work until it solves it or exhausts its approaches
- Not pause for confirmation mid-work (but log everything)
- Maintain the research state so the human can review the full trajectory
- Use verification at every step — autonomous operation without verification is just unsupervised hallucination

## Research State

### The universal structure

Good research across all STEM disciplines follows the same meta-level structure. The research state tracks this, not domain-specific content:

**Goal** — What we're trying to show, find, build, or understand.

**Questions** — The problem decomposed into sub-problems, each with a status (open / in-progress / blocked / resolved). Mathematicians call them lemmas, physicists call them subproblems. Same structure.

**Assumptions** — What we're taking as given. Each has a source (given, empirical, approximation, conjecture) and a confidence level. When stuck, revisit assumptions.

**Attempts** — What was tried, what the outcome was, why it was abandoned. Prevents revisiting dead ends. Often contains the seed of the eventual solution.

**Established Results** — Intermediate results that have been verified and won't change. Proven lemmas, conservation laws confirmed, benchmarks met. The hard facts of the session.

**Open Threads** — Active fronts of investigation, what's blocking each, priority relative to the main goal.

**Next Step** — Current approach, last result, intended next action. The warm-restart context for resuming after a break.

### Canonical extensions

The seven fields are the core. Addons may add section-level fields when the work genuinely needs them — but the extension pattern is explicit, not silent.

**Plan** is the first canonical extension, from the trial-1 MNIST study (see `docs/internal/trial-1-report.md` §1). Used when a session breaks down into stage-by-stage work where each stage is big enough to need its own slot (e.g. "Stage 1: SGD baseline → Stage 2: AdamW → Stage 3: regularization"). Implemented as an eighth section in `state.md` with a matching `type: plan` node in `deps.json`; `core.research.set_plan` / `advance_plan` / `mark_plan_done` are the helpers.

Extensions should follow two rules:

1. **Name the extension in the addon's docstring and in this PRD section.** No silent schema drift. If triptych's own `core/research.py` grows an extension, its `SECTIONS` constant and `STATE_TEMPLATE` update together, and the PRD is updated in the same commit.
2. **Extensions are fields, not replacements.** Don't reorder the seven; don't merge two. Append.

The reference implementation for Plan lives in a separate trial-1 fork outside this repo (see `docs/internal/trial-1-report.md` for the experiment context); triptych core itself stays at seven fields until an extension is genuinely needed here.

### Logical dependency graph

Every established result depends on assumptions and prior results. This is how mathematicians already think: theorems depend on lemmas, which depend on axioms. Physicists chain derivation steps. Engineers chain design decisions. The dependency structure is universal.

The dependency graph is stored as a **JSON file** (`dependencies.json`), separate from the narrative research state. This is the right tool for the job — parsing dependency relationships from prose is fragile; a node-edge graph is trivially machine-parseable:

```json
{
  "nodes": {
    "A1": { "type": "assumption", "label": "No friction", "status": "active" },
    "A2": { "type": "assumption", "label": "Rigid rod", "status": "active" },
    "R1": { "type": "result", "label": "L = ½ml²θ̇² - mgl cos(θ)", "status": "verified" },
    "R2": { "type": "result", "label": "θ̈ + (g/l)sin(θ) = 0", "status": "verified" }
  },
  "edges": [
    { "from": "A1", "to": "R1" },
    { "from": "A2", "to": "R1" },
    { "from": "R1", "to": "R2" }
  ]
}
```

**Automatic invalidation propagation** is a simple recursive walk: when assumption A1 is invalidated, find all edges from A1, flag those results, then find all edges from those results, flag their dependents. This continues down the chain until all downstream results are flagged for re-verification.

The JSON also renders naturally as a **visual graph** in the display panel — a d3 node-edge diagram showing the structure of the investigation. The human can see the shape of their reasoning, what depends on what, and where the weak points are.

Two files, each doing what it's good at:
- **`research-state.md`** — the human-readable narrative (goal, questions, attempts, established results, next step)
- **`dependencies.json`** — the machine-parseable structure (nodes, edges, status, propagation)

The working agent writes both when it establishes a result. No sync issues since they're written at the same time. The markdown is for thinking. The JSON is for structure. The d3 visualization is for seeing.

### Implementation

The research state is a markdown file the working agent maintains as it works. Not a database, not a formal schema — a living document. Domain-specific addons can layer richer views on top (dependency graphs for proofs, experiment trackers for lab work).

Claims feed into established results once verified. Failed verifications feed into attempts. Dependency chains link claims to their foundations. The research state, verification system, and dependency tracking are naturally coupled — three aspects of the same underlying structure.

## Core vs. Addons

The system has a clear boundary between what's universal and what's domain-specific:

**Core (domain-agnostic):**
- Verification architecture (claim emission, verifier agent protocol, cross-verification)
- Watcher system (snapshot reading, intervention logic, preference management)
- Research state structure (the seven fields above)
- Dependency graph with automatic invalidation propagation
- Autonomous operation loop
- Exploration / formalization phase model

**Addons (domain-specific):**
- Verification tools (SymPy for math, Wolfram for symbolic computation, SPICE for circuits)
- Workspace types (whiteboard for drawing, PDF viewer for reading, editor for writing)
- Display types (LaTeX for equations, plotly for data, 3D viewers for models)
- Domain-specific research state views (proof tree visualization for math, experiment log for lab work, design decision matrix for engineering)

A mathematician, a physicist, a biologist, and an engineer should all be able to use the same core system with different addons. The core handles the *structure* of collaboration and verification. Addons handle the *content* of specific disciplines.

## Spawned-Agent Architecture

Triptych runs work in parallel using a `/loop + Task` pattern (chosen deliberately over Anthropic's experimental Agent Teams — see `docs/internal/spawned-agents.md` for the trade-off; key reasons are 3× token cost for ongoing drainers, no `/resume` support for in-process teammates, and split-pane mode requiring tmux/iTerm2 which doesn't fit Quinn's Windows environment). Spawned work splits into two layers:

- **Peer-level** (long-lived `/loop` drainers, sibling stature to the main agent): `verifier`, `watcher`, `dashboard`. They drain a filesystem queue continuously while a phase of work is active, and communicate with the main agent only through queue files. The verifier loop additionally spawns `Task` subagents per claim for genuine context isolation.
- **Below-level** (one-shot `Task` subagents, dispatched by the main agent for a bounded question): `redteam`, `whats-missing`, the per-claim verifier subagent. Returns a summary, exits.

The `level: peer | below` field in each `SKILL.md` frontmatter makes this explicit. The choice of layer is a lifecycle question (ongoing vs one-shot), not an independence question — both layers run with fully isolated context windows (subagents inherit zero conversation history; the prompt is the entire context).

## The Mentor Layer

A research mentor is more than an executor. Triptych ships domain-specific mentor skills (`/physics-in-triptych`, `/math-in-triptych`, `/ml-in-triptych`) plus cross-domain rigor patterns (`/think-rigorously`, `/scientific-method`) and adversarial primitives (`/redteam`, `/whats-missing`). The mentor layer's job is to surface methodology proactively — calling out the dimensional analysis the user almost skipped, naming the canonical pitfall about to be hit, suggesting the right tool (`sympy-mcp`, `desmos-mcp`, `manim-mcp`) for the work — rather than waiting to be asked.

This compounds with the verification system. The verifier catches errors that have already been made. The mentor layer surfaces patterns that prevent them. Together they cover both halves of "someone is always checking": before the work, the mentor frames it; during the work, the verifier checks it; at milestones, red-team and whats-missing challenge it.

## Default Displays During Work

Three display defaults make the AI's reasoning visible by default rather than implicit:

1. **`show_research` or `show_progress`** — one of these stays live during work. `show_research` for formalization (state.md narrative + dependency graph); `show_progress` for exploration (live step / metric / decision panel). The human should never have to ask "what are you doing right now?"
2. **`show_assumptions`** — when the work depends on non-trivial assumptions, render them with status badges so the human can catch the wrong one before it becomes load-bearing. Pulls assumption nodes from the dependency graph or takes an inline list.
3. **`show_claims_status`** — once `emit_claim` is in play, this is the verification timeline (pending pulses, verified greens, failed reds). Refresh after `read_verification_results()`.

The principle: hard problems usually fail at the assumption layer, not the algebra layer. Displays that surface assumptions and claim status make the load-bearing parts of reasoning *visible* rather than buried in prose. This is the structural answer to the WSJ-piece observation that AI atrophies users when friction disappears — visible reasoning is friction by design.

## Integration Layer

Triptych has a clear three-tier addon architecture (formalized April 2026):

- **Workspaces** (`workspaces/`): HTML files the human works in (whiteboard, editors, PDF viewer, spreadsheet, CircuitJS).
- **Displays** (`displays/`): Python modules that render dark-themed output to `workspace/output/` (matplotlib, plotly, KaTeX, Three.js, research state, progress, assumptions, claims, derivation, table, code, autoresearch, CircuitJS waveforms).
- **Integrations** (`integrations/`): Python bridges to external tools that own their own UI. Two patterns — `EmbeddedTool` (own iframe in a workspace tab; CircuitJS is the reference) and `ExternalTool` (link out with a summary panel; Weights & Biases is the reference). The `/integration-design` skill helps decide between them. The integrations layer is explicitly *out* of `core/` — anything that reaches the network or holds credentials lives here, not in core.

Core stays lean. Domain knowledge lives in skills, addons, and integrations.

## Skill Surface

By April 2026 Triptych ships ~40 skills covering: peer/below spawned agents (verifier, watcher, dashboard, redteam, whats-missing); domain mentors (physics, math, ml); cross-domain rigor (think-rigorously, scientific-method); workflow primitives (autonomous, autoresearch, literature-review); display craft (display-craft, display-design-workflow, triptych-displays); workspace and integration design (triptych-workspaces, integration-design); the user-controlled feedback loop to the maintainer (field-report); first-boot setup with domain elicitation. Plus eight bundled K-Dense knowledge skills for scientific work (scientific-writing, scientific-critical-thinking, scientific-visualization, paper-lookup, citation-management, peer-review, hypothesis-generation, sympy). For tactical sub-skills outside the bundle, `/skill-finder` pulls from PRPM with K-Dense fallback.

## What Exists Today (v1 + v2 progressive)

- Three-panel system: workspace, display, terminal
- Filesystem as communication channel
- 30-second snapshot capture from workspace
- ~9 workspace addons, ~16 display addons (including assumptions + claims_status, April 2026)
- 2 integrations (CircuitJS, W&B); EmbeddedTool / ExternalTool reference base classes in `integrations/`
- Auto-reload on file changes
- Full Claude Code integration with filesystem access
- Dark theme, file management, drag-and-drop
- Verification system: `core/verify.py` claim/result/flag log + `read_verification_results` polling; per-claim verifier subagent via Task; cross-verifier (Opus) for milestones
- Watcher loop reading workspace snapshots; dashboard loop draining display request queue
- Research state: 7 canonical sections + Plan extension; `state.md` narrative + `deps.json` graph with d3 rendering and automatic invalidation propagation
- Session persistence via `core/session.py` (goal, phase, last-active)
- SessionStart / UserPromptSubmit / PreToolUse / Stop hooks for state injection and verifier-loop nudging
- ~40 skills + 8 bundled K-Dense knowledge skills
- Mentor layer: domain skills + rigor patterns + redteam/whats-missing milestone primitives
- OpenCode compatibility (PTY-hosted; bundled skills work cross-agent with caveats)

The remaining v2 work is mostly polish, hero GIF capture for launch, and pushing the branch to origin.

## Competitive Position

The competitive landscape has three tiers:

**Math provers** (Harmonic $1.45B, Axiom $1.6B, DeepMind AlphaProof): Narrow tools for formal theorem proving in Lean, primarily pure math. No physics, no workspace, no collaboration. Triptych isn't competing here — it's solving a different problem.

**Computational notebooks** (Wolfram Notebooks, Observable, Jupyter with AI plugins): These are the more interesting comparison. They're where researchers actually work today. But none of them independently verify the AI's claims. The AI generates a result, it appears in the notebook, and the researcher trusts it or manually checks it. That's the "flying blind" problem.

**Chat interfaces** (Claude, ChatGPT, Gemini in a browser): The current default for most researchers. Copy-paste between a chat window and their actual work. No shared workspace, no persistent state, no verification.

Triptych's core differentiator is the **verification architecture**. A workspace where the AI's claims are independently verified in real time — where the system can tell you "this step is wrong" before you build on it — is genuinely new. That's what directly addresses the problem stated at the top of this document.

The other differentiators support this:
- **Visual reasoning as a first-class input**: the human draws, the AI sees, verification closes the loop
- **Pluggable verification**: not locked to one proof system — CAS, cross-verification, red-team challenge, whats-missing assumption-surfacing, domain-specific tools
- **Push-back as a structural mode**: visible assumption tracking, milestone red-team passes, claim-in-flight timelines — the workspace makes back-and-forth structural rather than something the user has to remember to do
- **Mentor layer**: domain-specific methodology (physics / math / ml) + cross-domain rigor patterns surfaced proactively, not just on request
- **Human-AI collaboration**: shared workspace, shared state, real-time interaction — not "AI solves, human reads"
- **Domain breadth**: physics, engineering, biology, data science — not just pure math
- **Extensibility**: Claude builds new tools on the fly — no plugin marketplace, no installation step
- **Composes with autoresearch**: doesn't compete with metric-driven optimization tools; runs them as subskills when the problem is shaped right

The question isn't "can we beat AlphaProof at formal proofs?" — it's "is this measurably better than a researcher with Claude in a chat window and a notebook?" If the verification system catches real errors, the watcher provides real assistance, the mentor layer surfaces methodology before mistakes happen, and the milestone challenges catch the conceptual errors that survive verification, the answer is yes.

## Resolved Design Decisions

These were originally open questions, resolved through design discussion:

- **Research state flexibility**: The seven fields are the core. Domain-specific addons extend them as needed (a physics addon might add "experimental setup," a math addon might add "proof strategy"). The core doesn't anticipate every domain — it provides the universal structure, addons provide the rest.

- **Watcher intervention calibration**: Preferences are communicated in natural language ("be more active," "only flag errors," "shut up for now") and the AI remembers them. No settings UI or config files — consistent with "do the simple thing." On first use, the system runs a brief onboarding conversation to learn the human's working style and preferences. Each project gets its own instance (clone the repo per project), so preferences are project-scoped and each project gets a dedicated agent.

- **Claim granularity**: The working agent uses judgment. The guideline: emit a claim for each assertion that a reader would need to verify independently. Mechanical steps that follow directly from the last don't need their own claim. New equations, changes in approach, approximations, and key intermediate results do. The verifier can request finer granularity if a claim is too coarse to check.

- **Dependency chain granularity**: Dependencies are tracked at the milestone level (established results and assumptions), not per-derivation-step. Stored as a JSON graph for machine-parseability. Automatic invalidation propagation is core — it's a simple recursive graph walk. The graph also renders as a d3 visualization in the display panel.

- **Human-AI disagreement**: The AI distinguishes between factual and judgment-based disagreements. For judgment calls (choice of approach, which method to use, what's "interesting"), defer to the human — it's their research. For factual errors (algebra mistake, wrong formula, dimensional inconsistency), the AI should present its reasoning and evidence clearly so the human can evaluate it. The AI cannot force the human to accept a correction, but it should make its case rather than silently defer on something it believes is factually wrong. Log all disagreements in the research state regardless of outcome.

## Open Questions

- **Verification coverage**: What fraction of errors does the two-layer system actually catch in practice? This is one of the first things to measure once the system is running. Autonomous mode enables systematic benchmarking — run N problems, compare verified vs. unverified solve rates.

## Design Rationale

*This section records the thinking and research behind the key design decisions — not to justify them, but to help future implementors understand the tradeoffs and make good judgment calls in the gaps.*

### Why the verifier must be isolated from the working agent's reasoning

The most natural design is: the AI does work, then reads its own work and checks it. Research shows this does not work. Huang et al. (2023) found that LLMs "correct" right answers to wrong ones at similar rates to correcting wrong answers to right ones — self-verification without external grounding is not just unreliable, it's actively misleading.

The auto-mode analogy (from Claude Code) was the breakthrough: the oversight model sees only tool calls, not reasoning. This works because the overseer can't be persuaded by a convincing-but-wrong narrative. We apply the same pattern: claims + one-line context, never the full chain of thought.

We considered sending zero context (just the bare claim), but this would force the verifier to re-derive from scratch every time — too slow. We considered sending full reasoning — too contaminating. One line of context is the routing hint that tells the verifier *how* to check without telling it *what to think*.

### Why the verifier is an AI agent, not a fixed CAS pipeline

Early design had a "Layer 0" — a rigid CAS script that parsed equations and ran automated checks before any AI got involved. We rejected this because:

1. It constrains the working agent to only express itself in CAS-parseable formats. Qualitative arguments, geometric proofs, symmetry reasoning, physical intuition — all would be invisible to a CAS layer.
2. It creates a structural dependency between the working agent's output format and the verification system. If the agent can't emit a parseable equation, verification silently fails.
3. A Sonnet-class model is fast and cheap enough to run on every claim, and it brings judgment about *which* verification method to use — including CAS tools when they're the right fit.

The verifier *has* CAS tools. It's not *made of* CAS tools. This means verification flexes to whatever the working agent is doing, rather than forcing the working agent to flex to the verification system.

### Why Sonnet for continuous verification, not Opus or Haiku

Haiku is faster but lacks the reasoning depth to evaluate conceptual claims — it would rubber-stamp things a more capable model would catch. Opus is more thorough but too slow for real-time async verification of every claim. Sonnet is the sweet spot: fast enough to run in parallel with the working agent, capable enough to make intelligent verification decisions.

The cross-verification layer (final results, independent re-derivation) can use Opus because it runs less frequently and depth matters more than speed at that stage.

### The error landscape that shapes this system

Research on LLM math errors informed every major design decision:

- **On easy problems** (~GSM8K level): models are ~96% accurate, errors are mostly arithmetic. A CAS alone would catch most of them. The verification system is overkill here, but runs anyway because the cost is negligible.
- **On competition math** (~MATH benchmark): models are 71-89% accurate. ~30-40% of errors are computational (CAS catches these), ~60% are reasoning/strategy errors. The AI verifier layer catches some of these through limiting cases and independent reasoning.
- **On graduate/research level** (~GPQA Diamond and beyond): error rates reach 17-75%+. The majority of errors are conceptual — wrong approach, misapplied theorem, flawed setup. These are the hardest to catch automatically and are where cross-verification (solving the problem a different way) provides the most value.

Tool-augmented verification (MathSensei, 2024) showed +13.5% improvement on competition math, with gains increasing as problems get harder. This confirmed that the verification system is most valuable precisely where it's most needed.

The critical finding: as problem difficulty increases, errors move *earlier* in the solution chain. On hard problems, the AI doesn't "set up the problem correctly then fumble the algebra" — it often sets up the wrong problem entirely. This is why step-level verification (Lightman et al., "Let's Verify Step by Step") outperforms checking only the final answer, and why the system verifies claims as they're emitted rather than only at the end.

### Why the watcher and verifier are different roles of the same system, not separate systems

When the AI works, a separate verifier agent checks its claims. When the human works, the AI watches and checks the human's work. These sound like two different systems, but they follow the same principle: **whoever is not doing the work is checking the work.**

This simplifies the architecture. There aren't separate "watcher" and "verifier" subsystems — there's one verification principle applied in two directions. The tools differ (snapshot reading vs. claim parsing), but the logic is the same: observe, evaluate, flag if wrong, stay silent if right.

### Why autonomous mode is not a separate mode

We considered designing autonomous operation as a distinct system with its own architecture. But a good colleague doesn't switch personalities when you hand them a problem and leave the room. They work the same way — same care, same verification, same research state — just without real-time input from you.

Treating autonomy as "the same system, human not drawing" means every improvement to collaborative mode automatically improves autonomous mode, and vice versa. It also means the human can seamlessly shift between collaborating and stepping away — there's no mode switch, no different set of behaviors to learn.

Karpathy's autoresearch reinforced this: the system that works overnight is the same system that works while you watch. The key additions for unsupervised operation are clear scope ("derive the equation of motion," not "explore physics"), immutable evaluation (the verifier can't be influenced by the worker), and continuous logging (so the human can review the full trajectory).

### Why the dependency graph is JSON, not markdown

Dependency tracking is a structural problem: nodes, edges, propagation. Parsing relationships from prose is fragile; a JSON graph is trivially walkable and renderable. The research state narrative belongs in markdown (it's prose). The dependency structure belongs in JSON (it's a graph). Two files, each doing what it's good at. A dependency graph shoehorned into markdown would be the complicated thing; JSON is the simple thing.

### Why research state is a markdown file, not a database

The seven-field structure (goal, questions, assumptions, attempts, established results, open threads, next step) was derived from cross-disciplinary research methodology — lab notebooks, mathematical journals, engineering logs, and cognitive science on interruption recovery all converge on these same elements.

We chose markdown over any structured format because:
1. Claude can read and write it natively — no serialization layer
2. The human can read it too — transparency matters for trust
3. It's flexible enough to accommodate fields we haven't thought of yet
4. It's a file, which means it works with everything else in the system (filesystem watching, git, display rendering)

The research state is a living document, not a log. It gets updated, not appended to. Old attempts don't disappear (they move to the attempts section), but the document always reflects the current state of the investigation.

---

*This document describes the north star. Implementation details, sprint plans, and technical specs will follow as the system is built.*
