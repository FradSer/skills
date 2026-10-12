# Git-flow invariants

## Before mutation

- Require a Git repository with a clean working tree and existing Git-flow configuration.
- Read configured branch names and type prefixes instead of assuming main/develop.
- Validate inputs and CLI capabilities before changing branches or files.
- Starting may create a branch from its configured base regardless of the current branch.
- Finishing requires the exact current branch to match the resolved type and name.
- Validate all version manifests before branch creation; never change dependency versions.

## Before finishing

Run applicable project tests and release checks. Repair change-caused failures and
report unrelated failures; do not claim validation that did not run. Read changelog
references only when the project/request needs a changelog. Preserve user-curated entries.

## Scope and authorization

Use `--no-push` when only local operations are authorized. It disables remote operations
but still performs real local changes. A requested finish includes local merges, tags
when applicable, and the target branch lifecycle; clarify any unresolved destructive scope.
Publication, GitHub release creation, remote deletion, and unrelated cleanup each need
authorization covering their exact target. Reuse authorization already given.

The wrappers disable Git-flow's automatic remote operations before performing any
explicit publication. Verify all command results. A failed push is partial completion,
not a successful finish. Never silently force-push, force-delete, or publish all tags.

## Commits and cleanup

Stage only intended files. Use conventional commit messages and configured attribution
only when applicable. Verify this operation's branch/tag and preserve unrelated work.
Read [cleanup.md](cleanup.md) for conditional removal and managed-worktree handling.

For current CLI semantics, inspect local `git flow <type> <operation> --help` first.
If it lacks the required flags, stop before mutation and report the unsupported CLI.
