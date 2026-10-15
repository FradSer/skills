import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/review-pr/scripts/review-loop.sh"
CREATE_PR_SKILL = ROOT / "skills/create-pr/SKILL.md"
REVIEW_PR_SKILL = ROOT / "skills/review-pr/SKILL.md"
REVIEW_HANDOFF_REFERENCE = ROOT / "skills/create-pr/references/review-pr-handoff.md"
REVIEW_REFERENCES = ROOT / "skills/create-pr/references"
REVIEW_SCRIPTS = ROOT / "skills/create-pr/scripts"
REVIEW_BUNDLE = REVIEW_REFERENCES / "review-pr"
REVIEW_BUNDLE_SYNC = ROOT / "tools/skill-sync/sync-review-pr-refs.py"
PR_HANDOFFS = tuple(
    ROOT / "skills" / skill / "references" / "pr-creation-handoff.md"
    for skill in ("review-pr", "create-pr", "create-issues", "resolve-issues")
)

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
    if [ "${SUPPRESS_COMMENTS_WHEN_STATE_EXISTS:-}" = "1" ] && [ -f "${STATE_FILE:-}" ]; then :; else cat "$FIXTURE_DIR/issue_comments.txt"; fi ;;
  *"pulls/122/comments"*)
    if [ "${SUPPRESS_COMMENTS_WHEN_STATE_EXISTS:-}" = "1" ] && [ -f "${STATE_FILE:-}" ]; then :; else cat "$FIXTURE_DIR/pull_comments.txt"; fi ;;
  *"pulls/122/reviews"*)
    if [ "${SUPPRESS_COMMENTS_WHEN_STATE_EXISTS:-}" = "1" ] && [ -f "${STATE_FILE:-}" ]; then :; else cat "$FIXTURE_DIR/reviews.txt"; fi ;;
  *)
    : ;;
esac
"""


def run_watch(extra_args=(), extra_env=None, review_text=REVIEW_TEXT, continuous=False):
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
            f"{NEW_REVIEW_NODE}\t{review_text}\n", encoding="utf-8"
        )
        fake_gh = bin_directory / "gh"
        fake_gh.write_text(FAKE_GH, encoding="utf-8")
        fake_gh.chmod(0o755)
        if continuous:
            sleeper = bin_directory / "sleep"
            sleeper.write_text('#!/usr/bin/env bash\nprintf \'%s\\n\' \'{"createdAt":"2026-08-15T07:34:26Z","headRefOid":"head-sha","state":"MERGED","mergedAt":"2026-08-15T09:00:00Z"}\' > "$FIXTURE_DIR/metadata.json"\n')
            sleeper.chmod(0o755)

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
            ["bash", str(SCRIPT), *([] if continuous else ["--once"]), *extra_args],
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )


class ReviewLoopWatchTests(unittest.TestCase):
    def test_review_pr_discovers_a_host_continuation_facility_per_poll(self) -> None:
        skill = " ".join(REVIEW_PR_SKILL.read_text(encoding="utf-8").split())
        self.assertIn("Discover the host's continuation facility before the first poll", skill)
        self.assertIn("re-arm it after every processed batch", skill)
        self.assertIn("do not run a foreground `while` loop", skill.lower())
        self.assertIn("ongoing monitoring could not be established", skill)
        for name in ("runbook.md", "review-loop.md"):
            document = " ".join(
                (REVIEW_PR_SKILL.parent / "references" / name)
                .read_text(encoding="utf-8")
                .split()
            )
            self.assertIn("__REVIEW_POLL__", document)
            self.assertIn("continuation", document.lower())
            self.assertIn("ongoing monitoring could not be established", document)
            self.assertNotIn("monitor_start", document)
        runbook = " ".join(
            (REVIEW_PR_SKILL.parent / "references" / "runbook.md")
            .read_text(encoding="utf-8")
            .split()
        )
        self.assertIn("foreground `while` loop", runbook)
        reference = " ".join(
            (REVIEW_PR_SKILL.parent / "references" / "review-loop.md")
            .read_text(encoding="utf-8")
            .split()
        )
        self.assertIn("manual `while true` loop", reference)

    def test_review_pr_names_no_unverified_host_tool(self) -> None:
        # The watch named `monitor_start`, which no host exposed. The agent therefore
        # reported that monitoring could not be established and stopped after one poll.
        documents = (
            REVIEW_PR_SKILL,
            REVIEW_PR_SKILL.parent / "references" / "runbook.md",
            REVIEW_PR_SKILL.parent / "references" / "review-loop.md",
            CREATE_PR_SKILL,
            REVIEW_HANDOFF_REFERENCE,
        )
        for path in documents:
            self.assertNotIn("monitor_start", path.read_text(encoding="utf-8"), path)

    def test_a_settled_gate_keeps_the_watch_armed(self) -> None:
        # Passing CI plus a handled queue is "settled", not "finished". Stopping there is
        # why a reviewer comment that arrived later was never seen.
        skill = " ".join(REVIEW_PR_SKILL.read_text(encoding="utf-8").split())
        self.assertIn("Keep the watch armed while the PR is open", skill)
        self.assertIn("is NOT a stop signal", skill)
        self.assertIn("when the PR merges or closes", skill)
        self.assertIn("keep the watch armed, and present the result", skill)
        references = REVIEW_PR_SKILL.parent / "references"
        loop = " ".join((references / "review-loop.md").read_text(encoding="utf-8").split())
        self.assertIn("Preparing closeout does not stop the watch", loop)
        self.assertIn("The PR is merged or closed", loop)
        self.assertIn("This is the loop: poll, triage, fix, acknowledge, arm the next poll", loop)
        runbook = " ".join((references / "runbook.md").read_text(encoding="utf-8").split())
        self.assertIn("Keep the watch armed while the PR stays open", runbook)
        self.assertIn("When the gate holds, prepare closeout and keep polling", runbook)
        closeout = " ".join((references / "closeout.md").read_text(encoding="utf-8").split())
        self.assertIn("Keep the watch armed", closeout)
        self.assertNotIn("Stop monitoring", closeout)

    def test_review_pr_requires_explicit_confirmation_before_merge(self) -> None:
        skill = REVIEW_PR_SKILL.read_text(encoding="utf-8")
        closeout = (REVIEW_PR_SKILL.parent / "references" / "closeout.md").read_text(
            encoding="utf-8"
        )
        handoff = (REVIEW_PR_SKILL.parent / "references" / "pr-creation-handoff.md").read_text(
            encoding="utf-8"
        )
        hook = (REVIEW_PR_SKILL.parent / "scripts" / "closeout-stop.sh").read_text(
            encoding="utf-8"
        )
        for document in (skill, closeout, handoff, hook):
            self.assertIn("explicit user confirmation", document)
        self.assertNotIn("auto-merges", skill)
        self.assertNotIn("Never ask the user whether to merge", hook)

    def test_closeout_cleans_linked_worktree_and_merged_branch(self) -> None:
        closeout = (REVIEW_PR_SKILL.parent / "references" / "closeout.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("HEAD_BRANCH", closeout)
        self.assertIn('git branch -d "$HEAD_BRANCH"', closeout)
        self.assertIn('git -C "$MAIN_WORKTREE" worktree remove "$WORKTREE_PATH"', closeout)
        self.assertIn('cd "$MAIN_WORKTREE"', closeout)
        self.assertIn('git checkout "$BASE_BRANCH"', closeout)
        self.assertIn('git merge --ff-only "origin/$BASE_BRANCH"', closeout)
        self.assertNotIn("git branch --merged main", closeout)
        self.assertNotIn("git branch --merged develop", closeout)
        self.assertIn("separate explicit authorization", closeout)
        self.assertIn("must complete before reporting success", closeout)

    def test_waiting_for_merge_confirmation_allows_the_user_turn(self) -> None:
        scripts = REVIEW_PR_SKILL.parent / "scripts"
        with tempfile.TemporaryDirectory() as directory:
            subprocess.run(["git", "init", directory], check=True, capture_output=True)
            result = subprocess.run(["bash", str(scripts / "arm-closeout.sh"), "122", "--awaiting-confirmation"], cwd=directory, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            result = subprocess.run(["bash", str(scripts / "closeout-stop.sh")], input='{"stop_hook_active":false}', cwd=directory, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")
            state = json.loads((Path(directory) / ".git/review-pr-closeout.json").read_text())
            self.assertEqual(state["pr"], "122")
            self.assertTrue(state["awaiting_confirmation"])

    def test_received_confirmation_rearms_the_closeout_reminder(self) -> None:
        scripts = REVIEW_PR_SKILL.parent / "scripts"
        with tempfile.TemporaryDirectory() as directory:
            subprocess.run(["git", "init", directory], check=True, capture_output=True)
            for arguments in (("122", "--awaiting-confirmation"), ("122",)):
                result = subprocess.run(["bash", str(scripts / "arm-closeout.sh"), *arguments], cwd=directory, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
            result = subprocess.run(["bash", str(scripts / "closeout-stop.sh")], input='{"stop_hook_active":false}', cwd=directory, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("hookSpecificOutput", json.loads(result.stdout))
            state = json.loads((Path(directory) / ".git/review-pr-closeout.json").read_text())
            self.assertFalse(state["awaiting_confirmation"])

    def test_relative_closeout_hook_has_clean_helper_paths_with_cdpath(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            scripts = root / ".agents/skills/review-pr/scripts"
            shutil.copytree(REVIEW_PR_SKILL.parent / "scripts", scripts)
            subprocess.run(["git", "init", str(root)], check=True, capture_output=True)
            armed = subprocess.run(["bash", str(scripts / "arm-closeout.sh"), "122"], cwd=root, capture_output=True, text=True)
            self.assertEqual(armed.returncode, 0, armed.stderr)
            result = subprocess.run(
                ["bash", ".agents/skills/review-pr/scripts/closeout-stop.sh"],
                input='{"stop_hook_active":false}', cwd=root, env={**os.environ, "CDPATH": str(root)}, capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
            self.assertIn(str(scripts / "clear-closeout.sh"), context)
            self.assertNotIn("\n", context)

    def test_every_pr_handoff_requires_confirmation_before_merging(self) -> None:
        for handoff in PR_HANDOFFS:
            document = handoff.read_text(encoding="utf-8")
            self.assertIn("explicit user confirmation", document, handoff)
            self.assertNotIn("no user input is requested", document, handoff)
            self.assertNotIn("auto-merges", document, handoff)

    def test_resolve_issues_workflow_preserves_confirmation_before_merge(self) -> None:
        for path in (
            ROOT / "skills/resolve-issues/SKILL.md",
            ROOT / "skills/resolve-issues/references/workflow-details.md",
        ):
            document = path.read_text(encoding="utf-8")
            self.assertIn("explicit user confirmation", document, path)
            self.assertNotIn("auto-merge", document, path)
            self.assertNotIn("without any user question", document, path)

    def test_phase_four_enters_closeout_before_user_confirmation(self) -> None:
        skill = REVIEW_PR_SKILL.read_text(encoding="utf-8")
        self.assertIn("When the gate holds", skill)
        self.assertIn("[closeout.md](references/closeout.md)", skill)
        self.assertIn("explicit user confirmation before merging", skill)
        self.assertNotIn("the pipeline has run to completion.", skill)

    def test_explicitly_bounded_pr_requests_do_not_require_a_monitoring_handoff(self) -> None:
        for path in (CREATE_PR_SKILL, REVIEW_HANDOFF_REFERENCE):
            text = path.read_text()
            self.assertIn("single snapshot", text, path)
            self.assertIn("do not start monitoring", text, path)
            self.assertIn("explicit scope", text, path)

    def test_create_pr_requires_a_single_review_pr_handoff(self) -> None:
        skill = " ".join(CREATE_PR_SKILL.read_text(encoding="utf-8").split())
        self.assertIn("Start the standalone `review-pr` workflow exactly once", skill)
        self.assertIn("references/review-pr-handoff.md", skill)
        self.assertIn("host continuation facility", skill)
        self.assertIn("Do not call `review-pr` twice", skill)

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
        self.assertIn("host continuation facility", reference)

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
            self.assertEqual(
                [item["id"] for item in state["pending_comments"]],
                [HANDLED_NODE, NEW_REVIEW_NODE],
            )

            second = run_watch(extra_env={"STATE_FILE": str(state_file)})
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertIn(ISSUE_COMMENT_TEXT, second.stdout)
            self.assertIn(REVIEW_TEXT, second.stdout)

    def test_a_later_poll_emits_only_newly_arrived_comments(self) -> None:
        # Given a triaged and acknowledged batch 1, when a reviewer posts batch 2,
        # then the next poll emits the new comment and suppresses the acknowledged one.
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            fixtures = temporary_path / "fixtures"
            fixtures.mkdir()
            state_file = temporary_path / "watch-state.json"
            (fixtures / "metadata.json").write_text(
                '{"createdAt":"2026-08-15T07:34:26Z","headRefOid":"head-sha","state":"OPEN","mergedAt":null}\n',
                encoding="utf-8",
            )
            (fixtures / "checks.json").write_text("[]\n", encoding="utf-8")
            (fixtures / "pull_comments.txt").write_text("", encoding="utf-8")
            (fixtures / "reviews.txt").write_text("", encoding="utf-8")
            (fixtures / "issue_comments.txt").write_text(
                f"{HANDLED_NODE}\t{ISSUE_COMMENT_TEXT}\n", encoding="utf-8"
            )
            shared = {"FIXTURE_DIR": str(fixtures), "STATE_FILE": str(state_file)}

            first = run_watch(extra_env=shared)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertIn(ISSUE_COMMENT_TEXT, first.stdout)

            (fixtures / "reviews.txt").write_text(
                f"{NEW_REVIEW_NODE}\t{REVIEW_TEXT}\n", encoding="utf-8"
            )
            second = run_watch(extra_args=("--ack", HANDLED_NODE), extra_env=shared)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertNotIn(ISSUE_COMMENT_TEXT, second.stdout)
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
            calls = call_log.read_text(encoding="utf-8").splitlines() if call_log.exists() else []
            self.assertFalse(any("pr view" in call for call in calls))
            self.assertFalse(any("pr checks" in call for call in calls))
            self.assertFalse(any("issues/122/comments" in call for call in calls))
            self.assertFalse(any("pulls/122/comments" in call for call in calls))
            self.assertFalse(any("pulls/122/reviews" in call for call in calls))

    def test_expired_watch_skips_metadata_and_comment_endpoints(self) -> None:
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
                extra_env={
                    "STATE_FILE": str(state_file),
                    "CALL_LOG": str(call_log),
                    "GH_MODE": "metadata-failure",
                }
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("deadline reached", result.stdout)
            calls = call_log.read_text(encoding="utf-8").splitlines() if call_log.exists() else []
            self.assertEqual(calls, [])

    def test_rejects_invalid_pr_and_repository_inputs(self) -> None:
        for env in (
            {"PR": "https://github.com/octo/repo/pull/122", "REPO": "octo/repo"},
            {"PR": "122", "REPO": "octo/repo?x=1"},
        ):
            result = run_watch(extra_env=env)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("must be", result.stderr)

    def test_creates_parent_directory_for_explicit_state_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            state_file = Path(temporary_directory) / "nested" / "watch-state.json"
            result = run_watch(extra_env={"STATE_FILE": str(state_file)})
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(state_file.exists())

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

    def test_mismatched_state_deadline_is_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            state_file = Path(temporary_directory) / "watch-state.json"
            state_file.write_text(
                json.dumps(
                    {
                        "version": 2,
                        "pr": "999",
                        "repo": "other/repo",
                        "deadline_epoch": 0,
                    }
                ),
                encoding="utf-8",
            )
            result = run_watch(extra_env={"STATE_FILE": str(state_file)})
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("IC_kwHandled", result.stdout)
            self.assertEqual(json.loads(state_file.read_text(encoding="utf-8"))["pr"], "122")

    def test_unacknowledged_event_replays_when_cursor_returns_no_events(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            state_file = Path(temporary_directory) / "watch-state.json"
            first = run_watch(
                extra_env={
                    "STATE_FILE": str(state_file),
                    "SUPPRESS_COMMENTS_WHEN_STATE_EXISTS": "0",
                }
            )
            self.assertEqual(first.returncode, 0, first.stderr)
            second = run_watch(
                extra_env={
                    "STATE_FILE": str(state_file),
                    "SUPPRESS_COMMENTS_WHEN_STATE_EXISTS": "1",
                }
            )
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertIn(REVIEW_TEXT, second.stdout)

    def test_pending_comment_retains_tabs_in_the_body(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            state_file = Path(directory) / "watch-state.json"
            comment = REVIEW_TEXT + "\tadditional context"
            first = run_watch(extra_env={"STATE_FILE": str(state_file)}, review_text=comment)
            self.assertEqual(first.returncode, 0, first.stderr)
            second = run_watch(extra_env={"STATE_FILE": str(state_file), "SUPPRESS_COMMENTS_WHEN_STATE_EXISTS": "1"})
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertIn(comment, second.stdout)

    def test_continuous_mode_releases_lock_before_the_next_poll(self) -> None:
        result = run_watch(continuous=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("[status] PR #122 is MERGED", result.stdout)


if __name__ == "__main__":
    unittest.main()
