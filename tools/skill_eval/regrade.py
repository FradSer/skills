"""Reassess saved Codex task evidence without replacing original run results."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
from typing import Any

from tools.skill_eval.codex_eval import (
    ROOT,
    environment_blockers,
    execution_status,
    load_events,
    read_skill_receipts,
    source_hashes,
)
from tools.skill_eval.fixtures import grade_task


def regrade_case(run: Path) -> dict[str, Any]:
    original = json.loads((run / "result.json").read_text())
    case = json.loads((run / "case.json").read_text())
    context = json.loads((run / "fixture-context.json").read_text())
    events = load_events(run / "events.jsonl")
    final = (run / "final.txt").read_text() if (run / "final.txt").is_file() else ""
    status = "timeout" if original["status"] == "timeout" else execution_status(original.get("returncode", -1), events, final)
    expectations = []
    receipts = read_skill_receipts(events, case["skill"])
    if status == "completed":
        try:
            expectations = grade_task(case, run / "workspace", context, events, final)
        except (OSError, ValueError, ImportError, subprocess.SubprocessError) as error:
            status = "grader_error"
            expectations = [{"text": "Complete grading without an evaluator error", "passed": False, "evidence": str(error)}]
        expectations.insert(0, {"text": "Read the selected project-local skill", "passed": bool(receipts), "evidence": receipts})
        installed = run / "workspace/.agents/skills" / case["skill"]
        expected_hashes = json.loads((run / "source-hashes.json").read_text())
        expectations.append({"text": "Preserve the installed skill snapshot", "passed": source_hashes(installed) == expected_hashes, "evidence": "source-hashes.json"})
    passed = bool(expectations) and all(item["passed"] for item in expectations)
    blockers = environment_blockers(events, case)
    if status == "completed" and not passed and blockers:
        status = "environment_blocked"
    return {
        **original,
        "status": status,
        "passed": passed,
        "skill_read_receipts": receipts,
        "expectations": expectations,
        "environment_blockers": blockers,
        "original_status": original["status"],
        "original_passed": original["passed"],
        "original_result": str(run / "result.json"),
        "assessed_at": datetime.now(timezone.utc).isoformat(),
        "grader_hashes": {name: digest for name, digest in source_hashes(ROOT / "tools/skill_eval").items() if name.endswith(".py")},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--case", action="append", default=[])
    args = parser.parse_args()
    output = args.output_dir.resolve()
    runs = sorted(path.parent for path in output.glob("*/result.json") if not args.case or path.parent.name in args.case)
    if not runs:
        parser.error("no saved run results match the selection")
    results = []
    for run in runs:
        assessment = regrade_case(run)
        (run / "assessment.json").write_text(json.dumps(assessment, ensure_ascii=False, indent=2))
        results.append(assessment)
        print(json.dumps({"case": assessment["id"], "status": assessment["status"], "passed": assessment["passed"]}), flush=True)
    summary = {"results": results, "passed": sum(result["passed"] for result in results), "total": len(results)}
    (output / "assessment-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if all(result["passed"] for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
