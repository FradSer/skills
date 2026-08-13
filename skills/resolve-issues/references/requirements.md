# Requirements

## Worktree and TDD Workflow

- Use git worktrees for isolated development (`git worktree add/remove`, or the runtime's own worktree tool).
- Apply a TDD cycle (red → green → refactor) with appropriate sub-agent support.
- Reference resolved issues in commits and PR descriptions using auto-closing keywords — only fire on the default branch; see `auto-closing-keywords.md`.
- Delegate PR creation to `create-pr` (the only PR-creating path) — see `pr-creation-handoff.md` for the full contract and protected-PR workflow.
