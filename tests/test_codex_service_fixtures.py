from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from tools.skill_eval.service_fixtures import install_service_cli


class ServiceFixtureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp_dir.name)
        install_service_cli(self.workspace, {"allowed_writes": ["issue.create", "pr.create"]})
        self.gh = self.workspace / ".fixture" / "bin" / "gh"
        self.lark = self.workspace / ".fixture" / "bin" / "lark-cli"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _run(self, command: Path, *args: str, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(command), *args],
            cwd=self.workspace,
            input=input_text,
            text=True,
            capture_output=True,
            check=False,
        )

    def _calls(self) -> list[dict[str, object]]:
        path = self.workspace / ".fixture" / "service_calls.jsonl"
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

    def test_create_records_the_actual_body_file_and_returns_fixture_url(self) -> None:
        body = self.workspace / "body.md"
        body.write_text("第一行\n第二行\n", encoding="utf-8")

        result = self._run(
            self.gh,
            "issue",
            "create",
            "--repo",
            "fixture/taskbox",
            "--title",
            "Fixture issue",
            "--body-file",
            str(body),
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "https://github.com/fixture/taskbox/issues/8")
        call = self._calls()[-1]
        self.assertEqual(call["tool"], "gh")
        self.assertEqual(call["body_file"], "第一行\n第二行\n")
        self.assertEqual(call["body_file_path"], str(body))

    def test_json_and_jq_only_expose_requested_repo_fields(self) -> None:
        result = self._run(
            self.gh,
            "repo",
            "view",
            "--json",
            "nameWithOwner,defaultBranchRef",
            "--jq",
            ".nameWithOwner",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), '"fixture/taskbox"')

        raw = self._run(self.gh, "repo", "view", "--json", "nameWithOwner")
        self.assertEqual(json.loads(raw.stdout), {"nameWithOwner": "fixture/taskbox"})

    def test_pr_fixture_tracks_git_identity_and_passes_checks(self) -> None:
        result = self._run(self.gh, "pr", "view", "7", "--json", "number,baseRefName,headRefName,headRefOid,state,createdAt")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        expected_head = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
        ).stdout.strip()
        expected_branch = subprocess.run(
            ["git", "branch", "--show-current"], capture_output=True, text=True, check=True
        ).stdout.strip()
        self.assertEqual(payload["number"], 7)
        self.assertEqual(payload["baseRefName"], "main")
        self.assertEqual(payload["headRefName"], expected_branch)
        self.assertEqual(payload["headRefOid"], expected_head)
        self.assertEqual(payload["state"], "OPEN")
        self.assertLess(payload["createdAt"], "2026-10-03T00:00:00Z")

        checks = self._run(self.gh, "pr", "checks", "7", "--json", "name,state,conclusion")
        self.assertEqual(json.loads(checks.stdout), [{"name": "tests", "state": "SUCCESS", "conclusion": "success"}])

    def test_unauthorized_writes_and_unimplemented_commands_fail_but_are_recorded(self) -> None:
        state_path = self.workspace / ".fixture" / "state.json"
        state_path.write_text(json.dumps({"allowed_writes": []}) + "\n", encoding="utf-8")

        denied = self._run(self.gh, "issue", "comment", "7", "--body", "no")
        unknown = self._run(self.gh, "repo", "delete", "fixture/taskbox")

        self.assertNotEqual(denied.returncode, 0)
        self.assertIn("issue.comment", denied.stderr)
        denied_call = self._calls()[0]
        self.assertEqual(denied_call["operation"], "issue.comment")
        self.assertTrue(denied_call["write"])
        self.assertFalse(denied_call["allowed"])
        self.assertEqual(denied_call["returncode"], denied.returncode)
        self.assertEqual(denied_call["body"], "no")
        self.assertNotEqual(unknown.returncode, 0)
        self.assertIn("unsupported command", unknown.stderr)
        self.assertEqual([call["args"] for call in self._calls()], [
            ["issue", "comment", "7", "--body", "no"],
            ["repo", "delete", "fixture/taskbox"],
        ])

    def test_existing_issue_override_and_pr_diff_override_are_used(self) -> None:
        state_path = self.workspace / ".fixture" / "state.json"
        state_path.write_text(
            json.dumps({"allowed_writes": [], "existing_issues": [], "pr_diff": "diff --fixture\n"}) + "\n",
            encoding="utf-8",
        )

        issue_list = self._run(self.gh, "issue", "list", "--json", "number")
        issue_search = self._run(self.gh, "issue", "search", "normalize", "--json", "number")
        plain_list = self._run(self.gh, "issue", "list", "--state", "open")
        diff = self._run(self.gh, "pr", "diff", "7")

        self.assertEqual(json.loads(issue_list.stdout), [])
        self.assertEqual(json.loads(issue_search.stdout), [])
        self.assertEqual(plain_list.stdout.strip(), "")
        self.assertEqual(diff.returncode, 0)
        self.assertEqual(diff.stdout, "diff --fixture\n")

    def test_created_issue_metadata_is_visible_without_mutating_state(self) -> None:
        state_path = self.workspace / ".fixture/state.json"
        original = {"allowed_writes": ["issue.create"], "existing_issues": []}
        state_path.write_text(json.dumps(original) + "\n", encoding="utf-8")
        created = self._run(
            self.gh,
            "issue",
            "create",
            "--title",
            "Trim input",
            "--body",
            "Closes #7",
            "--label",
            "bug",
        )
        viewed = self._run(self.gh, "issue", "view", "8", "--json", "number,title,body,labels")

        self.assertEqual(created.returncode, 0, created.stderr)
        self.assertEqual(
            json.loads(viewed.stdout),
            {"number": 8, "title": "Trim input", "body": "Closes #7", "labels": [{"name": "bug"}]},
        )
        self.assertEqual(json.loads(state_path.read_text(encoding="utf-8")), original)

    def test_help_is_read_only_and_does_not_attempt_resource_creation(self) -> None:
        for args in (("--help",), ("help",), ("issue", "create", "--help"), ("pr", "create", "--help")):
            with self.subTest(args=args):
                result = self._run(self.gh, *args)
                self.assertEqual(result.returncode, 0, result.stderr)
                call = self._calls()[-1]
                self.assertEqual(call["operation"], "help")
                self.assertFalse(call["write"])

    def test_new_pr_fixture_is_empty_until_creation_and_retains_draft_metadata(self) -> None:
        state_path = self.workspace / ".fixture/state.json"
        state_path.write_text(json.dumps({"allowed_writes": ["pr.create"], "existing_prs": []}))
        before = self._run(self.gh, "pr", "list", "--json", "number")
        self.assertEqual(json.loads(before.stdout), [])
        created = self._run(self.gh, "pr", "create", "--title", "Trim input", "--body", "Closes #7", "--draft")
        self.assertEqual(created.returncode, 0, created.stderr)
        after = self._run(self.gh, "pr", "view", "7", "--json", "title,body,isDraft")
        self.assertEqual(json.loads(after.stdout), {"title": "Trim input", "body": "Closes #7", "isDraft": True})

    def test_stderr_receipt_matches_the_persisted_receipt_for_both_services(self) -> None:
        gh_result = self._run(self.gh, "repo", "view", "--json", "nameWithOwner")
        lark_result = self._run(self.lark, "skills", "read", "lark-shared")

        prefix = "SKILL_EVAL_SERVICE_RECEIPT "
        gh_receipt = json.loads(next(line[len(prefix):] for line in gh_result.stderr.splitlines() if line.startswith(prefix)))
        lark_receipt = json.loads(next(line[len(prefix):] for line in lark_result.stderr.splitlines() if line.startswith(prefix)))
        calls = self._calls()
        self.assertEqual(gh_receipt, calls[0])
        self.assertEqual(lark_receipt, calls[1])

    def test_known_write_forms_are_rejected_and_classified_as_writes(self) -> None:
        state_path = self.workspace / ".fixture/state.json"
        state_path.write_text(json.dumps({"allowed_writes": []}) + "\n", encoding="utf-8")
        commands = (
            (("auth", "login"), "auth.login"),
            (("auth", "logout"), "auth.logout"),
            (("repo", "delete", "fixture/taskbox"), "repo.delete"),
            (("label", "create", "priority:high"), "label.create"),
            (("label", "edit", "bug"), "label.edit"),
            (("label", "delete", "bug"), "label.delete"),
            (("api", "repos/fixture/taskbox/issues/7", "-f", "title=changed"), "api.write"),
        )
        for args, operation in commands:
            with self.subTest(args=args):
                result = self._run(self.gh, *args)
                self.assertNotEqual(result.returncode, 0)
                call = self._calls()[-1]
                self.assertEqual(call["operation"], operation)
                self.assertTrue(call["write"])
                self.assertFalse(call["allowed"])
                self.assertEqual(call["returncode"], result.returncode)

    def test_lark_auth_boundary_help_and_read_are_fixture_only(self) -> None:
        shared = self._run(self.lark, "skills", "read", "lark-shared")
        doc_skill = self._run(self.lark, "skills", "read", "lark-doc")
        help_result = self._run(self.lark, "docs", "+fetch", "--help")
        fetched = self._run(
            self.lark,
            "docs",
            "+fetch",
            "--doc",
            "fixture-doc",
            "--format",
            "markdown",
        )
        login = self._run(self.lark, "auth", "login")

        self.assertEqual(shared.returncode, 0)
        self.assertIn("已授权 user", shared.stdout)
        self.assertIn("docs +fetch", doc_skill.stdout)
        self.assertEqual(help_result.returncode, 0)
        self.assertIn("--doc <URL-or-token>", help_result.stdout)
        self.assertEqual(fetched.returncode, 0)
        self.assertEqual(fetched.stdout.strip(), "项目预算 650 元；负责人 Lin；截止日期待定")
        self.assertNotEqual(login.returncode, 0)
        self.assertIn("refused", login.stderr)
        calls = self._calls()
        self.assertEqual(calls[-1]["args"], ["auth", "login"])
        self.assertEqual(calls[1]["operation"], "skill.read")
        self.assertNotEqual(calls[1]["operation"], "doc.fetch")
        self.assertEqual(calls[3]["operation"], "doc.fetch")
        self.assertFalse(calls[-1]["allowed"])
        self.assertEqual(calls[-1]["returncode"], login.returncode)

    def test_lark_fetch_rejects_documents_outside_the_fixture_contract(self) -> None:
        wrong = self._run(
            self.lark,
            "docs",
            "+fetch",
            "--doc",
            "https://example.feishu.cn/docx/not_fixture",
            "--format",
            "markdown",
        )
        self.assertNotEqual(wrong.returncode, 0)
        self.assertIn("unsupported fixture document", wrong.stderr)
        call = self._calls()[-1]
        self.assertEqual(call["operation"], "doc.fetch")
        self.assertFalse(call["allowed"])
        self.assertEqual(call["returncode"], wrong.returncode)

        state_path = self.workspace / ".fixture/state.json"
        state_path.write_text(json.dumps({"lark_document_id": "fixture_budget"}) + "\n", encoding="utf-8")
        configured = self._run(
            self.lark,
            "docs",
            "+fetch",
            "--doc",
            "https://example.feishu.cn/docx/fixture_budget",
            "--format",
            "markdown",
        )
        another = self._run(self.lark, "docs", "+fetch", "--doc", "fixture-other")
        self.assertEqual(configured.returncode, 0, configured.stderr)
        self.assertNotEqual(another.returncode, 0)


if __name__ == "__main__":
    unittest.main()
