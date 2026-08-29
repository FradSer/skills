# PR Creation Handoff Contract

This is the canonical contract for how PRs get created across the github skill suite. All skills that need a PR created delegate to `create-pr`; none call `gh pr create` themselves.

## CRITICAL: create-pr is the ONLY PR-creating path

No other skill calls `gh pr create`. Other skills (`resolve-issues`, and any future caller) delegate to the `create-pr` skill so no PR escapes the quality gate or the mandatory `review-pr` handoff. **Do not add a bypass.**

## Duties owned by create-pr (not duplicated by callers)

1. **Pre-creation quality + security gate** — lint/test/build/type-check + secret scan, all must pass before `gh pr create`.
2. **Auto-closing-keyword linkage + non-default-branch warning** — see `auto-closing-keywords.md`.
3. **Mandatory handoff to `review-pr`** — after PR creation, normalize the PR URL to its bare number and start standalone `review-pr` exactly once with `$ARGUMENTS=<PR>`. If nested skill dispatch is unavailable, use the bundled operational references and scripts under `create-pr/references/` as the implementation fallback; this directory intentionally contains no nested `review-pr` skill or second `SKILL.md`. The review → fix → commit+push → wait-for-review loop continues until CI is green and every comment is triaged, then the closeout ceremony posts its summary and requests explicit user confirmation. Merge only after that confirmation. Escalate/ambiguous comments are recorded in the summary comment, not asked about. This handoff is unconditional — there is no opt-out flag.
4. **Post-merge branch + worktree hygiene** — delegated onward to `review-pr` (Phase 5 closeout), which deletes the remote + local head branches (when stack-safe and in the main worktree), removes the linked worktree (`git worktree remove <path>`), switches to `main`, fast-forwards local `main`/`develop` with origin, drops all other already-merged locals, runs `git worktree prune`, and scans for stale worktree directories. See `closeout.md`.

## Caller contract (resolve-issues and any future caller)

- Invoke the `create-pr` skill with the issue reference **verbatim** — do not re-derive or second-guess the auto-closing keyword.
- Pass `--draft` through if early feedback is needed.
- Do NOT wait inline for the PR URL; do NOT re-report the PR; do NOT call `gh pr create`.
- After `gh pr create`, the create-pr owner must normalize the returned URL and start standalone `review-pr` exactly once; if nested dispatch is unavailable, execute the bundled operational implementation from `references/` rather than merely describing a handoff or returning control.
- Creating the PR directly skips the quality gate, the auto-closing-keyword linkage, the non-default-branch warning, and the review-pr loop — all of it.

## Protected PR workflow

- No direct pushes to `main`/`develop`.
- All changes go through PR + review + CI.
- Every PR enters the `review-pr` loop after creation — review, fix what is verified, commit+push, wait for the next review round — until CI is green and every comment is triaged. The closeout ceremony then presents its summary and requests explicit user confirmation; the PR merges only after confirmation.
- Use worktrees to isolate development work; clean up after successful merge.

This file consolidates the four copies of the "only PR-creating path" contract that had drifted in their enumerated sub-items (duty order, owned-duties list).
