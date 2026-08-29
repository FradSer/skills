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

**Action**: Invoke Pi's `monitor_start` tool for one poll of
`scripts/review-loop.sh --once` per invocation. Its success result must match
`__REVIEW_POLL__ (?<json>\\{.*\\})`, failure result must match
`__REVIEW_POLL_FAILED__ (?<json>\\{.*\\})`, and its command must be the wrapper below. Never run the poll in the foreground
or substitute a manual loop. The monitor command MUST capture the poll's stdout and
embed every emitted event line INSIDE the terminal JSON sentinel: monitors with a
terminal-result contract may surface only the matched result line, so events printed
before the sentinel can be silently dropped (this lost a real review comment once).
Wrap the poll like:

```bash
bash -c '
  events=$(PR="$PR" REPO="$REPO" INTERVAL="$INTERVAL" bash "$SKILL_DIR/scripts/review-loop.sh" --once); rc=$?
  payload=$(printf "%s\n" "$events" | jq -Rsc 'split("\n") | map(select(length > 0))')
  if [ "$rc" -eq 0 ]; then
    printf "__REVIEW_POLL__ {\"status\":\"ok\",\"events\":%s}\n" "$payload"
  else
    printf "__REVIEW_POLL_FAILED__ {\"status\":\"failed\",\"exitCode\":%s,\"events\":%s}\n" "$rc" "$payload"
    exit "$rc"
  fi
'
```

Configure the monitor's equivalent success and failure matchers for
`__REVIEW_POLL__ (?<json>\\{.*\\})` and `__REVIEW_POLL_FAILED__ (?<json>\\{.*\\})`.
Parse the `events` array from the captured JSON and triage every line; never treat an
`ok` status as proof of no events. Handle the single poll result, then start the next
poll in a new monitor invocation until stop conditions hold. Do not run infinite mode
under a one-shot monitor. The bare path `scripts/review-loop.sh` does NOT resolve — use
the absolute skill path. Pass `PR`, `REPO`, `INTERVAL`, `STATE_FILE`, and any acknowledged
node IDs explicitly. Do NOT run a foreground `while` loop. The script is documented in
`references/review-loop.md`.

**Restarting a watch mid-PR**: pass the node ids already triaged by the previous run
via `ACK="<node-id> ..."` (or repeatable `--ack <node-id>`). `EXCLUDE`/`--exclude`
remains an input alias for existing callers, but these values mean acknowledged,
not merely emitted. Unacknowledged comments are intentionally replayed after a
restart. Never drop those lines with a `grep -v` chain instead — grep/sed/awk
block-buffer when piped, so events stall in the filter and never reach a streaming
watch (details in `references/review-loop.md`).

**CRITICAL: Do NOT skip the watch based on a launch-time snapshot.** "This repo has no CI workflow, so the watch would spin idly" is a **false** inference and not a valid reason to skip: CI is only one of the two things watched. Automated review services, org-level bots, and human reviewers post comments on no fixed schedule and are invisible in a launch-time snapshot — a repo with zero workflows can still accumulate a full review thread minutes after the PR opens. An empty `.github/workflows/` proves nothing about who will comment.

The only valid skip is a PR that is already merged or closed. If CI and reviewers both appear absent, start the monitor anyway; it costs nothing and emits nothing until something changes.

## Phase 3: React to Each Watch Event

**Goal**: Fix what is actionable, reject the noise, record the rest. Full rules, prompt template, verdict format, and reply/hide/resolve lifecycle in `references/review-loop.md`.

- `[ci] <name>: fail|cancel` → fetch logs (`gh run view <run-id> --log-failed`), apply the fix, commit+push via inline git commands (`git add <file> && git commit -m "<type>(<scope>): <summary>" && git push`). The push triggers a fresh CI run the same watch re-emits. **CRITICAL: stop and report (do NOT auto-fix) for auth/permission, missing-secret, flaky, or infrastructure failures.**
- `[comment]` batch → **CRITICAL: spawn an independent review-triage agent with clean context.** Apply ONLY the `fix` verdicts; reject/escalate the rest. **CRITICAL: reply by comment type** — inline review comment → `gh api repos/$REPO/pulls/$PR/comments/<id>/replies`; issue-level comment → `gh pr comment` (no reply endpoint); review summary → skip reply. Use the `id=<n>`/`node=<id>` tokens from each emitted line. Commit+push all `fix` changes in one round; then hide each fully-addressed comment (`fix` pushed or `reject` replied) as `OUTDATED` via `minimizeComment` and resolve its thread via `resolveReviewThread` (inline only). Leave `escalate` comments open; record each one (body + author + file context) for the closeout summary comment — they are documented, never asked about.
- `[comment]` ambiguous (design disagreement, scope change, unclear intent) → do not guess, reply, or hide. Reply with a one-line `reject`-style note stating the point is deferred, and record it (body + author + file context) for the closeout summary comment. Never notify the user and wait.

**CRITICAL mindset**: Comments are mostly from other agents (linters, code-review bots) and human reviewers — suggestions to *consider*, not orders. Default to skepticism; verify each claim against the diff and adopt only what is demonstrably correct and safe. Rejecting a comment is the normal outcome for noise and false positives.

## Phase 4: Stop Conditions

Stop the watch when EITHER holds — full conditions in `references/review-loop.md`:
- **Normal stop (all three)**: every `[ci]` check terminal + passing; every comment reflected on with resolved ones hidden + threads resolved (only `escalate` items remain visible, each recorded for the summary comment); the merge gate is ready, so stop the monitor and proceed to Phase 5's closeout and confirmation request.
- **Hard cap (overrides the above)**: ~2h wall-clock reached. Surface the unsettled state first (which of CI/comments is still open), then stop — do NOT keep polling because CI is red or comments remain. The cap exists so a stuck PR cannot hold the watch open forever. If the cap hits with everything actually settled (CI terminal + passing, comments all reflected on), that is a closeout trigger, not a stop: proceed to Phase 5's confirmation request.

**CRITICAL: a temporarily empty comment queue is NOT a stop signal** — other agents may post more comments later.

## Phase 5: Closeout — Ceremony and Confirmed Merge

**Goal**: Once Phase 4 holds, run the closeout ceremony (summary comment + body rewrite), stop the monitor, and ask the user to confirm the merge. Full templates and ordered steps in `references/closeout.md`.

**CRITICAL constraints (hold even when detail is delegated to L3):**
1. **Arm the closeout state the moment Phase 4 holds — before anything else**: `bash <skill-dir>/scripts/arm-closeout.sh "$PR"`. This writes the repo's `.git/review-pr-closeout.json`, arming closeout enforcement: while the file exists, one turn-end per user turn is blocked when the host provides a compatible stop hook; on other hosts, enforce the same rule in-prompt. **When enforcement blocks, first verify the pending closeout is real** — a stale state file (user declined and state was not cleared, or PR merged and cleanup completed) is a false alarm: judge simple checks directly (`gh pr view --json state,mergedAt`, cleanup evidence, and the `<!-- review-pr:summary -->` marker lookup), spawn an independent subagent with clean context for complex or ambiguous situations — see `references/closeout.md` (When enforcement fires). A verified-stale state is cleared, not re-run. Clear it only after the user declines or after the confirmed merge **and required cleanup** complete — `bash <skill-dir>/scripts/clear-closeout.sh "$PR"`. A stale file blocks the next stop; its message repeats the clear path.
2. The ceremony runs automatically when Phase 4 holds: capture the summary comment URL from `gh pr comment` stdout (`SUMMARY_URL=$(gh pr comment …)`), then rewrite the body with the Review-cycle line linking that URL.
2. Stop the active monitor and present the summary, CI result, and comment-triage outcome. Ask whether to merge. Wait for explicit user confirmation; silence, a new request, or a monitor completion is not confirmation.
3. Escalate/ambiguous comments never block a user-confirmed merge; record them in the summary comment (body + author + file context + the one-line outcome).
3. The Review-cycle line in the rewritten body MUST contain that literal URL — a count with no link is not a pointer, and the quoted heredoc will not expand `$SUMMARY_URL`, so paste it.
4. Steps are ordered — the body needs the comment URL, so summary first, body second.
5. Do not sign the summary as AI-generated; body describes the change, comment records the review cycle — keep them distinct.
6. Do not run the ceremony or merge while CI is red or comments remain untriaged — the gate must hold first.
8. Only after explicit user confirmation, merge with `gh pr merge "$PR" --repo "$REPO" --merge --delete-branch` (NOT `--auto`) once CI is green AND every comment is triaged. Omit `--delete-branch` in a linked worktree; delete the remote head separately if stack-safe, then remove the linked worktree.
9. If the merge fails (branch protection, required reviews, stale base), surface the error in the conversation and leave the PR open for manual handling — do not retry with different flags or force-push.
10. Never force long-lived branch updates. After a successful confirmed merge, cleanup is mandatory before reporting success: remove the linked worktree, delete its merged local branch, switch to `main`, and fast-forward-sync `main`/`develop` with origin — see `references/closeout.md` (After a successful merge).

Stop the monitor after closeout completes.

## References

- **Runbook**: `references/runbook.md` - Phase order, inputs, absolute script paths, monitor contract, and fallback execution
- **Review Loop**: `references/review-loop.md` - Watch script, size→INTERVAL table, triage agent prompt, verdict format, lifecycle/stop conditions
- **Closeout**: `references/closeout.md` - Summary comment, body rewrite, explicit merge confirmation, and post-merge hygiene constraints
- **Commit Standards**: `references/commit-standards.md` - Commit message format for the inline git commit rounds
- **Repository Templates**: `references/repository-templates.md` - Contributing guidelines conformance for fixes
- **Examples**: `references/examples.md` - Commit message examples
