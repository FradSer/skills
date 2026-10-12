---
name: review-pr
description: 'Reviews a pull request and resolves reviewer feedback: monitors CI and
  review comments, applies verified fixes, and closes out before any merge. Use for
  "review a PR", "monitor PR review comments", "address reviewer feedback on #123",
  or "watch CI on a pull request".'
disable-model-invocation: true
---

# Review a pull request

Use for an explicit request to review, monitor, or address feedback on a PR. Normalize
the supplied URL/number to a bare numeric `PR` before any `gh api` call and resolve
`REPO=<owner>/<repo>` from metadata or the origin remote. Resolve `SKILL_DIR` once and
use absolute script paths.

Read [runbook.md](references/runbook.md) for dispatch and sentinel details, then read
only the relevant sections of [review-loop.md](references/review-loop.md) for baseline
review, interval sizing, event triage, or stop conditions. Run an independent baseline
review and use clean-context triage for comment batches. Apply only verified fixes;
inspect CI logs before changing code and stop for auth, secret, flaky, or infrastructure
failures. A monitor result is not proof that there were no events.

In Pi, start every one-shot poll with `monitor_start`; other hosts use the actual bounded
execution/continuation facility described in the runbook. Do NOT run a foreground `while`
loop or invent an unavailable tool. Pass ACK IDs only after triage; unacknowledged events replay from
the persisted state. Stop when CI is terminal/passing and every comment is triaged, or
when the documented deadline is reached. An empty poll is not a stop signal. Resolve
material scope, correctness, and authorization escalations before declaring merge readiness.

When the gate holds, read [closeout.md](references/closeout.md), arm the closeout state,
post/update the summary and PR body, stop monitoring, and present the result. Mark the
awaiting-confirmation state so the turn can yield for the decision. Request
explicit user confirmation before merging; do not merge until that confirmation arrives.
If the user has already explicitly authorized this exact merge after the same closeout,
reuse that authorization rather than asking again. After a confirmed merge, complete
only the authorized worktree/branch synchronization and cleanup before reporting its success.

## References

- [Runbook](references/runbook.md) — monitor contract and fallback dispatch
- [Review loop](references/review-loop.md) — script, triage, and stop rules
- [Closeout](references/closeout.md) — summary, confirmation, merge, and cleanup
- [PR handoff](references/pr-creation-handoff.md) — the caller contract and merge gate for this PR
- [Commit standards](references/commit-standards.md) and [repository templates](references/repository-templates.md) when fixing code
- [Quality validation](references/quality-validation.md) when rerunning checks on a fix
- [Examples](references/examples.md) when a concrete output model is needed
