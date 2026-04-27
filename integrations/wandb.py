"""Weights & Biases integration — reference ExternalTool.

W&B is the canonical "external done right" case (per trial-1 report §3.4):
iframing it fights the auth wall, users already have accounts, and the
app is built for full-window use. Instead, we link out and render a
small summary panel in Triptych.

What this module does:
  - Check for WANDB_API_KEY in the environment or ~/.netrc.
  - Pull a one-run summary via the public W&B API (best metric, last
    update, run URL).
  - Render a compact HTML panel into workspace/output/ with a big link
    to the full dashboard and a few key numbers.
  - Persist the run URL + panel stem into research/integrations.json so
    other sessions can find it without re-running the HPO.

The actual `wandb` SDK is imported lazily so Triptych doesn't force the
dependency on users who don't use W&B. If the SDK is missing, the panel
still renders (with a "install wandb" hint) so the integration's shape
is always visible in the display pool.
"""

from __future__ import annotations

import html
import os
import re
from pathlib import Path
from typing import Any, Optional

from core.paths import OUTPUT_DIR
from displays._base import atomic_write_text

from ._base import ExternalTool


class WandBRun(ExternalTool):
    """Summary panel for a single W&B run.

    Usage:
        run = WandBRun(entity="quinn", project="mnist", run_id="abc123")
        if run.is_authenticated():
            run.render_panel(run.fetch_summary())
            run.record(url=run.dashboard_url(), run_id=run.run_id)
    """

    def __init__(self, entity: str, project: str, run_id: str,
                 *, panel_stem: Optional[str] = None):
        safe_run = re.sub(r'[^A-Za-z0-9_.-]', '-', run_id).strip('-.') or 'run'
        super().__init__(
            name=f"wandb:{entity}/{project}/{run_id}",
            panel_stem=panel_stem or f"wandb-{safe_run}",
        )
        self.entity = entity
        self.project = project
        self.run_id = run_id

    # ── Identity ─────────────────────────────────────────────

    def dashboard_url(self) -> str:
        return f"https://wandb.ai/{self.entity}/{self.project}/runs/{self.run_id}"

    # ── Auth ─────────────────────────────────────────────────

    def is_authenticated(self) -> bool:
        """True when WANDB_API_KEY is set or ~/.netrc has a wandb entry."""
        if os.environ.get("WANDB_API_KEY"):
            return True
        netrc = Path.home() / ".netrc"
        if netrc.exists():
            try:
                txt = netrc.read_text(encoding="utf-8", errors="ignore")
                return "machine api.wandb.ai" in txt
            except OSError:
                return False
        return False

    # ── Data ─────────────────────────────────────────────────

    def fetch_summary(self) -> dict[str, Any]:
        """Pull run summary via wandb.Api. Raises if the SDK isn't installed."""
        try:
            import wandb  # noqa: F401  # side-effect: ensures SDK is present
            from wandb.apis.public import Api
        except ImportError as e:
            raise RuntimeError(
                "wandb SDK not installed. `pip install wandb` and run "
                "`wandb login` before calling fetch_summary()."
            ) from e

        api = Api()
        run = api.run(f"{self.entity}/{self.project}/{self.run_id}")
        return {
            "name": run.name or self.run_id,
            "state": run.state,
            "summary": dict(run.summary._json_dict) if hasattr(run.summary, "_json_dict") else dict(run.summary),
            "config": dict(run.config),
            "tags": list(run.tags or []),
            "url": run.url,
        }

    # ── Render ───────────────────────────────────────────────

    def render_panel(self, summary: Optional[dict[str, Any]] = None) -> None:
        """Write a compact summary panel to workspace/output/<panel_stem>.html.

        Works even without the SDK installed — passes `summary=None` and
        renders a "not connected" card pointing at the dashboard URL.
        """
        out = OUTPUT_DIR / f"{self.panel_stem}.html"
        out.parent.mkdir(parents=True, exist_ok=True)

        authed = self.is_authenticated()
        url = html.escape(self.dashboard_url())

        if summary is None:
            body_inner = self._render_stub(authed, url)
        else:
            body_inner = self._render_summary(summary, url)

        page = _PANEL_TEMPLATE.format(
            title=html.escape(f"W&B — {self.run_id}"),
            body=body_inner,
        )
        atomic_write_text(out, page)

    # ── Private ──────────────────────────────────────────────

    def _render_stub(self, authed: bool, url: str) -> str:
        hint = ("WANDB_API_KEY not set — install the SDK and run `wandb login` "
                "to enable the summary.") if not authed else (
                "Install the `wandb` Python SDK to enable the summary panel.")
        return f"""
<div class="card">
  <div class="eyebrow">Weights &amp; Biases</div>
  <div class="headline">Run <code>{html.escape(self.run_id)}</code></div>
  <p class="hint">{html.escape(hint)}</p>
  <a class="button" href="{url}" target="_blank" rel="noopener">
    Open dashboard &rarr;
  </a>
</div>
"""

    def _render_summary(self, summary: dict[str, Any], url: str) -> str:
        metrics = summary.get("summary", {}) or {}
        top = sorted(
            ((k, v) for k, v in metrics.items() if isinstance(v, (int, float))),
            key=lambda kv: -abs(kv[1]) if isinstance(kv[1], (int, float)) else 0,
        )[:6]
        metric_rows = "".join(
            f'<div class="metric"><span class="metric-k">{html.escape(k)}</span>'
            f'<span class="metric-v">{_fmt_num(v)}</span></div>'
            for k, v in top
        ) or '<div class="metric"><span class="metric-k">no scalar metrics</span></div>'

        tags = "".join(f'<span class="tag">{html.escape(t)}</span>' for t in summary.get("tags", []))
        state = html.escape(str(summary.get("state", "unknown")))
        name = html.escape(str(summary.get("name", self.run_id)))

        return f"""
<div class="card">
  <div class="eyebrow">Weights &amp; Biases &middot; <span class="state state-{state}">{state}</span></div>
  <div class="headline">{name}</div>
  <div class="tags">{tags}</div>
  <div class="metrics">{metric_rows}</div>
  <a class="button" href="{url}" target="_blank" rel="noopener">
    Open in W&amp;B &rarr;
  </a>
</div>
"""


def _fmt_num(v: Any) -> str:
    if isinstance(v, float):
        if abs(v) >= 1000 or (abs(v) > 0 and abs(v) < 0.01):
            return f"{v:.3e}"
        return f"{v:.4f}"
    return str(v)


_PANEL_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{title}</title>
  <link rel="stylesheet" href="/core/theme.css">
  <style>
    body {{
      margin: 0;
      padding: 24px;
      background: var(--void);
      color: var(--text-hi);
      font-family: var(--font), system-ui, sans-serif;
      font-size: 13px;
    }}
    .card {{
      max-width: 520px;
      margin: 24px auto;
      padding: 20px 24px;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 6px;
    }}
    .eyebrow {{
      font-size: 10px;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: var(--text-dim);
      margin-bottom: 6px;
    }}
    .headline {{
      font-size: 18px;
      font-weight: 500;
      margin-bottom: 12px;
    }}
    code {{ font-family: var(--font-mono), monospace; font-size: 12px; color: var(--accent); }}
    .hint {{
      color: var(--text-mid);
      font-size: 12px;
      margin: 8px 0 16px;
    }}
    .tags {{ margin-bottom: 12px; display: flex; gap: 6px; flex-wrap: wrap; }}
    .tag {{
      background: var(--surface-2);
      border: 1px solid var(--border);
      padding: 2px 6px;
      border-radius: 3px;
      font-size: 10px;
      color: var(--text-mid);
    }}
    .metrics {{ display: grid; grid-template-columns: 1fr 1fr; gap: 4px 16px; margin: 12px 0; }}
    .metric {{ display: flex; justify-content: space-between; font-size: 12px; padding: 3px 0; border-bottom: 1px dotted var(--border); }}
    .metric-k {{ color: var(--text-mid); }}
    .metric-v {{ color: var(--text-hi); font-variant-numeric: tabular-nums; }}
    .state {{ font-size: 10px; padding: 1px 5px; border-radius: 2px; }}
    .state-running {{ color: var(--accent); }}
    .state-finished {{ color: var(--text-hi); }}
    .state-failed {{ color: #d47567; }}
    .button {{
      display: inline-block;
      margin-top: 12px;
      padding: 6px 12px;
      background: var(--surface-2);
      border: 1px solid var(--border);
      border-radius: 3px;
      color: var(--text-hi);
      text-decoration: none;
      font-size: 12px;
    }}
    .button:hover {{ background: var(--surface-3); }}
  </style>
</head>
<body>
  {body}
</body>
</html>
"""