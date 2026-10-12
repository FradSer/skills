#!/usr/bin/env python3
"""Validate all supported package versions before applying any updates."""

import argparse
import json
from pathlib import Path
import re
import sys
import tomllib


SEMVER = re.compile(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?")


def replace_json_version(original: str, version: str) -> str:
    """Locate the validated root field without rewriting other JSON text."""
    data = json.loads(original)
    if not isinstance(data, dict) or not isinstance(data.get("version"), str):
        raise ValueError("package.json: expected a root string version field")
    decoder = json.JSONDecoder()
    position = original.index("{") + 1
    fields: list[tuple[int, int]] = []
    while True:
        while original[position].isspace():
            position += 1
        if original[position] == "}":
            break
        key, position = decoder.raw_decode(original, position)
        while original[position].isspace():
            position += 1
        position += 1  # JSON validation above guarantees the colon.
        while original[position].isspace():
            position += 1
        start = position
        _, position = decoder.raw_decode(original, position)
        if key == "version":
            fields.append((start, position))
        while original[position].isspace():
            position += 1
        if original[position] == ",":
            position += 1
        else:
            break
    if len(fields) != 1:
        raise ValueError("package.json: duplicate root version fields are ambiguous")
    start, end = fields[0]
    return original[:start] + json.dumps(version) + original[end:]


def version_updates(root: Path, version: str) -> dict[Path, str]:
    """Return proposed contents, rejecting unsupported manifests without writing."""
    match = SEMVER.fullmatch(version)
    if not match or (match.group(4) and any(part.isdigit() and len(part) > 1 and part[0] == "0" for part in match.group(4).split("."))):
        raise ValueError("version must be SemVer, for example 1.2.3 or 1.2.3-rc.1")
    updates: dict[Path, str] = {}
    for filename in ("package.json", "VERSION", "version.txt", "pyproject.toml", "Cargo.toml"):
        path = root / filename
        if path.is_symlink():
            raise ValueError(f"{filename}: symlinked manifests are not supported")
        if not path.exists():
            continue
        original = path.read_text(encoding="utf-8")
        if filename == "package.json":
            updated = replace_json_version(original, version)
        elif filename in ("VERSION", "version.txt"):
            if not SEMVER.fullmatch(original.strip()):
                raise ValueError(f"{filename}: expected a single SemVer line")
            updated = version + ("\n" if original.endswith("\n") else "")
        else:
            data = tomllib.loads(original)
            if filename == "Cargo.toml":
                sections = ["package"] if isinstance(data.get("package", {}).get("version"), str) else []
            else:
                sections = []
                if isinstance(data.get("project", {}).get("version"), str):
                    sections.append("project")
                if isinstance(data.get("tool", {}).get("poetry", {}).get("version"), str):
                    sections.append("tool.poetry")
            if not sections:
                raise ValueError(f"{filename}: expected a static package version; dynamic or workspace-inherited versions need the project's own release tooling")
            remaining = set(sections)
            lines = original.splitlines(keepends=True)
            section = ""
            for index, line in enumerate(lines):
                heading = re.match(r"^\s*\[([^\[\]]+)\]\s*(?:#.*)?$", line.strip())
                if heading:
                    section = heading.group(1).strip()
                if section in remaining:
                    declaration = re.match(r"""^(\s*version\s*=\s*)(["'])([^"'\n]*)(["'])([ \t]*(?:#.*)?)(\r?\n)?$""", line)
                    if declaration and declaration.group(2) == declaration.group(4):
                        lines[index] = f"{declaration.group(1)}{declaration.group(2)}{version}{declaration.group(4)}{declaration.group(5)}{declaration.group(6) or ''}"
                        remaining.remove(section)
            if remaining:
                raise ValueError(f"{filename}: unsupported version declaration in {', '.join(sorted(remaining))}")
            updated = "".join(lines)
            tomllib.loads(updated)
        updates[path] = updated
    if not updates:
        raise ValueError("no supported version files found; use --name without --version for a branch-only operation")
    return updates


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    parser.add_argument("--check", action="store_true", help="Validate without modifying files")
    args = parser.parse_args()
    try:
        updates = version_updates(Path.cwd(), args.version)
        if not args.check:
            for path, contents in updates.items():
                path.write_text(contents, encoding="utf-8")
        for path in updates:
            print(path.name)
    except (ValueError, OSError) as error:
        print(f"bump-version.py: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
