# Independent Codex task checks

Run a repository skill in a fresh `codex exec` process with its own Git fixture and
source snapshot. This is an explicit invocation check. It does not measure implicit
triggering, compare old and new quality, or validate real service accounts.

The runner covers all 18 source skills with 23 selected tasks, including read-only
requests, detached HEAD, unavailable scheduling, missing Lark authorization, and
an offline browser challenge. GitHub and Lark commands are local fixtures; pushes
target a local bare repository. SwiftUI verification builds a small Swift package.

## Run

Inspect the cases without making model calls:

```bash
uv run --with pyyaml python -m tools.skill_eval.codex_eval --list
```

The following command makes authenticated model calls. Use it only when the user
has authorized independent Codex testing and the intended account is logged in:

```bash
codex --version
codex login status
uv run --with pyyaml python -m tools.skill_eval.codex_eval --workers 2
```

Use `--case commit-scoped`, `--skill gitflow`, `--timeout 300`, or a fresh
`--output-dir .skill-evals/my-run` to bound a run. Workers are limited to 1–3;
account for other active agents before choosing a value. Existing output
directories are rejected. `--list` and ordinary repository unit tests make no
model calls.

The current implementation was exercised with Codex CLI 0.160.0 on macOS. It
depends on the current CLI JSONL events and named
[permission profiles](https://learn.chatgpt.com/docs/permissions). The runner
ignores user configuration and does not set a model override. Authentication
still uses the existing Codex account.

## Boundaries and evidence

The per-process permission profile extends workspace permissions, allows Git
metadata writes where the task needs them, protects fixture executables and input
state, and disables command network access. The fixture directory is read-only
apart from designated scratch, receipt, cache, and bare-remote paths. Only the
creator case permits edits to its CSV skill target; the invoked skill remains
read-only. Plugins, apps, hooks,
chronicle, and web search are disabled. User and system Git configuration are
excluded; fixture identity and hooks are local. System temporary directories
remain writable under the workspace profile.

Child environments retain only documented runtime variables and explicit fixture
settings. Approved runtime directories are readable; unrelated home files and the
Codex authentication directory are excluded from command access. The runner uses
the resolved Codex executable so the startup helper can execute within the same
profile. Parent-side Python, Swift, and Git verification also uses that profile.
Gitflow and browser-challenge cases set fixture CDPATH to exercise the relative
script-path regression.

A passing case requires a successful command receipt reading the selected local
`SKILL.md`, a completed process/turn, a nonempty final response, unchanged source
hashes and protected inputs, and observable task assertions. A model saying it
used a skill or completed a task is insufficient. Deterministic checks verify
files, all bare-remote refs, native CLI operation receipts, and applicable
build/test results. An independently editable log is insufficient; observed
commands must use the protected fixture CLI without shell or PATH replacement.
The challenge wrapper may explicitly prepend the same protected fixture directory;
its log must show only session closure after challenge detection. The issue-fix case
also injects an empty-input regression in a separate sandboxed test process to confirm
that the generated tests protect that acceptance boundary.
Help receipts corroborate logs but cannot count as resource creation or document
retrieval. New-file checks use fixed directory exclusions rather than Git's
editable exclude settings.
Qualitative correctness still needs review of the actual output.

Each run saves `manifest.json`, `summary.json`, and `report.md`. Each case saves
its prompt, fixture context, command, source hashes, thread id, raw events,
stderr, final response, and grading result. The manifest also records the
evaluation harness hashes. Timing and usage come from the
process and event stream; missing token counts stay null. Process failures,
timeouts, grading errors, and Git metadata permission blockers cannot pass.
Failed runs remain available; repairs use a new output directory and fresh
fixtures.

After correcting an evaluator, reassess saved evidence without making model
calls or overwriting the original result:

```bash
uv run --with pyyaml python -m tools.skill_eval.regrade .skill-evals/my-run
```

This writes separate assessment files with the grader hashes. It reruns applicable
local verification in the sandbox and keeps incomplete attempts as failures.
Use a fresh Codex case to test any change to the skill itself.

Artifacts live under ignored `.skill-evals/` by default. They can contain the
task's generated content and full tool transcripts; retain them locally for
inspection. The runner does not publish its reports.
