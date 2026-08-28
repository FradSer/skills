---
name: resolve-issues
description: Resolves GitHub issues using isolated worktrees and test-driven development,
  then delegates PR creation to create-pr so the quality gate and the review-pr loop
  always run. This skill should be used when the user asks to "resolve an issue",
  "fix issue
disable-model-invocation: true
---

# Resolve GitHub Issues

Execute issue resolution workflow using isolated worktrees, TDD methodology, and agent collaboration.

## Runtime notes

- **Worktrees**: worktrees are plain git — `git worktree add -b <branch> <path> <base>` to
  create the isolated worktree, `git worktree remove <path>` (plus `git branch -D <branch>`
  if needed) to clean it up. Runtimes with a dedicated worktree tool may use it instead;
  the result is the same.
- **Skill invocation**: hand PR creation to the sibling `create-pr` skill using the
  runtime's own skill-invocation mechanism — the handoff contract in
  `references/pr-creation-handoff.md` is what matters, not the call syntax.

## Context

- Current git status: !`git status`
- Current branch: !`git branch --show-current`
- Existing worktrees: !`git worktree list`
- Open issues: !`gh issue list --state open --limit 10`
- GitHub authentication: !`gh auth status`

## Requirements Summary

Use isolated worktrees to avoid disrupting main development. Follow TDD cycle (red → green → refactor) with agent support. Reference issues in commits using auto-closing keywords. See `references/requirements.md` for protected PR workflow and commit standards.

## Phase 1: Issue Selection and Worktree Setup

**Goal**: Select target issue and prepare isolated development environment.

**Actions**:
1. Review open issues from context and select based on priority and `$ARGUMENTS`
2. Check existing worktrees to determine if reuse is possible
3. Create the worktree with a descriptive name (e.g., `fix-456-auth-redirect`): `git worktree add -b worktree-<name> .agents/worktrees/<name>` (or the runtime's worktree tool)
4. Rename the branch to match conventions: run `git branch -m <type>/<issue>-<description>` (see `references/workflow-details.md` for naming)
5. Verify issue acceptance criteria and dependencies

## Phase 2: TDD Implementation

**Goal**: Implement fix using test-driven development with agent collaboration.

**Actions**:
1. Plan implementation approach and assess architectural impact
2. Write failing tests that verify issue is resolved (RED phase)
3. Implement minimal code to make tests pass (GREEN phase)
4. Refactor while keeping tests green (REFACTOR phase)
5. Run quality validation commands to keep the TDD cycle honest (see `references/workflow-details.md` for project-specific checks). `create-pr` re-runs the full gate in Phase 3 and is the authoritative pre-PR check.

## Phase 3: PR Creation and Cleanup

**Goal**: Hand PR creation to `create-pr` so the quality gate and the review loop run. Cleanup happens only after the merge, which may be many turns later.

**Actions**:
1. Push branch to remote with `git push -u origin <branch-name>`
2. **CRITICAL: Do NOT call `gh pr create` here.** Invoke the `create-pr` skill with the issue reference (e.g. `create-pr: Closes #456`) via the runtime's skill mechanism. It is the only PR-creating path and owns the quality/security gate, the auto-closing-keyword linkage, the non-default-branch warning, and the mandatory `review-pr` handoff. See `references/pr-creation-handoff.md` for the full contract. Creating the PR directly skips all of it.
   - Append `--draft` to the arguments if the fix requires further feedback before review
3. **This skill does not resume here.** `create-pr` reports the PR URL, and `review-pr` then owns the PR for the rest of its life: a persistent watch spanning turns, the triage/fix/push rounds, and the automatic closeout (summary comment + body rewrite + auto-merge). Do NOT wait inline, do NOT re-report the URL, and do NOT run Phase 4 speculatively.

## Phase 4: Post-Merge Cleanup (later turn, fallback)

**Trigger**: The PR from Phase 3 has actually merged — normally a later turn, after `review-pr` completed its automatic closeout. **`review-pr`'s closeout now owns the post-merge cleanup** (worktree removal via `git worktree remove <path>`, switch to `main`, sync with origin), so this Phase runs only as a **fallback** when that cleanup was skipped: a merge failure or interrupt left the worktree behind, or this is a fresh session that cannot remove the worktree created by an earlier session. Never assume the worktree is gone — verify first.

**Actions**:
1. Verify the merge with `gh pr view <PR#> --json state -q .state` returning `MERGED`; never assume.
2. Check `git worktree list` whether the issue worktree still exists. If `review-pr` already removed it, skip straight to `git fetch --prune`.
3. If it persists: **CRITICAL: confirm still on the issue branch** before `git worktree remove <path>`. If checkout drifted onto `main`/`develop`, stop — removing would delete a long-lived branch. Remote head may already be gone; that is fine.
4. Remove the worktree with `git worktree remove <path>` (and `git branch -D <branch>` if the branch persists).
   - If uncommitted changes exist, removal refuses; confirm with the user before discarding them
5. `git fetch --prune` to sync remote-tracking branches.
6. Document resolution and any follow-up tasks

## References

- **Requirements**: `references/requirements.md` - Worktree setup, TDD, and commit standards
- **PR Creation Handoff**: `references/pr-creation-handoff.md` - Why PRs delegate to create-pr
- **Workflow Details**: `references/workflow-details.md` - Issue selection, TDD cycle, agent collaboration
- **Quality Validation**: `references/quality-validation.md` - Node.js/Python validation commands (shared)
- **Examples**: `references/examples.md` - Commit message examples
