---
name: finish-release
description: Finalizes a release and merges it into main and develop with a tag using git-flow, then prunes stale branches and worktrees. Use when the user asks to 'finish a release', 'merge release branch', 'complete release', 'git flow release finish', or wants to finalize a release.
---

# Finish release

Run the finish-release workflow.

Follow the pipeline in `references/gitflow-finish-pipeline.md`:
- **Workflow Type**: `release`
- **Arguments**: $ARGUMENTS

Mechanical steps (finish, push, return-to-develop, cleanup) run through
`scripts/finish-branch.sh` — see the pipeline reference for usage.

Pre-flight invariants (clean tree, correct branch) and testing requirements are enforced per `references/invariants.md`; cleanup after finishing follows `references/cleanup.md`.
