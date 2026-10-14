"""Build all upstream Interfaces workflows as single-router references."""
from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path

import yaml

from denest import RefPacker, normalize_markdown, strip_frontmatter

INITIAL_RESPONSE_RE = re.compile(
    r"\n## Initial Response\n\n"
    r"When this skill is first invoked without a specific question, respond only with:\n\n"
    r"(?:> .*\n)+\n"
    r"Do not provide any other information until the user asks a question\.\n"
)


def strip_initial_response(text: str) -> str:
    """Remove standalone initial-greeting sections from packed reference overviews."""
    return INITIAL_RESPONSE_RE.sub("", text)


def normalize_emil_markdown(text: str, mapping: dict[str, str], is_overview: bool = False) -> str:
    """Normalize an Emil reference markdown file for the single-router reference tree."""
    body = strip_frontmatter(text) if is_overview else text
    if is_overview:
        body = strip_initial_response(body)
    body = re.sub(r"(?<=/)SKILL\.md(?=[#)\s]|$)", "overview.md", body)
    body = re.sub(r"(?<=\()SKILL\.md(?=[#)])", "overview.md", body)
    body = re.sub(r"\bSKILL\.md\b", "overview.md", body)
    for name, target in sorted(mapping.items(), key=lambda item: len(item[0]), reverse=True):
        body = body.replace(f"`{name}` skill's", f"`{target}`'s")
        body = body.replace(f"`{name}` skill", f"`{target}`")
        body = re.sub(
            rf"`{re.escape(name)}(?P<args> (?:plan|execute|reconcile)[^`]*)`",
            lambda match, ref=target: f"`{ref}` ({match.group('args').strip()})",
            body,
        )
        body = re.sub(
            rf"(?<![/\w-])`{re.escape(name)}`(?!(?:/|\s*\(|\s+props\b))",
            f"`{target}`",
            body,
        )
    body = body.replace("the `references/", "`references/")
    return normalize_markdown(body)


def normalize_existing_emil_pack(pack: Path) -> int:
    """Idempotently normalize an already-packed references/emil directory in place."""
    entries = sorted(source for source in pack.iterdir() if source.is_dir() and (source / "overview.md").is_file())
    mapping = {source.name: f"references/emil/{source.name}/overview.md" for source in entries}
    changed = 0
    for source in entries:
        for file in sorted(source.rglob("*.md")):
            original = file.read_text(encoding="utf-8")
            updated = normalize_emil_markdown(original, mapping, is_overview=(file.name == "overview.md"))
            if updated != original:
                file.write_text(updated, encoding="utf-8")
                changed += 1
    return changed


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
    mapping = {source.name: f"references/emil/{source.name}/overview.md" for source in entries}
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
        for file in sorted(destination.rglob("*.md")):
            file.write_text(
                normalize_emil_markdown(
                    file.read_text(encoding="utf-8"),
                    mapping,
                    is_overview=(file.name == "overview.md"),
                ),
                encoding="utf-8",
            )
    license_file = upstream.parent / "LICENSE"
    if license_file.is_file():
        shutil.copyfile(license_file, pack / "LICENSE.txt")
    cheatsheet = upstream.parent / "performance-cheatsheet.md"
    if cheatsheet.is_file():
        (pack / cheatsheet.name).write_text(normalize_markdown(cheatsheet.read_text()))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("upstream", nargs="?", type=Path)
    parser.add_argument("target", nargs="?", type=Path)
    parser.add_argument("--emil", type=Path)
    parser.add_argument("--normalize-pack", type=Path)
    arguments = parser.parse_args()
    if arguments.normalize_pack is not None:
        normalize_existing_emil_pack(arguments.normalize_pack)
    else:
        if arguments.upstream is None or arguments.target is None:
            parser.error("upstream and target are required unless --normalize-pack is used")
        build(arguments.upstream, arguments.target)
        if arguments.emil is not None:
            merge_emil(arguments.emil, arguments.target)
