#!/usr/bin/env python3
"""Shared router index generator (marketing / lark mirrored plugins).

Regenerates the Sub-skill Index table in the router SKILL.md between the
`## Sub-skill Index` and `## Routing Rules` markers, from each sub-skill's
frontmatter (or embedded CLI metadata). Local-only SKILL.md/SYNC.md at the tree
root are never overwritten — only the index table region is edited.

Usage:
    python3 tools/skill-sync/gen-index.py --skills <dir> --router <SKILL.md> \
        [--versions <VERSIONS.md>] [--check]

    python3 tools/skill-sync/gen-index.py --from-cli --router <SKILL.md> \
        [--hoist lark-shared] [--check]
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

EXCLUDED_DIRS = {".backup"}

INDEX_START_MARKER = "## Sub-skill Index"
INDEX_END_MARKER = "## Routing Rules"

# VERSIONS.md row: "| skill-name | 1.2.3 | 2026-07-01 |" — fallback registry.
VERSION_ROW_RE = re.compile(r"^\|\s*([a-z0-9-]+)\s*\|\s*([0-9]+\.[0-9]+\.[0-9]+)\s*\|")


def load_version_registry(versions_md: Path | None) -> dict[str, str]:
    """Parse VERSIONS.md into {skill-name: version}."""
    registry: dict[str, str] = {}
    if versions_md is None or not versions_md.is_file():
        return registry
    for line in versions_md.read_text(encoding="utf-8").splitlines():
        m = VERSION_ROW_RE.match(line)
        if m:
            registry[m.group(1)] = m.group(2)
    return registry


def subskill_entry(sub: Path) -> Path | None:
    """Prefer denested <dirname>.md; fall back to upstream SKILL.md if present."""
    denested = sub / f"{sub.name}.md"
    if denested.is_file():
        return denested
    legacy = sub / "SKILL.md"
    if legacy.is_file():
        return legacy
    return None


def read_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    _, fm_raw, _ = text.split("---\n", 2)
    return yaml.safe_load(fm_raw) or {}


def load_subskills_from_dir(
    skills_dir: Path,
    registry: dict[str, str],
    hoist: list[str] | None = None,
    display: dict[str, str] | None = None,
) -> list[dict]:
    """Return one record per sub-skill directory with entry-file frontmatter."""
    hoist = hoist or []
    display = display or {}
    records: list[dict] = []
    for sub in sorted(skills_dir.iterdir()):
        if not sub.is_dir() or sub.name in EXCLUDED_DIRS:
            continue
        entry = subskill_entry(sub)
        if entry is None:
            print(
                f"warn: {sub.name}/{{SKILL.md|{sub.name}.md}} missing, skipping",
                file=sys.stderr,
            )
            continue
        fm = read_frontmatter(entry)
        name = display.get(sub.name, fm.get("name", sub.name))
        version = ""
        if isinstance(fm.get("metadata"), dict):
            version = str(fm["metadata"].get("version", ""))
        if not version:
            version = str(fm.get("version", ""))
        if not version:
            version = registry.get(sub.name, "")
        description = fm.get("description", "") or ""
        records.append(
            {
                "dir": sub.name,
                "name": name,
                "version": version,
                "description": " ".join(str(description).split()),
            }
        )
    hoist_order = {d: i for i, d in enumerate(hoist)}
    records.sort(key=lambda r: (hoist_order.get(r["dir"], len(hoist_order)), r["dir"]))
    return records


def load_subskills_from_cli(
    hoist: list[str] | None = None,
    display: dict[str, str] | None = None,
) -> list[dict]:
    """Return one record per sub-skill from `lark-cli skills list`."""
    hoist = hoist or []
    display = display or {}
    res = subprocess.run(
        ["lark-cli", "skills", "list"],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(res.stdout)
    skills = data.get("skills", [])
    records: list[dict] = []
    for s in skills:
        name_key = s["name"]
        display_name = display.get(name_key, name_key)
        version = s.get("version") or s.get("metadata", {}).get("version", "")
        desc = " ".join(str(s.get("description", "")).split())
        records.append(
            {
                "dir": name_key,
                "name": display_name,
                "version": str(version) if version is not None else "",
                "description": desc,
            }
        )
    hoist_order = {d: i for i, d in enumerate(hoist)}
    records.sort(key=lambda r: (hoist_order.get(r["dir"], len(hoist_order)), r["dir"]))
    return records


def render_table(records: list[dict], from_cli: bool = False) -> str:
    if from_cli:
        header = (
            "| Sub-skill | Read Command | Version | Use When |\n"
            "|-----------|--------------|---------|----------|"
        )
        rows = []
        for r in records:
            cmd = f"`lark-cli skills read {r['dir']}`"
            use_when = r["description"].replace("|", "\\|")
            rows.append(f"| {r['name']} | {cmd} | {r['version']} | {use_when} |")
        return header + "\n" + "\n".join(rows) + "\n\n"

    header = (
        "| Sub-skill | Entry | Version | Use When |\n"
        "|-----------|-------|---------|----------|"
    )
    rows = []
    for r in records:
        entry = f"{r['dir']}/{r['dir']}.md"
        use_when = r["description"].replace("|", "\\|")
        label = r["name"]
        rows.append(
            f"| {label} | [`{entry}`]({entry}) | {r['version']} | {use_when} |"
        )
    return header + "\n" + "\n".join(rows) + "\n\n"


def replace_index_table(text: str, table: str) -> str:
    """Replace the region between INDEX_START_MARKER and INDEX_END_MARKER.

    Keeps the ``## Sub-skill Index`` header line (it ends with a newline),
    then the table, then resumes at ``## Routing Rules``.
    """
    start = text.index(INDEX_START_MARKER)
    end = text.index(INDEX_END_MARKER, start)
    header_line = text[start : text.index("\n", start) + 1]
    return text[:start] + header_line + "\n" + table + text[end:]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--skills", type=Path, default=None, help="skills tree root")
    parser.add_argument("--router", required=True, type=Path, help="router SKILL.md")
    parser.add_argument(
        "--from-cli",
        action="store_true",
        help="load sub-skills directly from `lark-cli skills list`",
    )
    parser.add_argument(
        "--versions", type=Path, default=None, help="optional VERSIONS.md registry"
    )
    parser.add_argument(
        "--hoist",
        action="append",
        default=[],
        help="sub-skill dir to pin before alphabetical order (repeatable)",
    )
    parser.add_argument(
        "--display",
        action="append",
        default=[],
        help="display label as dir=Label (repeatable; lark's friendly names)",
    )
    parser.add_argument("--check", action="store_true", help="dry-run diff, exit 1 if drift")
    args = parser.parse_args()

    display: dict[str, str] = {}
    for item in args.display:
        d, _, label = item.partition("=")
        if d and label:
            display[d] = label

    if args.from_cli:
        records = load_subskills_from_cli(hoist=args.hoist, display=display)
        table = render_table(records, from_cli=True)
    else:
        if args.skills is None:
            print("error: --skills required when not using --from-cli", file=sys.stderr)
            return 1
        registry = load_version_registry(args.versions)
        records = load_subskills_from_dir(args.skills, registry, hoist=args.hoist, display=display)
        table = render_table(records, from_cli=False)

    router = args.router
    if not router.is_file():
        print(f"error: router not found: {router}", file=sys.stderr)
        return 1
    try:
        current = router.read_text(encoding="utf-8")
        updated = replace_index_table(current, table)
    except ValueError as e:
        print(f"error: {e} (markers missing in {router})", file=sys.stderr)
        return 1

    if args.check:
        if updated == current:
            print("OK: index table in sync")
            return 0
        print("FAILED: index table is stale", file=sys.stderr)
        return 1

    router.write_text(updated, encoding="utf-8")
    print(f"gen-index: rewrote {len(records)} rows in {router}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
