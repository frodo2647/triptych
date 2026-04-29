"""CircuitJS display — render analysis output and read-only schematics.

CircuitJS *editing* lives in the workspace panel (`workspaces/circuitjs.html`).
This display module is the agent-facing side: read-only renderings the
agent can write to the display panel without giving the user an editor.

Three entry points:

  show_circuit_schematic(source, ...)
      Render a *static* schematic for viewing. `source` may be:
        - an SVG string starting with "<svg" or "<?xml",
        - a path to a .png / .svg / .jpg image,
        - a path to a .circuit JSON envelope (renders the sibling
          `<stem>.svg` / `<stem>.png` if one exists; otherwise shows a
          short hint to export an image from the workspace).

      The display intentionally does NOT embed the Falstad iframe.
      Falstad is the editor; the editor lives in the workspace tab.
      For schematics drawn from code, the recommended path is the
      `schemdraw` library (pip install schemdraw):

          import schemdraw
          import schemdraw.elements as elm
          d = schemdraw.Drawing()
          d += elm.SourceV().label('5V')
          d += elm.Resistor().right().label('1kΩ')
          d += elm.Capacitor().down().label('100nF')
          d += elm.Line().left()
          d.save('workspace/files/rc-lowpass.svg')
          show_circuit_schematic('workspace/files/rc-lowpass.svg',
                                 title='RC low-pass')

  show_circuitjs_waveform(path, ...)
      Plotly time-domain plot from a `{t, v}` or `{t, probes}` JSON.

  show_circuitjs_bode(freqs, magnitudes, phases, ...)
      Plotly Bode plot from arrays.
"""

from __future__ import annotations

import html as html_mod
import json
from pathlib import Path
from typing import Optional

from ._base import (BG_VOID, BG_SURFACE, TEXT_PRIMARY, FONT,
                    atomic_write_text, resolve_display_path)


def show_circuit_schematic(source, *,
                           title: Optional[str] = None,
                           name: Optional[str] = None,
                           display_id: Optional[str] = None) -> None:
    """Render a static circuit schematic in the display, read-only.

    Args:
        source: one of:
            - SVG string (starts with "<svg" or "<?xml")
            - Path to a .png / .jpg / .svg image
            - Path to a .circuit JSON envelope. Renders a sibling
              `<stem>.svg` or `<stem>.png` if one exists; otherwise
              shows a hint pointing at the workspace.
        title: optional caption shown above the schematic
        name / display_id: named-tab stem

    The display does NOT load the Falstad iframe. Use the workspace
    `circuitjs` tab to edit; export an image from there
    (File → Export Image → Save to workspace/files/) and pass the
    image path here.
    """
    body = _render_schematic_body(source)
    cap = html_mod.escape(title) if title else ""

    page = _SCHEMATIC_TEMPLATE.format(
        title=html_mod.escape(title or "Circuit"),
        caption=f'<div class="caption">{cap}</div>' if cap else "",
        body=body,
    )

    out, effective = resolve_display_path(
        name=name, display_id=display_id,
        default_filename="circuit.html", extension=".html",
    )
    atomic_write_text(out / effective, page)


def _render_schematic_body(source) -> str:
    # SVG string. NOTE: SVG is inlined as-is — caller must trust the source
    # (SVG can carry <script> elements that execute in the display origin).
    if isinstance(source, str):
        s = source.strip()
        if s.startswith("<svg") or s.startswith("<?xml"):
            return f'<div class="schematic svg-wrap">{s}</div>'
        # Otherwise treat as a file path. Reject URLs and raw netlists —
        # those belong in the workspace, not the display.
        if s.startswith("http://") or s.startswith("https://"):
            raise ValueError(
                "show_circuit_schematic does not embed live Falstad URLs. "
                "The display is read-only; open the URL in the circuitjs "
                "workspace tab to edit, or export an image and pass the "
                "image path here."
            )
        if "\n" in s and ("$" in s or "w " in s or "r " in s):
            raise ValueError(
                "show_circuit_schematic does not render raw Falstad netlists. "
                "The display is static — use the circuitjs workspace tab to "
                "edit the netlist, or render the schematic to SVG/PNG via "
                "schemdraw and pass the path here."
            )
        return _render_path_source(Path(s))
    if isinstance(source, Path):
        return _render_path_source(source)
    raise TypeError(f"show_circuit_schematic: unsupported source type {type(source)}")


def _render_path_source(p: Path) -> str:
    if not p.exists():
        raise FileNotFoundError(f"schematic source not found: {p}")
    suf = p.suffix.lower()
    if suf in (".png", ".jpg", ".jpeg", ".webp", ".gif"):
        return _img_tag(p)
    if suf == ".svg":
        return f'<div class="schematic svg-wrap">{p.read_text(encoding="utf-8")}</div>'
    if suf == ".circuit":
        # Validate JSON shape but don't use share_url / netlist fields here —
        # those drive the *workspace* editor, not the static display.
        try:
            json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise ValueError(f".circuit is not valid JSON: {p}") from e
        # Look for a sibling rendered image: foo.circuit → foo.svg / foo.png
        for ext in (".svg", ".png", ".jpg", ".jpeg"):
            sibling = p.with_suffix(ext)
            if sibling.exists():
                if ext == ".svg":
                    return f'<div class="schematic svg-wrap">{sibling.read_text(encoding="utf-8")}</div>'
                return _img_tag(sibling)
        return (
            '<div class="schematic empty">'
            f'<div><strong>{html_mod.escape(p.name)}</strong> has no rendered schematic.</div>'
            '<div class="hint">'
            'Open it in the <code>circuitjs</code> workspace tab, then '
            'File → Export Image and save the PNG/SVG next to the '
            '<code>.circuit</code> file (same stem). The display will pick it up.'
            '</div>'
            '</div>'
        )
    raise ValueError(f"unsupported schematic file type: {suf}")


def _img_tag(p: Path) -> str:
    rel = "/api/files/" + p.as_posix().lstrip("./")
    return f'<div class="schematic"><img src="{html_mod.escape(rel)}" alt="circuit"></div>'


_SCHEMATIC_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{title}</title>
  <link rel="stylesheet" href="/core/theme.css">
  <style>
    *, *::before, *::after {{ margin: 0; padding: 0; box-sizing: border-box; }}
    html, body {{ height: 100%; background: var(--void); color: var(--text-hi); font-family: var(--font); font-size: 12px; overflow: hidden; }}
    #wrap {{ display: flex; flex-direction: column; height: 100%; }}
    .caption {{ padding: 8px 12px; font-size: 11px; color: var(--text-mid); border-bottom: 1px solid var(--border); }}
    .schematic {{ flex: 1; display: flex; align-items: center; justify-content: center; min-height: 0; position: relative; background: #fff; }}
    .schematic.empty {{ background: var(--void); color: var(--text-mid); padding: 32px; text-align: center; font-size: 13px; flex-direction: column; gap: 12px; }}
    .schematic.empty .hint {{ color: var(--text-dim); font-size: 11px; max-width: 360px; line-height: 1.5; }}
    .schematic.empty code {{ font-family: var(--font-mono, monospace); color: var(--accent); font-size: 11px; }}
    .schematic.svg-wrap svg {{ max-width: 100%; max-height: 100%; }}
    .schematic img {{ max-width: 100%; max-height: 100%; }}
  </style>
</head>
<body>
  <div id="wrap">
    {caption}
    {body}
  </div>
</body>
</html>
"""


def _require_plotly():
    try:
        import plotly.graph_objects as go  # noqa: F401
        from plotly.subplots import make_subplots  # noqa: F401
    except ModuleNotFoundError as e:
        raise ModuleNotFoundError(
            "plotly is required for displays/circuitjs.py — "
            "install with: pip install plotly"
        ) from e


def show_circuitjs_waveform(path: str | Path, *,
                            title: Optional[str] = None,
                            name: Optional[str] = None,
                            display_id: Optional[str] = None) -> None:
    """Load a waveform JSON from CircuitJS and render a time-domain plot.

    Args:
        path: path to the JSON file with `{t, v}` or `{t, probes}` shape.
        title: optional plot title (defaults to the file stem).
        name: if given, writes to `<name>.html` — appears as a named tab.
        display_id: alias for `name`.
    """
    _require_plotly()
    import plotly.graph_objects as go

    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"waveform file not found: {p}")
    data = json.loads(p.read_text(encoding="utf-8"))
    t = data.get("t") or []
    if not t:
        raise ValueError(f"waveform has no time axis: {p}")

    fig = go.Figure()
    if "v" in data:
        fig.add_trace(go.Scatter(x=t, y=data["v"], mode="lines", name="v"))
    elif "probes" in data:
        for probe_name, values in data["probes"].items():
            fig.add_trace(go.Scatter(x=t, y=values, mode="lines", name=probe_name))
    else:
        raise ValueError(f"waveform has no v / probes array: {p}")

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=BG_VOID,
        plot_bgcolor=BG_SURFACE,
        font=dict(family=FONT.replace("'", ""), color=TEXT_PRIMARY),
        margin=dict(l=50, r=20, t=40, b=40),
        title=title or p.stem,
        xaxis_title="time (s)",
        yaxis_title="voltage (V)",
        autosize=True,
    )
    html = fig.to_html(
        include_plotlyjs="cdn",
        full_html=True,
        default_width="100%",
        default_height="100%",
        config={"displayModeBar": True, "displaylogo": False, "responsive": True},
    )
    html = html.replace("<body>",
                        f'<body style="background:{BG_VOID};margin:0;height:100vh;">')
    html = html.replace(
        "<head>",
        "<head><style>html,body{height:100%;margin:0}"
        ".plotly-graph-div{width:100%!important;height:100%!important}</style>",
        1,
    )

    out, effective = resolve_display_path(
        name=name, display_id=display_id,
        default_filename=f"{p.stem}.html", extension=".html",
    )
    atomic_write_text(out / effective, html)


def show_circuitjs_bode(freqs, magnitudes, phases, *,
                        title: Optional[str] = None,
                        name: Optional[str] = None,
                        display_id: Optional[str] = None) -> None:
    """Render a Bode plot (magnitude + phase subplots) from arrays.

    Args:
        freqs: array of frequencies (Hz). Log axis by default.
        magnitudes: array of magnitudes (dB).
        phases: array of phases (degrees).
        title: optional plot title.
        name / display_id: named-tab stem.
    """
    _require_plotly()
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        subplot_titles=("magnitude (dB)", "phase (deg)"),
                        vertical_spacing=0.12)
    fig.add_trace(go.Scatter(x=list(freqs), y=list(magnitudes),
                             mode="lines", name="|H(f)|"), row=1, col=1)
    fig.add_trace(go.Scatter(x=list(freqs), y=list(phases),
                             mode="lines", name="∠H(f)"), row=2, col=1)
    fig.update_xaxes(type="log", title_text="frequency (Hz)", row=2, col=1)
    fig.update_yaxes(title_text="dB", row=1, col=1)
    fig.update_yaxes(title_text="deg", row=2, col=1)

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=BG_VOID,
        plot_bgcolor=BG_SURFACE,
        font=dict(family=FONT.replace("'", ""), color=TEXT_PRIMARY),
        margin=dict(l=60, r=20, t=60, b=40),
        title=title or "Bode plot",
        showlegend=False,
        autosize=True,
    )
    html = fig.to_html(
        include_plotlyjs="cdn",
        full_html=True,
        default_width="100%",
        default_height="100%",
        config={"displayModeBar": True, "displaylogo": False, "responsive": True},
    )
    html = html.replace("<body>",
                        f'<body style="background:{BG_VOID};margin:0;height:100vh;">')
    html = html.replace(
        "<head>",
        "<head><style>html,body{height:100%;margin:0}"
        ".plotly-graph-div{width:100%!important;height:100%!important}</style>",
        1,
    )

    out, effective = resolve_display_path(
        name=name, display_id=display_id,
        default_filename="bode.html", extension=".html",
    )
    atomic_write_text(out / effective, html)
