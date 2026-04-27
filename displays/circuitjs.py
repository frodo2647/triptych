"""CircuitJS display — render analysis output from a Falstad waveform export.

CircuitJS itself runs in the workspace panel (`workspaces/circuitjs.html`).
This display renders the analysis view: Bode plot, transient response, or
a bare time-domain waveform, depending on what the workspace exported.

Typical flow:
  1. User designs a circuit in the workspace iframe.
  2. `window.TriptychCircuit.exportWaveform()` is called (via the paired
     integration in `integrations/circuitjs.py` or by the user clicking).
  3. The waveform data lands in `workspace/files/circuitjs/<stem>.json`.
  4. `show_circuitjs_waveform(path)` loads it and writes a Plotly display
     to `workspace/output/<stem>.html`.

The JSON shape Falstad exports is small: `{ t: [...], v: [...] }` for a
single probe, or `{ t: [...], probes: { name: [...] } }` for multiple.
This module handles both shapes.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from ._base import (BG_VOID, BG_SURFACE, TEXT_PRIMARY, FONT,
                    atomic_write_text, resolve_display_path)


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
