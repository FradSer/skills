"""Build all upstream Interfaces workflows as single-router references."""
from __future__ import annotations

import argparse
import shutil
import re
from pathlib import Path

import yaml

from denest import RefPacker, normalize_markdown, strip_frontmatter


def build(upstream: Path, target: Path) -> None:
    """Preserve complete workflow bodies/resources without extra entrypoints."""
    if not (upstream / "better-interface/SKILL.md").is_file():
        raise ValueError("missing upstream better-interface router")
    target.mkdir(parents=True, exist_ok=True)
    router = target / "design-engineering"
    router.mkdir(exist_ok=True)
    for source in sorted(upstream.iterdir()):
        if not source.is_dir() or not (source / "SKILL.md").is_file():
            continue
        entry = (source / "SKILL.md").read_text()
        if not entry.startswith("---\n") or len(entry.split("---", 2)) != 3:
            raise ValueError(f"missing skill frontmatter: {source.name}")
        metadata = yaml.safe_load(entry.split("---", 2)[1])
        if not isinstance(metadata, dict) or metadata.get("name") != source.name:
            raise ValueError(f"invalid skill identity: {source.name}")
        if source.name == "better-interface":
            for resource in source.iterdir():
                if resource.name not in {"SKILL.md", "agents"}:
                    if resource.is_dir():
                        shutil.copytree(resource, router / resource.name)
                    else:
                        shutil.copyfile(resource, router / resource.name)
            (router / "upstream.md").write_text(normalize_markdown(strip_frontmatter((source / "SKILL.md").read_text())))
            continue
        shutil.copytree(source, target / source.name, ignore=shutil.ignore_patterns("agents"))
    RefPacker(target, "design-engineering", "better-").apply()
    license_file = upstream.parent / "LICENSE"
    if license_file.is_file():
        shutil.copyfile(license_file, router / "jakub-LICENSE.txt")


def merge_emil(upstream: Path, target: Path) -> None:
    """Retain design engineering workflows as references, with local links."""
    entries = sorted(source for source in upstream.iterdir() if source.is_dir() and (source / "SKILL.md").is_file())
    if not entries:
        raise ValueError("Emil upstream contains no skill workflows")
    pack = target / "design-engineering/references/emil"
    for source in entries:
        text = (source / "SKILL.md").read_text()
        if not text.startswith("---\n") or len(text.split("---", 2)) != 3:
            raise ValueError(f"missing Emil frontmatter: {source.name}")
        metadata = yaml.safe_load(text.split("---", 2)[1])
        if not isinstance(metadata, dict) or metadata.get("name") != source.name:
            raise ValueError(f"invalid Emil skill identity: {source.name}")
        destination = pack / source.name
        shutil.copytree(source, destination, ignore=shutil.ignore_patterns("agents"))
        (destination / "SKILL.md").rename(destination / "overview.md")
        for file in destination.rglob("*.md"):
            body = strip_frontmatter(file.read_text()) if file.name == "overview.md" else file.read_text()
            body = re.sub(r"(?<=/)SKILL\.md(?=[#)\s]|$)", "overview.md", body)
            body = re.sub(r"(?<=\()SKILL\.md(?=[#)])", "overview.md", body)
            file.write_text(normalize_markdown(body))
    license_file = upstream.parent / "LICENSE"
    if license_file.is_file():
        shutil.copyfile(license_file, pack / "LICENSE.txt")
    cheatsheet = upstream.parent / "performance-cheatsheet.md"
    if cheatsheet.is_file():
        (pack / cheatsheet.name).write_text(normalize_markdown(cheatsheet.read_text()))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("upstream", type=Path)
    parser.add_argument("target", type=Path)
    parser.add_argument("--emil", type=Path)
    arguments = parser.parse_args()
    build(arguments.upstream, arguments.target)
    if arguments.emil is not None:
        merge_emil(arguments.emil, arguments.target)
