# Git-flow cleanup

Cleanup is limited to this operation's authorized branch lifecycle. The wrapper keeps
the remote branch and leaves unrelated branches and worktree metadata in place.

## Verify the result

Record the exact configured branch prefix, name, bases, and tag before finishing.
Verify the operation's local branch state, the merge result, and the tag when applicable.
Git-flow configuration can retain the local branch; report that fact rather than
assuming deletion or bypassing the configured policy.

When Git-flow preserves the caller's linked worktree as detached after finishing,
verify its HEAD and report the retained checkout. Keep it in place; the development
branch may already be checked out in another worktree.

When removing the just-finished local branch is authorized and it is fully merged:

```bash
git branch -d "$BRANCH"
```

Do not delete the checked-out branch or an integration branch. If deletion refuses,
inspect the reason and report it; do not force-delete or suppress the error.

## Remote branch and worktrees

A local finish or publication of the integration branches does not authorize deletion
of a remote branch. Delete the exact remote head only when authorized and after checking
that no dependent PR or worktree still needs it.

A broader branch sweep, `git worktree prune`, or worktree removal requires a separate
explicit request with an enumerated target list. Use `git worktree list` for inventory.
Preserve pre-existing worktrees and local changes, and use the host's managed-worktree
lifecycle tool when applicable. Do not recommend blanket `rm -rf` cleanup.
