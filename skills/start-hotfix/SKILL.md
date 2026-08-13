---
name: start-hotfix
description: Starts a new hotfix branch using git-flow. Use when the user asks to "start a hotfix", "begin new hotfix", "git flow hotfix start", or wants to begin a new hotfix. Accepts either a branch name/version or a natural-language description.
---

# Start hotfix

Run the start-hotfix workflow.

Follow the pipeline in `references/gitflow-start-pipeline.md`:
- **Workflow Type**: `hotfix`
- **Arguments**: $ARGUMENTS

Pre-flight invariants (clean working tree) are enforced per `references/invariants.md`.
