---
name: finish-feature
description: Finalizes and merges a feature branch into develop using git-flow, then prunes stale branches and worktrees. Use when the user asks to 'finish a feature', 'merge feature branch', 'complete feature', 'git flow feature finish', or wants to finalize a feature branch.
---

# Finish feature

Run the finish-feature workflow.

Follow the pipeline in `references/gitflow-finish-pipeline.md`:
- **Workflow Type**: `feature`
- **Arguments**: $ARGUMENTS

Mechanical steps (finish, push, return-to-develop, cleanup) run through
`scripts/finish-branch.sh` — see the pipeline reference for usage.

Pre-flight invariants (clean tree, correct branch) and testing requirements are enforced per `references/invariants.md`; cleanup after finishing follows `references/cleanup.md`.
