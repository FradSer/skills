from pathlib import Path
import unittest
import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
WORD_BUDGET = 45

# The phrases a reader or a runtime matches before the body is opened. A trim that
# drops one of these changes routing, so it fails here instead of silently.
TRIGGERS = {
    "commit": ("commit", "git commit", "create commit"),
    "commit-and-push": ("commit and push", "push changes"),
    "create-issues": ("create an issue", "file a bug"),
    "create-pr": ("pull request",),
    "create-prd": ("product requirements document", "PRD"),
    "gitflow": ("gitflow start feature", "gitflow finish release", "create-pr"),
    "lark": ("lark-cli",),
    "loop": ("/loop",),
    "missav": ("missav", "/cn/search/{query}"),
    "patent-architect": ("patent", "prior-art"),
    "resolve-issues": ("resolve an issue", "fix issue"),
    "review-pr": ("review a PR", "watch CI on a pull request"),
    "storm": ("storm article", "Wikipedia-style article"),
    "swiftui": ("SwiftUI",),
    "tropes": ("style review", "trope removal"),
    "update-readme": ("update", "sync", "audit"),
}


def description(skill_md: Path) -> str:
    frontmatter = skill_md.read_text(encoding="utf-8").split("---", 2)[1]
    return " ".join(yaml.safe_load(frontmatter)["description"].split())


class SkillDescriptionTests(unittest.TestCase):
    """A description names the capability, the use condition, and the triggers."""

    def test_every_description_is_within_budget(self) -> None:
        over = {
            path.parent.name: len(description(path).split())
            for path in sorted(SKILLS.glob("*/SKILL.md"))
            if len(description(path).split()) > WORD_BUDGET
        }
        self.assertEqual({}, over, f"descriptions longer than {WORD_BUDGET} words")

    def test_every_description_keeps_its_trigger_phrases(self) -> None:
        missing = []
        for name, phrases in sorted(TRIGGERS.items()):
            text = description(SKILLS / name / "SKILL.md").lower()
            for phrase in phrases:
                if phrase.lower() not in text:
                    missing.append(f"{name}: {phrase}")
        self.assertEqual([], missing)

    def test_trigger_table_covers_every_skill(self) -> None:
        present = {path.parent.name for path in SKILLS.glob("*/SKILL.md")}
        self.assertEqual(present, set(TRIGGERS))

    def test_no_description_carries_markup(self) -> None:
        for path in sorted(SKILLS.glob("*/SKILL.md")):
            self.assertNotIn("<", description(path), path)
            self.assertNotIn(">", description(path), path)


if __name__ == "__main__":
    unittest.main()