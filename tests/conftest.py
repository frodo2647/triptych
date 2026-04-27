"""Shared test fixtures for Triptych v2 tests."""

import sys
import shutil
import tempfile
from pathlib import Path

import pytest

# Make project root importable
sys.path.insert(0, str(Path(__file__).parent.parent))

PROJECT_ROOT = Path(__file__).parent.parent


@pytest.fixture
def research_dir(tmp_path):
    """Create a temporary research directory for testing.

    Yields the path to the temp research dir. Cleaned up automatically.
    """
    research = tmp_path / "research"
    research.mkdir()
    yield research


@pytest.fixture
def workspace_dir(tmp_path):
    """Create a temporary workspace directory mimicking the real structure.

    Yields the path. Contains research/, output/, snapshots/ subdirs.
    """
    ws = tmp_path / "workspace"
    ws.mkdir()
    (ws / "research").mkdir()
    (ws / "output").mkdir()
    (ws / "snapshots").mkdir()
    yield ws
