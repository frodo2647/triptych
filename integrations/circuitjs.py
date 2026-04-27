"""CircuitJS integration -- reference EmbeddedTool.

CircuitJS is the canonical embed case per trial-1 report §3.4 and
docs/internal/use-cases.md: pure-web, no auth wall, iframes cleanly.
This is the reference EmbeddedTool implementation, paired with the
workspace addon at `workspaces/circuitjs.html` and the display helpers
at `displays/circuitjs.py`.

What this module does:
  - Knows the iframe URL (default: falstad.com/circuit/circuitjs.html).
  - Writes a minimal panel HTML to `workspace/output/<panel_stem>.html`
    that just redirects into the workspace (CircuitJS's home is the
    workspace panel, not the display; the display is for analysis).
  - Persists the session record to research/integrations.json so other
    sessions can see a CircuitJS run is in use.

Unlike W&B (ExternalTool), CircuitJS has no auth, no subprocess Triptych
has to manage (Falstad hosts it), and no SDK to import. `start()` /
`stop()` are effectively no-ops — the iframe is live whenever the
workspace panel is open on the circuitjs tab.
"""

from __future__ import annotations

import html as html_mod
import re
from typing import Optional

from core.paths import OUTPUT_DIR
from displays._base import atomic_write_text

from ._base import EmbeddedTool


DEFAULT_IFRAME_URL = "https://www.falstad.com/circuit/circuitjs.html"


class CircuitJSSession(EmbeddedTool):
    """Embedded CircuitJS session record.

    Usage:
        c = CircuitJSSession(name="rc-filter")
        c.record(workspace_tab="circuitjs", notes="RC low-pass, fc=1kHz")
        c.render_panel()  # writes a tiny pointer panel to workspace/output/

    The actual circuit lives in the Falstad iframe in the workspace panel.
    This session object is bookkeeping: it pins the iframe URL + any
    notes in research state so a future session knows a CircuitJS run
    was in use.
    """

    def __init__(self, name: str, *,
                 iframe_url: str = DEFAULT_IFRAME_URL,
                 panel_stem: Optional[str] = None):
        safe_name = re.sub(r'[^A-Za-z0-9_.-]', '-', name).strip('-.') or 'session'
        super().__init__(name=f"circuitjs:{name}",
                         panel_stem=panel_stem or f"circuitjs-{safe_name}")
        self.iframe_url = iframe_url

    # ── Lifecycle (no-ops, Falstad hosts the subprocess) ────────────

    def start(self) -> None:
        """No-op. Falstad hosts the iframe; it's live when the workspace opens."""
        pass

    def stop(self) -> None:
        """No-op. The iframe dies with the workspace panel."""
        pass

    def is_running(self) -> bool:
        """Always True — the iframe is Falstad's responsibility, not ours."""
        return True

    # ── Panel ───────────────────────────────────────────────────────

    def render_panel(self, notes: Optional[str] = None) -> None:
        """Write a compact pointer panel to workspace/output/<panel_stem>.html.

        The panel just says "CircuitJS is live in the workspace tab" with a
        link to open the workspace. Keep this small — CircuitJS's UI is the
        workspace iframe, not the display.
        """
        out = OUTPUT_DIR / f"{self.panel_stem}.html"
        out.parent.mkdir(parents=True, exist_ok=True)

        note_html = ""
        if notes:
            note_html = f'<p class="note">{html_mod.escape(notes)}</p>'

        page = _PANEL_TEMPLATE.format(
            title=html_mod.escape(f"CircuitJS — {self.name.split(':', 1)[-1]}"),
            url=html_mod.escape(self.iframe_url),
            note_html=note_html,
        )
        atomic_write_text(out, page)


_PANEL_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{title}</title>
  <link rel="stylesheet" href="/core/theme.css">
  <style>
    body {{
      margin: 0; padding: 24px;
      background: var(--void); color: var(--text-hi);
      font-family: var(--font), system-ui, sans-serif; font-size: 13px;
    }}
    .card {{
      max-width: 480px; margin: 24px auto;
      padding: 20px 24px;
      background: var(--surface); border: 1px solid var(--border); border-radius: 6px;
    }}
    .eyebrow {{
      font-size: 10px; letter-spacing: 0.12em; text-transform: uppercase;
      color: var(--text-dim); margin-bottom: 6px;
    }}
    .headline {{ font-size: 18px; font-weight: 500; margin-bottom: 12px; }}
    .note {{ color: var(--text-mid); font-size: 12px; margin: 8px 0 16px; }}
    .hint {{ color: var(--text-dim); font-size: 11px; margin-top: 20px; }}
    .button {{
      display: inline-block; margin-top: 12px;
      padding: 6px 12px;
      background: var(--surface-2); border: 1px solid var(--border); border-radius: 3px;
      color: var(--text-hi); text-decoration: none; font-size: 12px;
    }}
    .button:hover {{ background: var(--surface-3); }}
    code {{ font-family: var(--font-mono), monospace; font-size: 11px; color: var(--accent); }}
  </style>
</head>
<body>
  <div class="card">
    <div class="eyebrow">CircuitJS · Embedded</div>
    <div class="headline">{title}</div>
    {note_html}
    <p class="hint">The live circuit is in the workspace panel (circuitjs tab). For analysis plots — Bode, transient — use <code>displays.circuitjs.show_circuitjs_waveform()</code> or <code>show_circuitjs_bode()</code>.</p>
    <a class="button" href="{url}" target="_blank" rel="noopener">Open CircuitJS in new tab →</a>
  </div>
</body>
</html>
"""
