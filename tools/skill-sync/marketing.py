"""Build coreyhaines31/marketingskills as one discoverable marketing router.

Upstream ships 50 sibling skills. This collection exposes exactly one skill,
``marketing``: each upstream skill becomes ``<domain>/<domain>.md`` beside the
router, so no child document is independently discoverable. Discovery
frontmatter is dropped, upstream eval fixtures and agents metadata are not
copied, and the router owns a generated ``routes.yml`` manifest that
``gen-index.py`` renders into the SKILL.md index table.

Usage:
    python3 tools/skill-sync/marketing.py <upstream-repo-root> <out-dir> [--commit SHA]
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
from pathlib import Path

import yaml

from denest import Denester, normalize_markdown, strip_frontmatter

ROUTER = "marketing"
UPSTREAM_SKILLS_DIR = "skills"
EXCLUDED_PACK_DIRS = ("agents", "evals")
EXAMPLE_ORIGIN = "https://example.com"
ROUTES_NAME = "routes.yml"
LICENSE_NAME = "coreyhaines31-LICENSE.txt"
DESCRIPTION_LIMIT = 220
UPSTREAM_REPO = "coreyhaines31/marketingskills"
BLOB_URL_RE = re.compile(rf"https://github\.com/{UPSTREAM_REPO}/blob/main/")
CONDITION_PREFIX_RE = re.compile(r"^When the user (?:wants|needs) (?:to )?", re.IGNORECASE)
LINK_TARGET_RE = re.compile(r"\]\((?P<target>[^)\s#]+)(?P<anchor>#[^\s)]*)?\)")
PACK_PATH_RE = re.compile(r"`(?P<target>[^`\s]+\.md)(?P<anchor>#[^`\s]*)?`")
FENCE_RE = re.compile(r"^ {0,3}(?P<marker>```|~~~)")


def condense_description(text: str, limit: int = DESCRIPTION_LIMIT) -> str:
    """Keep the routing-relevant first sentence of an upstream description."""
    sentence = re.split(r"(?<=[.!?])\s+", " ".join(text.split()))[0]
    sentence = CONDITION_PREFIX_RE.sub("", sentence)
    if not sentence:
        return ""
    sentence = sentence[0].upper() + sentence[1:]
    if len(sentence) > limit:
        sentence = sentence[: limit - 1].rsplit(" ", 1)[0].rstrip(" ,;:-—") + "…"
    return sentence


def load_upstream_records(upstream: Path) -> list[dict]:
    """Return one validated record per upstream skill, in directory order."""
    skills_dir = upstream / UPSTREAM_SKILLS_DIR
    if not skills_dir.is_dir():
        raise ValueError(f"upstream skills directory not found: {skills_dir}")
    records: list[dict] = []
    for source in sorted(skills_dir.iterdir()):
        entry = source / "SKILL.md"
        if not source.is_dir() or not entry.is_file():
            continue
        text = entry.read_text(encoding="utf-8")
        if not text.startswith("---\n") or len(text.split("---", 2)) != 3:
            raise ValueError(f"missing skill frontmatter: {source.name}")
        metadata = yaml.safe_load(text.split("---", 2)[1])
        if not isinstance(metadata, dict) or metadata.get("name") != source.name:
            raise ValueError(f"invalid skill identity: {source.name}")
        description = metadata.get("description")
        if not isinstance(description, str) or not description.strip():
            raise ValueError(f"missing skill description: {source.name}")
        records.append(
            {
                "name": source.name,
                "entry": f"{source.name}/{source.name}.md",
                "description": condense_description(description),
                "source": source,
            }
        )
    if not records:
        raise ValueError(f"upstream contains no skills: {skills_dir}")
    return records


def pin_upstream_urls(router: Path, commit: str | None) -> None:
    """Point the migrated upstream-repo links at the synced revision."""
    if not commit:
        return
    pinned = f"https://github.com/{UPSTREAM_REPO}/blob/{commit}/"
    for path in sorted(router.rglob("*.md")):
        original = path.read_text(encoding="utf-8")
        updated = BLOB_URL_RE.sub(pinned, original)
        if updated != original:
            path.write_text(updated, encoding="utf-8")


def pack_path_target(path: Path, domain: Path, target: str) -> Path | None:
    """Resolve a backticked `.md` path against the file and its pack root."""
    if target.startswith(("http://", "https://", "mailto:", "#", "/")):
        return None
    candidates = {
        candidate.resolve()
        for base in (path.parent, domain)
        if (candidate := base / target).is_file()
    }
    return candidates.pop() if len(candidates) == 1 else None


def link_pack_paths(router: Path) -> int:
    """Link in-pack path mentions so every routed reference is reachable."""
    linked = 0
    for domain in sorted(path for path in router.iterdir() if path.is_dir()):
        for path in sorted(domain.rglob("*.md")):
            original = path.read_text(encoding="utf-8")
            lines: list[str] = []
            fence: str | None = None
            for line in original.splitlines(keepends=True):
                marker = FENCE_RE.match(line)
                if marker:
                    fence = None if fence else marker.group("marker")
                    lines.append(line)
                    continue
                if fence:
                    lines.append(line)
                    continue
                replaced = PACK_PATH_RE.sub(lambda m: _link_match(m, path, domain), line)
                linked += replaced != line
                lines.append(replaced)
            updated = "".join(lines)
            if updated != original:
                path.write_text(updated, encoding="utf-8")
    return linked


def _link_match(match: re.Match[str], path: Path, domain: Path) -> str:
    target = match.group("target")
    anchor = match.group("anchor") or ""
    resolved = pack_path_target(path, domain, target)
    if resolved is None or (match.start() > 0 and match.string[match.start() - 1] == "["):
        return match.group(0)
    relative = os.path.relpath(resolved, path.parent).replace(os.sep, "/")
    return f"[`{target}{anchor}`]({relative}{anchor})"


def repair_unresolved_links(router: Path) -> list[str]:
    """Point upstream example links at an explicit placeholder origin."""
    repaired: list[str] = []
    for path in sorted(router.rglob("*.md")):
        original = path.read_text(encoding="utf-8")

        def replace(match: re.Match[str]) -> str:
            target = match.group("target")
            anchor = match.group("anchor") or ""
            if target.startswith(("http://", "https://", "mailto:", "#", "<")):
                return match.group(0)
            if (path.parent / target).exists():
                return match.group(0)
            repaired.append(f"{path.relative_to(router)}: {target}{anchor}")
            return f"]({EXAMPLE_ORIGIN}/{target.lstrip('/')}{anchor})"

        updated = LINK_TARGET_RE.sub(replace, original)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
    return repaired


def write_routes(router: Path, records: list[dict]) -> None:
    """Write the router-owned route manifest read by gen-index.py."""
    rows = [
        {"name": record["name"], "entry": record["entry"], "description": record["description"]}
        for record in records
    ]
    (router / ROUTES_NAME).write_text(
        yaml.safe_dump({"routes": rows}, sort_keys=False, allow_unicode=True, width=1000),
        encoding="utf-8",
    )


def build(upstream: Path, target: Path, commit: str | None = None) -> None:
    """Write the complete candidate router tree under ``target``."""
    records = load_upstream_records(upstream)
    router = (target / ROUTER).resolve()
    if router.exists():
        shutil.rmtree(router)
    router.mkdir(parents=True)

    for record in records:
        destination = router / record["name"]
        shutil.copytree(
            record["source"], destination, ignore=shutil.ignore_patterns(*EXCLUDED_PACK_DIRS)
        )
        entry = destination / "SKILL.md"
        entry.write_text(
            normalize_markdown(strip_frontmatter(entry.read_text(encoding="utf-8"))),
            encoding="utf-8",
        )

    pin_upstream_urls(router, commit)
    write_routes(router, records)

    license_file = upstream / "LICENSE"
    if not license_file.is_file():
        raise ValueError(f"upstream license not found: {license_file}")
    shutil.copyfile(license_file, router / LICENSE_NAME)

    denester = Denester(router)
    denester.rename_nested()
    denester.rewrite_links()
    nested = denester.nested_skill_mds()
    if nested:
        raise ValueError(f"nested SKILL.md remain: {[str(path) for path in nested]}")
    linked = link_pack_paths(router)
    repaired = repair_unresolved_links(router)
    print(f"marketing: mirrored {len(records)} workflows into {router}", file=sys.stderr)
    print(f"marketing: linked {linked} in-pack paths", file=sys.stderr)
    if repaired:
        print(
            "marketing: upstream example links now use "
            f"{EXAMPLE_ORIGIN}: {', '.join(repaired)}",
            file=sys.stderr,
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("upstream", type=Path, help="marketingskills repository root")
    parser.add_argument("target", type=Path, help="output directory that receives marketing/")
    parser.add_argument("--commit", help="synced revision, used to pin upstream links")
    args = parser.parse_args()
    try:
        build(args.upstream, args.target, args.commit)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())