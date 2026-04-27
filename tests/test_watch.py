"""Tests for scripts/watch.py — desktop window watcher."""

import sys
import json
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from PIL import Image

# Make project root importable
sys.path.insert(0, str(Path(__file__).parent.parent))

PROJECT_ROOT = Path(__file__).parent.parent
WATCH_SCRIPT = str(PROJECT_ROOT / 'scripts' / 'watch.py')


# ── Unit Tests (mocked) ──────────────────────────────────────

class TestListWindows:
    """Test window enumeration."""

    def test_returns_list(self):
        """list_windows() returns a list of dicts."""
        from scripts.watch import list_windows
        result = list_windows()
        assert isinstance(result, list)

    def test_each_window_has_required_fields(self):
        """Each window dict has hwnd, title, width, height."""
        from scripts.watch import list_windows
        result = list_windows()
        # There should be at least one visible window on a running system
        if len(result) == 0:
            pytest.skip('No visible windows found (headless environment?)')
        for win in result:
            assert 'hwnd' in win
            assert 'title' in win
            assert 'width' in win
            assert 'height' in win
            assert isinstance(win['hwnd'], int)
            assert isinstance(win['title'], str)
            assert win['width'] >= 100
            assert win['height'] >= 100

    def test_skips_tiny_windows(self):
        """Windows smaller than 100x100 are filtered out."""
        from scripts.watch import list_windows
        result = list_windows()
        for win in result:
            assert win['width'] >= 100
            assert win['height'] >= 100

    def test_skips_system_windows(self):
        """Known system windows (Program Manager, etc.) are filtered."""
        from scripts.watch import list_windows, SKIP_TITLES
        result = list_windows()
        for win in result:
            assert win['title'] not in SKIP_TITLES


class TestSaveCapture:
    """Test saving captures to disk."""

    def test_saves_png_and_json(self, tmp_path):
        """save_capture writes latest.png and latest.json."""
        from scripts import watch
        # Monkeypatch WATCH_DIR
        original = watch.WATCH_DIR
        watch.WATCH_DIR = tmp_path
        try:
            img = Image.new('RGB', (100, 80), color='red')
            meta = watch.save_capture(img, 12345, 'Test Window')

            assert (tmp_path / 'latest.png').exists()
            assert (tmp_path / 'latest.json').exists()

            # Verify metadata
            data = json.loads((tmp_path / 'latest.json').read_text())
            assert data['hwnd'] == 12345
            assert data['title'] == 'Test Window'
            assert data['width'] == 100
            assert data['height'] == 80
            assert data['source'] == 'desktop-window'
            assert 'timestamp' in data

            # Verify PNG is valid
            saved = Image.open(str(tmp_path / 'latest.png'))
            assert saved.size == (100, 80)
        finally:
            watch.WATCH_DIR = original

    def test_overwrites_existing(self, tmp_path):
        """save_capture overwrites previous captures."""
        from scripts import watch
        original = watch.WATCH_DIR
        watch.WATCH_DIR = tmp_path
        try:
            img1 = Image.new('RGB', (100, 80), color='red')
            watch.save_capture(img1, 111, 'First')

            img2 = Image.new('RGB', (200, 160), color='blue')
            watch.save_capture(img2, 222, 'Second')

            data = json.loads((tmp_path / 'latest.json').read_text())
            assert data['hwnd'] == 222
            assert data['title'] == 'Second'
            assert data['width'] == 200
        finally:
            watch.WATCH_DIR = original


class TestCaptureWindow:
    """Test window capture (requires real windows)."""

    def test_invalid_hwnd_returns_error(self):
        """Capturing a non-existent window returns an error."""
        from scripts.watch import capture_window
        img, err = capture_window(999999999)
        assert img is None
        assert err is not None
        assert 'not' in err.lower() or 'no longer' in err.lower()

    def test_valid_window_returns_image(self):
        """Capturing a real window returns a PIL Image."""
        from scripts.watch import capture_window, list_windows
        windows = list_windows()
        if not windows:
            pytest.skip('No visible windows')
        hwnd = windows[0]['hwnd']
        img, err = capture_window(hwnd)
        if err and 'minimized' in err.lower():
            pytest.skip('First window is minimized')
        assert err is None
        assert isinstance(img, Image.Image)
        assert img.width > 0
        assert img.height > 0


# ── CLI Integration Tests ─────────────────────────────────────

class TestCLI:
    """Test the watch.py command-line interface."""

    def test_list_returns_valid_json(self):
        """'python watch.py list' outputs valid JSON array."""
        result = subprocess.run(
            [sys.executable, WATCH_SCRIPT, 'list'],
            capture_output=True, text=True, timeout=15,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)

    def test_capture_invalid_hwnd(self):
        """'python watch.py capture 999999999' exits with error."""
        result = subprocess.run(
            [sys.executable, WATCH_SCRIPT, 'capture', '999999999'],
            capture_output=True, text=True, timeout=15,
        )
        assert result.returncode != 0
        data = json.loads(result.stdout)
        assert 'error' in data

    def test_capture_valid_window(self):
        """'python watch.py capture <hwnd>' saves a screenshot."""
        # First get a valid hwnd
        list_result = subprocess.run(
            [sys.executable, WATCH_SCRIPT, 'list'],
            capture_output=True, text=True, timeout=15,
        )
        windows = json.loads(list_result.stdout)
        if not windows:
            pytest.skip('No visible windows')

        hwnd = windows[0]['hwnd']
        result = subprocess.run(
            [sys.executable, WATCH_SCRIPT, 'capture', str(hwnd)],
            capture_output=True, text=True, timeout=15,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data.get('ok') is True
        assert 'width' in data
        assert 'height' in data

    def test_no_args_shows_usage(self):
        """Running without args shows usage and exits 1."""
        result = subprocess.run(
            [sys.executable, WATCH_SCRIPT],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 1
        assert 'Usage' in result.stdout or 'usage' in result.stdout.lower()

    def test_watch_detects_closed_window(self):
        """'python watch.py watch 999999999' detects invalid window quickly."""
        result = subprocess.run(
            [sys.executable, WATCH_SCRIPT, 'watch', '999999999', '1'],
            capture_output=True, text=True, timeout=10,
        )
        # Should output watching status then stopped
        lines = result.stdout.strip().split('\n')
        assert len(lines) >= 2
        first = json.loads(lines[0])
        assert first['status'] == 'watching'
        last = json.loads(lines[-1])
        assert last['status'] == 'stopped'
        assert last['reason'] == 'window_closed'
