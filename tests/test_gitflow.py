import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills/gitflow/scripts"


class GitflowTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.log = self.root / "flow.jsonl"
        commands = self.root / "bin"
        commands.mkdir()
        self.env = {**os.environ, "PATH": f"{commands}{os.pathsep}{os.environ['PATH']}", "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull, "GIT_TERMINAL_PROMPT": "0", "FLOW_LOG": str(self.log)}
        flow = commands / "git-flow"
        flow.write_text(f"#!{sys.executable}\n" + '''import json, os, subprocess, sys
args = sys.argv[1:]
if '--help' in args or '-h' in args:
    print('--no-fetch --no-push --no-pushtag --keepremote --no-worktree --tagname')
    sys.exit(0)
with open(os.environ['FLOW_LOG'], 'a') as output:
    output.write(json.dumps(args) + '\\n')
def git(*arguments):
    return subprocess.check_output(['git', *arguments], text=True).strip()
kind, operation, name = args[:3]
prefix = git('config', '--get', 'gitflow.prefix.' + kind)
branch = prefix + name
develop = git('config', '--get', 'gitflow.branch.develop')
main = git('config', '--get', 'gitflow.branch.master')
if operation == 'start':
    git('checkout', '-b', branch, main if kind == 'hotfix' else develop)
else:
    git('checkout', develop)
    git('merge', '--no-edit', branch)
    if '--tagname' in args:
        git('tag', args[args.index('--tagname') + 1])
    git('branch', '-d', branch)
''')
        flow.chmod(0o755)
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Local fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("commit", "--allow-empty", "-m", "Initial fixture")
        self.git("checkout", "-b", "develop")
        for field, value in (("branch.master", "main"), ("branch.develop", "develop"), ("prefix.feature", "feature/"), ("prefix.release", "release/"), ("prefix.hotfix", "hotfix/")):
            self.git("config", f"gitflow.{field}", value)

    def git(self, *arguments: str) -> str:
        result = subprocess.run(["git", *arguments], cwd=self.repo, env=self.env, capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout.strip()

    def run_script(self, script: str, *arguments: str) -> subprocess.CompletedProcess:
        return subprocess.run(["bash", str(SCRIPTS / script), *arguments], cwd=self.repo, env=self.env, capture_output=True, text=True, timeout=30)

    def commit_files(self, files: dict[str, str]) -> None:
        for filename, content in files.items():
            (self.repo / filename).write_text(content)
        self.git("add", "--", *files)
        self.git("commit", "-m", "Add fixture manifests")

    def test_finish_rejects_another_branch_before_merge(self) -> None:
        self.git("branch", "feature/b")
        self.git("checkout", "-b", "feature/a")
        result = self.run_script("finish-branch.sh", "--type", "feature", "--name", "b", "--no-push")
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.git("branch", "--show-current"), "feature/a")
        self.assertEqual(self.git("branch", "--list", "feature/b"), "feature/b")
        self.assertFalse(self.log.exists())

    def test_finish_missing_origin_fails_before_mutation(self) -> None:
        self.git("checkout", "-b", "feature/a")
        result = self.run_script("finish-branch.sh", "--type", "feature", "--name", "a")
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.git("branch", "--show-current"), "feature/a")
        self.assertFalse(self.log.exists())

    def test_remote_failure_is_not_reported_as_finished(self) -> None:
        self.git("remote", "add", "origin", str(self.root / "missing-origin.git"))
        self.git("checkout", "-b", "feature/a")
        result = self.run_script("finish-branch.sh", "--type", "feature", "--name", "a")
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("feature/a finished", result.stdout)

    def test_local_finish_overrides_gitflow_remote_defaults(self) -> None:
        self.git("checkout", "-b", "feature/a")
        result = self.run_script("finish-branch.sh", "--type", "feature", "--name", "a", "--no-push")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        arguments = json.loads(self.log.read_text().splitlines()[-1])
        for flag in ("--no-fetch", "--no-push", "--no-pushtag", "--keepremote"):
            self.assertIn(flag, arguments)

    def test_explicit_version_needs_a_supported_manifest(self) -> None:
        result = self.run_script("start-branch.sh", "--type", "release", "--version", "1.2.3", "--no-push")
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.git("branch", "--show-current"), "develop")
        self.assertFalse(self.log.exists())

    def test_invalid_version_fails_before_branch_creation(self) -> None:
        self.commit_files({"VERSION": "1.0.0\n"})
        result = self.run_script("start-branch.sh", "--type", "release", "--version", "not-a-version", "--no-push")
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.git("branch", "--show-current"), "develop")
        self.assertFalse(self.log.exists())

    def test_all_manifests_are_validated_before_any_mutation(self) -> None:
        files = {"package.json": '{"name":"fixture","version":"1.0.0"}\n', "Cargo.toml": '[package]\nname = "fixture"\nversion = { workspace = true }\n'}
        self.commit_files(files)
        result = self.run_script("start-branch.sh", "--type", "release", "--version", "1.2.3", "--no-push")
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.git("status", "--porcelain"), "")
        self.assertEqual(self.git("branch", "--show-current"), "develop")
        self.assertFalse(self.log.exists())

    def test_bump_preserves_dependency_versions_and_updates_only_package_fields(self) -> None:
        self.commit_files({"package.json": '{"version":"1.0.0","metadata":{"version":"4.5.6"}}\n', "pyproject.toml": '[project]\nname = "fixture"\nversion = "1.0.0" # package\n[tool.example]\nversion = "4.5.6"\n', "Cargo.toml": '[package]\nname = "fixture"\nversion = "1.0.0"\n[dependencies.fixture]\nversion = "4.5.6"\n'})
        result = self.run_script("start-branch.sh", "--type", "release", "--version", "1.2.3-rc.1", "--no-push")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        package = json.loads((self.repo / "package.json").read_text())
        self.assertEqual(package["version"], "1.2.3-rc.1")
        self.assertEqual(package["metadata"]["version"], "4.5.6")
        for filename in ("pyproject.toml", "Cargo.toml"):
            text = (self.repo / filename).read_text()
            self.assertIn('version = "1.2.3-rc.1"', text)
            self.assertIn('version = "4.5.6"', text)
        self.assertEqual(self.git("status", "--porcelain"), "")

    def test_branch_name_uses_configured_prefix(self) -> None:
        self.git("config", "gitflow.prefix.feature", "work/")
        result = self.run_script("start-branch.sh", "--type", "feature", "--name", "a", "--no-push")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("branch work/a ready", result.stdout)
        result = self.run_script("finish-branch.sh", "--type", "feature", "--name", "a", "--no-push")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.git("branch", "--show-current"), "develop")

    def test_relative_installed_scripts_ignore_cdpath(self) -> None:
        installed = self.repo / ".agents/skills/gitflow/scripts"
        shutil.copytree(SCRIPTS, installed)
        (self.repo / ".git/info/exclude").write_text(".agents/\n")
        environment = {**self.env, "CDPATH": str(self.repo)}
        for script in ("start-branch.sh", "finish-branch.sh"):
            result = subprocess.run(
                ["bash", str(installed.relative_to(self.repo) / script), "--type", "feature", "--name", "topic", "--no-push"],
                cwd=self.repo, env=environment, capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.git("branch", "--show-current"), "develop")

    def test_json_version_bump_preserves_all_other_formatting(self) -> None:
        original = '{ "name": "fixture", "metadata": {"version": "4.5.6"}, "version": "1.0.0", "private": true }\n'
        (self.repo / "package.json").write_text(original)
        result = subprocess.run([sys.executable, str(SCRIPTS / "bump-version.py"), "--version", "1.2.3"], cwd=self.repo, capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.repo / "package.json").read_text(), original.replace('"1.0.0"', '"1.2.3"'))


class RealGitflowTests(unittest.TestCase):
    def test_current_classic_preset_local_lifecycle(self) -> None:
        if not shutil.which("git-flow"):
            self.skipTest("git-flow-next is not installed")
        version = subprocess.run(["git", "flow", "version"], capture_output=True, text=True, timeout=15)
        if "git-flow-next" not in version.stdout:
            self.skipTest("this integration checks the current git-flow-next preset")
        env = {**os.environ, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull, "GIT_TERMINAL_PROMPT": "0"}
        with tempfile.TemporaryDirectory() as directory:
            for kind, target in (("feature", "fixture"), ("release", "1.1.0"), ("hotfix", "1.0.1")):
                with self.subTest(kind=kind):
                    repo = Path(directory) / kind
                    repo.mkdir()
                    def run(*args: str) -> str:
                        result = subprocess.run(args, cwd=repo, env=env, capture_output=True, text=True, timeout=30)
                        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                        return result.stdout.strip()
                    run("git", "init", "-b", "main")
                    run("git", "config", "user.name", "Local fixture")
                    run("git", "config", "user.email", "fixture@example.invalid")
                    (repo / "VERSION").write_text("1.0.0\n")
                    run("git", "add", "VERSION")
                    run("git", "commit", "-m", "Initial local fixture")
                    run("git", "flow", "init", "--preset=classic", "--defaults", "--local")
                    arguments = ("--type", kind, "--name" if kind == "feature" else "--version", target, "--no-push")
                    run("bash", str(SCRIPTS / "start-branch.sh"), *arguments)
                    if kind == "feature":
                        (repo / "feature.txt").write_text("Local feature fixture\n")
                        run("git", "add", "feature.txt")
                        run("git", "commit", "-m", "Add local feature")
                    run("bash", str(SCRIPTS / "finish-branch.sh"), *arguments)
                    self.assertEqual(run("git", "branch", "--show-current"), "develop")
                    self.assertEqual(run("git", "status", "--porcelain"), "")
                    self.assertEqual(run("git", "branch", "--list", f"{kind}/{target}"), "")
                    if kind != "feature":
                        self.assertEqual(run("git", "show", f"v{target}:VERSION"), target)

    def test_finish_preserves_linked_worktree_with_develop_checked_out_elsewhere(self) -> None:
        if not shutil.which("git-flow"):
            self.skipTest("git-flow-next is not installed")
        version = subprocess.run(["git", "flow", "version"], capture_output=True, text=True, timeout=15)
        if "git-flow-next" not in version.stdout:
            self.skipTest("this integration checks the current git-flow-next preset")
        env = {**os.environ, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull, "GIT_TERMINAL_PROMPT": "0"}
        with tempfile.TemporaryDirectory() as directory:
            for kind, target in (("feature", "fixture"), ("release", "1.1.0"), ("hotfix", "1.0.1")):
                with self.subTest(kind=kind):
                    repo = Path(directory) / kind
                    linked = Path(directory) / f"{kind}-worktree"
                    repo.mkdir()

                    def run(*args: str, cwd: Path | None = None) -> str:
                        result = subprocess.run(args, cwd=cwd or repo, env=env, capture_output=True, text=True, timeout=30)
                        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                        return result.stdout.strip()

                    run("git", "init", "-b", "main")
                    run("git", "config", "user.name", "Local fixture")
                    run("git", "config", "user.email", "fixture@example.invalid")
                    (repo / "VERSION").write_text("1.0.0\n")
                    run("git", "add", "VERSION")
                    run("git", "commit", "-m", "Initial local fixture")
                    run("git", "flow", "init", "--preset=classic", "--defaults", "--local")
                    arguments = ("--type", kind, "--name" if kind == "feature" else "--version", target, "--no-push")
                    run("bash", str(SCRIPTS / "start-branch.sh"), *arguments)
                    run("git", "checkout", "develop")
                    run("git", "worktree", "add", str(linked), f"{kind}/{target}")
                    (linked / "change.txt").write_text(f"Local {kind} worktree fixture\n")
                    run("git", "add", "change.txt", cwd=linked)
                    run("git", "commit", "-m", "Add linked worktree change", cwd=linked)
                    output = run("bash", str(SCRIPTS / "finish-branch.sh"), *arguments, cwd=linked)
                    self.assertIn("detached", output)
                    self.assertEqual(run("git", "branch", "--show-current", cwd=linked), "")
                    self.assertEqual(run("git", "branch", "--show-current"), "develop")
                    self.assertEqual(run("git", "branch", "--list", f"{kind}/{target}"), "")
                    self.assertEqual(run("git", "show", "develop:change.txt"), f"Local {kind} worktree fixture")
                    self.assertTrue(repo.is_dir())
                    self.assertTrue(linked.is_dir())
                    if kind != "feature":
                        self.assertEqual(run("git", "show", f"v{target}:VERSION"), target)


if __name__ == "__main__":
    unittest.main()
