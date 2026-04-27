"""Dashboard queue -- main agent's handoff to the /dashboard subagent.

The main agent writes intent ("training-curve display, EMA vs raw, stage 5-6,
30s refresh") via `request_display()`. The /dashboard skill (spawned by
`/loop 30s /dashboard`) drains the queue, builds the display, marks the
request done.

Queue file: `workspace/research/dashboard-queue.json`
Shape:
  {
    "pending":   [{"id", "intent", "data_path", "ts"}],
    "completed": [{"id", "output_path", "ts"}]
  }

Why a queue instead of a direct display call? Building a new display addon,
polishing a one-off chart, or cleaning the output pool can interrupt the
main agent's main thread. The queue lets main say "I want this shape of
display" without switching into CSS/layout mode.
"""

from __future__ import annotations

import contextlib
import json
import os
import time
import uuid
from pathlib import Path
from typing import Any, Optional

from core.paths import RESEARCH_DIR as DEFAULT_DIR


QUEUE_FILE = "dashboard-queue.json"
LOCK_SUFFIX = ".lock"
LOCK_TIMEOUT = 5.0
LOCK_STALE_AGE = 15.0


def _file(research_dir: Optional[Path]) -> Path:
    d = Path(research_dir) if research_dir else DEFAULT_DIR
    d.mkdir(parents=True, exist_ok=True)
    return d / QUEUE_FILE


@contextlib.contextmanager
def _locked(research_dir: Optional[Path]):
    """Cross-platform advisory lock around the queue file.

    Uses atomic `os.O_CREAT | os.O_EXCL` creation of a sibling `.lock` file
    as the mutex. Polls with a short sleep until acquired or timeout. A
    stale lock (older than LOCK_STALE_AGE seconds) is broken so a crashed
    holder can't wedge the queue forever.
    """
    lock_path = _file(research_dir).with_suffix(
        _file(research_dir).suffix + LOCK_SUFFIX
    )
    deadline = time.monotonic() + LOCK_TIMEOUT
    fd = None
    while True:
        try:
            fd = os.open(str(lock_path),
                         os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            break
        except FileExistsError:
            try:
                age = time.time() - os.path.getmtime(lock_path)
                if age > LOCK_STALE_AGE:
                    os.unlink(lock_path)
                    continue
            except OSError:
                pass
            if time.monotonic() >= deadline:
                raise TimeoutError(f"dashboard queue lock busy: {lock_path}")
            time.sleep(0.01)
    try:
        yield
    finally:
        try:
            os.close(fd)
        finally:
            try:
                os.unlink(lock_path)
            except OSError:
                pass


def _read(research_dir: Optional[Path]) -> dict[str, list]:
    f = _file(research_dir)
    if not f.exists():
        return {"pending": [], "completed": []}
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"pending": [], "completed": []}
    data.setdefault("pending", [])
    data.setdefault("completed", [])
    return data


def _write_atomic(research_dir: Optional[Path], data: dict) -> None:
    f = _file(research_dir)
    tmp = f.with_name(f.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    os.replace(tmp, f)


def request_display(intent: str, data_path: Optional[str] = None,
                    *, research_dir: Optional[Path] = None) -> str:
    """Main agent side -- queue a display request. Returns the request id.

    `intent` is a plain-English sentence ("training-curve, EMA vs raw,
    stages 5-6"). `data_path` optionally points the dashboard agent at
    the data it should plot (a file or directory under workspace/files/).
    """
    req_id = f"d{uuid.uuid4().hex[:8]}"
    with _locked(research_dir):
        data = _read(research_dir)
        data["pending"].append({
            "id": req_id,
            "intent": intent,
            "data_path": data_path,
            "ts": time.time(),
        })
        _write_atomic(research_dir, data)
    return req_id


def drain_requests(research_dir: Optional[Path] = None) -> list[dict[str, Any]]:
    """Dashboard-agent side -- return all pending requests and clear pending.

    Caller is expected to handle each request, then call `mark_done(id, output_path)`
    per completed request.
    """
    with _locked(research_dir):
        data = _read(research_dir)
        requests = list(data["pending"])
        data["pending"] = []
        _write_atomic(research_dir, data)
    return requests


def mark_done(request_id: str, output_path: str,
              *, research_dir: Optional[Path] = None) -> None:
    """Dashboard-agent side -- record that a request produced output_path."""
    with _locked(research_dir):
        data = _read(research_dir)
        data["completed"].append({
            "id": request_id,
            "output_path": output_path,
            "ts": time.time(),
        })
        _write_atomic(research_dir, data)


def pending_count(research_dir: Optional[Path] = None) -> int:
    """Return the number of pending requests (for status panels / hooks)."""
    return len(_read(research_dir)["pending"])
