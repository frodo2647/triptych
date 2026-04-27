---
name: triptych-displays
description: Display addons for Triptych — Python modules that generate dark-themed output (matplotlib, plotly, LaTeX, HTML, images). Use when asked to visualize, plot, render equations, or show results in the display panel.
---

# Triptych Display Addons

Display addons are Python modules in `displays/`. Each generates dark-themed HTML and writes it to `workspace/output/`, which auto-reloads in the display panel.

## Available displays

| Addon | Import | Use for |
|-------|--------|---------|
| `matplotlib.py` | `from displays import show_figure` | Static plots, charts, figures |
| `plotly.py` | `from displays import show_plotly` | Interactive plots with zoom/pan |
| `latex.py` | `from displays import show_latex` | Math equations via KaTeX |
| `html.py` | `from displays import show_html` | Raw HTML (custom layouts, tables) |
| `image.py` | `from displays import show_image` | Static images (PNG, JPG, SVG) |
| `pdf.py` | `from displays import show_pdf` | PDF files |
| `markdown.py` | `from displays import show_markdown` | Rendered markdown with math |
| `code.py` | `from displays import show_code, show_diff` | Syntax-highlighted code, diffs |
| `table.py` | `from displays import show_table, show_dataframe` | Data tables (lists, dicts, DataFrames) |
| `d3.py` | `from displays import show_d3, d3_scaffold` | Custom D3.js visualizations |
| `progress.py` | `from displays import show_progress` | Live dashboard for long-running work |
| `research.py` | `from displays import show_research` | Research state + dependency graph |
| `assumptions.py` | `from displays import show_assumptions` | Surface load-bearing assumptions for the human to check |
| `claims_status.py` | `from displays import show_claims_status` | Verification timeline — claim → verdict, pending/passed/failed |
| `autoresearch.py` | `from displays import show_autoresearch` | Experiment dashboard |
| `_page.py` | `from displays import write_page, render_page` | Shared template — base for custom addons |
| `_command.py` | `from displays import query_workspace` | Query/control workspace addons |
| `_base.py` | `from displays import clear, clear_display` | Clear all output / a named tab |

## Quick usage

```python
import sys; sys.path.insert(0, '.')

# Matplotlib
from displays import show_figure
import matplotlib.pyplot as plt
fig, ax = plt.subplots(facecolor='#151210')
ax.set_facecolor('#1e1a16')
ax.plot(x, y, color='#cc7a58')
show_figure(fig, title='My Plot')

# Plotly (interactive)
from displays import show_plotly
import plotly.graph_objects as go
fig = go.Figure(data=go.Scatter(x=t, y=x))
show_plotly(fig)

# LaTeX equation
from displays import show_latex
show_latex(r'\nabla \times \mathbf{E} = -\frac{\partial \mathbf{B}}{\partial t}', title="Faraday's Law")

# Raw HTML
from displays import show_html
show_html('<div style="background:#151210;color:#d8d0c8;padding:20px">Custom content</div>')

# Three.js 3D surface
from displays import show_surface
show_surface("Math.sin(x) * Math.cos(z)", x_range=(-3,3), z_range=(-3,3), title="sin(x)cos(z)")

# Three.js vector field
from displays import show_vector_field
show_vector_field("[-y, x, 0]", range=(-2,2), resolution=5, title="Rotation field")

# Three.js parametric curve
from displays import show_parametric
show_parametric("[Math.cos(t), Math.sin(t), t/5]", t_range=(0, 12.56), title="Helix")

# Three.js custom scene
from displays import show_threejs
show_threejs("""
const geo = new THREE.SphereGeometry(1, 32, 32);
const mat = new THREE.MeshPhongMaterial({ color: colors.blue });
scene.add(new THREE.Mesh(geo, mat));
""")

# AutoResearch dashboard
from displays import show_autoresearch
show_autoresearch()

# Clear display
from displays import clear
clear()
```

## Dark theme palette

All display addons auto-apply the Triptych warm dark theme. If writing custom HTML, use tokens from `core/theme.css`:
- Background: `#151210` (void), `#1e1a16` (surface), `#282320` (surface-2)
- Text: `#d8d0c8` (primary), `#968e84` (secondary), `#685f56` (dim)
- Accent: `#cc7a58` (warm orange), `#3cc497` (green), `#d47567` (red), `#c4a045` (yellow), `#7a80d5` (blue)
- Borders: `#3a332b`
- Fonts: Archivo (UI), JetBrains Mono (code)

Display content controls its own theme — don't force dark mode on matplotlib plots, 3D scenes, or embedded tools.

## Named tabs

Every `show_*` accepts `name=`. `name="foo"` writes to a named tab in the display panel — multiple displays coexist as siblings. Omitting `name=` overwrites the default Main tab. Most addons also accept `title=` for a small caption above the body; the raw-passthrough addons (`show_html`, `show_image`, `show_pdf`) don't, since they serve their content verbatim.

```python
show_plotly(fig, name='energy', title='Energy curve')
show_latex('E=mc^2', name='eq')
show_code(src, name='code')
# Display panel now shows three named tabs alongside Main.
```

## Building new display addons

Funnel through `write_page` from `displays._page` so your addon inherits the shared template, name= behavior, and atomic write — supply only the body and any extra `<head>` tags:

```python
from displays import write_page

def show_my_thing(data, *, name=None, title=None):
    body = f'<pre>{data!r}</pre>'
    return write_page(body, name=name, title=title)
```

If you need theme tokens (e.g. for inline CSS in `head`), import them from `displays._base`: `BG_VOID`, `BG_SURFACE`, `TEXT_PRIMARY`, `TEXT_SECONDARY`, `BORDER`, `ACCENT`, `FONT`, etc.

Then add it to `displays/__init__.py` and update `tools.md`.
