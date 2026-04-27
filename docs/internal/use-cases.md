# Triptych Use Cases

*First pass, 2026-04-23. Revisit after Trial 2 + as new integrations land.*

Triptych covers a lot of ground — research, study, writing, data analysis, design. Each use case has opinionated defaults on which tools to reach for first. Absence of opinion creates decision fatigue; pick one and get moving, swap later if the tool fights you.

Each entry: **recommended integration(s)**, **default addons**, **steering** (the "what good looks like" one-liner).

---

## ML experiment tracking

- **Recommended integration:** W&B (external) for run tracking + collaboration; Optuna (embed) for HPO sweeps
- **Default addons:** `integrations/wandb.py`, `displays/optuna.py` (per-trial — when built), `displays/progress.py` (live status)
- **Steering:** Log to W&B as the source of truth — Quinn already has an account, collaborators can see the run, full-window UX. Triptych shows a compact summary panel with the run URL pinned in research state. Optuna Dashboard is the exception — local-only, no auth, embeds cleanly, so keep it in a display tab during sweeps.

## Physics derivation

- **Recommended integration:** SymPy (MCP) for symbolic algebra, arxiv-latex-mcp for papers, manim-mcp for narrated derivations
- **Default addons:** `show_latex` for equations, `show_research` for the kanban + graph, `displays/threejs` for geometry
- **Steering:** Exploration first (`show_progress`, sketches, reading). Crystallize to formalization when a clean question emerges → `init_research(goal)` → emit claims → `/loop 60s /verifier` drains the queue. Use `/scientific-critical-thinking` for claim quality checks.

## Circuit design

- **Recommended integration:** CircuitJS (embed, via Falstad iframe)
- **Default addons:** `workspaces/circuitjs.html` (design surface), `displays/circuitjs.py` (Bode / transient plots)
- **Steering:** Draft the circuit in the workspace → simulate in CircuitJS → export waveform → display renders Bode/transient/frequency response. Pure-web, no auth wall, no desktop-only UX baggage. ngspice bridge is a later upgrade if transistor-level accuracy matters.

## Mechanical CAD

- **Recommended integration:** CadQuery or build123d (Python parametric CAD) + YACV viewer (embed)
- **Default addons:** `displays/cadquery` (when built — not yet shipped), `show_html` as an interim renderer
- **Steering:** Script the geometry in Python → YACV renders to the display → iterate parameters → export STEP/STL when it's ready. Don't reach for OpenSCAD (weaker Python story). build123d over raw CadQuery for the cleaner API.

## Data analysis

- **Recommended integration:** marimo (embed, when built) for reactive Python; Plotly for any static chart
- **Default addons:** `show_plotly`, `show_html`, `show_progress`
- **Steering:** Reactive DAG in marimo keeps stale-cell confusion out of exploration. Summary + headline numbers in Triptych displays; the marimo workspace is where the actual analysis code lives. `/data:*` bundle (explore-data, sql-queries, statistical-analysis) covers common flows.

## Literature review

- **Recommended integration:** arxiv-latex-mcp (content, preserves equations), firecrawl (search + scrape), `/paper-lookup` (10-database search)
- **Default addons:** `show_research` in literature mode (Established Results = papers read, Open Threads = papers to read); PDF viewer via `workspaces/pdf.html`
- **Steering:** `/literature-review` runs the search → synthesis → annotated bibliography flow. Pull abstracts with arxiv-latex-mcp (better equation fidelity than PDF extraction). `/citation-management` validates and formats BibTeX before any manuscript draft.

## Math research

- **Recommended integration:** sympy-mcp (symbolic CAS), desmos-mcp (quick 2D plots), Wolfram Alpha (future — numerical oracle)
- **Default addons:** `show_latex`, `show_research`, `displays/derivation` for step-by-step writeups
- **Steering:** Same arc as physics — exploration → formalization → verifier. Lean 4 is the gold standard for the deepest rigor but very heavy; keep SymPy as the default backbone. `/sympy` skill (vendored from K-Dense) covers common symbolic-math patterns.

## Biology / lab notebook

- **Recommended integration:** _deferred — under-served in the current addon set_
- **Default addons:** `workspaces/tiptap` (prose entries), `show_plotly` (quick data viz), `/data:*` for measurement data
- **Steering:** TipTap + research state covers the "what I observed today" flow reasonably. Specific biology tooling (ELN integrations, instrument data pipes) isn't built yet. When a user actually does bio work in Triptych, that'll be the forcing function to pick a concrete integration target — log the ask, don't pre-commit to a specific stack.

---

## How to extend this doc

When a new use case repeats across 2–3 sessions, add an entry. Each entry should have a clear tool-of-first-resort and the "good shape" one-liner. If two tools in the same category compete (W&B vs. MLflow, CadQuery vs. OpenSCAD), pick one as the default and note the alternative in a parenthetical — don't leave readers balancing.

## Related

- `docs/internal/skill-sources.md` — where to find a skill for a specific use-case workflow
- `docs/internal/ecosystem-scan.md` — broader catalogue of integrations we could evaluate
- `.claude/skills/integration-design/SKILL.md` — embed-vs-external decision framework
- `tools.md` — implementation locations for all referenced addons
