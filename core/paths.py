"""Single source of truth for Triptych workspace paths.

No side effects at import time. Writers create their own subdirectories
on demand (parents=True, exist_ok=True).
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE = PROJECT_ROOT / 'workspace'
OUTPUT_DIR = WORKSPACE / 'output'
RESEARCH_DIR = WORKSPACE / 'research'
SNAPSHOTS_DIR = WORKSPACE / 'snapshots'
FILES_DIR = WORKSPACE / 'files'
