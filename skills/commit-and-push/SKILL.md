---
name: commit-and-push
description: Creates clean conventional git commits using standard git and pushes
  changes to the remote repository. Use when the user asks to "commit and push", "push
  changes", or complete a commit followed by git push.
disable-model-invocation: true
---

# Commit and push

Use this skill only for an explicit request to commit and push. Inspect status and both
diffs first, stage requested paths explicitly, and stop when there is nothing to commit.
Preserve unrelated work. Use the Conventional Commit format described by `commit`; read
[coauthor-attribution.md](references/coauthor-attribution.md) only when a trailer is
requested.

Before committing, verify that HEAD names a branch, `origin` exists, and the requested
branch is safe to publish. Never push a detached HEAD or directly push a protected
integration branch (`main`, `master`, `develop`, or `production`) unless the user has
explicitly named that branch and repository policy permits it. Commit locally first,
then push the exact branch; use `git push --set-upstream origin "$BRANCH"` only when no
upstream exists. A rejected push is a reportable failure: do not force-push, amend, or
retry with another remote. Report commit hash, branch, remote, and push result.
