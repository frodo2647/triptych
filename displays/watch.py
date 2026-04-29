"""Watch display addon — agent-facing window watcher.

The full watcher UI lives at `workspaces/watch.html` (picker + live preview
of any visible desktop window). This display addon wraps it in an iframe
so it can appear as a tab in the *display* panel — useful when the agent
wants to keep an eye on an external app (terminal, simulator, browser
window) without taking over the workspace pane.

Usage:
    from displays import show_watch
    show_watch()                # picker UI for the user to pick a window
    show_watch(name="terminal") # named tab — appears as "terminal" in the bar

The actual capture pipeline (win32 enumeration + screenshots) lives in
`scripts/watch.py` and is exposed via the `/api/watch/*` HTTP endpoints —
this module just renders an iframe pointed at the workspace UI.

Windows-only for now (uses win32gui under the hood). Browser-tab capture
is planned but not in this version.
"""

from __future__ import annotations

from typing import Optional

from ._base import atomic_write_text, resolve_display_path


def show_watch(*, name: Optional[str] = None,
               display_id: Optional[str] = None) -> None:
    """Render a Watch tab in the display panel.

    Embeds the existing watcher UI (window picker + live preview) so the
    agent can keep an eye on an external app while the workspace pane
    stays free for other work.

    Args:
        name / display_id: named-tab stem (defaults to "watch").
    """
    out, effective = resolve_display_path(
        name=name, display_id=display_id,
        default_filename="watch.html", extension=".html",
    )
    atomic_write_text(out / effective, _WATCH_TEMPLATE)


_WATCH_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Watch</title>
  <link rel="stylesheet" href="/core/theme.css">
  <style>
    *, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }
    html, body { height: 100%; overflow: hidden; background: var(--void); color: var(--text-hi); font-family: var(--font); font-size: 12px; }
    iframe { width: 100%; height: 100%; border: none; background: var(--void); }
  </style>
</head>
<body>
  <iframe src="/workspaces/watch.html"></iframe>
</body>
</html>
"""
