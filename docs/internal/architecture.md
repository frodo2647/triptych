# Triptych Architecture Layers

| Layer | Location | Pattern | Setup |
|-------|----------|---------|-------|
| **Core** | `core/` | Framework essentials — imported as modules, works out of the box | None |
| **Displays** | `displays/` | Output renderers — `from displays import show_*` | None |
| **Workspaces** | `workspaces/` | HTML editors — auto-discovered, loaded in iframe | None |
| **Integrations** | `integrations/` | External-tool bridges — `from integrations.<name> import …` | Varies (auth, keys) |
| **Scripts** | `scripts/` | Backend utilities — spawned by server as subprocesses | Varies |

Core must stay lean: cross-platform, zero config, **no external APIs**. Integrations are where credential-gated, per-domain, optional external tools live (W&B, Optuna, CircuitJS, etc.) — they may reach out over the network, which is exactly why they don't belong in core. Scripts are for optional features that need platform-specific code or external credentials (window capture, Google API, etc.).

## Where to put new code

- **Core addition** — only if it's a framework essential needed by many displays or workspaces, with no external deps. Examples: `verify.py`, `research.py`, `theme.css`.
- **Display addon** — a Python module that writes to `workspace/output/`. Auto-reloads in the display panel. Examples: `show_plotly`, `show_progress`, `show_research`.
- **Workspace addon** — an HTML file in `workspaces/`. Auto-discovered; loads in the left panel iframe. Examples: `files.html`, `tldraw.html`.
- **Integration addon** — a Python module in `integrations/` that subclasses `EmbeddedTool` (iframe / owned subprocess) or `ExternalTool` (link out + summary panel). Examples: `integrations/wandb.py`, `integrations/circuitjs.py`. Use `/integration-design` to decide between the two shapes.
- **Script** — a standalone executable (Node, Python, shell) that the server spawns as a subprocess. Use when you need OS-specific behavior or external credentials. Examples: window capture, Google Drive sync.

## Invariants

- `workspace/` is runtime state only — never framework code.
- Core modules never call out to external APIs.
- Displays write via `atomic_write_text` (or `resolve_display_path` + `atomic_write_text`) to avoid partial-file reads by the frontend.
- The server process hosts Claude's PTY — do not kill or restart it.
