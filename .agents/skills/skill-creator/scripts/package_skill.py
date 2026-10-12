#!/usr/bin/env python3
"""Create a validated .skill archive. Run directly or as scripts.package_skill."""

import fnmatch
import os
from pathlib import Path
import sys
import tempfile
import zipfile

if __package__:
    from .quick_validate import validate_skill
else:
    from quick_validate import validate_skill


EXCLUDE_DIRS = {"__pycache__", "node_modules", ".git", ".venv", ".pytest_cache"}
EXCLUDE_GLOBS = {"*.pyc", ".env", ".env.*"}
EXCLUDE_FILES = {".DS_Store"}
ROOT_EXCLUDE_DIRS = {"evals"}


def should_exclude(rel_path: Path) -> bool:
    """Exclude caches, private environment files, and root evaluation fixtures."""
    if any(part in EXCLUDE_DIRS for part in rel_path.parts):
        return True
    if len(rel_path.parts) > 1 and rel_path.parts[1] in ROOT_EXCLUDE_DIRS:
        return True
    return rel_path.name in EXCLUDE_FILES or any(
        fnmatch.fnmatch(rel_path.name, pattern) for pattern in EXCLUDE_GLOBS
    )


def package_skill(skill_path: str | Path, output_dir: str | Path | None = None) -> Path | None:
    """Write an archive atomically; preserve existing output on validation failure."""
    skill_path = Path(skill_path).resolve()
    valid, message = validate_skill(skill_path)
    if not valid:
        print(f"Validation failed: {message}", file=sys.stderr)
        return None
    output_path = Path(output_dir).resolve() if output_dir is not None else Path.cwd()
    skill_filename = output_path / f"{skill_path.name}.skill"
    temporary: Path | None = None
    try:
        files: list[tuple[Path, Path]] = []
        for path in sorted(skill_path.rglob("*")):
            relative = path.relative_to(skill_path.parent)
            if should_exclude(relative) or path == skill_filename:
                continue
            # Dereferencing resource links can copy unrelated private files.
            if path.is_symlink():
                raise ValueError(f"Symlink resource is not supported: {relative}")
            if path.is_file():
                files.append((path, relative))
        output_path.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=output_path, prefix=f".{skill_path.name}-", suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
        with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as archive:
            for path, relative in files:
                archive.write(path, relative)
        os.replace(temporary, skill_filename)
        temporary = None
        print(f"Packaged {len(files)} files: {skill_filename}")
        return skill_filename
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        print(f"Packaging failed: {error}", file=sys.stderr)
        return None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main() -> None:
    if not 2 <= len(sys.argv) <= 3:
        print("Usage: uv run --with pyyaml python package_skill.py <skill-directory> [output-directory]")
        raise SystemExit(2)
    result = package_skill(sys.argv[1], sys.argv[2] if len(sys.argv) == 3 else None)
    raise SystemExit(0 if result is not None else 1)


if __name__ == "__main__":
    main()
