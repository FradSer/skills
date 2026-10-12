#!/usr/bin/env python3
"""Run trigger evaluation for a skill description.

Tests whether a skill's description causes Claude to trigger (read the skill)
for a set of queries. Outputs results as JSON.
"""

import argparse
import json
import math
import os
import select
import subprocess
import sys
import time
import uuid
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from scripts.utils import parse_skill_md


def validate_eval_set(eval_set: list[dict]) -> None:
    """Reject inputs that cannot produce an unambiguous measured score."""
    if not isinstance(eval_set, list) or not eval_set:
        raise ValueError("eval_set must be a nonempty list")
    queries: set[str] = set()
    for item in eval_set:
        if not isinstance(item, dict) or not isinstance(item.get("query"), str) or not item["query"].strip():
            raise ValueError("each evaluation needs a nonempty query string")
        if type(item.get("should_trigger")) is not bool:
            raise ValueError("should_trigger must be a boolean")
        query = item["query"].strip()
        if query in queries:
            raise ValueError(f"duplicate evaluation query: {query}")
        queries.add(query)


def validate_execution_settings(num_workers: int, timeout: int, runs_per_query: int, trigger_threshold: float) -> None:
    """Validate controls before starting subprocesses or model requests."""
    for name, value in (("num_workers", num_workers), ("timeout", timeout), ("runs_per_query", runs_per_query)):
        if type(value) is not int or value < 1:
            raise ValueError(f"{name} must be a positive integer")
    if not isinstance(trigger_threshold, (int, float)) or not math.isfinite(trigger_threshold) or not 0 < trigger_threshold <= 1:
        raise ValueError("trigger_threshold must be finite, greater than 0, and at most 1")


def find_project_root() -> Path:
    """Find the project root by walking up from cwd looking for .claude/.

    Mimics how Claude Code discovers its project root, so the command file
    we create ends up where claude -p will look for it.
    """
    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / ".claude").is_dir():
            return parent
    return current


def run_single_query(
    query: str,
    skill_name: str,
    skill_description: str,
    timeout: int,
    project_root: str,
    model: str | None = None,
) -> bool:
    """Run a single query and return whether the skill was triggered.

    Creates a command file in .claude/commands/ so it appears in Claude's
    available_skills list, then runs `claude -p` with the raw query.
    Uses --include-partial-messages to detect triggering early from
    stream events (content_block_start) rather than waiting for the
    full assistant message, which only arrives after tool execution.
    """
    unique_id = uuid.uuid4().hex[:8]
    clean_name = f"{skill_name}-skill-{unique_id}"
    project_commands_dir = Path(project_root) / ".claude" / "commands"
    command_file = project_commands_dir / f"{clean_name}.md"

    try:
        project_commands_dir.mkdir(parents=True, exist_ok=True)
        # Use YAML block scalar to avoid breaking on quotes in description
        indented_desc = "\n  ".join(skill_description.split("\n"))
        command_content = (
            f"---\n"
            f"description: |\n"
            f"  {indented_desc}\n"
            f"---\n\n"
            f"# {skill_name}\n\n"
            f"This skill handles: {skill_description}\n"
        )
        command_file.write_text(command_content)

        cmd = [
            "claude",
            "-p", query,
            "--output-format", "stream-json",
            "--verbose",
            "--include-partial-messages",
        ]
        if model:
            cmd.extend(["--model", model])

        # Remove CLAUDECODE env var to allow nesting claude -p inside a
        # Claude Code session. The guard is for interactive terminal conflicts;
        # programmatic subprocess usage is safe.
        env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            cwd=project_root,
            env=env,
        )

        pending_tool_name = None
        accumulated_json = ""
        result_seen = False

        def consume(line: str) -> bool:
            nonlocal pending_tool_name, accumulated_json, result_seen
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                return False
            if event.get("type") == "stream_event":
                stream_event = event.get("event", {})
                kind = stream_event.get("type")
                if kind == "content_block_start":
                    block = stream_event.get("content_block", {})
                    pending_tool_name = block.get("name") if block.get("type") == "tool_use" else None
                    accumulated_json = ""
                elif kind == "content_block_delta" and pending_tool_name in ("Skill", "Read"):
                    delta = stream_event.get("delta", {})
                    if delta.get("type") == "input_json_delta":
                        accumulated_json += delta.get("partial_json", "")
                        if clean_name in accumulated_json:
                            return True
                elif kind == "content_block_stop":
                    pending_tool_name = None
            elif event.get("type") == "assistant":
                for item in event.get("message", {}).get("content", []):
                    if item.get("type") != "tool_use":
                        continue
                    arguments = item.get("input", {})
                    if item.get("name") == "Skill" and clean_name in arguments.get("skill", ""):
                        return True
                    if item.get("name") == "Read" and clean_name in arguments.get("file_path", ""):
                        return True
            elif event.get("type") == "result":
                if event.get("is_error") or str(event.get("subtype", "")).startswith("error"):
                    raise RuntimeError("Claude returned an evaluation error")
                result_seen = True
            return False

        deadline = time.monotonic() + timeout
        buffer = ""
        try:
            while time.monotonic() < deadline:
                completed = process.poll() is not None
                if completed:
                    # A fast CLI may exit before the first poll. Its queued
                    # events still contain the measurement and must be parsed.
                    chunk = process.stdout.read()
                else:
                    ready, _, _ = select.select([process.stdout], [], [], min(1.0, max(0.0, deadline - time.monotonic())))
                    if not ready:
                        continue
                    chunk = os.read(process.stdout.fileno(), 8192)
                    if not chunk:
                        process.wait(timeout=max(0.01, deadline - time.monotonic()))
                        completed = True
                buffer += chunk.decode("utf-8", errors="replace")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if line.strip() and consume(line):
                        return True
                if completed:
                    if buffer.strip() and consume(buffer):
                        return True
                    if process.returncode:
                        raise RuntimeError(f"Claude exited {process.returncode} before completing the measurement")
                    if not result_seen:
                        raise RuntimeError("Claude exited without a terminal evaluation result")
                    return False
            raise TimeoutError(f"Trigger evaluation exceeded {timeout} seconds")
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
            process.stdout.close()

    finally:
        if command_file.exists():
            command_file.unlink()


def run_eval(
    eval_set: list[dict],
    skill_name: str,
    description: str,
    num_workers: int,
    timeout: int,
    project_root: Path,
    runs_per_query: int = 1,
    trigger_threshold: float = 0.5,
    model: str | None = None,
) -> dict:
    """Run the full eval set and return results."""
    validate_eval_set(eval_set)
    validate_execution_settings(num_workers, timeout, runs_per_query, trigger_threshold)
    results = []

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        future_to_info = {}
        for item in eval_set:
            for run_idx in range(runs_per_query):
                future = executor.submit(
                    run_single_query,
                    item["query"],
                    skill_name,
                    description,
                    timeout,
                    str(project_root),
                    model,
                )
                future_to_info[future] = (item, run_idx)

        query_triggers: dict[str, list[bool]] = {}
        query_items: dict[str, dict] = {}
        query_errors: dict[str, list[str]] = {}
        for future in as_completed(future_to_info):
            item, _ = future_to_info[future]
            query = item["query"]
            query_items[query] = item
            if query not in query_triggers:
                query_triggers[query] = []
            try:
                query_triggers[query].append(future.result())
            except Exception as e:
                print(f"Warning: query failed: {e}", file=sys.stderr)
                query_errors.setdefault(query, []).append(str(e))
                query_triggers[query].append(False)

    for query, triggers in query_triggers.items():
        item = query_items[query]
        trigger_rate = sum(triggers) / len(triggers)
        should_trigger = item["should_trigger"]
        if should_trigger:
            did_pass = trigger_rate >= trigger_threshold
        else:
            did_pass = trigger_rate < trigger_threshold
        errors = query_errors.get(query, [])
        results.append({
            "query": query,
            "should_trigger": should_trigger,
            "trigger_rate": trigger_rate,
            "triggers": sum(triggers),
            "runs": len(triggers),
            "pass": did_pass and not errors,
            "errors": errors,
        })

    passed = sum(1 for r in results if r["pass"])
    total = len(results)

    return {
        "skill_name": skill_name,
        "description": description,
        "results": results,
        "summary": {
            "total": total,
            "passed": passed,
            "failed": total - passed,
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Run trigger evaluation for a skill description")
    parser.add_argument("--eval-set", required=True, help="Path to eval set JSON file")
    parser.add_argument("--skill-path", required=True, help="Path to skill directory")
    parser.add_argument("--description", default=None, help="Override description to test")
    parser.add_argument("--num-workers", type=int, default=10, help="Number of parallel workers")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout per query in seconds")
    parser.add_argument("--runs-per-query", type=int, default=3, help="Number of runs per query")
    parser.add_argument("--trigger-threshold", type=float, default=0.5, help="Trigger rate threshold")
    parser.add_argument("--model", default=None, help="Model to use for claude -p (default: user's configured model)")
    parser.add_argument("--verbose", action="store_true", help="Print progress to stderr")
    args = parser.parse_args()

    eval_set = json.loads(Path(args.eval_set).read_text())
    skill_path = Path(args.skill_path)

    if not (skill_path / "SKILL.md").exists():
        print(f"Error: No SKILL.md found at {skill_path}", file=sys.stderr)
        sys.exit(1)

    name, original_description, content = parse_skill_md(skill_path)
    description = args.description or original_description
    project_root = find_project_root()

    if args.verbose:
        print(f"Evaluating: {description}", file=sys.stderr)

    output = run_eval(
        eval_set=eval_set,
        skill_name=name,
        description=description,
        num_workers=args.num_workers,
        timeout=args.timeout,
        project_root=project_root,
        runs_per_query=args.runs_per_query,
        trigger_threshold=args.trigger_threshold,
        model=args.model,
    )

    if args.verbose:
        summary = output["summary"]
        print(f"Results: {summary['passed']}/{summary['total']} passed", file=sys.stderr)
        for r in output["results"]:
            status = "PASS" if r["pass"] else "FAIL"
            rate_str = f"{r['triggers']}/{r['runs']}"
            print(f"  [{status}] rate={rate_str} expected={r['should_trigger']}: {r['query'][:70]}", file=sys.stderr)

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
