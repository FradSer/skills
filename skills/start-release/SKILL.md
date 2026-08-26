---
name: start-release
description: Starts a new release branch using git-flow. Use when the user asks to "start a release", "begin new release", "git flow release start", or wants to begin a new release. Accepts either a branch name/version or a natural-language description.
disable-model-invocation: true
---

# Start release

Run the start-release workflow.

Follow the pipeline in `references/gitflow-start-pipeline.md`:
- **Workflow Type**: `release`
- **Arguments**: $ARGUMENTS

Mechanical steps (branch start, version bump, push) run through
`scripts/start-branch.sh` — see the pipeline reference for usage.

Pre-flight invariants (clean working tree) are enforced per `references/invariants.md`.
