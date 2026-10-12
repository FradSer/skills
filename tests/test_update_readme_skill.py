from pathlib import Path
import json
import unittest
import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills/update-readme"
SKILL = SKILL_DIR / "SKILL.md"
TEMPLATE = SKILL_DIR / "references/template.md"
EVALS = SKILL_DIR / "evals/evals.json"
DESCRIPTION_WORD_BUDGET = 45


def frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    _, raw, _ = text.split("---\n", 2)
    return yaml.safe_load(raw) or {}


class UpdateReadmeSkillTests(unittest.TestCase):
    """The skill must route structure by repository shape and never invent a target."""

    def setUp(self) -> None:
        self.text = SKILL.read_text(encoding="utf-8")
        self.template = TEMPLATE.read_text(encoding="utf-8")

    def test_routes_structure_by_repository_shape(self) -> None:
        for shape in ("collection", "single-artifact"):
            self.assertIn(shape, self.text)
            self.assertIn(shape, self.template)

    def test_read_condition_names_both_readme_cases(self) -> None:
        self.assertIn("references/template.md", self.text)
        self.assertIn("new README", self.text)
        self.assertIn("existing README", self.text)

    def test_template_sections_require_a_real_target(self) -> None:
        for token in ("LICENSE", "badge", "README.zh-CN.md"):
            self.assertIn(token, self.template)
        self.assertIn("only when it exists", self.template)

    def test_description_stays_concise_and_keeps_triggers(self) -> None:
        description = frontmatter(SKILL)["description"]
        self.assertLessEqual(len(description.split()), DESCRIPTION_WORD_BUDGET)
        lowered = description.lower()
        for trigger in ("readme", "update", "sync", "audit"):
            self.assertIn(trigger, lowered)

    def test_existing_readme_wins_over_a_create_request(self) -> None:
        self.assertIn("even when the user says", self.text)
        self.assertIn("create a README", self.text)

    def test_a_plain_update_is_not_a_structural_rewrite(self) -> None:
        self.assertIn("is not a rewrite", self.text)

    def test_evals_cover_the_existing_readme_without_optional_sections(self) -> None:
        data = json.loads(EVALS.read_text(encoding="utf-8"))
        prompts = " ".join(case["prompt"] for case in data["evals"]).lower()
        self.assertIn("license", prompts)


if __name__ == "__main__":
    unittest.main()