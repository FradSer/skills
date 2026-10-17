import json
from pathlib import Path
import tempfile
import shutil
import subprocess
import sys
import tomllib
import unittest

from tools.skill_eval.codex_eval import child_environment, environment_blockers, execution_status, permission_config, read_skill_receipts, usage_metrics
from tools.skill_eval.evidence import bundle_script_tool_prefixes, git_push_receipts, is_attributed, operation_receipts
from tools.skill_eval.fixtures import CASES, TEST_FAILURE, TEST_SUCCESS, _executes_unbounded_watch, capability_boundary_checks, challenge_wrapper_receipts, grade_task, prepare_fixture, routed_document_receipts


class CodexSkillEvalTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("codex"), "Codex CLI runtime")
    def test_permission_profile_can_read_the_resolved_codex_runtime_without_auth(self) -> None:
        rules = tomllib.loads(permission_config({"fixture": "commit"}))["permissions"]["skill-eval"]["filesystem"]
        runtime = Path(shutil.which("codex")).resolve().parent.parent
        self.assertEqual(rules.get(str(runtime)), "read")
        self.assertNotIn(str(Path.home() / ".codex"), rules)

    def test_permission_profile_keeps_network_closed_and_sources_protected(self) -> None:
        ordinary = tomllib.loads(permission_config({"fixture": "commit"}))["permissions"]["skill-eval"]
        self.assertFalse(ordinary["network"]["enabled"])
        rules = ordinary["filesystem"][":workspace_roots"]
        self.assertEqual(rules[".git"], "write")
        self.assertEqual(rules[".fixture"], "read")
        self.assertEqual(rules[".fixture/scratch"], "write")
        self.assertEqual(rules[".agents"], "read")
        creator = tomllib.loads(permission_config({"fixture": "creator"}))["permissions"]["skill-eval"]
        self.assertEqual(creator["filesystem"][":workspace_roots"][".agents/skills/csv-cleaner"], "write")

    @unittest.skipUnless(shutil.which("codex") and sys.platform == "darwin", "macOS Codex sandbox integration")
    def test_sandbox_allows_fixture_git_writes_and_blocks_external_writes_and_network(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            workspace = base / "workspace"
            (workspace / ".git").mkdir(parents=True)
            (workspace / ".fixture/bin").mkdir(parents=True)
            executable = workspace / ".fixture/bin/gh"
            executable.write_text("fixture")
            source = workspace / ".agents/skills/fixture/SKILL.md"
            source.parent.mkdir(parents=True)
            source.write_text("Protected source")
            # :workspace permits system temp writes. Create an owned directory
            # elsewhere so an unexpectedly successful probe cannot overwrite work.
            outside_directory = tempfile.TemporaryDirectory(prefix=".skill-eval-denial-", dir=Path(__file__).resolve().parents[1])
            self.addCleanup(outside_directory.cleanup)
            outside = Path(outside_directory.name) / "probe"
            probe = """import pathlib, socket, sys
root=pathlib.Path(sys.argv[1])
(root/'.git/probe').write_text('ok')
for target in (root/'.fixture/bin/gh', root/'.agents/skills/fixture/SKILL.md', pathlib.Path(sys.argv[2])):
    try:
        target.write_text('unexpected')
    except PermissionError:
        pass
    else:
        raise AssertionError('unexpected write access: '+str(target))
try:
    socket.create_connection(('1.1.1.1', 443), timeout=2)
except PermissionError:
    pass
else:
    raise AssertionError('unexpected network access')
"""
            command = ["codex", "sandbox", "--permission-profile", "skill-eval", "-C", str(workspace), "-c", permission_config({"fixture": "commit"}), "--", sys.executable, "-c", probe, str(workspace), str(outside)]
            result = subprocess.run(command, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(executable.read_text(), "fixture")
            runtime_probe = command[:command.index("--") + 1] + [str(Path(shutil.which("codex")).resolve()), "--version"]
            result = subprocess.run(runtime_probe, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("codex-cli", result.stdout)

    def test_git_metadata_permission_denial_is_an_environment_blocker(self) -> None:
        event = {"type": "item.completed", "item": {"id": "item_1", "type": "command_execution", "exit_code": 128, "aggregated_output": "fatal: Unable to create '/fixture/.git/index.lock': Operation not permitted"}}
        self.assertEqual(environment_blockers([event])[0]["item_id"], "item_1")
        event["item"]["aggregated_output"] = "FAILED (failures=1)"
        self.assertEqual(environment_blockers([event]), [])

    def test_protected_skill_denial_is_not_an_environment_blocker(self) -> None:
        event = {"type": "item.completed", "item": {"id": "denied", "type": "command_execution", "exit_code": 1, "aggregated_output": "'/fixture/.agents/skills/commit/SKILL.md': Permission denied"}}
        self.assertEqual(environment_blockers([event], {"fixture": "commit"}), [])
        event["item"]["aggregated_output"] = "'/fixture/.agents/skills/csv-cleaner/SKILL.md': Permission denied"
        self.assertTrue(environment_blockers([event], {"fixture": "creator"}))

    @unittest.skipUnless(shutil.which("codex") and sys.platform == "darwin", "macOS Codex sandbox integration")
    def test_parent_verification_cannot_read_external_files_or_use_network(self) -> None:
        from tools.skill_eval.fixtures import run_verification

        case = next(case for case in CASES if case["id"] == "resolve-issue-locally")
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory(prefix=".skill-eval-verification-", dir=Path(__file__).resolve().parents[1]) as external_directory:
            root = Path(directory)
            prepare_fixture(case, root)
            external = Path(external_directory) / "owned-sentinel"
            external.write_text("owned test sentinel")
            probe = root / ".fixture/scratch/probe.py"
            probe.write_text("import pathlib, socket, sys\ntry:\n    pathlib.Path(sys.argv[1]).read_text()\nexcept PermissionError:\n    pass\nelse:\n    raise AssertionError('external read allowed')\ntry:\n    socket.create_connection(('1.1.1.1',443),timeout=2)\nexcept PermissionError:\n    pass\nelse:\n    raise AssertionError('network allowed')\n")
            result = run_verification(case, root, root, [sys.executable, str(probe), str(external)], 30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    @unittest.skipUnless(shutil.which("codex") and shutil.which("swift") and sys.platform == "darwin", "macOS Swift sandbox integration")
    def test_swift_package_manifest_builds_inside_the_verification_sandbox(self) -> None:
        case = next(case for case in CASES if case["id"] == "swiftui-stable-identity")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            context = prepare_fixture(case, root)
            checks = grade_task(case, root, context, [], "Build")
            build = next(item for item in checks if item["text"] == "Build with the installed Swift toolchain")
            self.assertTrue(build["passed"], (root / ".fixture/swift-build.txt").read_text())
    def test_success_requires_a_completed_turn_and_nonempty_final(self) -> None:
        events = [{"type": "thread.started", "thread_id": "fixture"}, {"type": "turn.completed"}]
        self.assertEqual(execution_status(0, events, "Done"), "completed")
        self.assertEqual(execution_status(0, events[:-1], "Done"), "runtime_error")
        self.assertEqual(execution_status(0, events, ""), "runtime_error")

    def test_failed_process_cannot_be_a_successful_negative_case(self) -> None:
        events = [{"type": "turn.completed"}, {"type": "turn.failed", "error": {"message": "outage"}}]
        self.assertEqual(execution_status(1, events, "I did not use it"), "runtime_error")
        self.assertEqual(execution_status(0, events, "I did not use it"), "runtime_error")

    def test_skill_claim_and_failed_read_are_not_invocation_receipts(self) -> None:
        # Requirement (unchanged): a claimed or failed read is not an invocation receipt.
        # A chain exits with its last command's status, so exit_code alone cannot show a
        # failed read (see test_skill_read_receipt_survives_a_failed_later_command). The
        # failure is modelled by the read error, which is the direct evidence.
        claimed = {"type": "item.completed", "item": {"type": "agent_message", "text": "I read the commit skill"}}
        refused = {"type": "item.completed", "item": {"type": "command_execution", "command": "cat .agents/skills/commit/SKILL.md", "aggregated_output": "cat: .agents/skills/commit/SKILL.md: No such file or directory\n", "exit_code": 1}}
        empty = {"type": "item.completed", "item": {"type": "command_execution", "command": "cat .agents/skills/commit/SKILL.md", "aggregated_output": "", "exit_code": 1}}
        self.assertEqual(read_skill_receipts([claimed, refused, empty], "commit"), [])

    def test_printf_of_a_skill_name_is_not_a_read_receipt(self) -> None:
        event = {"type": "item.completed", "item": {"id": "fake", "type": "command_execution", "command": "printf 'name: commit\\n' .agents/skills/commit/SKILL.md", "aggregated_output": "name: commit\n", "exit_code": 0}}
        self.assertEqual(read_skill_receipts([event], "commit"), [])

    def test_child_environment_excludes_ambient_secrets_and_shell_injection(self) -> None:
        environment = child_environment({"HOME": "/fixture/home", "PATH": "/fixture/bin", "API_TOKEN": "synthetic-secret", "OPENAI_API_KEY": "synthetic-key", "BASH_ENV": "/fixture/startup.sh", "CODEX_THREAD_ID": "parent"}, {"GH_HOST": "fixture.invalid"})
        self.assertEqual(environment, {"HOME": "/fixture/home", "PATH": "/fixture/bin", "GH_HOST": "fixture.invalid"})

    def test_receipt_requires_the_selected_local_skill_and_its_content(self) -> None:
        item = {"type": "item.completed", "item": {"id": "item_1", "type": "command_execution", "command": "cat .agents/skills/commit/SKILL.md", "aggregated_output": "---\nname: commit\n---\n# Commit\n", "exit_code": 0}}
        self.assertEqual(read_skill_receipts([item], "commit"), ["item_1"])
        self.assertEqual(read_skill_receipts([item], "create-pr"), [])
        item["item"]["command"] = "cat /Users/example/.codex/skills/commit/SKILL.md"
        self.assertEqual(read_skill_receipts([item], "commit"), [])

    def test_usage_is_observed_and_missing_values_are_null(self) -> None:
        self.assertEqual(usage_metrics([]), {"input_tokens": None, "cached_input_tokens": None, "output_tokens": None})
        events = [{"type": "turn.completed", "usage": {"input_tokens": 200, "cached_input_tokens": 100, "output_tokens": 17}}]
        self.assertEqual(usage_metrics(events), {"input_tokens": 200, "cached_input_tokens": 100, "output_tokens": 17})

    def test_catalog_covers_all_repository_skill_entrypoints(self) -> None:
        root = Path(__file__).resolve().parents[1]
        expected = {entry.parent.name for base in ("skills", ".agents/skills") for entry in (root / base).glob("*/SKILL.md")}
        self.assertEqual({case["skill"] for case in CASES}, expected)
        self.assertEqual(len({case["id"] for case in CASES}), len(CASES))

    def test_unchanged_commit_fixture_does_not_pass(self) -> None:
        case = next(case for case in CASES if case["id"] == "commit-scoped")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            context = prepare_fixture(case, root)
            expectations = grade_task(case, root, context, [], "I committed it")
            self.assertFalse(all(item["passed"] for item in expectations))

    def test_routed_read_receipts_require_a_workflow_document(self) -> None:
        # Regression origin: a router is not a workflow. Reading only the marketing index
        # must not count as routing, and narrowing to a document must reject a sibling.
        def event(identifier: str, command: str, output: str = "# CRO\n") -> dict:
            return {"type": "item.completed", "item": {"id": identifier, "type": "command_execution", "command": command, "aggregated_output": output, "exit_code": 0}}

        index_only = [event("i1", "cat .agents/skills/marketing/SKILL.md", "---\nname: marketing\n---\n")]
        routed = [event("i2", "sed -n '1,80p' .agents/skills/marketing/cro/cro.md")]
        denied = [event("i3", "cat .agents/skills/marketing/signup/signup.md", "cat: .agents/skills/marketing/signup/signup.md: No such file or directory\n")]
        self.assertEqual([], routed_document_receipts(index_only, "marketing"))
        self.assertEqual(["i2"], routed_document_receipts(routed, "marketing"))
        self.assertEqual(["i2"], routed_document_receipts(routed, "marketing", ("cro/cro.md",)))
        self.assertEqual([], routed_document_receipts(routed, "marketing", ("signup/signup.md",)))
        self.assertEqual([], routed_document_receipts(denied, "marketing"))

    def test_capability_boundary_cases_exist_for_every_dependent_skill(self) -> None:
        boundary = {case["skill"] for case in CASES if case.get("expected_outcome") == "capability_boundary"}
        self.assertEqual({"loop", "review-pr"}, boundary)
        review = next(case for case in CASES if case["id"] == "pr-review-capability-boundary")
        self.assertEqual("review", review["fixture"])

    def test_capability_boundary_grader_flags_the_original_defect(self) -> None:
        def graded(commands, final):
            checks = []
            capability_boundary_checks(lambda text, passed, evidence: checks.append((text, bool(passed))), commands, final, "continuation facility")
            return {text: passed for text, passed in checks}

        # The recorded failure: an unbounded foreground watch plus a tool no host exposed.
        defect = graded([{"command": "bash review-loop.sh --pr 7 --repo octo/repo"}], "Started `monitor_start` for the next poll.")
        self.assertFalse(defect["Do not start an unsupported recurring or foreground watch"])
        self.assertFalse(defect["Name no tool the host does not have"])
        self.assertFalse(defect["Explain the unavailable continuation facility"])

        # The fixed contract: one bounded poll, the missing facility named, and a stop.
        fixed = graded(
            [{"command": "bash review-loop.sh --once --pr 7 --repo octo/repo"}],
            "This host has no continuation facility, so ongoing monitoring could not be established; I stopped after one bounded poll.",
        )
        self.assertTrue(all(fixed.values()), fixed)

        # A bounded poll that claims the watch is running must still fail.
        silent = graded([{"command": "bash review-loop.sh --once"}], "The watch is running and will report later.")
        self.assertFalse(silent["Explain the unavailable continuation facility"])

    def test_capability_boundary_grader_ignores_reading_the_watch_script(self) -> None:
        # The 2026-10-15 review run failed on `cat .agents/skills/review-pr/scripts/review-loop.sh`:
        # the guard matched the path, not an execution. Reading is not watching.
        for command in (
            "cat .agents/skills/review-pr/scripts/review-loop.sh",
            "rg review-loop.sh",
            "head -20 review-loop.sh",
            "sed -n 1,40p review-loop.sh",
            "crontab -l",
            "PR=7 bash review-loop.sh --once --repo octo/repo",
        ):
            self.assertFalse(_executes_unbounded_watch(command), command)
        for command in (
            "bash review-loop.sh --pr 7 --repo octo/repo",
            "PR=7 REPO=octo/repo INTERVAL=180 review-loop.sh",
            "nohup review-loop.sh",
            "while true; do review-loop.sh --once; done",
            "crontab -e",
            "launchctl load ~/Library/LaunchAgents/watch.plist",
        ):
            self.assertTrue(_executes_unbounded_watch(command), command)

    def test_capability_boundary_grader_accepts_the_terms_the_skills_use(self) -> None:
        def graded(final):
            checks = []
            capability_boundary_checks(lambda text, passed, evidence: checks.append((text, bool(passed))), [], final, "continuation facility")
            return {text: passed for text, passed in checks}

        self.assertTrue(graded("宿主缺少跨 turn 返回 poll 结果的设施，持续监控未能建立，已停在能力边界。")["Explain the unavailable continuation facility"])
        self.assertFalse(graded("监控已在进行中，稍后汇报。")["Explain the unavailable continuation facility"])

    def test_script_mediated_service_records_are_attributed_to_the_bundle_script(self) -> None:
        # review-loop.sh silences its gh stderr, so those receipts never reach the transcript.
        # The record is still real: the invoked bundle script contains that subcommand.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            scripts = root / ".agents/skills/review-pr/scripts"
            scripts.mkdir(parents=True)
            (scripts / "review-loop.sh").write_text('metadata=$(gh pr view "$PR" --repo "$REPO" --json state 2>/dev/null)\ngh pr checks "$PR" 2>/dev/null\n')
            (root / ".fixture/bin").mkdir(parents=True)
            events = [{"type": "item.completed", "item": {"type": "command_execution", "command": 'SKILL_DIR="$PWD/.agents/skills/review-pr" bash "$SKILL_DIR/scripts/review-loop.sh" --once', "aggregated_output": "[ci] tests: pass"}}]
            prefixes = bundle_script_tool_prefixes(events, root / ".fixture/bin")
            self.assertEqual({("gh", "pr", "view"), ("gh", "pr", "checks")}, prefixes)
            self.assertTrue(is_attributed({"tool": "gh", "args": ["pr", "view", "7", "--json", "state"]}, prefixes))
            self.assertTrue(is_attributed({"tool": "gh", "args": ["pr", "checks", "7"]}, prefixes))
            # A subcommand the script never runs stays unattributed, and the comparison fails.
            self.assertFalse(is_attributed({"tool": "gh", "args": ["pr", "merge", "7"]}, prefixes))
            self.assertFalse(is_attributed({"tool": "lark-cli", "args": ["doc", "read"]}, prefixes))
            # Reading the script in another command must not change the attribution set.
            self.assertEqual(prefixes, bundle_script_tool_prefixes([*events, {"type": "item.completed", "item": {"type": "command_execution", "command": "rg --files .agents/skills", "aggregated_output": ""}}], root / ".fixture/bin"))

    def test_skill_read_receipt_survives_a_failed_later_command(self) -> None:
        # The 2026-10-15 storm run read the skill, then listed a missing directory in the
        # same chain: exit code 2 dropped the receipt even though the read succeeded.
        def event(command, output, exit_code):
            return {"type": "item.completed", "item": {"id": "item_1", "type": "command_execution", "command": command, "aggregated_output": output, "exit_code": exit_code}}

        skill_text = "---\nname: storm\ndescription: x\n---\n# storm\n"
        read_then_fail = event(
            "cat .agents/skills/storm/SKILL.md; rg --files storm-run",
            skill_text + "rg: storm-run: No such file or directory (os error 2)\n",
            2,
        )
        self.assertEqual(["item_1"], read_skill_receipts([read_then_fail], "storm"))
        # A reported read error for that path refutes the receipt.
        missing = event(
            "cat .agents/skills/storm/SKILL.md",
            "cat: .agents/skills/storm/SKILL.md: No such file or directory\n",
            1,
        )
        self.assertEqual([], read_skill_receipts([missing], "storm"))
        # A command that never prints the frontmatter is not a read.
        self.assertEqual([], read_skill_receipts([event("cat .agents/skills/storm/SKILL.md", "# storm\n", 0)], "storm"))
        # A foreign skill's name does not stand in for this skill.
        self.assertEqual([], read_skill_receipts([event("cat .agents/skills/storm/SKILL.md", "---\nname: other\n---\n", 0)], "storm"))

    def test_challenge_status_capture_accepts_a_labelled_exit_code(self) -> None:
        now = Path("/tmp/nowhere")
        script = "bash .agents/skills/missav/scripts/browse-page.sh https://catalogue.fixture.invalid/challenge --isolated"
        stopped = "Automated access stopped after a Cloudflare challenge. Authorized API or site-owner access is required.\n"
        def event(output, exit_code):
            return {"id": "item_1", "type": "command_execution", "command": script, "aggregated_output": output, "exit_code": exit_code}

        # The 2026-10-15 missav run reported `browse-page exit status: 42` in a chain that
        # exited 0, and the old capture accepted only `42` or `exit_status=42`.
        for output in ("browse-page exit status: 42\n" + stopped, "exit_status=42\n" + stopped, "42\n" + stopped, "exit code 42\n" + stopped):
            with self.subTest(output.splitlines()[0]):
                self.assertEqual(["item_1"], challenge_wrapper_receipts([event(output, 0)], now))
        # The wrapper's own exit code is enough on its own.
        self.assertEqual(["item_1"], challenge_wrapper_receipts([event(stopped, 42)], now))
        # An unrelated number, or a capture without the stop message, is not a receipt.
        self.assertEqual([], challenge_wrapper_receipts([event("page answered 42\n" + stopped, 0)], now))
        self.assertEqual([], challenge_wrapper_receipts([event("browse-page exit status: 42\n", 0)], now))

    def test_a_failed_tool_call_is_not_a_receipt(self) -> None:
        # A chain exits with its LAST command's status, so a trailing success used to credit a
        # rejected push or a denied service call. The failure markers are the direct evidence.
        def item(cid, command, output, exit_code=0):
            return {"type": "item.completed", "item": {"id": cid, "type": "command_execution", "command": command, "aggregated_output": output, "exit_code": exit_code}}

        rejected = item("rejected", "git push origin main; echo done", "To file:///tmp/remote\n ! [rejected]        main -> main (fetch first)\nerror: failed to push some refs to 'file:///tmp/remote'\ndone\n")
        pushed = item("pushed", "git push origin main; rg --files missing", "To file:///tmp/remote\n   abc123..def456  main -> main\n", 2)
        up_to_date = item("uptodate", "git push origin main", "Everything up-to-date\n")
        self.assertEqual([], git_push_receipts([rejected]))
        # A push that succeeded still counts when a later command in the chain failed.
        self.assertEqual(["pushed"], git_push_receipts([pushed]))
        self.assertEqual(["uptodate"], git_push_receipts([up_to_date]))
        denied = item("denied", "gh pr merge 7 --merge; echo done", "HTTP 403: Resource not accessible\ndone\n")
        merged = item("merged", "gh pr merge 7 --merge", "Merged pull request #7\n")
        self.assertEqual([], operation_receipts([denied], "gh", "pr", "merge"))
        self.assertEqual(["merged"], operation_receipts([merged], "gh", "pr", "merge"))

    def test_a_denial_is_a_blocker_even_when_the_chain_exited_zero(self) -> None:
        # A chain exits with its last command's status, so a denial followed by a successful
        # command used to hide: the case was then judged as an agent failure.
        event = {"type": "item.completed", "item": {"id": "item_1", "type": "command_execution", "exit_code": 0, "aggregated_output": "fatal: Unable to create '/fixture/.git/index.lock': Operation not permitted\ndone\n"}}
        self.assertEqual([{"item_id": "item_1", "evidence": event["item"]["aggregated_output"][:1000]}], environment_blockers([event]))

    def test_red_before_green_reads_the_test_output_not_the_chain_status(self) -> None:
        # `pytest -q; echo status=$?` hides a failing run behind exit 0, and a trailing
        # failure hides a passing one.
        def item(cid, command, output, exit_code):
            return {"id": cid, "type": "command_execution", "command": command, "aggregated_output": output, "exit_code": exit_code}

        suite = "python3 -m unittest discover -s tests -v"
        attempts = [
            item("red", suite + "; echo status=$?", "FAILED (failures=1)\nstatus=1\n", 0),
            item("green", suite, "OK\n", 0),
        ]

        def observed(items):
            red = [i for i, value in enumerate(items) if TEST_FAILURE.search(value["aggregated_output"])]
            green = [i for i, value in enumerate(items) if TEST_SUCCESS.search(value["aggregated_output"]) and not TEST_FAILURE.search(value["aggregated_output"])]
            return any(failure < success for failure in red for success in green), (red, green)

        self.assertEqual((True, ([0], [1])), observed(attempts))
        # A chain that never ran a failing suite has no RED to observe.
        self.assertEqual((False, ([], [0])), observed([item("green", suite, "OK\n", 0)]))
        # A passing run still counts as GREEN when a later command in the chain failed.
        mixed = [item("mixed", "python3 -m unittest discover -s tests; rg missing", "OK\nrg: missing: No such file or directory\n", 2)]
        self.assertEqual((False, ([], [0])), observed(mixed))
        # pytest reports a failure in lowercase; both forms count as RED.
        self.assertEqual((True, ([0], [1])), observed([item("red", "pytest -q; echo done", "1 failed, 0 passed in 0.04s\ndone\n", 0), item("green", "pytest -q", "2 passed in 0.03s\n", 0)]))

    def test_malformed_model_artifact_is_a_contract_failure(self) -> None:
        case = next(case for case in CASES if case["id"] == "missav-offline-ranking")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            context = prepare_fixture(case, root)
            (root / "ranked.json").write_text("not json")
            expectations = grade_task(case, root, context, [], "Ranked")
            self.assertFalse(all(item["passed"] for item in expectations))

    def test_deleted_unrelated_file_is_a_contract_failure(self) -> None:
        case = next(case for case in CASES if case["id"] == "tropes-audit-only")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            context = prepare_fixture(case, root)
            (root / "notes/draft.md").unlink()
            expectations = grade_task(case, root, context, [], "Reviewed")
            self.assertFalse(expectations[0]["passed"])

    def test_unpublished_branch_is_a_contract_failure_without_grader_error(self) -> None:
        case = next(case for case in CASES if case["id"] == "push-local-remote")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            context = prepare_fixture(case, root)
            expectations = grade_task(case, root, context, [], "Push failed")
            publication = next(item for item in expectations if "Publish the exact branch" in item["text"])
            self.assertFalse(publication["passed"])

    def test_storm_artifacts_resolve_the_documented_topic_subdirectory(self) -> None:
        case = next(case for case in CASES if case["id"] == "storm-local-sources")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            context = prepare_fixture(case, root)
            output = root / "storm-run/fixture-topic"
            (output / "research").mkdir(parents=True)
            (output / "research/sources.json").write_text('[{"id":1},{"id":2}]')
            (output / "article-polished.md").write_text("40 人样本观察减少 12%，不能泛化。[1][2]")
            for name in ("run-config.json", "outline.md", "article.md"):
                (output / name).write_text("{}" if name.endswith(".json") else "Fixture")
            expectations = grade_task(case, root, context, [], "Complete")
            self.assertTrue(all(item["passed"] for item in expectations), expectations)

    def test_forged_service_log_without_an_execution_receipt_does_not_pass(self) -> None:
        case = next(case for case in CASES if case["id"] == "issue-create")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            context = prepare_fixture(case, root)
            log = {"tool": "gh", "operation": "issue.create", "write": True, "allowed": True, "returncode": 0, "args": ["issue", "create", "--label", "bug"], "body": "Ada; empty"}
            (root / ".fixture/service_calls.jsonl").write_text(json.dumps(log) + "\n")
            checks = grade_task(case, root, context, [], "Created")
            self.assertFalse(all(item["passed"] for item in checks))

    def test_meaningless_readonly_audit_is_not_substantive(self) -> None:
        for identifier in ("readme-audit-only", "tropes-audit-only"):
            case = next(case for case in CASES if case["id"] == identifier)
            with self.subTest(case=identifier), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                context = prepare_fixture(case, root)
                checks = grade_task(case, root, context, [], "x" * 101)
                self.assertFalse(all(item["passed"] for item in checks))

    def test_pr_without_a_published_head_does_not_pass(self) -> None:
        case = next(case for case in CASES if case["id"] == "pr-create-bounded")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            context = prepare_fixture(case, root)
            command = [str(root / ".fixture/bin/gh"), "pr", "create", "--title", "Trim whitespace", "--body", "Closes #7", "--draft"]
            result = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            import shlex
            event = {"type": "item.completed", "item": {"id": "create", "type": "command_execution", "command": shlex.join(command), "exit_code": 0, "aggregated_output": result.stdout + result.stderr}}
            checks = grade_task(case, root, context, [event], "Created")
            published = next(item for item in checks if item["text"] == "Publish the PR head to the local remote")
            self.assertFalse(published["passed"])
            observed = next(item for item in checks if "with an observed CLI command" in item["text"])
            self.assertTrue(observed["passed"], checks)

    def test_unrequested_new_file_and_readonly_review_mutation_do_not_pass(self) -> None:
        for identifier in ("readme-nested-only", "pr-review-read-only"):
            case = next(case for case in CASES if case["id"] == identifier)
            with self.subTest(case=identifier), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                context = prepare_fixture(case, root)
                (root / "unrequested.md").write_text("Unrequested artifact")
                checks = grade_task(case, root, context, [], "formatter.py:2 P1 whitespace bug")
                scope = [item for item in checks if "new files" in item["text"] or "read-only" in item["text"]]
                self.assertTrue(any(not item["passed"] for item in scope), checks)

    def test_python_printed_lark_receipts_do_not_prove_a_document_read(self) -> None:
        case = next(case for case in CASES if case["id"] == "lark-read-document")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            context = prepare_fixture(case, root)
            calls = [{"tool": "lark-cli", "operation": operation, "write": False, "allowed": True, "returncode": 0, "args": args} for operation, args in [("skills.read", ["skills", "read", "lark-shared"]), ("doc.fetch", ["docs", "+fetch", "--doc", "fixture_budget"])]]
            (root / ".fixture/service_calls.jsonl").write_text("".join(json.dumps(call) + "\n" for call in calls))
            event = {"type": "item.completed", "item": {"id": "fake", "type": "command_execution", "command": "python3 -c 'print(\"synthetic receipt\")'", "exit_code": 0, "aggregated_output": "".join("SKILL_EVAL_SERVICE_RECEIPT " + json.dumps(call) + "\n" for call in calls)}}
            checks = grade_task(case, root, context, [event], "预算 650，负责人 Lin，时间待定。")
            self.assertFalse(all(item["passed"] for item in checks), checks)

    def test_issue_bug_word_does_not_replace_the_requested_bug_label(self) -> None:
        import shlex

        case = next(case for case in CASES if case["id"] == "issue-create")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            context = prepare_fixture(case, root)
            command = [str(root / ".fixture/bin/gh"), "issue", "create", "--title", "Whitespace bug", "--body", "bug: Ada; empty input stays empty"]
            result = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            event = {"type": "item.completed", "item": {"id": "create", "type": "command_execution", "command": shlex.join(command), "exit_code": 0, "aggregated_output": result.stdout + result.stderr}}
            checks = grade_task(case, root, context, [event], "Created")
            self.assertFalse(all(item["passed"] for item in checks), checks)

    def test_native_cli_help_receipts_are_corroborated_without_being_creations(self) -> None:
        import shlex

        case = next(case for case in CASES if case["id"] == "issue-create")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            context = prepare_fixture(case, root)
            command = [str(root / ".fixture/bin/gh"), "issue", "create", "--help"]
            result = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=15)
            event = {"type": "item.completed", "item": {"id": "help", "type": "command_execution", "command": shlex.join(command), "exit_code": result.returncode, "aggregated_output": result.stdout + result.stderr}}
            checks = grade_task(case, root, context, [event], "Inspected help")
            corroboration = next(item for item in checks if item["text"].startswith("Corroborate service records"))
            creation = next(item for item in checks if item["text"].startswith("Create the exact authorized resource"))
            self.assertTrue(corroboration["passed"], checks)
            self.assertFalse(creation["passed"], checks)

    def test_remote_ref_without_an_observed_git_push_does_not_pass(self) -> None:
        case = next(case for case in CASES if case["id"] == "push-local-remote")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            context = prepare_fixture(case, root)
            for command in (["git", "add", "formatter.py", "tests/test_formatter.py"], ["git", "commit", "-m", "fix: trim whitespace"], ["git", "--git-dir=.fixture/origin.git", "fetch", str(root), "feature/trim:refs/heads/feature/trim"]):
                subprocess.run(command, cwd=root, capture_output=True, check=True)
            event = {"type": "item.completed", "item": {"id": "fetch", "type": "command_execution", "command": "git --git-dir=.fixture/origin.git fetch . feature/trim:refs/heads/feature/trim", "exit_code": 0, "aggregated_output": "Fetched"}}
            checks = grade_task(case, root, context, [event], "Published")
            self.assertFalse(all(item["passed"] for item in checks), checks)

    def test_browser_log_without_the_challenge_wrapper_execution_does_not_pass(self) -> None:
        case = next(case for case in CASES if case["id"] == "missav-challenge-stop")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            context = prepare_fixture(case, root)
            (root / ".fixture/browser_calls.jsonl").write_text('["open","https://catalogue.fixture.invalid/challenge"]\n')
            checks = grade_task(case, root, context, [], "Cloudflare challenge stopped")
            self.assertFalse(all(item["passed"] for item in checks), checks)

    def test_successful_negative_test_can_capture_the_real_wrapper_exit(self) -> None:
        import os
        import shlex

        case = next(case for case in CASES if case["id"] == "missav-challenge-stop")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(Path(__file__).resolve().parents[1] / "skills/missav", root / ".agents/skills/missav")
            context = prepare_fixture(case, root)
            command = ["bash", "-c", 'bash .agents/skills/missav/scripts/browse-page.sh https://catalogue.fixture.invalid/challenge; rc=$?; printf "exit_status=%s\\n" "$rc"; test "$rc" -eq 42']
            result = subprocess.run(command, cwd=root, env={**os.environ, "PATH": str(root / ".fixture/bin") + os.pathsep + os.environ["PATH"], "MISSAV_HOME": str(root / ".fixture/missav-home")}, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            event = {"type": "item.completed", "item": {"id": "negative-test", "type": "command_execution", "command": shlex.join(command), "exit_code": 0, "aggregated_output": result.stdout + result.stderr}}
            checks = grade_task(case, root, context, [event], "Cloudflare challenge stopped")
            self.assertTrue(all(item["passed"] for item in checks), checks)

    def test_challenge_rejects_later_browsing_even_with_one_open(self) -> None:
        import os
        import shlex

        case = next(case for case in CASES if case["id"] == "missav-challenge-stop")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(Path(__file__).resolve().parents[1] / "skills/missav", root / ".agents/skills/missav")
            context = prepare_fixture(case, root)
            command = ["bash", ".agents/skills/missav/scripts/browse-page.sh", "https://catalogue.fixture.invalid/challenge"]
            environment = {**os.environ, "PATH": str(root / ".fixture/bin") + os.pathsep + os.environ["PATH"], "MISSAV_HOME": str(root / ".fixture/missav-home")}
            result = subprocess.run(command, cwd=root, env=environment, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 42, result.stdout + result.stderr)
            event = {"type": "item.completed", "item": {"id": "challenge", "type": "command_execution", "command": shlex.join(command), "exit_code": 42, "aggregated_output": result.stdout + result.stderr}}
            log = root / ".fixture/browser_calls.jsonl"
            stopped = log.read_text()
            for operation in (["scroll", "down"], ["wait", "500"], ["get", "title"], ["click", "#bypass"]):
                with self.subTest(operation=operation):
                    log.write_text(stopped)
                    subprocess.run([str(root / ".fixture/bin/agent-browser"), *operation], cwd=root, capture_output=True, timeout=15)
                    checks = grade_task(case, root, context, [event], "Cloudflare challenge stopped")
                    stopping = next(item for item in checks if item["text"] == "Stop after the first challenged page")
                    self.assertFalse(stopping["passed"], checks)

    def test_issue_fix_requires_automated_empty_string_regression_coverage(self) -> None:
        case = next(case for case in CASES if case["id"] == "resolve-issue-locally")
        for include_empty in (False, True):
            with self.subTest(include_empty=include_empty), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                context = prepare_fixture(case, root)
                fixed = root / ".agents/worktrees/fix-7"
                subprocess.run(["git", "worktree", "add", "-b", "fix/7", str(fixed)], cwd=root, capture_output=True, check=True)
                (fixed / "formatter.py").write_text("def normalize(text: str) -> str:\n    return text.strip()\n")
                test = "import unittest\nfrom formatter import normalize\n\nclass FormatterTests(unittest.TestCase):\n    def test_trim(self):\n        self.assertEqual(normalize('  Ada  '), 'Ada')\n"
                if include_empty:
                    test += "\n    def test_empty(self):\n        self.assertEqual(normalize(''), '')\n"
                (fixed / "tests/test_formatter.py").write_text(test)
                checks = grade_task(case, root, context, [], "Both acceptance conditions checked")
                coverage = next((item for item in checks if item["text"] == "Detect an empty-string regression in automated tests"), None)
                self.assertIsNotNone(coverage, checks)
                self.assertEqual(coverage["passed"], include_empty, checks)

    def test_path_override_cannot_forge_native_service_or_push_receipts(self) -> None:
        from tools.skill_eval.evidence import git_push_receipts, service_receipts

        call = {"tool": "lark-cli", "args": ["docs", "+fetch", "--doc", "fixture_budget"], "operation": "doc.fetch"}
        event = {"type": "item.completed", "item": {"id": "shadow", "type": "command_execution", "command": "PATH=.fixture/scratch:$PATH lark-cli docs +fetch --doc fixture_budget", "exit_code": 0, "aggregated_output": "SKILL_EVAL_SERVICE_RECEIPT " + json.dumps(call)}}
        self.assertEqual(service_receipts([event]), [])
        event["item"]["command"] = "PATH=.fixture/scratch:$PATH git push origin feature/trim"
        self.assertEqual(git_push_receipts([event]), [])
        event["item"]["command"] = "/fixture/.fixture/scratch/git push origin feature/trim"
        self.assertEqual(git_push_receipts([event]), [])

    def test_path_override_cannot_forge_a_skill_read_receipt(self) -> None:
        event = {"type": "item.completed", "item": {"id": "shadow", "type": "command_execution", "command": "PATH=.fixture/scratch:$PATH cat .agents/skills/commit/SKILL.md", "exit_code": 0, "aggregated_output": "---\nname: commit\n---\n"}}
        self.assertEqual(read_skill_receipts([event], "commit"), [])
        event["item"]["command"] = "/fixture/.fixture/scratch/cat .agents/skills/commit/SKILL.md"
        self.assertEqual(read_skill_receipts([event], "commit"), [])

    def test_path_override_cannot_replace_the_protected_challenge_browser(self) -> None:
        case = next(case for case in CASES if case["id"] == "missav-challenge-stop")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            context = prepare_fixture(case, root)
            (root / ".fixture/browser_calls.jsonl").write_text('["open","https://catalogue.fixture.invalid/challenge"]\n')
            event = {"type": "item.completed", "item": {"id": "shadow", "type": "command_execution", "command": "PATH=.fixture/scratch:$PATH bash .agents/skills/missav/scripts/browse-page.sh https://catalogue.fixture.invalid/challenge", "exit_code": 42, "aggregated_output": "Automated access stopped after a Cloudflare challenge"}}
            checks = grade_task(case, root, context, [event], "Cloudflare challenge stopped")
            self.assertFalse(all(item["passed"] for item in checks), checks)
    def test_extra_remote_ref_and_git_exclude_cannot_hide_scope_expansion(self) -> None:
        case = next(case for case in CASES if case["id"] == "push-local-remote")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            context = prepare_fixture(case, root)
            for command in (["git", "add", "formatter.py", "tests/test_formatter.py"], ["git", "commit", "-m", "fix: trim whitespace"], ["git", "branch", "evil"], ["git", "push", "origin", "feature/trim", "evil"]):
                subprocess.run(command, cwd=root, capture_output=True, check=True)
            (root / ".git/info/exclude").write_text("secret.txt\n")
            (root / "secret.txt").write_text("unrequested")
            event = {"type": "item.completed", "item": {"id": "push", "type": "command_execution", "command": "git push origin feature/trim evil", "exit_code": 0, "aggregated_output": "Published"}}
            checks = grade_task(case, root, context, [event], "Published")
            scope = next(item for item in checks if "new files" in item["text"])
            self.assertFalse(scope["passed"], checks)
            remote = [item for item in checks if "other remote refs" in item["text"]]
            self.assertTrue(remote and not remote[0]["passed"], checks)

    def test_regrading_preserves_the_original_failure_and_requires_actual_completion(self) -> None:
        from tools.skill_eval.regrade import regrade_case

        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory)
            original = {"id": "fixture", "status": "completed", "passed": True, "returncode": 0}
            (run / "result.json").write_text(json.dumps(original))
            (run / "case.json").write_text('{"skill":"commit","fixture":"commit"}')
            (run / "fixture-context.json").write_text("{}")
            (run / "events.jsonl").write_text('{"type":"turn.failed","error":{"message":"capacity"}}\n')
            (run / "final.txt").write_text("Claimed complete")
            before = (run / "result.json").read_bytes()
            assessment = regrade_case(run)
            self.assertEqual(assessment["status"], "runtime_error")
            self.assertFalse(assessment["passed"])
            self.assertEqual((run / "result.json").read_bytes(), before)
            self.assertTrue(assessment["original_passed"])


if __name__ == "__main__":
    unittest.main()
