# Git-flow finish pipeline

Finishing merges, may create a tag, and deletes the operation's local branch. Confirm
these actions are within the user's request before running them. Read
[invariants.md](invariants.md) for checks and [cleanup.md](cleanup.md) for boundaries.

## Resolve and verify the exact branch

Read the current branch and configured type prefix. An explicit target must match
the entire current branch, not just its type. Without a target, use the exact current
branch suffix. Reject a detached HEAD or a mismatched target before any merge.

Read configured production/development branches. Verify required local bases exist,
the working tree is clean, and a requested tag is valid and absent. The default tag
is `v<version>`; pass `--tagname` for the repository's actual tag convention.

## Verify the project

Run the affected project checks using its existing commands and package manager
(`pnpm` for Node, `uv` for Python). Fix failures caused by the branch before finishing.
Report unrelated failures and follow repository release policy.

Update an existing changelog when required by the project or request. Preserve manual
entries and use [changelog-generation.md](changelog-generation.md) and
[changelog-example.md](changelog-example.md) for commit mapping and output. Stage only
the changelog and intended changes. Attribution is conditional on an explicit identity
or repository policy; see [coauthor-attribution.md](coauthor-attribution.md).

## Finish locally, then publish if authorized

```bash
bash <skill-dir>/scripts/finish-branch.sh --type feature --name "$NAME" --no-push
bash <skill-dir>/scripts/finish-branch.sh --type hotfix --version "$VERSION" --no-push
bash <skill-dir>/scripts/finish-branch.sh --type release --version "$VERSION" --no-push
# Optional for release/hotfix: --tagname "$TAG" --message "Release $VERSION"
```

The wrapper requires an installed CLI supporting `--no-fetch`, `--no-push`,
`--no-pushtag`, and `--keepremote`. It uses these flags even when publication is
requested, then performs its own exact push. A local finish normally returns to the
configured development branch. If Git-flow retains the caller's worktree as detached
after finishing, the wrapper preserves and reports that state instead of forcing a
checkout of a branch that may be in use elsewhere. No pull, remote branch deletion,
unrelated branch sweep, or worktree pruning is implicit.

Native git-flow-next topic/base keys and legacy AVH keys are resolved by the shared
configuration helper. When supported, `--keep-worktree` also preserves a Git-flow-created
checkout; removal is a separate authorized action. Custom hierarchies require reviewing
the configured parent/startpoint and auto-update relationships before finishing.

Existing script callers retain publication by default. Omit `--no-push` only when the
user authorized the exact remote publication. Feature publication pushes the configured
development branch; release/hotfix publication pushes the configured integration branches
and this operation's exact tag. It never pushes every local tag. Missing origin fails
before the local finish; a later push failure returns failure and reports that only
the local finish completed. Preserve this state for recovery instead of rerunning finish.

For a manual fallback, inspect installed help and apply the same target, remote-operation,
and error checks. Stop when the CLI cannot safely enforce them.

## Optional release publication and cleanup

Create a GitHub release only when requested or already explicitly authorized. Prepare
its notes from verified changes and use a notes file with `gh release create --notes-file`.
Local Git-flow finish alone does not authorize publication or remote branch deletion.
Read [cleanup.md](cleanup.md) to verify only this operation's branch and tag.
