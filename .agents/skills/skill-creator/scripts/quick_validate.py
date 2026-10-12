#!/usr/bin/env python3
"""Validate collection skill metadata without executing its instructions."""

from pathlib import Path
import re
import sys

import yaml


ALLOWED_PROPERTIES = {
    "name", "description", "license", "allowed-tools", "metadata",
    "compatibility", "disable-model-invocation",
}


def validate_skill(skill_path: str | Path) -> tuple[bool, str]:
    """Return the first actionable metadata or incomplete-content error."""
    skill_path = Path(skill_path)
    skill_md = skill_path / "SKILL.md"
    if not skill_md.is_file():
        return False, "SKILL.md not found"
    try:
        content = skill_md.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        return False, f"Cannot read SKILL.md: {error}"
    match = re.match(r"^---\r?\n(.*?)\r?\n---(?:\r?\n|$)", content, re.DOTALL)
    if not match:
        return False, "Invalid or missing YAML frontmatter"
    try:
        metadata = yaml.safe_load(match.group(1))
    except yaml.YAMLError as error:
        return False, f"Invalid YAML: {error}"
    if not isinstance(metadata, dict):
        return False, "Frontmatter must be a YAML dictionary"
    unexpected = set(metadata) - ALLOWED_PROPERTIES
    if unexpected:
        return False, f"Unexpected frontmatter keys: {', '.join(str(key) for key in unexpected)}"
    name = metadata.get("name")
    if not isinstance(name, str) or not name.strip():
        return False, "Name must be a non-empty string"
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) or len(name) > 64:
        return False, "Name must be hyphen-case and at most 64 characters"
    if name != skill_path.name:
        return False, "Name must match the skill directory name"
    description = metadata.get("description")
    if not isinstance(description, str) or not description.strip():
        return False, "Description must be a non-empty string"
    if len(description) > 1024 or re.search(r"[<>]", description):
        return False, "Description must be at most 1024 characters without angle brackets"
    if "compatibility" in metadata:
        compatibility = metadata["compatibility"]
        if not isinstance(compatibility, str) or len(compatibility) > 500:
            return False, "Compatibility must be a string of at most 500 characters"
    if "disable-model-invocation" in metadata and not isinstance(metadata["disable-model-invocation"], bool):
        return False, "disable-model-invocation must be a boolean"
    if "metadata" in metadata and not isinstance(metadata["metadata"], dict):
        return False, "metadata must be a dictionary"
    body = content[match.end():]
    if not body.strip():
        return False, "Skill instructions are empty"
    if description.lstrip().startswith("[TODO:"):
        return False, "Description contains an unfinished placeholder"
    return True, "Skill is valid"


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: uv run --with pyyaml python quick_validate.py <skill-directory>")
        raise SystemExit(2)
    valid, message = validate_skill(sys.argv[1])
    print(message)
    raise SystemExit(0 if valid else 1)
