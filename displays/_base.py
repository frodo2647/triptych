"""Shared constants and utilities for Triptych display addons."""

import json
import os
import shutil
import time
from pathlib import Path

from core.paths import OUTPUT_DIR

# Dark theme palette (warm browns — matches core/theme.css)
BG_VOID = '#151210'
BG_SURFACE = '#1e1a16'
TEXT_PRIMARY = '#d8d0c8'
TEXT_SECONDARY = '#968e84'
TEXT_DIM = '#685f56'
ACCENT = '#cc7a58'
ACCENT_BLUE = '#7a80d5'
ACCENT_GREEN = '#3cc497'
ACCENT_RED = '#d47567'
ACCENT_YELLOW = '#c4a045'
BORDER = '#3a332b'
FONT = "'Archivo', system-ui, sans-serif"
FONT_MONO = "'JetBrains Mono', monospace"


def atomic_write_text(path, content, encoding='utf-8'):
    """Write text atomically: write to .tmp, then os.replace into place."""
    path = Path(path)
    tmp = path.with_name(path.name + '.tmp')
    tmp.write_text(content, encoding=encoding)
    os.replace(tmp, path)


def atomic_write_bytes(path, content):
    """Write bytes atomically: write to .tmp, then os.replace into place."""
    path = Path(path)
    tmp = path.with_name(path.name + '.tmp')
    tmp.write_bytes(content)
    os.replace(tmp, path)


def atomic_copy(src, dst):
    """Copy a file atomically: copy to .tmp, then os.replace into place."""
    dst = Path(dst)
    tmp = dst.with_name(dst.name + '.tmp')
    shutil.copy2(src, tmp)
    os.replace(tmp, dst)


def resolve_display_path(name=None, display_id=None, default_filename='index.html',
                          extension=None, output_dir=None, force_extension=False):
    """Compute the output file path for a display call.

    Display addons accept an optional `name` (or `display_id` alias) to write
    their output to a named file instead of the default `index.html`. Tabs in
    the display panel correspond to files in `workspace/output/`, so giving
    two calls different names makes them appear as distinct tabs.

    - `name="training"` with extension `.html` → `workspace/output/training.html`
    - `name=None` → `workspace/output/<default_filename>`
    - If the name already contains an extension (e.g. `training.html`), it's
      preserved; otherwise `extension` (or default_filename's extension) is
      appended.

    `force_extension=True` (for binary addons like image/pdf) always ensures
    the filename ends with `extension` — appends it even if `name` already
    contains a dot. This avoids silently producing a file with a wrong MIME
    type when the name has a version suffix like `v1.2`.
    """
    out = Path(output_dir) if output_dir else OUTPUT_DIR
    out.mkdir(parents=True, exist_ok=True)

    effective_name = name if name is not None else display_id
    if effective_name is None:
        return out, default_filename

    # Sanitise: allow letters/digits/dash/underscore/dot only. Prevents
    # accidental path traversal via slashes or null bytes.
    import re
    safe = re.sub(r'[^A-Za-z0-9_.-]', '-', str(effective_name))
    safe = safe.strip('-.') or 'display'

    ext = extension or Path(default_filename).suffix or '.html'
    if not ext.startswith('.'):
        ext = '.' + ext

    if force_extension:
        if not safe.lower().endswith(ext.lower()):
            safe += ext
    elif '.' not in safe:
        safe += ext
    return out, safe


def focus_display(name='index', output_dir=None):
    """Tell the display panel to switch to a specific tab.

    `name` matches the display stem (the filename minus extension). Pass
    `"index"` for the Main tab, or e.g. `"training"` for a named display
    written by `show_progress(name="training")`.

    Works by writing a `.focus` marker file that the display iframe polls.
    """
    out = Path(output_dir) if output_dir else OUTPUT_DIR
    out.mkdir(parents=True, exist_ok=True)
    payload = json.dumps({'stem': str(name), 'ts': time.time()})
    atomic_write_text(out / '.focus', payload)


def active_display(output_dir=None):
    """Return the stem of the tab the user is currently viewing, or None.

    Reads `workspace/output/.userFocus`, which the display iframe writes on
    every user-initiated tab switch (click or keyboard). Distinct from
    `.focus` (the last programmatic `focus_display()` request) — this is
    what the human is *actually* looking at.

    Returns a dict `{"stem": str, "ts": float}` when the user has switched
    tabs at least once this session; `None` otherwise. `ts` is the
    server-side timestamp of the last switch, so callers can judge staleness
    (e.g. "was the user on this tab in the last 30 seconds?").
    """
    out = Path(output_dir) if output_dir else OUTPUT_DIR
    marker = out / '.userFocus'
    if not marker.exists():
        return None
    try:
        return json.loads(marker.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError):
        return None


def clear():
    """Clear all output files."""
    for f in OUTPUT_DIR.iterdir():
        if f.is_file():
            f.unlink()
    print('[display] Cleared output')


def clear_display(name):
    """Remove a single named display from the pool.

    `clear_display("training")` deletes `workspace/output/training.*`.
    """
    import re
    safe = re.sub(r'[^A-Za-z0-9_.-]', '-', str(name)).strip('-.')
    if not safe:
        return
    removed = 0
    for f in OUTPUT_DIR.iterdir():
        if f.is_file() and f.stem == safe:
            f.unlink()
            removed += 1
    print(f'[display] Cleared {removed} file(s) for "{name}"')


def cleanup_displays(keep=None):
    """Remove everything from the output pool except the given stems.

    Complements `clear()` (nuke all) and `clear_display(name)` (nuke one)
    for end-of-phase cleanup where you want to prune iteration residue
    but keep a few live tabs. Pass `keep=['research', 'index']` to retain
    those stems and delete the rest.

    Skips dotfiles (e.g. `.focus`) and preserves `research.html` by default
    since the research-state tab is meant to live across the whole session.
    Returns the number of files removed.
    """
    keep_set = {'research', 'index'}
    if keep:
        keep_set.update(str(k).lstrip('.') for k in keep)

    removed = 0
    kept = []
    for f in OUTPUT_DIR.iterdir():
        if not f.is_file() or f.name.startswith('.'):
            continue
        if f.stem in keep_set:
            kept.append(f.stem)
            continue
        f.unlink()
        removed += 1

    kept_desc = ', '.join(sorted(set(kept))) if kept else 'none'
    print(f'[display] Cleaned up {removed} file(s); kept: {kept_desc}')
    return removed
