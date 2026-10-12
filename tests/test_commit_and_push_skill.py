from pathlib import Path
import unittest
import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/commit-and-push/SKILL.md"
COMMIT_SKILL = ROOT / "skills/commit/SKILL.md"


def frontmatter(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8").split("---", 2)[1])


class CommitAndPushSkillTests(unittest.TestCase):
    """Publishing is a separate authorization from committing."""

    def setUp(self) -> None:
        self.text = SKILL.read_text(encoding="utf-8")

    def test_requires_an_explicit_push_request(self) -> None:
        self.assertIn("only for an explicit request to commit and push", self.text)

    def test_refuses_detached_head_and_protected_branches(self) -> None:
        self.assertIn("Never push a detached HEAD", self.text)
        for branch in ("main", "master", "develop", "production"):
            self.assertIn(branch, self.text)

    def test_a_rejected_push_is_reported_rather_than_forced(self) -> None:
        self.assertIn("reportable failure", self.text)
        self.assertIn("do not force-push, amend, or", self.text)

    def test_reports_the_result_facts(self) -> None:
        self.assertIn("Report commit hash, branch, remote, and push result", self.text)

    def test_commit_skill_does_not_authorize_a_push(self) -> None:
        commit = COMMIT_SKILL.read_text(encoding="utf-8")
        self.assertIn("do not push", commit)
        self.assertIn("commit-and-push", frontmatter(COMMIT_SKILL)["description"])


if __name__ == "__main__":
    unittest.main()