#!/usr/bin/env python3
"""Generate local router indexes from router-owned route manifests or CLI metadata.

Local child entries are documents, not independently discoverable skills, so
this tool never reads child frontmatter. For a local router, provide a
``routes.yml`` manifest beside the router entry (or pass ``--routes``).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import yaml

EXCLUDED_DIRS = {".backup"}
INDEX_START_MARKER = "## Sub-skill Index"
INDEX_END_MARKER = "## Routing Rules"


def load_version_registry(versions_md: Path | None) -> dict[str, str]:
    """Parse an optional legacy version registry."""
    if versions_md is None or not versions_md.is_file():
        return {}
    registry: dict[str, str] = {}
    for row in versions_md.read_text(encoding="utf-8").splitlines():
        cells = [cell.strip() for cell in row.strip("|").split("|")]
        if len(cells) >= 2 and cells[0] and cells[1]:
            registry[cells[0]] = cells[1]
    return registry


def load_routes(routes_file: Path | None) -> dict[str, dict[str, str]]:
    """Load router-owned child labels without requiring child frontmatter."""
    if routes_file is None or not routes_file.is_file():
        return {}
    data = yaml.safe_load(routes_file.read_text(encoding="utf-8")) or {}
    rows = data.get("routes", data) if isinstance(data, dict) else data
    if not isinstance(rows, list):
        raise ValueError(f"routes manifest must contain a list: {routes_file}")
    routes: dict[str, dict[str, str]] = {}
    for row in rows:
        if not isinstance(row, dict) or not row.get("name"):
            raise ValueError(f"invalid route row in {routes_file}")
        name = str(row["name"])
        routes[name] = {
            "name": name,
            "entry": str(row.get("entry", "")),
            "description": " ".join(str(row.get("description", "")).split()),
        }
    return routes


def subskill_entry(sub: Path) -> Path | None:
    """Return the denested child document."""
    entry = sub / f"{sub.name}.md"
    return entry if entry.is_file() else None


def load_subskills_from_dir(
    skills_dir: Path,
    registry: dict[str, str],
    hoist: list[str] | None = None,
    display: dict[str, str] | None = None,
    routes: dict[str, dict[str, str]] | None = None,
) -> list[dict]:
    """Return one record per child directory using router-owned route data."""
    hoist = hoist or []
    display = display or {}
    routes = routes or {}
    records: list[dict] = []
    for sub in sorted(skills_dir.iterdir()):
        if not sub.is_dir() or sub.name in EXCLUDED_DIRS:
            continue
        if subskill_entry(sub) is None:
            print(f"warn: {sub.name}/{sub.name}.md missing, skipping", file=sys.stderr)
            continue
        route = routes.get(sub.name, {})
        entry = route.get("entry") or f"{sub.name}/{sub.name}.md"
        records.append(
            {
                "dir": sub.name,
                "entry": entry,
                "name": display.get(sub.name, route.get("name", sub.name)),
                "version": registry.get(sub.name, ""),
                "description": route.get("description", ""),
            }
        )
    hoist_order = {directory: i for i, directory in enumerate(hoist)}
    records.sort(key=lambda row: (hoist_order.get(row["dir"], len(hoist_order)), row["dir"]))
    return records


def load_subskills_from_cli(
    hoist: list[str] | None = None,
    display: dict[str, str] | None = None,
) -> list[dict]:
    """Return one record per embedded CLI skill."""
    hoist = hoist or []
    display = display or {}
    result = subprocess.run(
        ["lark-cli", "skills", "list"],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(result.stdout)
    records = []
    for skill in data.get("skills", []):
        name = skill["name"]
        records.append(
            {
                "dir": name,
                "name": display.get(name, name),
                "version": str(skill.get("version") or skill.get("metadata", {}).get("version", "")),
                "description": " ".join(str(skill.get("description", "")).split()),
            }
        )
    hoist_order = {directory: i for i, directory in enumerate(hoist)}
    records.sort(key=lambda row: (hoist_order.get(row["dir"], len(hoist_order)), row["dir"]))
    return records


def render_table(records: list[dict], from_cli: bool = False) -> str:
    if from_cli:
        header = "| Sub-skill | Read Command | Version | Use When |\n|-----------|--------------|---------|----------|"
        rows = [
            f"| {row['name']} | `lark-cli skills read {row['dir']}` | {row['version']} | {row['description'].replace('|', '\\|')} |"
            for row in records
        ]
    else:
        header = "| Sub-skill | Entry | Use When |\n|-----------|-------|----------|"
        rows = [
            f"| {row['name']} | [`{row['entry']}`]({row['entry']}) | {row['description'].replace('|', '\\|')} |"
            for row in records
        ]
    return header + "\n" + "\n".join(rows) + "\n\n"


def replace_index_table(text: str, table: str) -> str:
    start = text.index(INDEX_START_MARKER)
    end = text.index(INDEX_END_MARKER, start)
    header_end = text.index("\n", start) + 1
    return text[:start] + text[start:header_end] + "\n" + table + text[end:]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--skills", type=Path)
    parser.add_argument("--router", required=True, type=Path)
    parser.add_argument("--from-cli", action="store_true")
    parser.add_argument("--versions", type=Path)
    parser.add_argument("--routes", type=Path)
    parser.add_argument("--hoist", action="append", default=[])
    parser.add_argument("--display", action="append", default=[])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    display: dict[str, str] = {}
    for item in args.display:
        directory, _, label = item.partition("=")
        if directory and label:
            display[directory] = label

    if args.from_cli:
        records = load_subskills_from_cli(hoist=args.hoist, display=display)
        table = render_table(records, from_cli=True)
    else:
        if args.skills is None:
            print("error: --skills required when not using --from-cli", file=sys.stderr)
            return 1
        try:
            routes = load_routes(args.routes or args.router.parent / "routes.yml")
            records = load_subskills_from_dir(
                args.skills,
                load_version_registry(args.versions),
                hoist=args.hoist,
                display=display,
                routes=routes,
            )
        except ValueError as error:
            print(f"error: {error}", file=sys.stderr)
            return 1
        table = render_table(records)

    if not args.router.is_file():
        print(f"error: router not found: {args.router}", file=sys.stderr)
        return 1
    current = args.router.read_text(encoding="utf-8")
    try:
        updated = replace_index_table(current, table)
    except ValueError as error:
        print(f"error: {error} (markers missing in {args.router})", file=sys.stderr)
        return 1
    if args.check:
        if updated == current:
            print("OK: index table in sync")
            return 0
        print("FAILED: index table is stale", file=sys.stderr)
        return 1
    args.router.write_text(updated, encoding="utf-8")
    print(f"gen-index: rewrote {len(records)} rows in {args.router}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
