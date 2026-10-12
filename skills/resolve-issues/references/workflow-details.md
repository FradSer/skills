# Workflow Details

## Issue Selection

Evaluate open issues from context and prioritize the next actionable item:
- Check issue labels for priority (priority:high, priority:medium, priority:low)
- Review issue description for complexity and dependencies
- Confirm issue is not blocked by other open issues
- Verify issue has clear acceptance criteria

## Worktree Setup

Create an isolated worktree session with plain git (runtimes with a dedicated
worktree tool may use it instead — the result is the same):

1. **Create worktree**:
   Create a worktree under `.agents/worktrees/` with a descriptive name (e.g.,
   `fix-456-auth-redirect`):
   ```bash
   git worktree add -b worktree-fix-456-auth-redirect .agents/worktrees/fix-456-auth-redirect
   ```
   `.agents/worktrees/` must be ignored in the repo's tracked `.gitignore` (not only a local
   `.git/info/exclude` entry) so a fresh clone doesn't show the worktree directory as
   untracked — verify with `git check-ignore -v .agents/worktrees` before relying on it.

2. **Rename branch to match conventions**:
   The branch was created as `worktree-<name>`. Rename it before committing:
   ```bash
   git branch -m fix/456-auth-redirect
   ```

3. **Branch naming convention**:
   - Bug fixes: `fix/ISSUE-short-description` (e.g., `fix/456-auth-redirect`)
   - Features: `feat/ISSUE-short-description` (e.g., `feat/123-oauth-login`)
   - Refactoring: `refactor/ISSUE-short-description`

4. **Existing worktree reuse**:
   - Check existing worktrees using `git worktree list`
   - If a worktree already exists for the issue, navigate to it directly instead of creating a new one

## TDD Implementation Cycle

Follow the red-green-refactor cycle:

1. **Plan implementation**:
   - Map every explicit acceptance criterion, including preserved boundaries, to an automated test
   - Assess architectural impact of the change
   - Identify potential design issues or anti-patterns
   - Plan the implementation approach

2. **Red Phase**: Write failing tests
   - Add tests for the reported bug and all preserved acceptance boundaries
   - Confirm the bug test fails for the expected reason; already-correct boundary tests may pass

3. **Green Phase**: Implement minimal fix
   - Write code to make tests pass
   - Focus on solving the problem, not optimization

4. **Refactor Phase**:
   - Simplify and optimize code
   - Remove duplication and improve readability
   - Ensure tests still pass after refactoring

## Quality Validation

During the TDD cycle, run project-specific checks for local feedback; see `quality-validation.md`. Before opening a PR, `create-pr` verifies the applicable project checks and changed-content boundaries. Report unavailable checks and unrelated failures precisely.

## PR Creation and Cleanup

1. **Push branch when authorized**: `git push -u origin <branch-name>`.
2. **Create PR**: **CRITICAL: never call `gh pr create` from this skill.** Invoke the
   `create-pr` skill with the issue reference (e.g. `create-pr: Closes #456`) — see
   `pr-creation-handoff.md` for the contract. Use actual host tools for bounded review,
   triage, verified fixes, and closeout. Resolve material escalations before readiness.
   Request missing explicit user confirmation after presenting the reviewed merge.
3. **After a confirmed merge**: `review-pr` verifies the result and owns authorized cleanup
   of this PR's exact branch/worktree. A fallback must first verify the merge, inspect
   `git worktree list`, and confirm the target was created by this task or its removal
   was explicitly authorized. Preserve local changes and unrelated worktrees. A merge
   failure leaves the PR open and does not trigger deletion. Use the PR's actual base;
   do not synchronize every integration branch or run a broader cleanup sweep.
