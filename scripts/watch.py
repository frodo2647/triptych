#!/usr/bin/env python3
"""Desktop window watcher for Triptych.

Captures screenshots of any visible window and saves them for Claude to read.

Usage:
    python scripts/watch.py list                  # List visible windows as JSON
    python scripts/watch.py capture <hwnd>        # One-shot capture
    python scripts/watch.py watch <hwnd> [interval]  # Continuous capture (default 3s)
"""

import sys
import os
import json
import time
import ctypes
from pathlib import Path

import win32gui
import win32process
import mss
from PIL import Image

# DPI awareness — get accurate window coordinates on scaled displays
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent
WATCH_DIR = PROJECT_ROOT / "workspace" / "snapshots" / "watch"
WATCH_DIR.mkdir(parents=True, exist_ok=True)

# Window titles to always skip
SKIP_TITLES = frozenset([
    '', 'Program Manager', 'Windows Shell Experience Host',
    'Windows Input Experience', 'Microsoft Text Input Application',
    'MSCTFIME UI', 'Default IME',
])


def list_windows():
    """Enumerate all visible, sizable windows."""
    windows = []

    def callback(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return True
        title = win32gui.GetWindowText(hwnd)
        if title in SKIP_TITLES:
            return True

        rect = win32gui.GetWindowRect(hwnd)
        w = rect[2] - rect[0]
        h = rect[3] - rect[1]
        if w < 100 or h < 100:
            return True

        # Get process name
        proc = ''
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            import psutil
            proc = psutil.Process(pid).name()
        except Exception:
            pass

        windows.append({
            'hwnd': hwnd,
            'title': title,
            'process': proc,
            'x': rect[0], 'y': rect[1],
            'width': w, 'height': h,
        })
        return True

    win32gui.EnumWindows(callback, None)
    # Sort: foreground window first, then by title
    fg = win32gui.GetForegroundWindow()
    windows.sort(key=lambda w: (0 if w['hwnd'] == fg else 1, w['title'].lower()))
    return windows


def capture_window(hwnd):
    """Capture a window screenshot via mss screen region grab."""
    hwnd = int(hwnd)
    if not win32gui.IsWindow(hwnd):
        return None, 'Window no longer exists'

    try:
        rect = win32gui.GetWindowRect(hwnd)
    except Exception as e:
        return None, f'Cannot get window rect: {e}'

    x, y, x2, y2 = rect
    w, h = x2 - x, y2 - y
    if w <= 0 or h <= 0:
        return None, 'Window is minimized or has no size'

    region = {'left': x, 'top': y, 'width': w, 'height': h}
    with mss.mss() as sct:
        shot = sct.grab(region)
        img = Image.frombytes('RGB', shot.size, shot.bgra, 'raw', 'BGRX')

    return img, None


def save_capture(img, hwnd, title=''):
    """Save screenshot and metadata to workspace/snapshots/watch/."""
    img_path = WATCH_DIR / 'latest.png'
    img.save(str(img_path), 'PNG', optimize=True)

    meta = {
        'hwnd': int(hwnd),
        'title': title,
        'width': img.width,
        'height': img.height,
        'timestamp': int(time.time() * 1000),
        'source': 'desktop-window',
    }
    (WATCH_DIR / 'latest.json').write_text(json.dumps(meta, indent=2))
    return meta


def cmd_list():
    print(json.dumps(list_windows(), indent=2))


def cmd_capture(hwnd):
    hwnd = int(hwnd)
    title = win32gui.GetWindowText(hwnd)
    img, err = capture_window(hwnd)
    if err:
        print(json.dumps({'error': err}))
        sys.exit(1)
    meta = save_capture(img, hwnd, title)
    print(json.dumps({'ok': True, **meta}))


def cmd_watch(hwnd, interval=3):
    hwnd = int(hwnd)
    interval = float(interval)
    title = win32gui.GetWindowText(hwnd)

    msg = {'status': 'watching', 'hwnd': hwnd, 'title': title, 'interval': interval}
    print(json.dumps(msg), flush=True)

    last_size = None
    while True:
        if not win32gui.IsWindow(hwnd):
            print(json.dumps({'status': 'stopped', 'reason': 'window_closed'}), flush=True)
            break

        img, err = capture_window(hwnd)
        if err:
            # Window might be minimized — wait and retry
            time.sleep(interval)
            continue

        # Only write if image changed (compare size as fast proxy)
        size = img.tobytes().__len__()  # raw byte count changes with content
        if size != last_size:
            try:
                title = win32gui.GetWindowText(hwnd)
            except Exception:
                pass
            save_capture(img, hwnd, title)
            last_size = size

        time.sleep(interval)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: watch.py list | capture <hwnd> | watch <hwnd> [interval]')
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == 'list':
        cmd_list()
    elif cmd == 'capture' and len(sys.argv) >= 3:
        cmd_capture(sys.argv[2])
    elif cmd == 'watch' and len(sys.argv) >= 3:
        iv = float(sys.argv[3]) if len(sys.argv) >= 4 else 3
        cmd_watch(sys.argv[2], iv)
    else:
        print('Usage: watch.py list | capture <hwnd> | watch <hwnd> [interval]')
        sys.exit(1)
