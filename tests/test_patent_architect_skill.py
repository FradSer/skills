from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/patent-architect/SKILL.md"


class PatentArchitectSkillTests(unittest.TestCase):
    """Guard the legal boundary and the source-evidence rules."""

    def setUp(self) -> None:
        self.text = SKILL.read_text(encoding="utf-8")

    def test_never_asserts_a_legal_conclusion(self) -> None:
        self.assertIn("Never report", self.text)
        for conclusion in ("novel", "patentable", "grantable", "ready to file"):
            self.assertIn(conclusion, self.text)

    def test_keeps_the_attorney_boundary(self) -> None:
        self.assertIn("patent attorney", self.text)
        self.assertIn("claim-scope decisions", self.text)

    def test_requires_source_ledger_fields_for_each_comparison(self) -> None:
        for field in ("jurisdiction", "retrieval date", "passage", "publication"):
            self.assertIn(field, self.text)

    def test_treats_a_snippet_as_a_lead(self) -> None:
        self.assertIn("leads until the source page", self.text)

    def test_reports_missing_retrieval_instead_of_fabricating_it(self) -> None:
        self.assertIn("without a fabricated search result", self.text)
        self.assertIn("Do not assume", self.text)

    def test_requires_authorization_before_an_external_action(self) -> None:
        self.assertIn("without explicit user authorization", self.text)


if __name__ == "__main__":
    unittest.main()