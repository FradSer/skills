---
name: create-issues
description: Creates GitHub issues following test-driven development principles and
  proper labeling conventions. This skill should be used when the user asks to "create
  an issue", "file a bug", or needs to document new requirements, epics, or PR-scoped
  tasks.
disable-model-invocation: true
---

# Create GitHub issues

Use this skill for an explicit request to file a bug, feature, epic, or review issue.
`$ARGUMENTS` is the source for the issue intent; preserve supplied issue links and
references. Begin with read-only repository/branch and authentication checks, search
open issues for duplicates, and read repository guidance/templates before drafting.

Route only the material needed for the request:

- Read [decision-logic.md](references/decision-logic.md) to classify the issue and
  decide whether a PR-branch comment should replace a new issue.
- Read [repository-templates.md](references/repository-templates.md) when templates or
  contributing rules may apply; read [issue-structure.md](references/issue-structure.md)
  to shape the body.
- Read [auto-closing-keywords.md](references/auto-closing-keywords.md) for a PR-scoped
  issue. Auto-close works only when the eventual PR merges into the repository default
  branch; warn when that condition is unknown or false. Epics never use close keywords.
- Read [pr-creation-handoff.md](references/pr-creation-handoff.md) when the issue will be
  implemented through the PR path, so the delegation to `create-pr` and the
  confirmation-before-merge rule are stated.

Draft the title, body, labels, assignee, milestone, and project from the request and
show the planned mutation. Create or update labels only when needed; do not hide a
permission or network failure with `|| true`. Ask for confirmation immediately before
creating an issue, comment, label, assignment, milestone, or project link unless the
user's request explicitly authorizes that exact write. Report the resulting URL/number,
chosen labels, and any skipped or failed mutation. TDD/commit guidance is conditional
support for the eventual implementation; read [requirements.md](references/requirements.md)
only when the issue needs those rules. When the issue prescribes the commits that will
resolve it, read [commit-standards.md](references/commit-standards.md) and
[examples.md](references/examples.md).
