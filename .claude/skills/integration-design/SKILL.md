---
name: integration-design
description: Decide whether to embed a third-party tool in a display tab (EmbeddedTool) or link out with a summary panel (ExternalTool). Run before adding any integration, especially for experiment trackers, notebooks, CAD tools, dashboards, or anything with its own web UI.
---

# Integration Design

Every third-party tool Triptych touches hits the same fork: **embed it in a
display tab, or link out and show a summary?** Trial 1 made the wrong call
on Optuna Dashboard — embedded it, then needed four scripts + a `min-width:
1400px` iframe clamp to make it behave. The right call is decided up front,
not discovered through residue.

## The decision table

| Condition | Default |
|---|---|
| Tool renders well at panel size, has a clean iframe API, same-origin or permissive CORS | **Embed** |
| Tool is the de-facto standard, users already have accounts, team-collaborative, or full-screen-assuming | **External** (link + API summary panel) |
| Tool is desktop-only, has complex auth, or its UX fights the panel | **External** |
| User explicitly prefers one | **User wins** |

If two conditions conflict (e.g. "embeds cleanly" *and* "users already have
accounts"), default to external. The cost of a bad embed (scripts,
subprocess management, iframe clamps, auth proxies) is much higher than
the cost of a summary panel.

## Walkthrough

### 1. Does the tool work in-panel at all?

Open the tool in a browser at the Triptych display panel's typical width
(800–1200px). If it says "this app requires at least N pixels wide" or
the UI breaks visibly, you have one of:
- An `ExternalTool` with a link-out
- A redesigned workspace/ workspace addon (not a display) that *is* the
  full-width thing

If the tool is usable but cramped, you can still embed — but the tool is
telling you its design expects full-window use.

### 2. What does auth look like?

- **No auth** (OSS tool, local subprocess): embedding is low-cost. Start
  subprocess with `EmbeddedTool.start()`.
- **SSO / OAuth / cookie auth**: embedding fights the auth wall. Either
  the iframe gets redirected to a login page, or cross-origin cookies
  fail silently. `ExternalTool` is almost always correct here.
- **API token**: ambiguous. The tool's UI probably needs the cookie auth
  path anyway. But the API can drive an `ExternalTool` summary panel
  cleanly.

### 3. What do users actually do with the tool?

- **They open it to read a dashboard**: summary panel + link to full
  dashboard is usually better. They don't need the full UI to glance at
  the number.
- **They interact deeply** (drag components, annotate, simulate): embed,
  if feasible. The interaction model loses too much value through an API
  summary.
- **They collaborate with others in it** (W&B, Notion, Figma): external.
  Triptych is single-user; the tool's collaborative features are lost in
  an iframe anyway.

### 4. What's the update cadence?

- **High-frequency (seconds)**: a live iframe isn't necessarily bad, but
  polling an API for a summary is usually fine at the cadences humans
  actually look at.
- **On-demand**: no live update needed; summary panel refreshes when the
  agent asks.

### 5. Pick, implement, document

Based on steps 1–4:

- **EmbeddedTool**: subclass `integrations.EmbeddedTool`. Implement
  `start()` (idempotent), `stop()`, `is_running()`. Typically writes a
  display HTML file with `<iframe src="http://localhost:PORT/">`. Manage
  the subprocess lifecycle in `scripts/<tool>_server.py`.
- **ExternalTool**: subclass `integrations.ExternalTool`. Implement
  `is_authenticated()`, `fetch_summary()`, `render_panel(summary)`. The
  panel is small, skimmable, and links out. See
  `integrations/wandb.py` as the reference.

Both call `self.record(url=..., ...)` to persist the integration's
coordinates in `workspace/research/integrations.json`.

Register the integration in `tools.md` under "Integrations" with the
embed/external tag so future sessions can see which tools are in use.

## Red flags

Pause and reconsider if you find yourself:

- **Clamping an iframe's min-width.** The tool is telling you it doesn't
  want to be embedded. Listen.
- **Writing a proxy layer to strip auth headers.** The tool has a real
  security model; fighting it is a maintenance sink.
- **Managing more than one subprocess per integration.** Combine them or
  split the integration.
- **Three scripts named `<tool>_push.py`, `<tool>_backfill.py`,
  `<tool>_republish.py`.** This is iteration residue from "the embed
  isn't quite right" — the tool probably wanted to be external.

### The Optuna scar (trial-1-report §3.4)

Trial 1 embedded Optuna Dashboard. Cost:
- 4 scripts (`optuna_server.py`, `optuna_backfill.py`, `optuna_push_ema_panel.py`, `optuna_republish_panels.py`)
- 120-line `core/optuna_helper.py` for trial buffering + auto-publish
- `min-width: 1400px` iframe clamp because the dashboard expected a
  desktop window, not a 800px panel

Compare: W&B rebuilt as `ExternalTool` (`integrations/wandb.py`) ships
in ~250 lines, no scripts, no clamps. **When the tool's CSS fights your
layout, the layout is right.** Make it External, render a summary panel,
move on.

## Per-domain strategy

### ML
| Tool | Default | Why |
|---|---|---|
| Weights & Biases | **External** (canonical) | Users already logged in; collaborative; full-window UX. See `integrations/wandb.py`. |
| MLflow | External | Same reasoning as W&B |
| Hugging Face Hub | External | SSO; collaborative |
| TensorBoard | Embed (local-only) | No auth, iframe-friendly |
| Optuna Dashboard | Embed only if no W&B | See "Optuna scar" below; prefer running Optuna headless and feeding metrics to W&B |

### Physics / math
SymPy, Desmos, Manim are all wired as MCPs (`mcp__sympy-mcp__*`,
`mcp__desmos-mcp__*`, `mcp__manim-mcp__*`). Use them; don't reinvent.

### General
| Tool | Default | Why |
|---|---|---|
| Jupyter / marimo notebook | Workspace addon (not display) | Interactive, full-width |
| Figma / FigJam | External | SSO; collaborative |
| Notion | External | SSO; collaborative |
| CircuitJS | Embed | Pure-web, no auth, well-behaved iframe |
| CadQuery + YACV | Embed | Local viewer, no auth |

When in doubt, ship an External first. If users keep clicking through to
the tool anyway, you made the right call.

## Related

- `integrations/_base.py` — the two base classes (top-level addon layer, not core)
- `integrations/wandb.py` — the reference ExternalTool
- `/display-design-workflow` — for building the summary panel once you've
  picked External
