"""Shared metadata parsing for skill evaluation scripts."""

from pathlib import Path
import re

import yaml


def parse_skill_md(skill_path: Path) -> tuple[str, str, str]:
    """Parse YAML metadata, returning (name, description, full content)."""
    content = (skill_path / "SKILL.md").read_text(encoding="utf-8")
    match = re.match(r"^---\r?\n(.*?)\r?\n---(?:\r?\n|$)", content, re.DOTALL)
    if not match:
        raise ValueError("SKILL.md has invalid or missing frontmatter")
    metadata = yaml.safe_load(match.group(1))
    if not isinstance(metadata, dict):
        raise ValueError("Skill metadata must be a dictionary")
    name = metadata.get("name")
    description = metadata.get("description")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Skill name must be a non-empty string")
    if not isinstance(description, str) or not description.strip():
        raise ValueError("Skill description must be a non-empty string")
    return name, description, content
