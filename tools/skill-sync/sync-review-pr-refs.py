#!/usr/bin/env python3
"""Sync review-pr's fallback references and scripts into create-pr.

The standalone review-pr skill remains the source of truth. Only its
operational references and scripts are copied; SKILL.md and skill metadata are
never duplicated. Markdown stays under references/ and executables under
scripts/ so the fallback follows the repository's skill layout convention.
"""

from __future__ import annotations

import argparse
import filecmp
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "skills" / "review-pr"
REFERENCE_TARGET = ROOT / "skills" / "create-pr" / "references"
SCRIPT_TARGET = ROOT / "skills" / "create-pr" / "scripts"


REFERENCE_FILES = (
    "runbook.md",
    "review-loop.md",
    "closeout.md",
)
SCRIPT_FILES = (
    "review-loop.sh",
    "arm-closeout.sh",
    "clear-closeout.sh",
    "closeout-stop.sh",
)


def expected_files() -> dict[Path, Path]:
    return {
        **{
            REFERENCE_TARGET / name: SOURCE / "references" / name
            for name in REFERENCE_FILES
        },
        **{SCRIPT_TARGET / name: SOURCE / "scripts" / name for name in SCRIPT_FILES},
    }


def check() -> bool:
    expected = expected_files()
    ok = True
    nested = REFERENCE_TARGET / "review-pr"
    if nested.exists():
        print(f"unexpected nested review-pr directory: {nested.relative_to(ROOT)}")
        ok = False
    for name in SCRIPT_FILES:
        legacy = REFERENCE_TARGET / name
        if legacy.exists():
            print(f"script is in references instead of scripts: {legacy.relative_to(ROOT)}")
            ok = False
    for destination, source in sorted(expected.items()):
        if not destination.exists() or not filecmp.cmp(source, destination, shallow=False):
            print(f"out of sync: {destination.relative_to(ROOT)}")
            ok = False

    return ok


def sync() -> None:
    REFERENCE_TARGET.mkdir(parents=True, exist_ok=True)
    SCRIPT_TARGET.mkdir(parents=True, exist_ok=True)

    nested = REFERENCE_TARGET / "review-pr"
    if nested.exists():
        shutil.rmtree(nested)
    for name in SCRIPT_FILES:
        legacy = REFERENCE_TARGET / name
        if legacy.exists():
            legacy.unlink()

    expected = expected_files()
    for destination, source in expected.items():
        shutil.copy2(source, destination)

    for destination in (
        REFERENCE_TARGET / name for name in ("runbook.md", "review-loop.md", "closeout.md")
    ):
        destination.chmod(0o644)
    for destination in (SCRIPT_TARGET / name for name in SCRIPT_FILES):
        destination.chmod(0o755)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        return 0 if check() else 1
    sync()
    return 0


if __name__ == "__main__":
    sys.exit(main())
