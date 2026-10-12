---
name: resolve-issues
description: Resolves GitHub issues using isolated worktrees and test-driven development,
  then delegates PR creation to create-pr so the quality gate and the review-pr loop
  always run. This skill should be used when the user asks to "resolve an issue",
  "fix issue", or wants to implement fixes or features linked to tracked GitHub issues.
disable-model-invocation: true
---

# Resolve GitHub issues

Use this skill for an explicit request to implement a tracked issue. Start with
read-only issue, branch, worktree, and repository-guidance checks; confirm the issue's
acceptance criteria and dependencies before changing files.

Create or reuse an isolated worktree under `.agents/worktrees/` and a branch that
identifies the issue (`fix/<number>-<slug>`, `feat/<number>-<slug>`, or
`refactor/<number>-<slug>`). Read [workflow-details.md](references/workflow-details.md)
for naming/reuse rules and [requirements.md](references/requirements.md) for the workflow
requirements as a whole; read [repository-templates.md](references/repository-templates.md)
only when repository templates or contributing rules are present. Implement with a
real RED → GREEN → REFACTOR loop and run the relevant checks described in
[quality-validation.md](references/quality-validation.md). Map every explicit
acceptance criterion to an automated test, including boundary behavior the fix must
preserve. A manual assertion supplements this coverage; it does not replace a
regression test. In RED, the bug test must fail for the reported reason while
already-correct boundary tests may pass. Read
[commit-standards.md](references/commit-standards.md) when making commits, and
[examples.md](references/examples.md) when a concrete commit message model is needed.

Before any remote push or issue/PR mutation, verify the target branch and remote and
use the authorization already given for that exact action. Push the branch only after
the local checks pass. Delegate PR creation to `create-pr` exactly as specified in
[pr-creation-handoff.md](references/pr-creation-handoff.md); never call `gh pr create`
from this skill. `create-pr`/`review-pr` own the review, confirmation-before-merge,
and normal post-merge cleanup; every merge still requires explicit user confirmation.
This skill's cleanup section is a fallback only after
verifying the PR is actually merged and the worktree still exists; never discard
uncommitted changes without confirmation.
