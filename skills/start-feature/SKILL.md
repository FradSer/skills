---
name: start-feature
description: Starts a new feature branch using git-flow. Use when the user asks to "start a feature", "begin new feature", "git flow feature start", or wants to begin a new feature. Accepts either a branch name/version or a natural-language description.
---

# Start feature

Run the start-feature workflow.

Follow the pipeline in `references/gitflow-start-pipeline.md`:
- **Workflow Type**: `feature`
- **Arguments**: $ARGUMENTS

Mechanical steps (branch start, version bump, push) run through
`scripts/start-branch.sh` — see the pipeline reference for usage.

Pre-flight invariants (clean working tree) are enforced per `references/invariants.md`.
