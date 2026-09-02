---
name: review-pr
description: 'Reviews a pull request: runs an independent baseline review, monitors
  CI and incoming reviewer comments with Pi monitor_start, triages and applies verified
  fixes, then presents a closeout summary and waits for explicit user confirmation before
  merging and cleaning the worktree and branch. Use this skill when the user asks to
  "review a PR", "monitor PR review comments", "address reviewer feedback on #123",
  or "watch CI on a pull request".'
disable-model-invocation: true
---

# Review a Pull Request

Run the baseline review of the PR diff, then use Pi's `monitor_start` tool to watch CI and new reviewer comments until the PR settles. Present the closeout summary and request explicit user confirmation before merging. The detailed operational sequence lives in `references/runbook.md`; load it when dispatching the monitor or when a runtime cannot provide nested workflow execution.

## Runtime notes

- Resolve `SKILL_DIR` once and use absolute paths to every script.
- Start every one-shot review poll with Pi's `monitor_start` tool; never run the poll in the foreground or use an infinite loop.
- Use clean-context agents for baseline review and comment triage.
- Once the merge gate holds, post the closeout summary, rewrite the PR body, stop monitoring, and ask the user to explicitly confirm the merge. Do not merge unless that confirmation arrives.
- After a confirmed merge, complete worktree and branch cleanup before reporting success.

## Context

- PR argument: `$ARGUMENTS`
- PR metadata: !`gh pr view "$ARGUMENTS" --json number,title,headRepository,headRepositoryOwner,additions,deletions,headRefName 2>/dev/null || printf 'set %s to a PR number or URL\n' "$ARGUMENTS"`
- Remote: !`git remote -v 2>/dev/null | head -2`
- Auth: !`gh auth status 2>&1 | head -3`

## Phase 1: Baseline Review and Sizing

**Goal**: Run the initial review, resolve the repo, and pick a poll interval sized to the PR.

**Actions**:
1. Parse the PR number or URL from `$ARGUMENTS`. If absent, resolve the PR automatically: the current branch's open PR via `gh pr view --json number -q .number` (falls back to the branch's head PR), else the most recently updated open PR via `gh pr list --state open --json number,updatedAt --limit 1` — never ask the user which PR to review. **Normalize `PR` to the bare number** before any `gh api` REST call: `gh pr *` commands accept a URL, but `gh api repos/$REPO/issues/$PR/...` interpolates `$PR` into the URL path and breaks on a full URL — run `PR=$(gh pr view "$ARGUMENTS" --json number -q .number)` (the Context block already fetches `--json number`) and use `$PR` as the number everywhere downstream.
2. **Run the baseline review** — spawn an independent review agent with clean context (it did not author the code) to review the PR diff. Pull the diff with `gh pr diff <PR>`; pass the agent the PR title/body and the diff, and ask for findings as `path:line: issue` lines (full prompt in `references/review-loop.md`, Baseline review agent). Treat its findings as the **first `[comment]` batch** — feed them straight into the Phase 3 triage flow before starting the monitor. Do not act on them inline; the main context is biased (it likely authored the PR) and the same skeptical gatekeeping must apply to the baseline as to live comments.
3. Resolve `REPO=<owner>/<repo>` from the PR metadata above (fallback: `git remote get-url origin` parsed into `owner/repo`).
4. Read PR size from `additions+deletions` and pick `INTERVAL` (seconds) from the size table in `references/review-loop.md`: 180 / 300 / 480 for small / medium / large; floor 60s, cap 7200s (~2h).

## Phase 2: Start the Monitor

**Goal**: One monitor carrying CI + comment events across turns.

**Action**: Invoke Pi's `monitor_start` tool for one poll of `scripts/review-loop.sh --once` per invocation using the monitor wrapper defined in `references/runbook.md`. Do NOT run a foreground `while` loop.

- Match `__REVIEW_POLL__ (?<json>\{.*\})` for success and `__REVIEW_POLL_FAILED__ (?<json>\{.*\})` for failure.
- Parse the `events` array from the captured JSON; triage each line and never treat an `ok` status as absence of events.
- On restart, pass acknowledged IDs via `ACK="<node-id> ..."`. Unacknowledged comments replay automatically.
- Never skip the watch on launch-time checks (even with empty `.github/workflows/`, reviews/bots arrive asynchronously). Full details in `references/review-loop.md`.

## Phase 3: React to Each Watch Event

**Goal**: Fix actionable issues, reject noise, record escalations. Full rules in `references/review-loop.md`.

- `[ci] <name>: fail|cancel` → inspect logs (`gh run view <run-id> --log-failed`), commit & push inline fixes. Do not auto-fix auth, secret, or flaky infrastructure issues.
- `[comment]` batch → spawn an independent triage subagent with clean context. Apply only `fix` verdicts, commit & push in one batch, hide resolved items as `OUTDATED` and resolve threads. Record `escalate` items for closeout.
- `[comment]` ambiguous → defer via a one-line reject note and record for summary. Never block on plain questions. Default to skepticism against bot/linter noise.

## Phase 4: Stop Conditions

Stop monitor when EITHER condition holds (details in `references/review-loop.md`):
- **Normal stop**: All CI checks passing + all comments triaged/hidden + merge gate ready. Stop the monitor and proceed to Phase 5's confirmation request.
- **Hard cap**: ~2h wall-clock reached. Surface remaining unsettled items and stop. If all items settled, proceed to Phase 5's confirmation request.

## Phase 5: Closeout — Ceremony and Confirmed Merge

**Goal**: Execute closeout ceremony, stop monitor, and await explicit user confirmation before merging. Detailed templates and steps in `references/closeout.md`.

1. **Arm closeout state**: Run `bash <skill-dir>/scripts/arm-closeout.sh "$PR"` to arm turn-end protection.
2. **Execute ceremony**: Post summary comment (`gh pr comment`), capture URL, and rewrite PR body linking the review cycle.
3. **Request confirmation**: Stop monitor, present summary/CI status, and ask user for explicit merge confirmation.
4. **Merge & cleanup upon confirmation**: Merge via `gh pr merge "$PR" --repo "$REPO" --merge --delete-branch` (omit `--delete-branch` in worktree). Complete worktree/branch cleanup and branch sync before reporting success. Clear state with `bash <skill-dir>/scripts/clear-closeout.sh "$PR"`.

## References

- **Runbook**: `references/runbook.md` - Phase order, inputs, absolute script paths, monitor contract, and fallback execution
- **Review Loop**: `references/review-loop.md` - Watch script, size→INTERVAL table, triage agent prompt, verdict format, lifecycle/stop conditions
- **Closeout**: `references/closeout.md` - Summary comment, body rewrite, explicit merge confirmation, and post-merge hygiene constraints
- **Commit Standards**: `references/commit-standards.md` - Commit message format for the inline git commit rounds
- **Repository Templates**: `references/repository-templates.md` - Contributing guidelines conformance for fixes
- **Examples**: `references/examples.md` - Commit message examples
