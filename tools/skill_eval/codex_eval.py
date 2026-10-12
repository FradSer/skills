"""Run explicit source-skill tasks in fresh, bounded Codex CLI processes."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import time
from typing import Any

from tools.skill_eval.evidence import trusted_argvs


ROOT = Path(__file__).resolve().parents[2]


def execution_status(returncode: int, events: list[dict[str, Any]], final: str) -> str:
    failed = any(event.get("type") in {"turn.failed", "error"} for event in events)
    completed = any(event.get("type") == "turn.completed" for event in events)
    return "completed" if returncode == 0 and completed and final.strip() and not failed else "runtime_error"


def read_skill_receipts(events: list[dict[str, Any]], skill: str) -> list[str]:
    receipts = []
    local_path = f".agents/skills/{skill}/SKILL.md"
    name = re.compile(rf"^name:\s*['\"]?{re.escape(skill)}['\"]?\s*$", re.M)
    for event in events:
        item = event.get("item", {})
        if event.get("type") != "item.completed" or item.get("type") != "command_execution":
            continue
        if item.get("exit_code") != 0 or local_path not in item.get("command", ""):
            continue
        reads = [argv for reader in ("cat", "sed", "head", "tail") for argv in trusted_argvs(item.get("command", ""), reader, Path(shutil.which(reader)) if shutil.which(reader) else None) if any(value.endswith(local_path) for value in argv[1:])]
        if reads and name.search(item.get("aggregated_output", "")):
            receipts.append(str(item.get("id", "unknown")))
    return receipts


def usage_metrics(events: list[dict[str, Any]]) -> dict[str, int | None]:
    usage = next((event.get("usage", {}) for event in reversed(events) if event.get("type") == "turn.completed"), {})
    return {key: usage.get(key) if isinstance(usage.get(key), int) else None for key in ("input_tokens", "cached_input_tokens", "output_tokens")}


def permission_config(case: dict[str, Any], workspace: Path | None = None) -> str:
    rules = {".": "read" if case.get("readonly") or case["fixture"] == "review" else "write", ".agents": "read", ".git": "write" if case["fixture"] in {"commit", "push", "pr", "gitflow", "resolve"} and not case.get("readonly") else "read", ".fixture": "read"}
    for path in ("scratch", "service_calls.jsonl", "browser_calls.jsonl", "origin.git", "clang-cache", "swift-cache", "missav-home"):
        rules[f".fixture/{path}"] = "write"
    if case["fixture"] == "creator":
        rules[".agents/skills/csv-cleaner"] = "write"
        rules[".agents/skills/csv-cleaner/agents"] = "read"
        rules[".agents/skills/csv-cleaner/references"] = "read"
    if case["fixture"] == "resolve":
        rules[".agents/worktrees"] = "write"
    entries = ",".join(f"{json.dumps(path)}={json.dumps(access)}" for path, access in rules.items())
    reads = {":root": "deny", ":minimal": "read", ":tmpdir": "write", ":slash_tmp": "write", str(Path.home() / ".local/bin"): "read", str(Path.home() / ".local/share/uv"): "read", str(Path.home() / ".cache/uv"): "read", "/opt/homebrew": "read", "/usr/local": "read", "/Library/Developer": "read", "/Applications/Xcode.app": "read", "/System/Library/OpenSSL": "read"}
    node = shutil.which("node")
    if node:
        reads[str(Path(node).resolve().parent.parent)] = "read"
    codex = shutil.which("codex")
    if codex:
        reads[str(Path(codex).resolve().parent.parent)] = "read"
    if case["fixture"] == "gitflow" and workspace is not None:
        reads[str(workspace.resolve() / ".git/worktrees/topic")] = "write"
    outside = ",".join(f"{json.dumps(path)}={json.dumps(access)}" for path, access in reads.items())
    parent = ":read-only" if case.get("readonly") else ":workspace"
    return 'permissions.skill-eval={extends=' + json.dumps(parent) + ',filesystem={' + outside + ',":workspace_roots"={' + entries + '}},network={enabled=false}}'


def child_environment(host: dict[str, str], overrides: dict[str, str]) -> dict[str, str]:
    allowed = {"HOME", "CODEX_HOME", "PATH", "USER", "LOGNAME", "SHELL", "LANG", "LC_ALL", "LC_CTYPE", "TERM", "TZ", "TMPDIR", "TMP", "TEMP"}
    return {**{key: value for key, value in host.items() if key in allowed}, **overrides}


def environment_blockers(events: list[dict[str, Any]], case: dict[str, Any] | None = None) -> list[dict[str, str]]:
    blockers = []
    patterns = [r"\.git/"] if case is None or (case["fixture"] in {"commit", "push", "pr", "gitflow", "resolve"} and not case.get("readonly")) else []
    if case is None:
        patterns.append(r"\.agents/")
    elif case["fixture"] == "creator":
        patterns.append(r"\.agents/skills/csv-cleaner/SKILL\.md")
    elif case["fixture"] == "resolve":
        patterns.append(r"\.agents/worktrees/")
    for event in events:
        item = event.get("item", {})
        output = item.get("aggregated_output", "")
        if event.get("type") != "item.completed" or item.get("type") != "command_execution" or item.get("exit_code") in (0, None):
            continue
        if any(re.search(path + r"[^\n]*?(?:Operation not permitted|Permission denied|Read-only file system)", output, re.I) for path in patterns):
            blockers.append({"item_id": str(item.get("id", "unknown")), "evidence": output[:1000]})
    return blockers


def source_hashes(directory: Path) -> dict[str, str]:
    return {
        str(path.relative_to(directory)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(directory.rglob("*"))
        if path.is_file() and not any(part in {"__pycache__", ".git", ".DS_Store"} for part in path.parts)
    }


def load_events(path: Path) -> list[dict[str, Any]]:
    events = []
    for number, line in enumerate(path.read_text().splitlines(), 1):
        if line.strip():
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"event line {number} must be an object")
            events.append(value)
    return events


def run_case(case: dict[str, Any], snapshot: Path, output: Path, timeout: int) -> dict[str, Any]:
    from tools.skill_eval.fixtures import grade_task, prepare_fixture

    run = output / case["id"]
    run.mkdir()
    workspace = run / "workspace"
    workspace.mkdir()
    skill = case["skill"]
    source = snapshot / (".agents/skills" if skill == "skill-creator" else "skills") / skill
    installed = workspace / ".agents/skills" / skill
    shutil.copytree(source, installed, ignore=shutil.ignore_patterns("__pycache__", ".DS_Store"))
    hashes = source_hashes(installed)
    context = prepare_fixture(case, workspace)
    (run / "fixture-context.json").write_text(json.dumps(context, ensure_ascii=False, indent=2))
    cwd = Path(context.get("cwd", workspace))
    prompt = f"Use ${skill}. Read the project-local .agents/skills/{skill}/SKILL.md and follow it.\n\n{case['prompt']}"
    (run / "prompt.txt").write_text(prompt)
    (run / "case.json").write_text(json.dumps(case, ensure_ascii=False, indent=2))
    (run / "source-hashes.json").write_text(json.dumps(hashes, indent=2))
    environment = {
        "PATH": str(workspace / ".fixture/bin") + os.pathsep + os.environ["PATH"],
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_OPTIONAL_LOCKS": "0",
        "GH_HOST": "github.fixture.invalid",
        "UV_OFFLINE": "true",
        "MISSAV_HOME": str(workspace / ".fixture/missav-home"),
        "OFFICE_GLOBAL_LOCAL": "",
        "OFFICE_GLOBAL_SHARED": "",
        "OFFICE_PROJECT_LOCAL": "",
        "OFFICE_PROJECT_SHARED": str(workspace / ".agents/office.json"),
        "CLANG_MODULE_CACHE_PATH": str(workspace / ".fixture/clang-cache"),
        "SWIFTPM_MODULECACHE_OVERRIDE": str(workspace / ".fixture/swift-cache"),
        "ZDOTDIR": str(workspace / ".fixture/zsh"),
    }
    if case["fixture"] in {"gitflow", "missav-challenge"}:
        environment["CDPATH"] = str(workspace)
    env_config = "shell_environment_policy.set={" + ",".join(f"{key}={json.dumps(value)}" for key, value in environment.items()) + "}"
    command = [
        str(Path(shutil.which("codex") or "codex").resolve()), "--no-daemon", "-a", "never", "exec", "--ignore-user-config", "--ignore-rules",
        "--ephemeral", "--skip-git-repo-check", "--json",
        "--disable", "plugins", "--disable", "apps", "--disable", "hooks", "--disable", "chronicle",
        "-c", 'web_search="disabled"', "-c", 'default_permissions="skill-eval"', "-c", permission_config(case, workspace), "-c", env_config,
        "-C", str(cwd), "--add-dir", str(workspace), "-o", str(run / "final.txt"), "-",
    ]
    (run / "command.json").write_text(json.dumps(command, indent=2))
    started = time.monotonic()
    print(json.dumps({"case": case["id"], "event": "started"}), flush=True)
    status = "runtime_error"
    returncode = -1
    try:
        with (run / "events.jsonl").open("w") as stdout, (run / "stderr.log").open("w") as stderr:
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=stdout, stderr=stderr, text=True, env=child_environment(dict(os.environ), environment), start_new_session=True)
            try:
                process.communicate(prompt, timeout=timeout)
                returncode = process.returncode
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.communicate(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.communicate()
                status = "timeout"
        final = (run / "final.txt").read_text() if (run / "final.txt").exists() else ""
        try:
            events = load_events(run / "events.jsonl")
        except (ValueError, json.JSONDecodeError) as error:
            events = []
            (run / "event-error.txt").write_text(str(error))
        if status != "timeout":
            status = execution_status(returncode, events, final)
        receipts = read_skill_receipts(events, skill)
        blockers = environment_blockers(events, case)
        expectations = []
        if status == "completed":
            try:
                expectations = grade_task(case, workspace, context, events, final)
            except (OSError, ValueError, ImportError, subprocess.SubprocessError) as error:
                expectations = [{"text": "Complete grading without an evaluator error", "passed": False, "evidence": str(error)}]
                status = "grader_error"
            expectations.insert(0, {"text": "Read the selected project-local skill", "passed": bool(receipts), "evidence": receipts})
            expectations.append({"text": "Preserve the installed skill snapshot", "passed": source_hashes(installed) == hashes, "evidence": "source-hashes.json"})
        passed = bool(expectations) and all(item["passed"] for item in expectations)
        if status == "completed" and not passed and blockers:
            status = "environment_blocked"
        result = {
            "id": case["id"], "skill": skill, "expected_outcome": case.get("expected_outcome", "completed_task"),
            "status": status, "passed": passed, "returncode": returncode,
            "duration_seconds": round(time.monotonic() - started, 3),
            "thread_id": next((event.get("thread_id") for event in events if event.get("type") == "thread.started"), None),
            "skill_read_receipts": receipts, "usage": usage_metrics(events),
            "environment_blockers": blockers,
            "expectations": expectations, "artifact_directory": str(run),
        }
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        result = {"id": case["id"], "skill": skill, "status": "runner_error", "passed": False, "error": str(error), "artifact_directory": str(run)}
    (run / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(json.dumps({"case": case["id"], "event": "finished", "status": result["status"], "passed": result["passed"]}), flush=True)
    return result


def snapshot_skills(output: Path) -> Path:
    snapshot = output / "skill-snapshot"
    for base in ("skills", ".agents/skills"):
        for entry in sorted((ROOT / base).glob("*/SKILL.md")):
            shutil.copytree(entry.parent, snapshot / base / entry.parent.name, ignore=shutil.ignore_patterns("__pycache__", ".DS_Store"))
    return snapshot


def write_report(output: Path, results: list[dict[str, Any]], version: str) -> None:
    summary = {
        "runtime": version, "configuration": "CLI default model; user config ignored; no parent history; scoped permission profile with fixture Git writes and command network disabled; plugins/apps/hooks disabled",
        "results": results,
        "completed": sum(result["status"] == "completed" for result in results),
        "passed": sum(result["passed"] for result in results), "total": len(results),
    }
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    lines = ["# Independent Codex skill task runs", "", f"Runtime: {version}", "", "Each case uses a fresh Codex process, explicit skill invocation, a source snapshot, and an isolated local repository. External services are fixtures; Git remotes are local bare repositories. This measures selected task contracts, not live account integration, implicit triggering, or population-wide quality gains.", "", "| Case | Skill | Runtime outcome | Contract | Seconds |", "|---|---|---|---|---|"]
    for result in results:
        lines.append(f"| [{result['id']}]({result['id']}/result.json) | {result['skill']} | {result['status']} | {'pass' if result['passed'] else 'fail'} | {result.get('duration_seconds', 'unavailable')} |")
    for result in results:
        failed = [item for item in result.get("expectations", []) if not item["passed"]]
        if failed:
            lines.extend(["", f"## {result['id']}", ""] + [f"- {item['text']}: {item['evidence']}" for item in failed])
    (output / "report.md").write_text("\n".join(lines) + "\n")


def main() -> int:
    from tools.skill_eval.fixtures import CASES

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", action="append", default=[])
    parser.add_argument("--skill", action="append", default=[])
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()
    if args.workers < 1 or args.workers > 3 or args.timeout < 1:
        parser.error("workers must be 1..3 and timeout must be positive")
    selected = [case for case in CASES if (not args.case or case["id"] in args.case) and (not args.skill or case["skill"] in args.skill)]
    if not selected or set(args.case) - {case["id"] for case in CASES} or set(args.skill) - {case["skill"] for case in CASES}:
        parser.error("select existing cases or skills")
    if args.list:
        print(json.dumps(selected, ensure_ascii=False, indent=2))
        return 0
    version = subprocess.run(["codex", "--version"], check=True, capture_output=True, text=True).stdout.strip()
    output = (args.output_dir or ROOT / ".skill-evals" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")).resolve()
    output.mkdir(parents=True, exist_ok=False)
    snapshot = snapshot_skills(output)
    (output / "manifest.json").write_text(json.dumps({"runtime": version, "cases": selected, "harness_hashes": source_hashes(ROOT / "tools/skill_eval"), "created_at": datetime.now(timezone.utc).isoformat()}, ensure_ascii=False, indent=2))
    print(json.dumps({"output_directory": str(output), "cases": len(selected), "workers": args.workers}), flush=True)
    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        tasks = {pool.submit(run_case, case, snapshot, output, args.timeout): case for case in selected}
        for task in as_completed(tasks):
            case = tasks[task]
            try:
                result = task.result()
            except Exception as error:
                result = {"id": case["id"], "skill": case["skill"], "status": "runner_error", "passed": False, "error": str(error)}
            results.append(result)
            write_report(output, sorted(results, key=lambda item: item["id"]), version)
    return 0 if all(result["passed"] for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
