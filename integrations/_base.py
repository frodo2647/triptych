"""Base classes for Triptych integrations.

An integration is the bridge between Triptych and an external tool the
agent hands work off to (experiment tracker, CAD viewer, circuit simulator,
notebook runner). Two shapes cover the field:

    EmbeddedTool    tool renders inside a display tab; Triptych owns its
                    subprocess or iframe. Good when the tool has a clean
                    iframe API, renders well at panel size, and has
                    permissive CORS / no auth wall.

    ExternalTool    tool runs outside Triptych (separate browser window,
                    desktop app, cloud service); Triptych shows a compact
                    summary panel and pins the external URL in research
                    state. Good when the tool is the de-facto standard,
                    users already have accounts, or its UX fights a
                    sub-panel viewport.

Pick EmbeddedTool when you control or can iframe the UI cleanly. Pick
ExternalTool when iframing would fight the tool rather than help it. User
preference always wins -- if the user says "just link out," that's the call.

Both shapes persist a per-integration record to
`workspace/research/integrations.json` and produce a display panel
identified by stem.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Optional

from core.paths import RESEARCH_DIR as DEFAULT_RESEARCH_DIR


def _integrations_file(research_dir: Optional[Path]) -> Path:
    d = Path(research_dir) if research_dir else DEFAULT_RESEARCH_DIR
    d.mkdir(parents=True, exist_ok=True)
    return d / "integrations.json"


def _read_integrations(research_dir: Optional[Path]) -> dict[str, Any]:
    f = _integrations_file(research_dir)
    if not f.exists():
        return {}
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _record(name: str, panel_stem: str, kind: str,
            research_dir: Optional[Path], fields: dict[str, Any]) -> None:
    data = _read_integrations(research_dir)
    entry = data.setdefault(name, {})
    entry.update({
        "kind": kind,
        "panel_stem": panel_stem,
        "updated_at": time.time(),
        **fields,
    })
    f = _integrations_file(research_dir)
    tmp = f.with_name(f.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    os.replace(tmp, f)


class EmbeddedTool:
    """Tool that renders inside a display tab.

    Concrete subclasses typically:
      1. Start (or attach to) a local subprocess in `start()`.
      2. Write an HTML tab to `workspace/output/<panel_stem>.html` whose
         body is an `<iframe src="...">`.
      3. Stop the subprocess in `stop()`.
    """

    kind = "embedded"

    def __init__(self, name: str, *, panel_stem: Optional[str] = None):
        self.name = name
        self.panel_stem = panel_stem or f"integration-{name}"

    def record(self, *, research_dir: Optional[Path] = None, **fields: Any) -> None:
        """Write/update this integration's entry in research/integrations.json."""
        _record(self.name, self.panel_stem, self.kind, research_dir, fields)

    def start(self) -> None:
        """Start the underlying subprocess / server. Idempotent."""
        raise NotImplementedError

    def stop(self) -> None:
        """Stop the subprocess. Idempotent."""
        raise NotImplementedError

    def is_running(self) -> bool:
        """Return True when the embedded subprocess is up."""
        raise NotImplementedError


class ExternalTool:
    """Tool that runs outside Triptych; we show a summary panel + pin the URL.

    Concrete subclasses typically:
      1. Check availability / auth in `is_authenticated()`.
      2. Fetch a compact data summary via the tool's API in `fetch_summary()`.
      3. Render that summary into `workspace/output/<panel_stem>.html` with
         the external URL prominent.
      4. Call `self.record(url=..., summary=...)` so the run URL lands in
         research state.
    """

    kind = "external"

    def __init__(self, name: str, *, panel_stem: Optional[str] = None):
        self.name = name
        self.panel_stem = panel_stem or f"integration-{name}"

    def record(self, *, research_dir: Optional[Path] = None, **fields: Any) -> None:
        """Write/update this integration's entry in research/integrations.json."""
        _record(self.name, self.panel_stem, self.kind, research_dir, fields)

    def is_authenticated(self) -> bool:
        """Return True when credentials are present and usable."""
        raise NotImplementedError

    def fetch_summary(self) -> dict[str, Any]:
        """Return a summary dict for rendering. Raise on error."""
        raise NotImplementedError

    def render_panel(self, summary: dict[str, Any]) -> None:
        """Write the summary panel HTML to workspace/output/<panel_stem>.html."""
        raise NotImplementedError
