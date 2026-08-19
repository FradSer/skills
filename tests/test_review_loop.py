import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/review-pr/scripts/review-loop.sh"
CREATE_PR_SKILL = ROOT / "skills/create-pr/SKILL.md"
REVIEW_HANDOFF_REFERENCE = ROOT / "skills/create-pr/references/review-pr-handoff.md"
REVIEW_REFERENCES = ROOT / "skills/create-pr/references"
REVIEW_SCRIPTS = ROOT / "skills/create-pr/scripts"
REVIEW_BUNDLE = REVIEW_REFERENCES / "review-pr"
REVIEW_BUNDLE_SYNC = ROOT / "tools/skill-sync/sync-review-pr-refs.py"

HANDLED_NODE = "IC_kwHandledHandled"
NEW_REVIEW_NODE = "PRR_kwNewReview01"

ISSUE_COMMENT_TEXT = (
    f"[comment] issue node={HANDLED_NODE} id=11 @bot: already handled"
)
REVIEW_TEXT = (
    f"[comment] review node={NEW_REVIEW_NODE} id=22 @bot [COMMENTED]: new review"
)

FAKE_GH = """#!/usr/bin/env bash
if [ -n "${CALL_LOG:-}" ]; then
  printf '%s\\n' "$*" >> "$CALL_LOG"
fi
case "$*" in
  "pr view "*)
    if [ "${GH_MODE:-}" = "metadata-failure" ]; then
      exit 1
    fi
    cat "$FIXTURE_DIR/metadata.json" ;;
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
        (fixtures / "metadata.json").write_text(
            '{"createdAt":"2026-08-15T07:34:26Z","headRefOid":"head-sha","state":"OPEN","mergedAt":null}\n',
            encoding="utf-8",
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
            "STATE_FILE": str(temporary_path / "watch-state.json"),
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
    def test_create_pr_requires_a_single_review_pr_handoff(self) -> None:
        skill = CREATE_PR_SKILL.read_text(encoding="utf-8")
        self.assertIn("Start the standalone `review-pr` workflow exactly once", skill)
        self.assertIn("references/review-pr-handoff.md", skill)
        self.assertIn("do not reproduce its review workflow here", skill)

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

    def test_default_state_path_uses_git_path(self) -> None:
        script = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('git rev-parse --git-path "review-pr-watch-${PR}.json"', script)

    def test_create_pr_uses_a_focused_review_pr_reference(self) -> None:
        reference = REVIEW_HANDOFF_REFERENCE.read_text(encoding="utf-8")
        self.assertIn("fallback under `references/` and `scripts/`", reference)
        self.assertIn("Start standalone `review-pr` exactly once", reference)
        self.assertIn("`review-pr` owns", reference)

    def test_review_pr_operational_references_are_conventionally_organized(self) -> None:
        result = subprocess.run(
            ["python3", str(REVIEW_BUNDLE_SYNC), "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(REVIEW_BUNDLE.exists())
        self.assertTrue((REVIEW_REFERENCES / "runbook.md").exists())
        self.assertTrue((REVIEW_REFERENCES / "review-loop.md").exists())
        self.assertTrue((REVIEW_REFERENCES / "closeout.md").exists())
        for name in ("review-loop.sh", "arm-closeout.sh", "clear-closeout.sh", "closeout-stop.sh"):
            script = REVIEW_SCRIPTS / name
            self.assertTrue(script.exists())
            self.assertTrue(script.stat().st_mode & 0o111)

    def test_sync_preserves_create_pr_references_and_cleans_legacy_layout(self) -> None:
        spec = importlib.util.spec_from_file_location("sync_review_pr_refs", REVIEW_BUNDLE_SYNC)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        sync_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sync_module)

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "review-pr"
            source_references = source / "references"
            source_scripts = source / "scripts"
            target_references = root / "create-pr" / "references"
            target_scripts = root / "create-pr" / "scripts"
            source_references.mkdir(parents=True)
            source_scripts.mkdir(parents=True)
            target_references.mkdir(parents=True)
            target_scripts.mkdir(parents=True)
            for name in ("runbook.md", "review-loop.md", "closeout.md"):
                (source_references / name).write_text(name, encoding="utf-8")
            for name in ("review-loop.sh", "arm-closeout.sh", "clear-closeout.sh", "closeout-stop.sh"):
                (source_scripts / name).write_text(name, encoding="utf-8")
            (target_references / "keep.md").write_text("keep", encoding="utf-8")
            (target_references / "review-loop.sh").write_text("legacy", encoding="utf-8")
            (target_references / "review-pr").mkdir()
            sync_module.SOURCE = source
            sync_module.REFERENCE_TARGET = target_references
            sync_module.SCRIPT_TARGET = target_scripts
            sync_module.sync()

            self.assertEqual((target_references / "keep.md").read_text(encoding="utf-8"), "keep")
            self.assertFalse((target_references / "review-pr").exists())
            self.assertFalse((target_references / "review-loop.sh").exists())
            for name in ("runbook.md", "review-loop.md", "closeout.md"):
                self.assertEqual((target_references / name).read_text(encoding="utf-8"), name)
            for name in ("review-loop.sh", "arm-closeout.sh", "clear-closeout.sh", "closeout-stop.sh"):
                self.assertEqual((target_scripts / name).read_text(encoding="utf-8"), name)

    def test_watch_persists_cursor_and_unacknowledged_events_for_replay(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            state_file = Path(temporary_directory) / "review-pr-watch-122.json"
            first = run_watch(extra_env={"STATE_FILE": str(state_file)})
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertTrue(state_file.exists())
            state = json.loads(state_file.read_text(encoding="utf-8"))
            self.assertEqual(state["pr"], "122")
            self.assertEqual(state["repo"], "octo/repo")
            self.assertEqual(state["emitted_comments"], [HANDLED_NODE, NEW_REVIEW_NODE])
            self.assertEqual(state["acknowledged_comments"], [])
            self.assertNotEqual(state["since"], "2026-08-15T07:34:26Z")

            second = run_watch(extra_env={"STATE_FILE": str(state_file)})
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertIn(ISSUE_COMMENT_TEXT, second.stdout)
            self.assertIn(REVIEW_TEXT, second.stdout)

    def test_changed_head_resets_persisted_ci_buckets(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            state_file = Path(temporary_directory) / "watch-state.json"
            state_file.write_text(
                json.dumps(
                    {
                        "version": 2,
                        "pr": "122",
                        "repo": "octo/repo",
                        "head_sha": "old-sha",
                        "since": "2026-08-15T07:34:26Z",
                        "deadline_epoch": 4102444800,
                        "emitted_comments": [],
                        "acknowledged_comments": [],
                        "last_ci": ["tests=pass"],
                    }
                ),
                encoding="utf-8",
            )
            result = run_watch(extra_env={"STATE_FILE": str(state_file)})
            self.assertEqual(result.returncode, 0, result.stderr)
            state = json.loads(state_file.read_text(encoding="utf-8"))
            self.assertEqual(state["head_sha"], "head-sha")
            self.assertEqual(state["last_ci"], [])

    def test_metadata_failure_does_not_advance_persisted_cursor(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            state_file = Path(temporary_directory) / "watch-state.json"
            original = {
                "version": 2,
                "pr": "122",
                "repo": "octo/repo",
                "head_sha": "head-sha",
                "since": "2026-08-15T07:34:26Z",
                "deadline_epoch": 4102444800,
                "emitted_comments": [],
                "acknowledged_comments": [],
                "last_ci": ["tests=pass"],
            }
            state_file.write_text(json.dumps(original), encoding="utf-8")
            result = run_watch(
                extra_env={"STATE_FILE": str(state_file), "GH_MODE": "metadata-failure"}
            )
            self.assertEqual(result.returncode, 1)
            state = json.loads(state_file.read_text(encoding="utf-8"))
            self.assertEqual(state["since"], original["since"])

    def test_deadline_skips_comment_endpoints(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            state_file = temporary_path / "watch-state.json"
            call_log = temporary_path / "gh-calls.log"
            state_file.write_text(
                json.dumps(
                    {
                        "version": 2,
                        "pr": "122",
                        "repo": "octo/repo",
                        "head_sha": "head-sha",
                        "since": "2026-08-15T07:34:26Z",
                        "deadline_epoch": 0,
                        "emitted_comments": [],
                        "acknowledged_comments": [],
                        "last_ci": [],
                    }
                ),
                encoding="utf-8",
            )
            result = run_watch(
                extra_env={"STATE_FILE": str(state_file), "CALL_LOG": str(call_log)}
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            calls = call_log.read_text(encoding="utf-8").splitlines()
            self.assertTrue(any("pr view" in call for call in calls))
            self.assertFalse(any("pr checks" in call for call in calls))
            self.assertFalse(any("issues/122/comments" in call for call in calls))
            self.assertFalse(any("pulls/122/comments" in call for call in calls))
            self.assertFalse(any("pulls/122/reviews" in call for call in calls))

    def test_acknowledged_comments_are_suppressed_but_emitted_comments_replay(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            state_file = Path(temporary_directory) / "watch-state.json"
            state_file.write_text(
                json.dumps(
                    {
                        "version": 2,
                        "pr": "122",
                        "repo": "octo/repo",
                        "since": "2026-08-15T07:34:26Z",
                        "emitted_comments": [HANDLED_NODE, NEW_REVIEW_NODE],
                        "acknowledged_comments": [HANDLED_NODE],
                        "last_ci": [],
                    }
                ),
                encoding="utf-8",
            )
            result = run_watch(extra_env={"STATE_FILE": str(state_file)})
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(REVIEW_TEXT, result.stdout)
            self.assertNotIn(ISSUE_COMMENT_TEXT, result.stdout)


if __name__ == "__main__":
    unittest.main()
