---
name: finish-hotfix
description: Finalizes a hotfix and merges it into main and develop using git-flow, then prunes stale branches and worktrees. Use when the user asks to 'finish a hotfix', 'merge hotfix branch', 'complete hotfix', 'git flow hotfix finish', or wants to finalize a hotfix.
---

# Finish hotfix

Run the finish-hotfix workflow.

Follow the pipeline in `references/gitflow-finish-pipeline.md`:
- **Workflow Type**: `hotfix`
- **Arguments**: $ARGUMENTS

Mechanical steps (finish, push, return-to-develop, cleanup) run through
`scripts/finish-branch.sh` — see the pipeline reference for usage.

Pre-flight invariants (clean tree, correct branch) and testing requirements are enforced per `references/invariants.md`; cleanup after finishing follows `references/cleanup.md`.
