from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
LINK = re.compile(r"\[[^\]]*\]\(([^)#\s]+)")


def reachable_files(skill_dir: Path) -> set[Path]:
    """Files an agent can reach from SKILL.md by following relative links."""
    entry = (skill_dir / "SKILL.md").resolve()
    seen: set[Path] = {entry}
    queue = [entry]
    root = skill_dir.resolve()
    while queue:
        current = queue.pop()
        for target in LINK.findall(current.read_text(encoding="utf-8")):
            if target.startswith(("http://", "https://", "mailto:", "<")):
                continue
            candidate = (current.parent / target).resolve()
            if not candidate.is_file() or candidate in seen:
                continue
            if root not in candidate.parents:
                continue
            seen.add(candidate)
            queue.append(candidate)
    return seen


class SkillReferenceTests(unittest.TestCase):
    """A reference file that no link reaches is dead weight: no agent will read it."""

    def test_every_reference_is_reachable_from_skill_md(self) -> None:
        unreachable = []
        for entry in sorted(SKILLS.glob("*/SKILL.md")):
            skill_dir = entry.parent
            references = sorted((skill_dir / "references").rglob("*.md"))
            reached = reachable_files(skill_dir)
            for reference in references:
                if reference.resolve() not in reached:
                    unreachable.append(f"{skill_dir.name}: {reference.relative_to(skill_dir)}")
        self.assertEqual([], unreachable)


if __name__ == "__main__":
    unittest.main()