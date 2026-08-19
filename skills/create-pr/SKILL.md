---
name: create-pr
description: Creates a GitHub pull request after repository validation, then starts the standalone review-pr workflow for CI monitoring, comment triage, closeout, and merge. Use when asked to create or submit a pull request.
---

# Create a Pull Request

Create a PR only after the repository passes its quality and security gate. After
creation, hand ownership to `review-pr`; do not reproduce its review workflow here.

## Workflow

### 1. Validate the repository

- Read `$ARGUMENTS` before deriving anything. Preserve issue references such as
  `Closes #456` verbatim, use free text as the PR description basis, and pass
  through `--draft`.
- Verify GitHub authentication, current branch, unpushed commits, repository
  status, and the changed-file scope.
- Read applicable `CONTRIBUTING.md` and PR templates.
- Check for merge conflicts, missing tests, and other repository blockers.
- Run the project-specific lint, type-check, test, build, and security checks.
- Resolve failures and rerun the complete gate before creating the PR.

Use [requirements](references/requirements.md),
[quality validation](references/quality-validation.md),
[repository templates](references/repository-templates.md), and
[failure resolution](references/failure-resolution.md).

### 2. Assemble and create the PR

- Generate an imperative, conventional PR title of at most 70 characters.
- Assemble the body using [PR structure](references/pr-structure.md).
- Preserve the issue reference from `$ARGUMENTS`; identify additional related
  issues without changing the supplied reference.
- Apply labels based on the changed files.
- Warn when the target is not the repository default branch: GitHub does not
  auto-close linked issues on non-default branches.
- Run `gh pr create` with the assembled title, body, labels, reviewers,
  assignees, and `--draft` when requested.

Read [auto-closing keywords](references/auto-closing-keywords.md) before writing
issue references and [examples](references/examples.md) when the body or title
needs a concrete model.

### 3. Hand off exactly once

- Capture the URL returned by `gh pr create`.
- Normalize the PR number from GitHub's data, not by parsing the URL:

  ```bash
  PR=$(gh pr view "$PR_URL" --json number --jq '.number')
  ```

- Read [review-pr handoff](references/review-pr-handoff.md).
- Start the standalone `review-pr` workflow exactly once with the normalized
  PR number. Use a host-supported continuation or dispatch mechanism. If the
  host cannot dispatch a sibling skill from inside the current skill, use the
  bundled operational references and scripts under
  `references/` and `scripts/` as the implementation fallback; do not emit a slash
  command as if it were a callable tool.
- Do not report completion or return to the caller until `review-pr` owns the PR.

`create-pr` owns PR creation. `review-pr` owns baseline review, CI and comment
monitoring, triage, fixes, closeout, merge, and post-merge cleanup. Do not call
`review-pr` twice and do not run a second review loop from this skill.

## Protected workflow

This skill is the only PR-creating path. Other skills delegate here instead of
calling `gh pr create` directly. No direct pushes to `main` or `develop`.

## References

- [Requirements](references/requirements.md)
- [Quality validation](references/quality-validation.md)
- [Repository templates](references/repository-templates.md)
- [Failure resolution](references/failure-resolution.md)
- [PR structure](references/pr-structure.md)
- [Auto-closing keywords](references/auto-closing-keywords.md)
- [Review-pr handoff](references/review-pr-handoff.md)
- [Review-pr operational references](references/runbook.md), [review loop](references/review-loop.md), and [closeout](references/closeout.md)
- [Review-pr scripts](scripts/)
- [Commit standards](references/commit-standards.md)
- [Examples](references/examples.md)
