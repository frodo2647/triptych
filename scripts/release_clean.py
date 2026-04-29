#!/usr/bin/env python3
"""Wipe local workspace state to a release-clean baseline.

Use before recording a demo, before testing first-boot, or before tagging
a release. Does NOT touch git-tracked code — only the gitignored runtime
directories under `workspace/`.

What gets wiped:
  workspace/output/        rendered display tabs
  workspace/snapshots/     screenshot history
  workspace/research/      research state, claims, integrations.json
  workspace/files/         user files (the file manager root)
  workspace/.first-run-completed  first-boot marker

What is preserved:
  workspace/.gitkeep       so the empty dirs survive in git

Usage:
    python scripts/release_clean.py            # interactive confirm
    python scripts/release_clean.py --yes      # skip confirm
    python scripts/release_clean.py --dry-run  # show what would be removed
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE = PROJECT_ROOT / "workspace"

WIPE_DIRS = [
    WORKSPACE / "output",
    WORKSPACE / "snapshots",
    WORKSPACE / "research",
    WORKSPACE / "files",
]

WIPE_FILES = [
    WORKSPACE / ".first-run-completed",
]


def _list_targets() -> list[tuple[Path, str]]:
    found = []
    for d in WIPE_DIRS:
        if d.exists():
            count = sum(1 for _ in d.rglob("*") if _.is_file())
            found.append((d, f"directory ({count} file{'s' if count != 1 else ''})"))
    for f in WIPE_FILES:
        if f.exists():
            found.append((f, "file"))
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--yes", action="store_true", help="skip confirmation prompt")
    parser.add_argument("--dry-run", action="store_true",
                        help="print what would be removed and exit")
    args = parser.parse_args()

    targets = _list_targets()
    if not targets:
        print("Already clean — nothing to remove.")
        return 0

    print("Will remove:")
    for path, kind in targets:
        print(f"  {path.relative_to(PROJECT_ROOT)}  [{kind}]")

    if args.dry_run:
        return 0

    if not args.yes:
        resp = input("\nProceed? [y/N] ").strip().lower()
        if resp not in ("y", "yes"):
            print("Aborted.")
            return 1

    for path, _ in targets:
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
    print("Clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
