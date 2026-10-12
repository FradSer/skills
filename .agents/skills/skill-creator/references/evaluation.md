# Skill evaluation

Read this for comparative task runs, description benchmarks, or output review. Ordinary documentation updates can use reference and metadata checks without running this workflow.

## Choose evidence

Use two or three realistic cases initially: an ordinary request, a near miss for trigger testing, and a known failure or edge condition. Add cases when a demonstrated gap warrants them. Assertions should measure outputs or decisions, not the presence of a heading or a word copied from the instructions.

For an existing skill, compare the old version with the edited one using the same prompts and fixtures. Snapshot only the requested skill before editing, or recover its original files from Git into a temporary directory. Keep generated outputs outside the skill and avoid using a dirty working tree as the baseline.

Use a temporary or user-selected workspace:

```text
workspace/
  skill-snapshot/
  iteration-1/
    eval-<id>-<purpose>/
      eval_metadata.json
      new_skill/run-1/outputs/
      old_skill/run-1/outputs/
```

For a new skill, use `with_skill` and `without_skill` configurations instead. Existing-skill comparisons use `new_skill` and `old_skill` as above. Keep repeated runs in `run-1`, `run-2`, and so on for benchmark aggregation. Bound parallelism to the host's available agents; paired runs can be sequential when resources or cost require it. Isolate filesystem state and live side effects in both configurations.

## Record and grade

Store cases in `evals/evals.json` with `skill_name`, unique `id`, `prompt`, `expected_output`, and optional `files` and `assertions`. Read the relevant section of [schemas.md](schemas.md) before producing machine-readable evaluation artifacts.

Each case's metadata records its prompt, name, identifier, and assertions. Grade deterministic outputs with a reusable check. Read [grader.md](../agents/grader.md) when agent judgement is needed; keep evidence tied to actual output. `grading.json` expectation entries use `text`, `passed`, and `evidence`.

Record timing and token counts only if the runtime supplies them. Missing data is unavailable, not zero. Keep errors, timeouts, blocked runs, and unavailable tools separate from a measured pass or intentional non-trigger. Do not turn an infrastructure failure into a successful negative trigger result.

For qualitative comparison, give the independent evaluator anonymized outputs and read [comparator.md](../agents/comparator.md). For interpretation of repeated measurements, read [analyzer.md](../agents/analyzer.md). Report variance and non-discriminating assertions rather than assuming every change improved quality.

## Aggregate and show outputs

From the creator directory, aggregate completed runs with:

```bash
uv run python -m scripts.aggregate_benchmark <workspace>/iteration-1 --skill-name <name>
```

Only measured `with_skill`/`without_skill` or `new_skill`/`old_skill` pairs produce a
default delta. For other names, explicitly pass `--primary-config` and
`--baseline-config`; unrelated configurations are summarized without a comparison.
The table contains only measured configurations. Uneven repetition counts and missing
timing/token data remain marked unavailable rather than being replaced with defaults.

Generate a static viewer when outputs or benchmarks would benefit from user review:

```bash
uv run python <creator-dir>/eval-viewer/generate_review.py <workspace>/iteration-1 \
  --skill-name <name> --benchmark <workspace>/iteration-1/benchmark.json \
  --static <workspace>/review.html
```

Omit `--benchmark` when no benchmark exists. Use `--previous-workspace` for an actual earlier iteration. Show the saved file and identify what was measured; do not say a browser opened or a service started unless it did. Feedback from the static page is a downloaded JSON file. Preserve it when the user provides it, and use observed feedback to guide the next narrow revision.

The optional viewer server is for local review. Static output avoids a persistent process. Generated HTML outputs are untrusted material: display them in a sandbox and do not grant access to parent-page state or user accounts.

## Optional Claude description measurements

The bundled `run_eval.py`, `improve_description.py`, and `run_loop.py` use `claude -p`; they are Claude-specific and do not prove Codex or Pi trigger behavior. They use authenticated model calls and create temporary command files under the selected working directory. Run them only when that runtime and its execution are explicitly in scope, in an isolated directory without private project data or production tools.

Use module invocation from the creator directory so imports resolve:

```bash
uv run --with pyyaml python -m scripts.run_eval --help
uv run --with pyyaml python -m scripts.run_loop --help
```

For actual measurements, specify the intended model, bounded workers, per-query timeout, run count, and iteration limit. Inspect the current CLI's help before assuming its event schema. Positive and negative cases must have unique queries and boolean `should_trigger` fields. Keep enough examples in training and reserve independent cases for validation.

The current description loop chooses among iterations using its holdout set, so that set is validation data. Use a separate untouched test set to make a final generalization claim. Compare descriptions at the same model/runtime/settings; do not equate a held-out score, an in-session review, or a static check with successful live integration.

## Iterate and stop

Repair demonstrated failures, update cases when the behavior contract changes, and rerun affected checks. Stop when the requested scope is complete or a documented bound is reached. Report unresolved evidence and actual execution blockers rather than inventing results or repeatedly adding universal rules for hypothetical cases.
