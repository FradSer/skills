from pathlib import Path
import re
import unittest
import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
EXPECTED_SKILLS = {
    "commit",
    "commit-and-push",
    "create-issues",
    "create-pr",
    "create-prd",
    "gitflow",
    "lark",
    "loop",
    "missav",
    "patent-architect",
    "resolve-issues",
    "review-pr",
    "storm",
    "swiftui",
    "tropes",
    "update-readme",
}


def parse_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    _, raw, _ = text.split("---\n", 2)
    return yaml.safe_load(raw) or {}


class SkillsStructureTests(unittest.TestCase):
    def test_exact_expected_skills_exist(self) -> None:
        actual = {
            path.name
            for path in SKILLS.iterdir()
            if path.is_dir() and not path.name.startswith(".")
        }
        self.assertEqual(EXPECTED_SKILLS, actual)

    def test_each_skill_has_a_root_skill_md_and_no_nested_skills(self) -> None:
        for skill_name in EXPECTED_SKILLS:
            skill_dir = SKILLS / skill_name
            entry = skill_dir / "SKILL.md"
            self.assertTrue(entry.is_file(), f"{entry} must exist")
            nested = list(skill_dir.rglob("SKILL.md"))
            self.assertEqual([entry], nested, f"No nested SKILL.md in {skill_name}")

    def test_skill_frontmatter_metadata(self) -> None:
        for skill_name in EXPECTED_SKILLS:
            entry = SKILLS / skill_name / "SKILL.md"
            metadata = parse_frontmatter(entry)
            self.assertEqual(skill_name, metadata.get("name"))
            self.assertTrue(metadata.get("description"))

    def test_human_only_skills_have_disable_model_invocation(self) -> None:
        human_only_skills = {
            "commit-and-push",
            "create-issues",
            "create-pr",
            "create-prd",
            "gitflow",
            "missav",
            "patent-architect",
            "resolve-issues",
            "review-pr",
            "storm",
            "update-readme",
        }
        model_callable_skills = {
            "commit",
            "lark",
            "loop",
            "swiftui",
            "tropes",
        }
        self.assertEqual(EXPECTED_SKILLS, human_only_skills | model_callable_skills)

        for skill_name in human_only_skills:
            entry = SKILLS / skill_name / "SKILL.md"
            metadata = parse_frontmatter(entry)
            self.assertTrue(
                metadata.get("disable-model-invocation"),
                f"{skill_name} must have disable-model-invocation: true",
            )

        for skill_name in model_callable_skills:
            entry = SKILLS / skill_name / "SKILL.md"
            metadata = parse_frontmatter(entry)
            self.assertFalse(
                metadata.get("disable-model-invocation", False),
                f"{skill_name} should be model-callable (no disable-model-invocation)",
            )

    def test_gitflow_is_a_unified_skill_without_subskills(self) -> None:
        gitflow_dir = SKILLS / "gitflow"
        subdirs = [p for p in gitflow_dir.iterdir() if p.is_dir()]
        self.assertEqual(
            {"references", "scripts"},
            {p.name for p in subdirs},
            "gitflow should only contain references and scripts directories",
        )
        self.assertTrue((gitflow_dir / "scripts" / "start-branch.sh").is_file())
        self.assertTrue((gitflow_dir / "scripts" / "finish-branch.sh").is_file())

    def test_markdown_links_resolve(self) -> None:
        ignored = {"…", "README.md", "README.zh-CN.md", "LICENSE", "链接", "inflect: true"}
        missing = []
        for path in SKILLS.rglob("*.md"):
            text = path.read_text(encoding="utf-8")
            for target in re.findall(r"\[[^]]+\]\(([^)#]+)", text):
                if target.startswith(("http://", "https://", "mailto:", "#", "<")):
                    continue
                if target in ignored:
                    continue
                candidate = (path.parent / target).resolve()
                if not candidate.exists():
                    missing.append(f"{path}: {target}")
        self.assertEqual([], missing)

    def test_readmes_catalog_all_skills(self) -> None:
        for readme in (ROOT / "README.md", ROOT / "README.zh-CN.md"):
            text = readme.read_text(encoding="utf-8")
            for skill_name in EXPECTED_SKILLS:
                self.assertIn(f"skills/{skill_name}/", text)
                self.assertIn(f"--skill {skill_name}", text)


if __name__ == "__main__":
    unittest.main()
