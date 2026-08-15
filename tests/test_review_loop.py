import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/review-pr/scripts/review-loop.sh"

HANDLED_NODE = "IC_kwHandledHandled"
NEW_REVIEW_NODE = "PRR_kwNewReview01"

ISSUE_COMMENT_TEXT = (
    f"[comment] issue node={HANDLED_NODE} id=11 @bot: already handled"
)
REVIEW_TEXT = (
    f"[comment] review node={NEW_REVIEW_NODE} id=22 @bot [COMMENTED]: new review"
)

# The script feeds every gh call through `--jq`, so the fake gh prints the
# jq-transformed shape directly: `<node_id>\t<emitted line>` for the comment
# endpoints, raw JSON for `pr checks`, and the bare timestamp for `pr view`.
FAKE_GH = """#!/usr/bin/env bash
case "$*" in
  "pr view "*)
    cat "$FIXTURE_DIR/created_at.txt" ;;
  "pr checks "*)
    cat "$FIXTURE_DIR/checks.json" ;;
  *"issues/122/comments"*)
    cat "$FIXTURE_DIR/issue_comments.txt" ;;
  *"pulls/122/comments"*)
    cat "$FIXTURE_DIR/pull_comments.txt" ;;
  *"pulls/122/reviews"*)
    cat "$FIXTURE_DIR/reviews.txt" ;;
  *)
    : ;;
esac
"""


def run_watch(extra_args=(), extra_env=None):
    with tempfile.TemporaryDirectory() as temporary_directory:
        temporary_path = Path(temporary_directory)
        bin_directory = temporary_path / "bin"
        bin_directory.mkdir()
        fixtures = temporary_path / "fixtures"
        fixtures.mkdir()
        (fixtures / "created_at.txt").write_text(
            "2026-08-15T07:34:26Z\n", encoding="utf-8"
        )
        (fixtures / "checks.json").write_text("[]\n", encoding="utf-8")
        (fixtures / "issue_comments.txt").write_text(
            f"{HANDLED_NODE}\t{ISSUE_COMMENT_TEXT}\n", encoding="utf-8"
        )
        (fixtures / "pull_comments.txt").write_text("", encoding="utf-8")
        (fixtures / "reviews.txt").write_text(
            f"{NEW_REVIEW_NODE}\t{REVIEW_TEXT}\n", encoding="utf-8"
        )
        fake_gh = bin_directory / "gh"
        fake_gh.write_text(FAKE_GH, encoding="utf-8")
        fake_gh.chmod(0o755)

        env = {
            **os.environ,
            "PATH": f"{bin_directory}{os.pathsep}{os.environ['PATH']}",
            "FIXTURE_DIR": str(fixtures),
            "PR": "122",
            "REPO": "octo/repo",
        }
        if extra_env:
            env.update(extra_env)
        return subprocess.run(
            ["bash", str(SCRIPT), "--once", *extra_args],
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )


class ReviewLoopWatchTests(unittest.TestCase):
    def test_exclude_flag_suppresses_handled_node(self) -> None:
        result = run_watch(extra_args=("--exclude", HANDLED_NODE))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn(HANDLED_NODE, result.stdout)
        self.assertIn(REVIEW_TEXT, result.stdout)

    def test_exclude_env_suppresses_handled_node(self) -> None:
        result = run_watch(extra_env={"EXCLUDE": HANDLED_NODE})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn(HANDLED_NODE, result.stdout)
        self.assertIn(REVIEW_TEXT, result.stdout)

    def test_without_exclusions_every_event_is_emitted(self) -> None:
        result = run_watch()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(ISSUE_COMMENT_TEXT, result.stdout)
        self.assertIn(REVIEW_TEXT, result.stdout)


if __name__ == "__main__":
    unittest.main()
