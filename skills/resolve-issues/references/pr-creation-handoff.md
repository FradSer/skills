# PR creation handoff

Use `create-pr` as the shared PR creation path so issue links, checks, and review
ownership remain consistent. Honor a user's explicit narrower request.

## Duties owned by create-pr

1. Run the relevant project checks and changed-content checks in
   [quality-validation.md](quality-validation.md); state skipped or unrelated failures.
2. Preserve issue references and apply [auto-closing-keywords.md](auto-closing-keywords.md)
   only when the PR targets the default branch.
3. After creation, capture the URL, normalize the bare PR number, and start standalone
   `review-pr` exactly once. If sibling dispatch is unavailable, execute the bundled
   operational fallback under `create-pr/references/` and `create-pr/scripts/` using
   actual host tools. A description of a handoff does not start it.
4. Review owns baseline review, bounded polling, validated fixes, and closeout. Resolve
   material scope, correctness, authorization, and repository-policy escalations; record
   optional items explicitly deferred by the user or policy. Prepare and present the
   result before requesting any missing explicit user confirmation for merge.
5. After a confirmed merge, verify it and complete only the authorized cleanup of this
   PR's exact head/worktree. Preserve unrelated branches, checkouts, and changes; a broader
   sweep requires separate explicit authorization.

## Caller contract

- Pass supplied issue references and draft status through unchanged. Do not duplicate
  `gh pr create` or start a second review monitor.
- Read the sibling skill when available; otherwise follow the executable fallback and
  report an unavailable dispatch/continuation facility precisely.
- Do not claim review ownership, active monitoring, passing CI, or a merge from merely
  printing a command or receiving a PR URL.
- Reuse an explicit authorization already covering the same reviewed merge. A material
  head/scope change must be reviewed and authorized before merging.
- Follow repository branch policy. Preserve local work and use a managed worktree when
  appropriate; cleanup is limited to task-created or explicitly approved targets.

For the merge gate, awaiting-confirmation state, and cleanup procedure, use review-pr's
closeout reference or the synchronized create-pr fallback. Explicit user confirmation
is required before merging when no applicable authorization already exists.
