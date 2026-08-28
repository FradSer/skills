#!/usr/bin/env python3
"""Sync review-pr fallback references and scripts into promoted create-pr.

The review-pr child remains the source of truth for its operational fallback.
Only the selected references and scripts are copied into the directly
exposed create-pr skill; the promoted mirror is synchronized separately by
``sync-promoted.py``.
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
        if not destination.exists():
            print(f"out of sync: {destination.relative_to(ROOT)}")
            ok = False
            continue
        source_text = source.read_text(encoding="utf-8")
        destination_text = destination.read_text(encoding="utf-8")
        if destination.name == "runbook.md":
            source_text = source_text.replace(
                "SKILL_DIR=/absolute/path/to/skills/review-pr",
                "SKILL_DIR=/absolute/path/to/skills/review-pr",
            )
        if source_text != destination_text:
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
        if destination.name == "runbook.md":
            text = destination.read_text(encoding="utf-8")
            text = text.replace(
                "SKILL_DIR=/absolute/path/to/skills/review-pr",
                "SKILL_DIR=/absolute/path/to/skills/review-pr",
            )
            destination.write_text(text, encoding="utf-8")

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
