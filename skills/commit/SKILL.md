---
name: commit
description: Creates clean, conventional git commits using standard git. Use when the user asks to "commit", "git commit", "create commit", or wants to commit staged or unstaged changes. Does not push; use commit-and-push when the request includes a push.
---

# Commit

Create one atomic Conventional Commit from the changes the user placed in scope.

Inspect `git status --short`, staged diff, and unstaged diff first. Preserve unrelated
work; stage paths explicitly and include untracked files only when they belong to the
requested change. If there is nothing to commit, report that and stop. If HEAD is
detached, report the commit hash and ask for a branch decision before committing.

Use `<type>(<optional-scope>): <imperative summary>` with a type such as `feat`, `fix`,
`docs`, `refactor`, `test`, `build`, `ci`, or `chore`. Keep the message factual and
short; include a body only when it explains why. Run the narrow relevant checks before
committing when the repository documents them, then report the new commit hash and
files included. A commit is a local mutation authorized by the user's commit request;
do not push, amend, reset, or change unrelated files.

For a requested co-author trailer, read [coauthor-attribution.md](references/coauthor-attribution.md).
