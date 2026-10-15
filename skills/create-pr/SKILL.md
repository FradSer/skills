---
name: create-pr
description: Creates a GitHub pull request after repository validation and follows the requested post-creation review scope. Use when asked to create or submit a pull request, including a draft or creation-only request.
disable-model-invocation: true
---

# Create a pull request

Use for an explicit request to open a PR. Read `$ARGUMENTS` first and preserve supplied
issue references verbatim; pass through `--draft`. Before any write, inspect the current
branch, remote, status, changed-file scope, authentication, applicable contributing
rules, and PR template. Run only the repository's relevant lint/type/test/build and
security checks, using [quality validation](references/quality-validation.md) and
[failure resolution](references/failure-resolution.md) as routing aids. Resolve failures
and rerun the complete applicable gate before creating the PR.

Draft a title/body from [PR structure](references/pr-structure.md), retain requested
issue links, and read [auto-closing-keywords.md](references/auto-closing-keywords.md)
when linking an issue. Warn when the base is not the repository default branch because
GitHub will not auto-close the issue there. Labels, reviewers, assignees, and projects
are applied only when requested or required by repository policy. `gh pr create` is the
single PR-creation write owned by this skill; do not push protected branches.

Honor the user's explicit scope after creation. For a creation-only request, return
the verified PR URL and validation results. For a single snapshot, inspect CI and
review metadata once, report that snapshot, and do not start monitoring. Neither
request authorizes comments, merging, or branch cleanup. Apply the full handoff
below only within the requested workflow scope.

After creation, capture the URL and normalize its number from GitHub's data, not by
parsing the URL:

  ```bash
  PR=$(gh pr view "$PR_URL" --json number --jq '.number')
  ```

- Read [review-pr handoff](references/review-pr-handoff.md).
- For the full workflow: Start the standalone `review-pr` workflow exactly once with the normalized PR number.
  Use the host's
  sibling-skill dispatch when available; otherwise use this skill's bundled references
  and scripts as the implementation fallback. Arm every fallback poll through the host
  continuation facility required by [runbook.md](references/runbook.md), never a
  foreground loop or a fake slash command. Do not report completion until `review-pr` owns
  the PR.

`create-pr` owns PR creation. `review-pr` owns baseline review, CI and comment monitoring, triage, fixes, closeout, merge, and post-merge cleanup. Do not call `review-pr` twice and do not run a second review loop from this skill.

## Protected workflow

This skill is the only PR-creating path. Other skills delegate here instead of calling `gh pr create` directly. No direct pushes to `main` or `develop`.

## References

- [Requirements](references/requirements.md)
- [Quality validation](references/quality-validation.md)
- [Repository templates](references/repository-templates.md)
- [Failure resolution](references/failure-resolution.md)
- [PR structure](references/pr-structure.md)
- [Auto-closing keywords](references/auto-closing-keywords.md)
- [Review-pr handoff](references/review-pr-handoff.md)
- [Review-pr operational fallback](references/runbook.md), [review loop](references/review-loop.md), [closeout](references/closeout.md), and `scripts/` (synced from `review-pr`; run the sync check before release)
- [PR creation handoff](references/pr-creation-handoff.md)
- [Commit standards](references/commit-standards.md)
- [Examples](references/examples.md)
