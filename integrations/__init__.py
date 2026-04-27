"""Integrations -- wrappers for external tools Triptych hands work off to.

Two shapes: tools you *embed* (iframe in a display tab, subprocess owned by
Triptych) and tools you *link out* to (user runs them separately, Triptych
shows a summary panel + pins the URL in research state).

See `integrations/_base.py` for when to pick which.
"""

from ._base import EmbeddedTool, ExternalTool

__all__ = ["EmbeddedTool", "ExternalTool"]
