"""Session persistence -- track the active goal and phase across sessions.

Written to `workspace/research/session.json`. Consumed by the SessionStart
hook to inject goal/phase context, and by `/first-boot` Stage 2 to seed the
session when a new goal is elicited. `lastActive` is pinged on every
research-state write so staleness checks are meaningful.

This is an intentionally thin module. Session intent lives in `session.json`;
the research-state fields (Goal, Assumptions, ...) live in `state.md`. The
two are kept in sync via `init_research()` which calls `write_session()`.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Optional

from core.paths import RESEARCH_DIR as DEFAULT_DIR


SESSION_FILE = "session.json"
PHASES = ("exploration", "formalization")
MODES = ("single-agent", "team")


def _file(research_dir: Optional[Path]) -> Path:
    d = Path(research_dir) if research_dir else DEFAULT_DIR
    d.mkdir(parents=True, exist_ok=True)
    return d / SESSION_FILE


def _write_atomic(path: Path, text: str) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def _soft_write_atomic(path: Path, text: str) -> bool:
    """Like _write_atomic but swallows PermissionError/OSError.

    On Windows the SessionStart hook (Node) can hold a read handle on
    session.json briefly, which races os.replace from Python. Bookkeeping
    writes from touch_session() shouldn't raise into research callers when
    that happens — lastActive is a hint, not correctness.
    """
    try:
        _write_atomic(path, text)
        return True
    except (PermissionError, OSError):
        return False


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def read_session(research_dir: Optional[Path] = None) -> Optional[dict]:
    """Return the session dict, or None if unset."""
    f = _file(research_dir)
    if not f.exists():
        return None
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def write_session(goal: str, phase: str, *, mode: Optional[str] = None,
                  research_dir: Optional[Path] = None) -> dict:
    """Create or replace session.json with a goal + phase (+ mode).

    Resets lastActive to now. Use `touch_session()` to refresh lastActive
    without changing the goal.
    """
    if phase not in PHASES:
        raise ValueError(f"phase must be one of {PHASES}, got {phase!r}")
    if mode is not None and mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}, got {mode!r}")
    now = _now_iso()
    data = {
        "goal": goal,
        "phase": phase,
        "mode": mode or "single-agent",
        "setAt": now,
        "lastActive": now,
    }
    _write_atomic(_file(research_dir), json.dumps(data, indent=2))
    return data


def touch_session(research_dir: Optional[Path] = None) -> Optional[dict]:
    """Refresh lastActive. No-op (returns None) when no session exists."""
    data = read_session(research_dir)
    if data is None:
        return None
    data["lastActive"] = _now_iso()
    _soft_write_atomic(_file(research_dir), json.dumps(data, indent=2))
    return data


def clear_session(research_dir: Optional[Path] = None) -> None:
    """Remove session.json. Use when a goal completes or is abandoned."""
    f = _file(research_dir)
    if f.exists():
        f.unlink()
