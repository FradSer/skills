#!/usr/bin/env python3
"""
Aggregate individual run results into benchmark summary statistics.

Reads grading.json files from run directories and produces:
- run_summary with mean, stddev, min, max for each metric
- delta between with_skill and without_skill configurations

Usage:
    python aggregate_benchmark.py <benchmark_dir>

Example:
    python aggregate_benchmark.py benchmarks/2026-01-15T10-30-00/

The script supports two directory layouts:

    Workspace layout (from skill-creator iterations):
    <benchmark_dir>/
    └── eval-N/
        ├── with_skill/
        │   ├── run-1/grading.json
        │   └── run-2/grading.json
        └── without_skill/
            ├── run-1/grading.json
            └── run-2/grading.json

    Legacy layout (with runs/ subdirectory):
    <benchmark_dir>/
    └── runs/
        └── eval-N/
            ├── with_skill/
            │   └── run-1/grading.json
            └── without_skill/
                └── run-1/grading.json
"""

import argparse
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


def calculate_stats(values: list[float]) -> dict:
    """Calculate mean, stddev, min, max for a list of values."""
    if not values:
        return {"mean": None, "stddev": None, "min": None, "max": None}

    n = len(values)
    mean = sum(values) / n

    if n > 1:
        variance = sum((x - mean) ** 2 for x in values) / (n - 1)
        stddev = math.sqrt(variance)
    else:
        stddev = 0.0

    return {
        "mean": round(mean, 4),
        "stddev": round(stddev, 4),
        "min": round(min(values), 4),
        "max": round(max(values), 4)
    }


def load_run_results(benchmark_dir: Path) -> dict:
    """
    Load all run results from a benchmark directory.

    Returns dict keyed by config name (e.g. "with_skill"/"without_skill",
    or "new_skill"/"old_skill"), each containing a list of run results.
    """
    # Support both layouts: eval dirs directly under benchmark_dir, or under runs/
    runs_dir = benchmark_dir / "runs"
    if runs_dir.exists():
        search_dir = runs_dir
    elif list(benchmark_dir.glob("eval-*")):
        search_dir = benchmark_dir
    else:
        print(f"No eval directories found in {benchmark_dir} or {benchmark_dir / 'runs'}")
        return {}

    results: dict[str, list] = {}

    for eval_idx, eval_dir in enumerate(sorted(search_dir.glob("eval-*"))):
        if eval_dir.is_symlink() or not eval_dir.is_dir():
            continue
        metadata_path = eval_dir / "eval_metadata.json"
        if not metadata_path.is_symlink() and metadata_path.is_file():
            try:
                with open(metadata_path) as mf:
                    metadata = json.load(mf)
                    identifier = metadata.get("eval_id") if isinstance(metadata, dict) else None
                    eval_id = identifier if type(identifier) is int else eval_idx
            except (json.JSONDecodeError, OSError):
                eval_id = eval_idx
        else:
            try:
                eval_id = int(eval_dir.name.split("-")[1])
            except ValueError:
                eval_id = eval_idx

        # Discover config directories dynamically rather than hardcoding names
        for config_dir in sorted(eval_dir.iterdir()):
            if config_dir.is_symlink() or not config_dir.is_dir():
                continue
            # Skip non-config directories (inputs, outputs, etc.)
            if not list(config_dir.glob("run-*")):
                continue
            config = config_dir.name
            if config not in results:
                results[config] = []

            for run_dir in sorted(config_dir.glob("run-*")):
                match = re.fullmatch(r"run-([0-9]+)", run_dir.name)
                if not match or run_dir.is_symlink() or not run_dir.is_dir():
                    print(f"Warning: skipping malformed or linked run directory {run_dir}")
                    continue
                run_number = int(match.group(1))
                grading_file = run_dir / "grading.json"

                if grading_file.is_symlink() or not grading_file.is_file():
                    print(f"Warning: grading.json not found in {run_dir}")
                    continue

                try:
                    with open(grading_file) as f:
                        grading = json.load(f)
                except (json.JSONDecodeError, OSError) as e:
                    print(f"Warning: Invalid JSON in {grading_file}: {e}")
                    continue

                if not isinstance(grading, dict) or not isinstance(grading.get("summary"), dict):
                    print(f"Warning: missing grading summary in {grading_file}")
                    continue
                summary = grading["summary"]
                rate = summary.get("pass_rate")
                if not isinstance(rate, (int, float)) or not math.isfinite(rate) or not 0 <= rate <= 1 or not isinstance(summary.get("total"), int) or summary["total"] < 1:
                    print(f"Warning: no valid measured pass rate in {grading_file}")
                    continue
                # Extract only measured metrics; missing values are not zero.
                result = {
                    "eval_id": eval_id,
                    "run_number": run_number,
                    "pass_rate": rate,
                    "passed": grading.get("summary", {}).get("passed", 0),
                    "failed": grading.get("summary", {}).get("failed", 0),
                    "total": grading.get("summary", {}).get("total", 0),
                }

                # Extract timing — check grading.json first, then sibling timing.json
                timing = grading.get("timing", {})
                result["time_seconds"] = timing.get("total_duration_seconds")
                result["tokens"] = timing.get("total_tokens")
                timing_file = run_dir / "timing.json"
                if not timing_file.is_symlink() and timing_file.is_file():
                    try:
                        with open(timing_file) as tf:
                            timing_data = json.load(tf)
                        if result["time_seconds"] is None:
                            result["time_seconds"] = timing_data.get("total_duration_seconds")
                        if result["tokens"] is None:
                            result["tokens"] = timing_data.get("total_tokens")
                    except (json.JSONDecodeError, OSError):
                        pass

                # Extract metrics if available
                metrics = grading.get("execution_metrics", {})
                result["tool_calls"] = metrics.get("total_tool_calls", 0)
                if result["tokens"] is None:
                    result["tokens"] = metrics.get("total_tokens")
                for metric in ("time_seconds", "tokens"):
                    value = result[metric]
                    if not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                        result[metric] = None
                result["errors"] = metrics.get("errors_encountered", 0)

                # Extract expectations — viewer requires fields: text, passed, evidence
                raw_expectations = grading.get("expectations", [])
                for exp in raw_expectations:
                    if "text" not in exp or "passed" not in exp:
                        print(f"Warning: expectation in {grading_file} missing required fields (text, passed, evidence): {exp}")
                result["expectations"] = raw_expectations

                # Extract notes from user_notes_summary
                notes_summary = grading.get("user_notes_summary", {})
                notes = []
                notes.extend(notes_summary.get("uncertainties", []))
                notes.extend(notes_summary.get("needs_review", []))
                notes.extend(notes_summary.get("workarounds", []))
                result["notes"] = notes

                results[config].append(result)

    return results


def aggregate_results(results: dict, primary_config: str | None = None, baseline_config: str | None = None) -> dict:
    """
    Aggregate run results into summary statistics.

    Returns run_summary with stats for each configuration and delta.
    """
    run_summary = {}
    configs = list(results.keys())

    for config in configs:
        runs = results.get(config, [])

        if not runs:
            continue

        pass_rates = [r["pass_rate"] for r in runs]
        times = [r["time_seconds"] for r in runs if r["time_seconds"] is not None]
        tokens = [r["tokens"] for r in runs if r.get("tokens") is not None]

        run_summary[config] = {
            "pass_rate": calculate_stats(pass_rates),
            "time_seconds": calculate_stats(times),
            "tokens": calculate_stats(tokens)
        }

    # Compare only measured configurations, in an explicit primary/baseline order.
    if (primary_config is None) != (baseline_config is None):
        raise ValueError("primary_config and baseline_config must be supplied together")
    comparison = None
    if primary_config is not None:
        if primary_config == baseline_config or not all(config in run_summary for config in (primary_config, baseline_config)):
            raise ValueError("comparison needs two distinct measured configurations")
        comparison = (primary_config, baseline_config)
    else:
        for pair in (("with_skill", "without_skill"), ("new_skill", "old_skill")):
            if all(config in run_summary for config in pair):
                comparison = pair
                break
    if comparison is not None:
        configs = list(comparison)
        primary, baseline = (run_summary[config] for config in configs)
        delta = {}
        for metric, precision in (("pass_rate", 2), ("time_seconds", 1), ("tokens", 0)):
            a, b = primary[metric]["mean"], baseline[metric]["mean"]
            if a is not None and b is not None:
                delta[metric] = f"{a - b:+.{precision}f}"
        run_summary = {config: run_summary[config] for config in [*configs, *[name for name in run_summary if name not in configs]]}
        run_summary["delta"] = delta

    return run_summary


def generate_benchmark(benchmark_dir: Path, skill_name: str = "", skill_path: str = "", primary_config: str | None = None, baseline_config: str | None = None) -> dict:
    """
    Generate complete benchmark.json from run results.
    """
    results = {config: runs for config, runs in load_run_results(benchmark_dir).items() if runs}
    run_summary = aggregate_results(results, primary_config, baseline_config)

    # Build runs array for benchmark.json
    runs = []
    for config in results:
        for result in results[config]:
            runs.append({
                "eval_id": result["eval_id"],
                "configuration": config,
                "run_number": result["run_number"],
                "result": {
                    "pass_rate": result["pass_rate"],
                    "passed": result["passed"],
                    "failed": result["failed"],
                    "total": result["total"],
                    "time_seconds": result["time_seconds"],
                    "tokens": result.get("tokens", 0),
                    "tool_calls": result.get("tool_calls", 0),
                    "errors": result.get("errors", 0)
                },
                "expectations": result["expectations"],
                "notes": result["notes"]
            })

    # Determine eval IDs from results
    eval_ids = sorted(set(
        r["eval_id"]
        for config in results.values()
        for r in config
    ))
    counts = {config: {str(eval_id): sum(run["eval_id"] == eval_id for run in runs) for eval_id in eval_ids} for config, runs in results.items()}
    observed_counts = {count for groups in counts.values() for count in groups.values()}

    benchmark = {
        "metadata": {
            "skill_name": skill_name or "<skill-name>",
            "skill_path": skill_path or "<path/to/skill>",
            "executor_model": "<model-name>",
            "analyzer_model": "<model-name>",
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "evals_run": eval_ids,
            "runs_per_configuration": next(iter(observed_counts)) if len(observed_counts) == 1 else None,
            "run_counts_by_eval": counts
        },
        "runs": runs,
        "run_summary": run_summary,
        "notes": []  # To be filled by analyzer
    }

    return benchmark


def generate_markdown(benchmark: dict) -> str:
    """Generate human-readable benchmark.md from benchmark data."""
    metadata = benchmark["metadata"]
    run_summary = benchmark["run_summary"]

    # Determine config names (excluding "delta")
    configs = [k for k in run_summary if k != "delta"]
    labels = [config.replace("_", " ").title() for config in configs]
    count = metadata["runs_per_configuration"]
    repetitions = f"{count} runs each per configuration" if count is not None else "uneven or unmeasured runs; see run_counts_by_eval"
    delta = run_summary.get("delta")

    lines = [
        f"# Skill Benchmark: {metadata['skill_name']}",
        "",
        f"**Model**: {metadata['executor_model']}",
        f"**Date**: {metadata['timestamp']}",
        f"**Evals**: {', '.join(map(str, metadata['evals_run']))} ({repetitions})",
        "",
        "## Summary",
        "",
        "| Metric | " + " | ".join(labels + (["Delta"] if delta is not None else [])) + " |",
        "|--------|" + "------------|" * (len(labels) + (delta is not None)),
    ]

    for metric, label, factor, precision, suffix in (("pass_rate", "Pass Rate", 100, 0, "%"), ("time_seconds", "Time", 1, 1, "s"), ("tokens", "Tokens", 1, 0, "")):
        cells = []
        for config in configs:
            stats = run_summary[config][metric]
            if stats["mean"] is None:
                cells.append("—")
            else:
                cells.append(f"{stats['mean'] * factor:.{precision}f}{suffix} ± {stats['stddev'] * factor:.{precision}f}{suffix}")
        if delta is not None:
            cells.append(delta.get(metric, "—"))
        lines.append(f"| {label} | " + " | ".join(cells) + " |")

    # Notes section
    if benchmark.get("notes"):
        lines.extend([
            "",
            "## Notes",
            ""
        ])
        for note in benchmark["notes"]:
            lines.append(f"- {note}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Aggregate benchmark run results into summary statistics"
    )
    parser.add_argument(
        "benchmark_dir",
        type=Path,
        help="Path to the benchmark directory"
    )
    parser.add_argument(
        "--skill-name",
        default="",
        help="Name of the skill being benchmarked"
    )
    parser.add_argument(
        "--skill-path",
        default="",
        help="Path to the skill being benchmarked"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        help="Output path for benchmark.json (default: <benchmark_dir>/benchmark.json)"
    )
    parser.add_argument("--primary-config", help="Primary configuration for a custom comparison")
    parser.add_argument("--baseline-config", help="Measured baseline configuration for a custom comparison")

    args = parser.parse_args()

    if not args.benchmark_dir.exists():
        print(f"Directory not found: {args.benchmark_dir}")
        sys.exit(1)

    # Generate benchmark
    try:
        benchmark = generate_benchmark(args.benchmark_dir, args.skill_name, args.skill_path, args.primary_config, args.baseline_config)
    except ValueError as error:
        parser.error(str(error))

    # Determine output paths
    output_json = args.output or (args.benchmark_dir / "benchmark.json")
    output_md = output_json.with_suffix(".md")

    # Write benchmark.json
    with open(output_json, "w") as f:
        json.dump(benchmark, f, indent=2)
    print(f"Generated: {output_json}")

    # Write benchmark.md
    markdown = generate_markdown(benchmark)
    with open(output_md, "w") as f:
        f.write(markdown)
    print(f"Generated: {output_md}")

    # Print summary
    run_summary = benchmark["run_summary"]
    configs = [k for k in run_summary if k != "delta"]
    delta = run_summary.get("delta", {})

    print(f"\nSummary:")
    for config in configs:
        pr = run_summary[config]["pass_rate"]["mean"]
        label = config.replace("_", " ").title()
        print(f"  {label}: {pr*100:.1f}% pass rate")
    print(f"  Delta:         {delta.get('pass_rate', '—')}")


if __name__ == "__main__":
    main()
