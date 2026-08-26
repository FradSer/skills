---
name: start-hotfix
description: Starts a new hotfix branch using git-flow. Use when the user asks to "start a hotfix", "begin new hotfix", "git flow hotfix start", or wants to begin a new hotfix. Accepts either a branch name/version or a natural-language description.
disable-model-invocation: true
---

# Start hotfix

Run the start-hotfix workflow.

Follow the pipeline in `references/gitflow-start-pipeline.md`:
- **Workflow Type**: `hotfix`
- **Arguments**: $ARGUMENTS

Mechanical steps (branch start, version bump, push) run through
`scripts/start-branch.sh` — see the pipeline reference for usage.

Pre-flight invariants (clean working tree) are enforced per `references/invariants.md`.
