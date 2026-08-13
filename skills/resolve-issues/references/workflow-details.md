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

Follow the red-green-refactor cycle with agent collaboration:

1. **Plan implementation**:
   - Assess architectural impact of the change
   - Identify potential design issues or anti-patterns
   - Plan the implementation approach

2. **Red Phase**: Write failing tests
   - Create test cases that verify issue is fixed
   - Run tests to confirm they fail as expected

3. **Green Phase**: Implement minimal fix
   - Write code to make tests pass
   - Focus on solving the problem, not optimization

4. **Refactor Phase**:
   - Simplify and optimize code
   - Remove duplication and improve readability
   - Ensure tests still pass after refactoring

## Quality Validation

During the TDD cycle, run project-specific quality checks for fast local feedback — see `quality-validation.md` for commands. `create-pr` re-runs the full quality and security gate before it opens the PR, so these checks are not the gate itself.

## PR Creation and Cleanup

1. **Push branch**: `git push -u origin <branch-name>`
2. **Create PR**: **CRITICAL: never call `gh pr create` from this skill.** Invoke the
   `create-pr` skill with the issue reference (e.g. `create-pr: Closes #456`) — see
   `pr-creation-handoff.md` for the full contract. The review loop is unconditional and
   fully automatic: CI watch, comment triage, fixes, closeout ceremony, and auto-merge
   with a merge commit run without any user question.
3. **After merge**: `review-pr` owns the automatic closeout and the post-merge cleanup — it
   removes the linked worktree (`git worktree remove <path>`), switches to `main`, and syncs
   `main`/`develop` with origin. resolve-issues Phase 4 only runs as a fallback if review-pr's
   cleanup was skipped (a merge failure or interrupt, or a fresh session) — check
   `git worktree list` first and `git worktree remove <path>` only if the worktree persists.
   - If uncommitted changes exist, removal will refuse; confirm with the user before
     discarding them.
