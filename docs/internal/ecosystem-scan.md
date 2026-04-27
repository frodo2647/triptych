# Ecosystem Scan — Claude Code & Agent-Skill Projects for Triptych

**Last updated:** 2026-04-21
**Owner:** Quinn
**Purpose:** A scannable, named catalogue of projects in the Claude Code / agent-skill ecosystem that are candidates for integration, imitation, or awareness. Revisit each planning cycle.

**How to read this:** Each entry is `Name` plus URL, one-line "what", one-line "fit", priority (HIGH / MED / LOW). HIGH entries get a second sentence explaining *why*. Star counts / last-update dates are as of 2026-04-21 from GitHub API; some are approximate.

**Skill portability note:** Where possible, each skill entry notes whether it follows the `agentskills.io` SKILL.md open spec (portable across Claude Code, Codex CLI, Gemini CLI, Cursor, VS Code Copilot, Amp, Goose, OpenCode, Letta) or is Claude-specific.

---

## A. Skill aggregators / marketplaces

### hesreallyhim/awesome-claude-code
- **URL:** https://github.com/hesreallyhim/awesome-claude-code
- **What:** The canonical awesome-list for Claude Code — skills, hooks, slash commands, agent orchestrators, plugins.
- **Stars/updated:** ~40k / active daily.
- **Fit:** Reference material — scrape quarterly for new entries to evaluate.
- **Priority:** HIGH — This is the single highest-signal index for new Claude Code projects; Quinn should skim it every planning cycle.

### VoltAgent/awesome-agent-skills
- **URL:** https://github.com/VoltAgent/awesome-agent-skills
- **What:** 1000+ curated agent skills, cross-platform (Claude, Codex, Gemini, Cursor).
- **Stars/updated:** ~17k / active. SKILL.md portable.
- **Fit:** Reference material + source for candidate skills to bundle.
- **Priority:** HIGH — biggest portable-skill pile; a single pass here usually yields 3–5 Triptych-relevant skills.

### VoltAgent/awesome-claude-code-subagents
- **URL:** https://github.com/VoltAgent/awesome-claude-code-subagents
- **What:** 100+ specialized subagents (reviewers, auditors, researchers).
- **Stars/updated:** ~18k / active.
- **Fit:** Pattern source for Triptych's `/verifier`, `/watcher`, `/autonomous` skills.
- **Priority:** MED

### sickn33/antigravity-awesome-skills
- **URL:** https://github.com/sickn33/antigravity-awesome-skills
- **What:** 1,400+ installable skills with a CLI installer; cross-tool (Claude, Cursor, Codex, Gemini, Antigravity).
- **Stars/updated:** ~34k / active.
- **Fit:** Installer pattern worth studying; Triptych could adopt something similar for its skills dir.
- **Priority:** MED

### rohitg00/awesome-claude-code-toolkit
- **URL:** https://github.com/rohitg00/awesome-claude-code-toolkit
- **What:** 135 agents, 35 curated skills, 176+ plugins, 20 hooks, 15 rules, MCP configs, companion apps.
- **Stars/updated:** ~1.4k / active.
- **Fit:** Reference for plugin + hook patterns; includes "companion apps" category useful for workspace addons.
- **Priority:** MED

### karanb192/awesome-claude-skills
- **URL:** https://github.com/karanb192/awesome-claude-skills
- **What:** 50+ verified Claude skills focused on methodology (TDD, debugging, git).
- **Stars/updated:** ~270 / active. Small but curated.
- **Fit:** Reference material.
- **Priority:** LOW

### ComposioHQ/awesome-claude-skills
- **URL:** https://github.com/ComposioHQ/awesome-claude-skills
- **What:** Curated Claude Skills list from Composio.
- **Stars/updated:** ~55k / active.
- **Fit:** Reference — heavily starred, worth scanning but lower signal-to-noise than hesreallyhim's.
- **Priority:** LOW

### travisvn/awesome-claude-skills
- **URL:** https://github.com/travisvn/awesome-claude-skills
- **What:** Another awesome-list, Claude Code-leaning.
- **Stars/updated:** ~11k / active.
- **Fit:** Reference; overlaps heavily with others.
- **Priority:** LOW

### rahulvrane/awesome-claude-agents
- **URL:** https://github.com/rahulvrane/awesome-claude-agents
- **What:** Curated subagents collection.
- **Stars/updated:** ~300 / active.
- **Fit:** Reference.
- **Priority:** LOW

### vijaythecoder/awesome-claude-agents
- **URL:** https://github.com/vijaythecoder/awesome-claude-agents
- **What:** Orchestrated sub-agent dev team example.
- **Stars/updated:** ~4.2k / active.
- **Fit:** Pattern source for dev-team orchestration; relevant if Triptych adds code-writing specialists.
- **Priority:** LOW

### skillmatic-ai/awesome-agent-skills
- **URL:** https://github.com/skillmatic-ai/awesome-agent-skills
- **What:** Definitive resource for modular agent-skill capabilities.
- **Fit:** Reference material.
- **Priority:** LOW

### agentskills.io (spec site)
- **URL:** https://agentskills.io/
- **What:** Official open spec for SKILL.md format (Apache-2.0 code, CC-BY docs); governs portability across Claude Code, Codex, Gemini CLI, Cursor, VS Code Copilot, Amp, Goose, OpenCode, Letta.
- **Fit:** **Pattern to adopt** — Triptych's own skills should conform to this spec so they're portable.
- **Priority:** HIGH — directly affects how Triptych writes its skills; following the spec means Triptych skills work in any compliant harness for free.

### skills.sh
- **URL:** https://skills.sh/
- **What:** Vercel-backed official directory focused on SKILL.md across 19 AI agents.
- **Fit:** Distribution channel — if Triptych publishes portable skills, list them here.
- **Priority:** MED

### skillsmp.com
- **URL:** https://skillsmp.com/
- **What:** 66,500+ (self-reported 500k+) aggregated skills, independent of Anthropic/Vercel.
- **Fit:** Reference material — low signal-to-noise, useful only as a long-tail backstop.
- **Priority:** LOW

### awesomeclaude.ai
- **URL:** https://awesomeclaude.ai/awesome-claude-skills
- **What:** Visual directory of Claude Skills with filters and an agentskills.io-compliance flag.
- **Fit:** Reference material.
- **Priority:** LOW

### agentskill.sh
- **URL:** https://agentskill.sh/
- **What:** 44k+ skills directory with two-layer security scanning; defaults to grade-A only.
- **Fit:** Source for *vetted* skills worth considering; better hygiene than skillsmp.
- **Priority:** MED

### lobehub.com/skills
- **URL:** https://lobehub.com/skills
- **What:** Agent skills marketplace tied to LobeHub.
- **Fit:** Reference.
- **Priority:** LOW

### Ghost references (flagged)
- **"awesome-skills.com"** — no active site/repo found under that exact name.
- **"agentskills.so"** — no active site/repo found.
- Treat these as unreliable until confirmed.

---

## B. Notable skill-packs / methodology skills

### anthropics/skills
- **URL:** https://github.com/anthropics/skills
- **What:** Anthropic's official public skills repo.
- **Stars/updated:** ~122k / active.
- **Fit:** Pattern source + direct skills to bundle. Follows the SKILL.md spec (Anthropic wrote it).
- **Priority:** HIGH — this is the reference implementation of the spec; Triptych's skills should mirror its shape.

### obra/superpowers
- **URL:** https://github.com/obra/superpowers
- **What:** Agentic skills framework and software-development methodology. Opinionated, heavy.
- **Stars/updated:** ~163k / active.
- **Fit:** Pattern source — methodology (TDD, review, debug loops) worth mining.
- **Priority:** HIGH — the most-starred agent methodology repo; skim for loop patterns that complement Triptych's `/autonomous` + `/verifier`.

### obra/superpowers-marketplace
- **URL:** https://github.com/obra/superpowers-marketplace
- **What:** Curated Claude Code plugin marketplace from the superpowers author.
- **Stars/updated:** ~900 / active.
- **Fit:** Reference + source of vetted plugins.
- **Priority:** MED

### trailofbits/skills
- **URL:** https://github.com/trailofbits/skills
- **What:** Professional security-skill pack — CodeQL/Semgrep static analysis, variant analysis, fix verification, differential review, smart-contract auditing.
- **Stars/updated:** ~4.7k / active.
- **Fit:** Direct candidate for bundling when/if Triptych adds a security research mode.
- **Priority:** MED — Triptych is scientific-focused, but the verification-first patterns (fix verification, differential review) map directly onto the `/verifier` loop.

### trailofbits/skills-curated
- **URL:** https://github.com/trailofbits/skills-curated
- **What:** Curated plugin marketplace from Trail of Bits.
- **Stars/updated:** ~370 / active.
- **Fit:** Reference.
- **Priority:** LOW

### trailofbits/claude-code-config
- **URL:** https://github.com/trailofbits/claude-code-config
- **What:** Opinionated defaults, docs, and workflows for Claude Code at Trail of Bits.
- **Stars/updated:** ~1.9k / active.
- **Fit:** Pattern source for Triptych's `CLAUDE.md` and `.claude/` conventions.
- **Priority:** MED

### diet103/claude-code-infrastructure-showcase
- **URL:** https://github.com/diet103/claude-code-infrastructure-showcase
- **What:** Examples of skill auto-activation, hooks, and agents wired together.
- **Stars/updated:** ~9.5k / active.
- **Fit:** Pattern source for auto-activating skills in Triptych (Quinn doesn't like to remember skill names).
- **Priority:** MED

### disler/claude-code-hooks-mastery
- **URL:** https://github.com/disler/claude-code-hooks-mastery
- **What:** Reference implementations of every Claude Code hook with working examples.
- **Stars/updated:** ~3.5k / active.
- **Fit:** Pattern source for hooks (e.g., enforce display-first workflow, auto-start loops).
- **Priority:** MED

### wshobson/agents
- **URL:** https://github.com/wshobson/agents
- **What:** Multi-agent orchestration for Claude Code; dev-team archetype.
- **Stars/updated:** ~34k / active.
- **Fit:** Pattern for multi-agent orchestration — compare against Anthropic's Agent Teams.
- **Priority:** MED

### belokonm/claude-supercode-skills
- **URL:** https://github.com/belokonm/claude-supercode-skills
- **What:** 133 agent skills converted from subagents to the Agent Skills format (claims 100% quality compliance).
- **Fit:** Candidate source — a pre-converted subagent library is a cheap way to add breadth.
- **Priority:** LOW

### alirezarezvani/claude-skills
- **URL:** https://github.com/alirezarezvani/claude-skills
- **What:** 232+ skills spanning engineering, marketing, product, compliance, C-level advisory.
- **Fit:** Reference.
- **Priority:** LOW

### kieranklaassen gists (multiple)
- **URL:** https://gist.github.com/kieranklaassen
- **Notable gists:**
  - Swarm Orchestration Skill — https://gist.github.com/kieranklaassen/4f2aba89594a4aea4ad64d753984b2ea
  - Multi-Agent Orchestration System — https://gist.github.com/kieranklaassen/d2b35569be2c7f1412c64861a219d51f
  - Token-usage analyzer — https://gist.github.com/kieranklaassen/7b2ebb39cbbb78cc2831497605d76cc6
  - `cc.md` capabilities report — https://gist.github.com/kieranklaassen/7ee400209d0454f7c859f8d99fd34144
- **What:** Reverse-engineered details of Claude Code's hidden TeammateTool and orchestration internals.
- **Fit:** Reference material — read before building on Agent Teams.
- **Priority:** MED

---

## C. Scientific / engineering skill-packs

### K-Dense-AI/scientific-agent-skills (formerly claude-scientific-skills)
- **URL:** https://github.com/K-Dense-AI/scientific-agent-skills
- **What:** Ready-to-use Agent Skills for research, science, engineering, analysis, finance, writing.
- **Stars/updated:** ~19k / active. SKILL.md portable.
- **Fit:** **Direct bundle candidate** for Triptych — covers exactly the verification/analysis workflows Triptych targets.
- **Priority:** HIGH — this is arguably the single best-aligned skill-pack for Triptych's scientific-derivation focus; bundle subset into `.claude/skills/` next cycle.

### sympy/sympy
- **URL:** https://github.com/sympy/sympy
- **What:** Pure-Python computer algebra system.
- **Stars/updated:** ~14.6k / active.
- **Fit:** Already available via `sympy-mcp`; keep as the symbolic backbone for verifier.
- **Priority:** HIGH — core of the verifier loop for formal math claims; Triptych already uses it and should lean harder on its tensor/ODE/PDE modules.

### leanprover/lean4
- **URL:** https://github.com/leanprover/lean4
- **What:** Lean 4 programming language and theorem prover.
- **Stars/updated:** ~7.9k / active.
- **Fit:** Alternative verification path for the deepest claims — heavy, but gold-standard rigor.
- **Priority:** MED

### CadQuery/cadquery
- **URL:** https://github.com/CadQuery/cadquery
- **What:** Python parametric CAD based on OCCT kernel.
- **Stars/updated:** ~5k / active.
- **Fit:** Workspace addon — when Quinn studies mechanical/engineering geometry, have a CAD scratchpad. Pairs with YACV.
- **Priority:** MED

### gumyr/build123d
- **URL:** https://github.com/gumyr/build123d
- **What:** Modern Python CAD library (CadQuery-compatible, better API).
- **Stars/updated:** ~2k / active.
- **Fit:** Prefer over raw CadQuery for display-side CAD if we add it.
- **Priority:** MED

### CadQuery/awesome-cadquery
- **URL:** https://github.com/CadQuery/awesome-cadquery
- **What:** Curated CadQuery resources, examples, parts.
- **Stars/updated:** ~170 / active.
- **Fit:** Reference.
- **Priority:** LOW

### yeicor-3d/yet-another-cad-viewer (YACV)
- **URL:** https://github.com/yeicor-3d/yet-another-cad-viewer
- **What:** Browser-based viewer for CadQuery/build123d OCP models.
- **Stars/updated:** ~120 / active.
- **Fit:** Embed in display panel for CAD — drops in without a desktop viewer.
- **Priority:** MED

### bernhard-42/vscode-ocp-cad-viewer
- **URL:** https://github.com/bernhard-42/vscode-ocp-cad-viewer
- **What:** CadQuery/build123d viewer plugin (VS Code).
- **Fit:** Reference for how to render OCP geometry interactively; lift its rendering code if we embed YACV-style.
- **Priority:** LOW

### openscad/openscad
- **URL:** https://github.com/openscad/openscad
- **What:** The Programmer's Solid 3D CAD Modeller.
- **Stars/updated:** ~9.3k / active.
- **Fit:** Alternative to CadQuery — heavier tooling, weaker Python story. Probably skip.
- **Priority:** LOW

### pfalstad/circuitjs1
- **URL:** https://github.com/pfalstad/circuitjs1
- **What:** In-browser electronic circuit simulator (the original Falstad simulator).
- **Stars/updated:** ~2.2k / active.
- **Fit:** Workspace addon — perfect "live domain visual" for EE-adjacent physics work.
- **Priority:** MED

### sharpie7/circuitjs1
- **URL:** https://github.com/sharpie7/circuitjs1
- **What:** Active fork of pfalstad/circuitjs1 with more component types and features.
- **Stars/updated:** ~2.8k / active.
- **Fit:** Prefer this fork if embedding — it's more actively developed than the original.
- **Priority:** MED

### MaxPastushkov/KiCad_to_Falstad
- **URL:** https://github.com/MaxPastushkov/KiCad_to_Falstad
- **What:** Converts KiCad schematics into Falstad-simulator format.
- **Stars/updated:** ~7 / active but small.
- **Fit:** Niche utility — bundle only if Triptych gains a real-EE workflow.
- **Priority:** LOW

### 3b1b/manim
- **URL:** https://github.com/3b1b/manim
- **What:** 3blue1brown's original animation engine for explanatory math videos.
- **Stars/updated:** ~86k / active.
- **Fit:** Heavy dependency; use ManimCommunity instead for most cases.
- **Priority:** LOW

### ManimCommunity/manim
- **URL:** https://github.com/ManimCommunity/manim
- **What:** Community fork of manim; cleaner API, better docs.
- **Stars/updated:** ~38k / active.
- **Fit:** Display-side tool for math animations. Already exposed via `manim-mcp`.
- **Priority:** MED

### helblazer811/ManimML
- **URL:** https://github.com/helblazer811/ManimML
- **What:** ML-specific Manim animations (neural nets, training curves).
- **Fit:** Reference only.
- **Priority:** LOW

---

## D. Visualization / display-related

### mrdoob/three.js
- **URL:** https://github.com/mrdoob/three.js
- **What:** JavaScript 3D library; WebGL under the hood.
- **Stars/updated:** ~112k / active.
- **Fit:** **Already core to Triptych's 3D displays.** Keep as baseline.
- **Priority:** HIGH — Quinn explicitly prefers interactive 3D via Three.js; this is a foundational dependency, not a candidate.

### mermaid-js/mermaid
- **URL:** https://github.com/mermaid-js/mermaid
- **What:** Generate diagrams (flowcharts, sequence, state) from text.
- **Stars/updated:** ~88k / active.
- **Fit:** Quick-diagram display addon — low friction, matches Quinn's "describe-less, show-more" rule.
- **Priority:** MED

### excalidraw/excalidraw
- **URL:** https://github.com/excalidraw/excalidraw
- **What:** Virtual whiteboard with hand-drawn look.
- **Stars/updated:** ~121k / active.
- **Fit:** Workspace addon — embed for sketched-reasoning sessions.
- **Priority:** MED

### excalidraw/mermaid-to-excalidraw
- **URL:** https://github.com/excalidraw/mermaid-to-excalidraw
- **What:** Convert Mermaid to Excalidraw JSON.
- **Stars/updated:** ~790 / active.
- **Fit:** Bridge utility if Triptych supports both editors.
- **Priority:** LOW

### tldraw/tldraw
- **URL:** https://github.com/tldraw/tldraw
- **What:** Whiteboard / infinite-canvas SDK.
- **Stars/updated:** ~46k / active.
- **Fit:** Already used for Triptych's workspace sketch panel.
- **Priority:** HIGH — already embedded; keep current and watch for v3 changes that could improve perf.

### observablehq/plot
- **URL:** https://github.com/observablehq/plot
- **What:** Layered grammar-of-graphics library for exploratory viz (JS).
- **Stars/updated:** ~5.2k / active.
- **Fit:** Display addon — cleaner API than raw D3 for ad-hoc plots.
- **Priority:** MED

### observablehq/framework
- **URL:** https://github.com/observablehq/framework
- **What:** Static-site generator for data apps; JS front, any lang back.
- **Stars/updated:** ~3.4k / active.
- **Fit:** Reference architecture for "notebook-as-dashboard" that Triptych's display panel partly emulates.
- **Priority:** LOW

### thomasballinger/observable-jupyter
- **URL:** https://github.com/thomasballinger/observable-jupyter
- **What:** Embed Observable notebook viz into Jupyter.
- **Stars/updated:** ~200 / stale (last updated late 2025).
- **Fit:** Reference — "embed JS viz in Python context" pattern that Triptych partially implements.
- **Priority:** LOW

### mysimulator.uk
- **URL:** https://www.mysimulator.uk/
- **What:** 309+ in-browser interactive physics/bio/chem simulations, each exposing governing equations via sliders.
- **Fit:** Workspace addon — iframe-embed individual simulations for specific topics Quinn studies.
- **Priority:** MED

### myphysicslab.com
- **URL:** https://www.myphysicslab.com/
- **What:** Classic physics simulations (pendulums, springs, chaos).
- **Fit:** Alternative simulation source; simpler than mysimulator but more classical.
- **Priority:** LOW

### Mattercraft (Zappar)
- **URL:** https://zap.works/mattercraft/
- **What:** Browser-based Three.js editor with real-time Havok physics — visual 3D scene editing, rigid bodies, AR/VR/WebXR.
- **Fit:** Reference for what a polished in-browser 3D physics environment looks like; Triptych's Three.js displays could borrow UX ideas.
- **Priority:** LOW

### jupyter-widgets/ipywidgets
- **URL:** https://github.com/jupyter-widgets/ipywidgets
- **What:** Interactive widgets for Jupyter.
- **Stars/updated:** ~3.3k / active.
- **Fit:** Reference; not directly usable outside Jupyter kernel.
- **Priority:** LOW

---

## E. Hook libraries and patterns

### disler/claude-code-hooks-mastery (also listed in B)
- **URL:** https://github.com/disler/claude-code-hooks-mastery
- **Fit:** The go-to reference for every hook type. Mine it for Triptych's `/watcher` hook setup.
- **Priority:** MED

### disler/claude-code-hooks-multi-agent-observability
- **URL:** https://github.com/disler/claude-code-hooks-multi-agent-observability
- **What:** Real-time monitoring for Claude Code agents via simple hook events.
- **Stars/updated:** ~1.4k / active.
- **Fit:** Pattern source for Triptych's loop health + verifier-queue dashboards.
- **Priority:** MED

### Anthropic's hook reference docs
- **URL:** https://code.claude.com/docs/en/hooks
- **What:** Official hook documentation.
- **Fit:** Authoritative reference — check quarterly for new hook lifecycle events.
- **Priority:** MED

---

## F. Multi-agent / subagent frameworks

### Anthropic "Agent Teams"
- **URL:** https://code.claude.com/docs/en/agent-teams
- **What:** Experimental feature shipped with Opus 4.6 — coordinate multiple Claude Code sessions with a team lead + named teammates, enabled via `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`.
- **Fit:** **Adopt directly** for Triptych's `/autonomous` verifier fleet when it stabilizes out of experimental.
- **Priority:** HIGH — this is the official path for what Triptych already approximates with subagent spawning; migrating to Agent Teams aligns Triptych with the platform direction.

### ruvnet/ruflo
- **URL:** https://github.com/ruvnet/ruflo
- **What:** Multi-agent swarm orchestration platform; Claude Code + Codex integrations.
- **Stars/updated:** ~33k / active.
- **Fit:** Alternative/inspiration — heavier than Agent Teams; borrow patterns, don't depend.
- **Priority:** MED

### wshobson/agents (also listed in B)
- **Fit:** Dev-team archetype; compare against Agent Teams.
- **Priority:** MED

### microsoft/autogen
- **URL:** https://github.com/microsoft/autogen
- **What:** Python framework for agentic AI (conversational agent graphs).
- **Stars/updated:** ~57k / active.
- **Fit:** Alternative awareness; different ecosystem (Python-first, not Claude-native).
- **Priority:** LOW

### crewAIInc/crewAI
- **URL:** https://github.com/crewAIInc/crewAI
- **What:** Role-playing autonomous-agent orchestration.
- **Stars/updated:** ~49k / active.
- **Fit:** Alternative awareness.
- **Priority:** LOW

### langchain-ai/langgraph
- **URL:** https://github.com/langchain-ai/langgraph
- **What:** Build agents as stateful graphs (LangChain stack).
- **Stars/updated:** ~30k / active.
- **Fit:** Alternative awareness.
- **Priority:** LOW

### huggingface/smolagents
- **URL:** https://github.com/huggingface/smolagents
- **What:** Barebones library for agents that think in code.
- **Stars/updated:** ~27k / active.
- **Fit:** Reference for code-acting agents; compact, easy to study.
- **Priority:** LOW

### OpenHands/OpenHands (formerly OpenDevin)
- **URL:** https://github.com/OpenHands/OpenHands
- **What:** AI-driven development agent platform.
- **Stars/updated:** ~72k / active.
- **Fit:** Alternative autonomous dev-agent awareness.
- **Priority:** LOW

### stitionai/devika
- **URL:** https://github.com/stitionai/devika
- **What:** Open-source implementation of an "Agentic Software Engineer".
- **Stars/updated:** ~20k / slowing.
- **Fit:** Reference.
- **Priority:** LOW

---

## G. Browser-embeddable tools (workspace / display candidates)

### marimo-team/marimo
- **URL:** https://github.com/marimo-team/marimo
- **What:** Reactive Python notebook stored as pure Python; runs as script, app, or notebook; AI-native editor.
- **Stars/updated:** ~21k / active.
- **Fit:** **Strong candidate for Triptych's Python scratch panel** — reactivity + pure-Python storage solves the "why is my notebook state stale" problem.
- **Priority:** HIGH — aligns with Triptych's "filesystem is the channel" philosophy (files are readable as Python); a good alternative to JupyterLite when Quinn wants inline Python.

### jupyterlite/jupyterlite
- **URL:** https://github.com/jupyterlite/jupyterlite
- **What:** Wasm-powered Jupyter entirely in the browser.
- **Stars/updated:** ~4.8k / active.
- **Fit:** Alternative to marimo — pure-browser, no server. Good for quick embed.
- **Priority:** MED

### pyodide/pyodide
- **URL:** https://github.com/pyodide/pyodide
- **What:** Python distribution for the browser (WebAssembly). Underlies JupyterLite and PyScript.
- **Stars/updated:** ~14.5k / active.
- **Fit:** Foundational — use directly if Triptych embeds in-browser Python without a full notebook UI.
- **Priority:** MED

### Chainlit/chainlit
- **URL:** https://github.com/Chainlit/chainlit
- **What:** Conversational AI UI framework.
- **Stars/updated:** ~12k / active.
- **Fit:** Alternative to Triptych's custom Express+WS UI — probably skip since Triptych already has its own shell.
- **Priority:** LOW

### streamlit/streamlit
- **URL:** https://github.com/streamlit/streamlit
- **What:** Python data-app framework.
- **Stars/updated:** ~44k / active.
- **Fit:** Alternative awareness.
- **Priority:** LOW

### gradio-app/gradio
- **URL:** https://github.com/gradio-app/gradio
- **What:** Share ML apps from Python.
- **Stars/updated:** ~42k / active.
- **Fit:** Alternative awareness; interesting for the workspace "file-in-file-out" model.
- **Priority:** LOW

### dream-num/univer
- **URL:** https://github.com/dream-num/univer
- **What:** AI-native spreadsheets — full-stack JS spreadsheet with natural-language driving.
- **Fit:** Already referenced in Triptych memory as the spreadsheet editor. Keep.
- **Priority:** MED

### Aslam97/minimal-tiptap (and hunghg255/reactjs-tiptap-editor)
- **URL:** https://github.com/Aslam97/minimal-tiptap
- **What:** Minimal Tiptap rich-text editor.
- **Fit:** Already used in Triptych docs editor. Keep.
- **Priority:** MED

### quarto-dev/quarto-cli
- **URL:** https://github.com/quarto-dev/quarto-cli
- **What:** Scientific & technical publishing system on Pandoc.
- **Stars/updated:** ~5.5k / active.
- **Fit:** **Output-side publishing** — render Triptych research sessions to polished PDF/HTML reports.
- **Priority:** MED

---

## H. External tools to integrate via API

### wandb/weave
- **URL:** https://github.com/wandb/weave
- **What:** W&B's toolkit for AI-powered applications (traces, evals, monitoring).
- **Stars/updated:** ~1.1k / active.
- **Fit:** **Candidate for the verifier loop's eval logging** — every claim's verification could be a Weave trace.
- **Priority:** MED

### mlflow/mlflow
- **URL:** https://github.com/mlflow/mlflow
- **What:** Open-source AI engineering platform; experiment + agent tracking.
- **Stars/updated:** ~25k / active.
- **Fit:** Alternative to Weave; heavier, more "ML ops"-shaped.
- **Priority:** LOW

### tensorflow/tensorboard
- **URL:** https://github.com/tensorflow/tensorboard
- **What:** Training-run visualization toolkit.
- **Stars/updated:** ~7.2k / active.
- **Fit:** Only relevant if Triptych adds ML training workflows.
- **Priority:** LOW

### neptune.ai
- **URL:** https://neptune.ai/
- **What:** Metadata store for ML model training.
- **Fit:** Alternative awareness.
- **Priority:** LOW

---

## I. Status lines, dashboards, introspection tools

### snipeship/ccflare
- **URL:** https://github.com/snipeship/ccflare
- **What:** Claude Code proxy with load-balancing across accounts.
- **Stars/updated:** ~950 / active.
- **Fit:** Tool to embed for rate-limit / cost management.
- **Priority:** LOW — Triptych is single-user; ccflare shines at team scale.

### lis186/ccxray
- **URL:** https://github.com/lis186/ccxray
- **What:** Transparent HTTP proxy + dashboard for Claude Code sessions; logs req/res as JSON.
- **Stars/updated:** ~130 / active.
- **Fit:** **Strong candidate for Triptych's introspection story** — drop-in session recording without hooking into Claude Code internals.
- **Priority:** HIGH — solves the "what is Claude actually doing" problem for Quinn without requiring custom instrumentation; slots in as an optional layer.

### vibe-log/vibe-log-cli
- **URL:** https://github.com/vibe-log/vibe-log-cli
- **What:** CLI for logging and analyzing Claude Code and Cursor sessions; generates productivity reports via subagents; runs fully local.
- **Stars/updated:** ~320 / active.
- **Fit:** Could power Triptych's session-end summaries (already required by CLAUDE.local.md's study integration).
- **Priority:** MED

### ColeMurray/claude-code-otel
- **URL:** https://github.com/ColeMurray/claude-code-otel
- **What:** OTel-based observability for Claude Code usage, perf, cost.
- **Stars/updated:** ~360 / active.
- **Fit:** Alternative to ccxray if Triptych wants OTel-native traces.
- **Priority:** LOW

### simple10/agents-observe
- **URL:** https://github.com/simple10/agents-observe
- **What:** Real-time observability of Claude Code sessions and multi-agent runs.
- **Stars/updated:** ~490 / active.
- **Fit:** Alternative/complement to ccxray; focuses on multi-agent view.
- **Priority:** LOW

### vkartaviy/claude-code-observability
- **URL:** https://github.com/vkartaviy/claude-code-observability
- **What:** Local OTel stack for Claude Code — dashboards, cost, cache monitoring.
- **Fit:** Alternative reference.
- **Priority:** LOW

### Haleclipse/CCometixLine
- **URL:** https://github.com/Haleclipse/CCometixLine
- **What:** Rust-based Claude Code statusline.
- **Fit:** Reference for statusline authoring; Triptych's shell already shows this info.
- **Priority:** LOW

### kamranahmedse/claude-statusline
- **URL:** https://github.com/kamranahmedse/claude-statusline
- **What:** Minimal statusline setup.
- **Fit:** Reference.
- **Priority:** LOW

### Wangnov/claude-code-statusline-pro and rz1989s/claude-code-statusline
- **Fit:** Reference.
- **Priority:** LOW

---

## J. Alternative agents / CLIs to stay aware of

### anomalyco/opencode (sst/opencode)
- **URL:** https://github.com/anomalyco/opencode
- **What:** Open-source coding agent, terminal-native.
- **Stars/updated:** ~147k / active.
- **Fit:** Alternative awareness; SKILL.md-compatible.
- **Priority:** MED — if Triptych writes spec-compliant skills, they'll run here for free; useful compatibility check.

### Aider-AI/aider
- **URL:** https://github.com/Aider-AI/aider
- **What:** AI pair programming in the terminal.
- **Stars/updated:** ~44k / active.
- **Fit:** Alternative awareness.
- **Priority:** LOW

### cline/cline
- **URL:** https://github.com/cline/cline
- **What:** Autonomous coding agent in the IDE (VS Code extension).
- **Stars/updated:** ~61k / active.
- **Fit:** Alternative awareness.
- **Priority:** LOW

### RooCodeInc/Roo-Code
- **URL:** https://github.com/RooCodeInc/Roo-Code
- **What:** In-IDE agent team (Cline fork, heavier features).
- **Stars/updated:** ~23k / active.
- **Fit:** Alternative awareness.
- **Priority:** LOW

### openai/codex
- **URL:** https://github.com/openai/codex
- **What:** OpenAI's terminal coding agent. Adopts SKILL.md spec.
- **Stars/updated:** ~77k / active.
- **Fit:** Compatibility target — write portable skills that work here too.
- **Priority:** MED

### google-gemini/gemini-cli
- **URL:** https://github.com/google-gemini/gemini-cli
- **What:** Google's open-source terminal agent (Gemini).
- **Stars/updated:** ~102k / active. SKILL.md-compatible.
- **Fit:** Compatibility target.
- **Priority:** MED

### aaif-goose/goose (block/goose)
- **URL:** https://github.com/aaif-goose/goose
- **What:** Extensible open-source agent that installs, edits, executes. SKILL.md-compatible.
- **Stars/updated:** ~43k / active.
- **Fit:** Compatibility target.
- **Priority:** LOW

### continuedev/continue
- **URL:** https://github.com/continuedev/continue
- **What:** Source-controlled CI-enforceable AI checks; Continue CLI under the hood.
- **Stars/updated:** ~33k / active.
- **Fit:** Reference for "AI checks in CI" — could inspire a Triptych mode where verifier runs on commit.
- **Priority:** LOW

### Google Antigravity
- **URL:** https://antigravity.google/
- **What:** Agent-first IDE (VS Code fork); Gemini-native, also supports Claude Sonnet 4.5.
- **Fit:** Alternative awareness; borrow "Manager view" pattern for multi-agent UX.
- **Priority:** LOW

### AWS Kiro
- **URL:** https://kiro.dev/
- **What:** Spec-driven agent IDE, Claude Sonnet 4.5 only.
- **Fit:** Alternative awareness; "spec-first" workflow is a notable contrast to Triptych's free-form exploration.
- **Priority:** LOW

### Cursor, Zed, Windsurf
- **URLs:** https://cursor.com/, https://zed.dev/, https://windsurf.com/
- **Fit:** Alternative awareness; all AI-native editors with their own plugin systems.
- **Priority:** LOW

### Devin, Manus, Bolt.new, v0
- **URLs:** https://devin.ai/, https://manus.im/, https://bolt.new/, https://v0.dev/
- **Fit:** Closed/hosted autonomous-agent alternatives; reference only.
- **Priority:** LOW

---

## K. Adjacent research / notebook environments

### NotebookLM (Google)
- **URL:** https://notebooklm.google.com/
- **What:** Source-grounded LLM notebook; audio overviews, citations.
- **Fit:** Reference — the citation/grounding UX is worth copying for Triptych's literature-review skill output.
- **Priority:** MED

### Copilot Notebooks (Microsoft)
- **URL:** https://github.com/features/copilot
- **What:** GitHub Copilot's notebook integration.
- **Fit:** Reference.
- **Priority:** LOW

### Deepnote
- **URL:** https://deepnote.com/
- **What:** Cloud notebook with AI + collaboration.
- **Fit:** Reference.
- **Priority:** LOW

### Observable (observablehq.com)
- **URL:** https://observablehq.com/
- **What:** Reactive JS notebooks, the original "cells re-run reactively" model.
- **Fit:** Reference — Triptych's display auto-reload is a file-based analogue.
- **Priority:** LOW

### Hex
- **URL:** https://hex.tech/
- **What:** Collaborative data notebook.
- **Fit:** Reference.
- **Priority:** LOW

---

## L. MCP servers worth shipping

### takashiishida/arxiv-latex-mcp
- **URL:** https://github.com/takashiishida/arxiv-latex-mcp
- **What:** Fetches arXiv papers as flattened LaTeX — preserves equation fidelity, unlike PDF-text extraction.
- **Stars/updated:** ~130 / active.
- **Fit:** **Already loaded in Triptych's MCP set.** Keep and use — this is the right primitive for scientific paper ingestion.
- **Priority:** HIGH — the LaTeX-over-PDF approach is exactly what formal-verification workflows need.

### sdiehl/sympy-mcp
- **URL:** https://github.com/sdiehl/sympy-mcp
- **What:** MCP server for SymPy symbolic math.
- **Fit:** **Already loaded.** Core verifier dependency.
- **Priority:** HIGH — used by the `/verifier` loop; keep and extend with additional SymPy modules as needed.

### abhiemj/manim-mcp-server (also wstcpyt/manim-mcp, Avik-creator/manim-mcp)
- **URL:** https://github.com/abhiemj/manim-mcp-server
- **What:** MCP wrapper around Manim for math animations.
- **Fit:** **Already loaded.** Use for narrated math derivations.
- **Priority:** MED

### TheGrSun/Desmos-MCP (or AndresMuelas2004/MCP-Desmos)
- **URL:** https://github.com/TheGrSun/Desmos-MCP
- **What:** MCP for Desmos graphing.
- **Fit:** Already loaded; quick 2D plots when Quinn wants them.
- **Priority:** LOW

### firecrawl/firecrawl-mcp-server
- **URL:** https://github.com/firecrawl/firecrawl-mcp-server
- **What:** Official Firecrawl MCP — scraping, search, crawling, extraction.
- **Stars/updated:** ~6.1k / active.
- **Fit:** **Already loaded.** Workhorse for research mode.
- **Priority:** HIGH — the default web-fetching primitive; more reliable than WebFetch for modern JS sites.

### upstash/context7 (and its MCP)
- **URL:** https://github.com/upstash/context7
- **What:** Always-current library docs for LLMs, via MCP.
- **Stars/updated:** ~53k / active.
- **Fit:** **Already loaded.** Use first for library-API questions.
- **Priority:** HIGH — prevents outdated-docs errors; replacing WebSearch for API/config lookups is a proven win.

### punkpeye/awesome-mcp-servers
- **URL:** https://github.com/punkpeye/awesome-mcp-servers
- **What:** The largest MCP-server index.
- **Stars/updated:** ~85k / active.
- **Fit:** Reference — scan quarterly for new server capabilities.
- **Priority:** HIGH — highest-signal index for new MCP tools Triptych could ship.

### modelcontextprotocol/servers
- **URL:** https://github.com/modelcontextprotocol/servers
- **What:** Official reference MCP server implementations.
- **Stars/updated:** ~84k / active.
- **Fit:** Reference for building Triptych-native MCP tools if ever needed.
- **Priority:** MED

### cnosuke/mcp-wolfram-alpha
- **URL:** https://github.com/cnosuke/mcp-wolfram-alpha
- **What:** Wolfram Alpha via MCP.
- **Fit:** Candidate for adding a numerical oracle next to sympy; needs an API key.
- **Priority:** LOW

### blazickjp/arxiv-mcp-server
- **URL:** https://github.com/blazickjp/arxiv-mcp-server
- **What:** arXiv search + analysis MCP (alt to arxiv-latex-mcp, covers discovery more than content).
- **Fit:** Pair with arxiv-latex-mcp — one for search, one for content.
- **Priority:** MED

### SepineTam/latex-mcp
- **URL:** https://github.com/SepineTam/latex-mcp
- **What:** Compile TeX files via MCP in Docker.
- **Fit:** Candidate for Triptych output-to-PDF rendering.
- **Priority:** LOW

### shahidhustles/tldraw-mcp (and AndresMuelas2004/tldraw-mcp-server)
- **URL:** https://github.com/shahidhustles/tldraw-mcp
- **What:** MCP servers for creating/editing tldraw canvases.
- **Fit:** Since Triptych already uses tldraw in the workspace, this would let Claude author sketches directly.
- **Priority:** MED

### metorial/mcp-containers
- **URL:** https://github.com/metorial/mcp-containers
- **What:** Dockerized MCP servers, easy to spin up.
- **Fit:** Reference for safe MCP sandboxing.
- **Priority:** LOW

### husayni/inspect-ai-skill
- **URL:** https://github.com/husayni/inspect-ai-skill
- **What:** Claude Code skill for writing/debugging Inspect AI evaluations.
- **Fit:** Candidate if Triptych adopts Inspect AI for autoresearch metric harnesses.
- **Priority:** LOW

---

## M. Benchmarks / evaluations (for Triptych's autoresearch loop)

### SWE-bench/SWE-bench
- **URL:** https://github.com/SWE-bench/SWE-bench
- **What:** Canonical "can LLMs resolve real GitHub issues" benchmark.
- **Stars/updated:** ~4.7k / active.
- **Fit:** Reference — software-engineering focused, probably too narrow for scientific Triptych.
- **Priority:** LOW

### multi-swe-bench/multi-swe-bench
- **URL:** https://github.com/multi-swe-bench/multi-swe-bench
- **What:** Multilingual SWE-bench.
- **Fit:** Reference.
- **Priority:** LOW

### AutoCodeRoverSG/auto-code-rover
- **URL:** https://github.com/AutoCodeRoverSG/auto-code-rover
- **What:** Autonomous program-improvement agent with strong SWE-bench scores.
- **Fit:** Reference for autonomous-loop architecture.
- **Priority:** LOW

### xlang-ai/OSWorld
- **URL:** https://github.com/xlang-ai/OSWorld
- **What:** NeurIPS 2024 benchmark for multimodal agents in real computer environments.
- **Fit:** Reference — relevant if Triptych adds a desktop-watcher track.
- **Priority:** LOW

### GAIA benchmark
- **URL:** https://huggingface.co/datasets/gaia-benchmark/GAIA
- **What:** General AI assistant benchmark (reasoning, retrieval, tool use).
- **Fit:** **Good candidate for Triptych's autoresearch metric** — mixes research, reasoning, and tool use.
- **Priority:** MED

### SkillsBench
- **URL:** https://www.skillsbench.ai/skillsbench.pdf (paper: arxiv.org/html/2602.12670v1)
- **What:** First benchmark evaluating Agent Skills as first-class artifacts; 84 tasks over 11 domains, 3 conditions (no skills / curated / self-generated).
- **Fit:** **Direct fit** — this is what Triptych's `/autoresearch` is trying to do, but with published methodology.
- **Priority:** HIGH — gives Triptych a published evaluation harness to plug into rather than hand-rolling metrics from scratch.

### augmentcode/augment-swebench-agent
- **URL:** https://github.com/augmentcode/augment-swebench-agent
- **What:** #1 open-source SWE-bench Verified implementation.
- **Fit:** Reference.
- **Priority:** LOW

### openai/SWELancer-Benchmark
- **URL:** https://github.com/openai/SWELancer-Benchmark
- **What:** Frontier LLMs on freelance SWE tasks (archived).
- **Fit:** Reference (historical).
- **Priority:** LOW

### UK AISI Inspect AI
- **URL:** https://inspect.aisi.org.uk/
- **What:** UK AI Safety Institute's eval framework.
- **Fit:** **Strong candidate** for Triptych's autoresearch eval harness — Anthropic-endorsed and Python-native.
- **Priority:** MED

---

## N. Reference reads (blog posts, papers, canonical guides)

### Building Effective AI Agents (Anthropic)
- **URL:** https://www.anthropic.com/research/building-effective-agents
- **What:** Canonical Anthropic guide — workflows vs agents, common patterns (chain, router, orchestrator-workers, eval-iterate).
- **Fit:** **Must-read reference.** Triptych's verifier loop maps onto the "evaluator-optimizer" pattern described here.
- **Priority:** HIGH — the vocabulary in this post is the lingua franca of the ecosystem; align Triptych's docs with its terms.

### Effective Context Engineering for AI Agents (Anthropic)
- **URL:** https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- **What:** The progression from prompt engineering to context engineering.
- **Fit:** Reference for CLAUDE.md design.
- **Priority:** MED

### Writing Effective Tools for AI Agents (Anthropic)
- **URL:** https://www.anthropic.com/engineering/writing-tools-for-agents
- **What:** How to design tool schemas and behaviors.
- **Fit:** Reference when building new MCP servers or workspace addons.
- **Priority:** MED

### Building Agents with the Claude Agent SDK (Anthropic)
- **URL:** https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk
- **What:** The "give agents a computer" design principle.
- **Fit:** Reference.
- **Priority:** MED

### Code Execution with MCP (Anthropic)
- **URL:** https://www.anthropic.com/engineering/code-execution-with-mcp
- **What:** Building efficient agents via MCP-driven code execution.
- **Fit:** Reference for Triptych's Python-execution story.
- **Priority:** MED

### anthropics/claude-cookbooks
- **URL:** https://github.com/anthropics/claude-cookbooks
- **What:** Notebooks/recipes showing effective Claude usage.
- **Stars/updated:** ~41k / active.
- **Fit:** Reference + inspiration source.
- **Priority:** MED

### anthropics/anthropic-cookbook (patterns/agents)
- **URL:** https://github.com/anthropics/anthropic-cookbook/tree/main/patterns/agents
- **What:** Reference implementations of the "Building Effective Agents" patterns.
- **Fit:** Copyable starting points for new Triptych subagent patterns.
- **Priority:** MED

### code.claude.com/docs/en
- **URL:** https://code.claude.com/docs/en/
- **What:** Official Claude Code docs.
- **Fit:** Authoritative reference — check quarterly.
- **Priority:** HIGH — new features (Agent Teams, skills spec updates, hook types) land here first.

### platform.claude.com/docs/en/agents-and-tools/agent-skills/overview
- **URL:** https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview
- **What:** Official Agent Skills API reference.
- **Fit:** Reference.
- **Priority:** MED

### Deep Dive SKILL.md (ABVijayKumar, Medium)
- **URL:** https://abvijaykumar.medium.com/deep-dive-skill-md-part-1-2-09fc9a536996
- **What:** Detailed walkthrough of the SKILL.md spec in practice.
- **Fit:** Reference.
- **Priority:** LOW

### "The SKILL.md Pattern" (Bibek Poudel, Medium)
- **URL:** https://bibek-poudel.medium.com/the-skill-md-pattern-how-to-write-ai-agent-skills-that-actually-work-72a3169dd7ee
- **What:** Pragmatic advice for authoring skills.
- **Fit:** Reference.
- **Priority:** LOW

### Karpathy's self-improvement loop essays (reference for `/autoresearch`)
- **URL:** https://karpathy.ai/ (various threads; see Quinn's memory note `project_autoresearch.md`)
- **Fit:** Foundational inspiration for Triptych's autoresearch direction.
- **Priority:** MED

---

## Top 15 candidates Triptych should pull in next

Ranked by expected value to Quinn's scientific/study workflow, given Triptych's current state:

1. **K-Dense-AI/scientific-agent-skills** — directly aligned with Triptych's formal-science focus; bundle a vetted subset into `.claude/skills/`.
2. **agentskills.io spec conformance** — audit every Triptych skill against the SKILL.md spec so they become portable (and cleaner).
3. **trailofbits/skills (+ claude-code-config)** — the verification-first patterns (fix verification, differential review) map onto Triptych's `/verifier` loop; cherry-pick the methodology.
4. **lis186/ccxray** — drop-in session introspection without modifying Triptych internals; answers "what is Claude doing?" on demand.
5. **SkillsBench** — published benchmark for skills-as-artifacts; a concrete harness for `/autoresearch` instead of ad-hoc metrics.
6. **Anthropic Agent Teams** — start designing a migration from Triptych's ad-hoc subagent spawning to the official team model.
7. **marimo-team/marimo** — candidate Python scratchpad for the workspace; reactive + pure-Python aligns with Triptych's filesystem-first design.
8. **disler/claude-code-hooks-mastery + hooks-multi-agent-observability** — reference patterns for auto-activating skills and dashboarding loop health.
9. **obra/superpowers** — mine methodology primitives (planning, review, loops) that can slot beside Triptych's `/autonomous`.
10. **yeicor-3d/yet-another-cad-viewer + build123d** — workspace/display pair for parametric geometry when Quinn's study crosses into mechanical/engineering.
11. **takashiishida/arxiv-latex-mcp + blazickjp/arxiv-mcp-server** — already using the former; add the latter for discovery-side paper search.
12. **vibe-log/vibe-log-cli** — powers the session-end study summaries required by CLAUDE.local.md.
13. **UK AISI Inspect AI (+ husayni/inspect-ai-skill)** — Python-native eval harness; cleaner than hand-rolled metrics for autoresearch.
14. **sharpie7/circuitjs1 (fork of Falstad) + MaxPastushkov/KiCad_to_Falstad** — workspace-embedded circuit simulator for EE-adjacent physics topics.
15. **quarto-dev/quarto-cli** — output-side publishing pipeline so a completed research session can produce a polished PDF/HTML report with one command.

---

## Revisit checklist (run each planning cycle)

- [ ] Skim hesreallyhim/awesome-claude-code for new skills/hooks/plugins.
- [ ] Skim VoltAgent/awesome-agent-skills for new portable skills.
- [ ] Scan punkpeye/awesome-mcp-servers for new MCP primitives.
- [ ] Check code.claude.com/docs/en for new hook types or Agent Teams stability.
- [ ] Re-check anthropics/skills and obra/superpowers for methodology updates.
- [ ] Re-check K-Dense-AI/scientific-agent-skills for new science-focused skills.
- [ ] Flag any entry above whose repo hasn't been updated in 90 days as at-risk.
