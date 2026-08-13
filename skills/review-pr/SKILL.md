---
name: review-pr
description: 'Reviews a pull request: runs its own baseline review of the PR diff, then a persistent watch polls CI and incoming reviewer comments via a script, triages each comment through an independent skeptical agent, applies only verified fixes, and commits+pushes via inline git commands until CI passes and no comments remain to adopt — then runs the closeout ceremony and auto-merges. Fully automatic, no user questions. Use this skill when the user asks to "review a PR", "monitor PR review comments", "address reviewer feedback on #123", or "watch CI on a pull request".'
---

# Review a Pull Request

Run the baseline review of the PR diff, then keep a persistent watch over CI and new reviewer comments until the PR settles and auto-merges.

## Runtime notes

- **Script paths**: every `bash <skill-dir>/scripts/...` command below needs the absolute path to this skill's installed directory (e.g. `~/.agents/skills/review-pr`). Resolve it once at the start, export it as `SKILL_DIR`, and use `$SKILL_DIR/scripts/<name>.sh` everywhere. The scripts live in this skill's `scripts/`, never in the repository you are working in.
- **Watch (monitor)**: the CI + comment watch is `scripts/review-loop.sh`, run under the runtime's generic monitor (e.g. pi's `monitor_start`) so each emitted line arrives as a monitor notification across turns; on runtimes without a monitor, run it with `--once` once per turn (it emits one tagged line per new event), re-enter across turns, and stop once the stop conditions hold. Never use a blocking foreground `while` loop.
- **Tool mapping**: independent review/triage -> spawn a clean-context subagent (or route the script's output through an independent agent); notifying the user -> report in the conversation; stopping the watch -> stop the monitor task or stop re-invoking. The workflow is tool-agnostic. **The pipeline never asks the user for a decision** — everything from baseline review through merge runs automatically.
- **Closeout enforcement**: the closeout state (`arm-closeout.sh`/`clear-closeout.sh` + `.git/review-pr-closeout.json`) is enforced by `scripts/closeout-stop.sh` on runtimes with stop hooks, and in-prompt on others: arm the state the moment Phase 4 holds, run the automatic closeout (summary comment + body rewrite + auto-merge), clear the state when the merge completes or aborts — never end the turn while the state is armed. Never ask the user whether to merge; never pause the pipeline for user input.

## Context


- PR argument: `$ARGUMENTS`
- PR metadata: !`gh pr view "$ARGUMENTS" --json number,title,headRepository,headRepositoryOwner,additions,deletions,headRefName 2>/dev/null || printf 'set %s to a PR number or URL\n' "$ARGUMENTS"`
- Remote: !`git remote -v 2>/dev/null | head -2`
- Auth: !`gh auth status 2>&1 | head -3`

## Phase 1: Baseline Review and Sizing

**Goal**: Run the initial review, resolve the repo, and pick a poll interval sized to the PR.

**Actions**:
1. Parse the PR number or URL from `$ARGUMENTS`. If absent, resolve the PR automatically: the current branch's open PR via `gh pr view --json number -q .number` (falls back to the branch's head PR), else the most recently updated open PR via `gh pr list --state open --json number,updatedAt --limit 1` — never ask the user which PR to review. **Normalize `PR` to the bare number** before any `gh api` REST call: `gh pr *` commands accept a URL, but `gh api repos/$REPO/issues/$PR/...` interpolates `$PR` into the URL path and breaks on a full URL — run `PR=$(gh pr view "$ARGUMENTS" --json number -q .number)` (the Context block already fetches `--json number`) and use `$PR` as the number everywhere downstream.
2. **Run the baseline review** — spawn an independent review agent with clean context (it did not author the code) to review the PR diff. Pull the diff with `gh pr diff <PR>`; pass the agent the PR title/body and the diff, and ask for findings as `path:line: issue` lines (full prompt in `references/review-loop.md`, Baseline review agent). Treat its findings as the **first `[comment]` batch** — feed them straight into the Phase 3 triage flow before launching the watch. Do not act on them inline; the main context is biased (it likely authored the PR) and the same skeptical gatekeeping must apply to the baseline as to live comments.
3. Resolve `REPO=<owner>/<repo>` from the PR metadata above (fallback: `git remote get-url origin` parsed into `owner/repo`).
4. Read PR size from `additions+deletions` and pick `INTERVAL` (seconds) from the size table in `references/review-loop.md`: 180 / 300 / 480 for small / medium / large; floor 60s, cap 7200s (~2h).

## Phase 2: Launch the Persistent Watch

**Goal**: One background watch streaming CI + comment events across turns.

**Action**: Launch `scripts/review-loop.sh` as a monitor (runtimes with a generic monitor
such as pi's `monitor_start`), or run it with `--once` once per turn on runtimes without one. The
bare path `scripts/review-loop.sh` does NOT resolve — the skill runs in the PR's repository
cwd, not the skill dir, so the script must be addressed by its absolute skill path. Pass
`PR`, `REPO`, and `INTERVAL` as env vars (the script also accepts
`--pr`/`--repo`/`--interval`). Use a specific watch description like
`"CI + new comments on PR #<n> (<m> poll)"`. Do NOT run a foreground `while` loop. The
script is documented in `references/review-loop.md`.

**CRITICAL: Do NOT skip the watch based on a launch-time snapshot.** "This repo has no CI workflow, so the watch would spin idly" is a **false** inference and not a valid reason to skip: CI is only one of the two things watched. Third-party auto-review services (GitHub Copilot code review, CodeRabbit, Greptile, Codex, Sourcery, and similar), org-level bots, and human reviewers post comments on no fixed schedule and are invisible in a launch-time snapshot — a repo with zero workflows can still accumulate a full review thread minutes after the PR opens. An empty `.github/workflows/` proves nothing about who will comment.

The only valid skip is a PR that is already merged or closed. If CI and reviewers both appear absent, launch the watch anyway; it costs nothing and emits nothing until something changes.

## Phase 3: React to Each Watch Event

**Goal**: Fix what is actionable, reject the noise, record the rest. Full rules, prompt template, verdict format, and reply/hide/resolve lifecycle in `references/review-loop.md`.

- `[ci] <name>: fail|cancel` → fetch logs (`gh run view <run-id> --log-failed`), apply the fix, commit+push via inline git commands (`git add <file> && git commit -m "<type>(<scope>): <summary>" && git push`). The push triggers a fresh CI run the same watch re-emits. **CRITICAL: stop and report (do NOT auto-fix) for auth/permission, missing-secret, flaky, or infrastructure failures.**
- `[comment]` batch → **CRITICAL: spawn an independent review-triage agent with clean context.** Apply ONLY the `fix` verdicts; reject/escalate the rest. **CRITICAL: reply by comment type** — inline review comment → `gh api repos/$REPO/pulls/$PR/comments/<id>/replies`; issue-level comment → `gh pr comment` (no reply endpoint); review summary → skip reply. Use the `id=<n>`/`node=<id>` tokens from each emitted line. Commit+push all `fix` changes in one round; then hide each fully-addressed comment (`fix` pushed or `reject` replied) as `OUTDATED` via `minimizeComment` and resolve its thread via `resolveReviewThread` (inline only). Leave `escalate` comments open; record each one (body + author + file context) for the closeout summary comment — they are documented, never asked about.
- `[comment]` ambiguous (design disagreement, scope change, unclear intent) → do not guess, reply, or hide. Reply with a one-line `reject`-style note stating the point is deferred, and record it (body + author + file context) for the closeout summary comment. Never notify the user and wait.

**CRITICAL mindset**: Comments are mostly from other agents (linters, code-review bots) and human reviewers — suggestions to *consider*, not orders. Default to skepticism; verify each claim against the diff and adopt only what is demonstrably correct and safe. Rejecting a comment is the normal outcome for noise and false positives.

## Phase 4: Stop Conditions

Stop the watch when EITHER holds — full conditions in `references/review-loop.md`:
- **Normal stop (all three)**: every `[ci]` check terminal + passing; every comment reflected on with resolved ones hidden + threads resolved (only `escalate` items remain visible, each recorded for the summary comment); the pipeline has run to completion.
- **Hard cap (overrides the above)**: ~2h wall-clock reached. Surface the unsettled state first (which of CI/comments is still open), then stop — do NOT keep polling because CI is red or comments remain. The cap exists so a stuck PR cannot hold the watch open forever. If the cap hits with everything actually settled (CI terminal + passing, comments all reflected on), that is a closeout trigger, not a stop: proceed to Phase 5's auto-merge.

**CRITICAL: a temporarily empty comment queue is NOT a stop signal** — other agents may post more comments later.

## Phase 5: Closeout — Ceremony and Auto-Merge

**Goal**: Once Phase 4 holds, run the closeout ceremony (summary comment + body rewrite) and auto-merge — with no user question. Full templates and ordered steps in `references/closeout.md`.

**CRITICAL constraints (hold even when detail is delegated to L3):**
1. **Arm the closeout state the moment Phase 4 holds — before anything else**: `bash <skill-dir>/scripts/arm-closeout.sh "$PR"`. This writes the repo's `.git/review-pr-closeout.json`, arming closeout enforcement: while the file exists, one turn-end per user turn is blocked (mechanically by `scripts/closeout-stop.sh` on stop-hook runtimes, in-prompt otherwise) naming the pending closeout — the automatic ceremony cannot be skipped by a premature stop. **When enforcement blocks, first verify the pending closeout is real** — a stale state file (summary posted, PR merged without clearing) is a false alarm: judge simple checks directly (`gh pr view --json state,mergedAt`, the `<!-- review-pr:summary -->` marker lookup), spawn an independent subagent with clean context for complex or ambiguous situations — see `references/closeout.md` (When enforcement fires). A verified-stale state is cleared, not re-run. Clear it the moment the closeout is resolved — `bash <skill-dir>/scripts/clear-closeout.sh "$PR"`: after the auto-merge completes or aborts. A stale file blocks the next stop; its message repeats the clear path.
2. The ceremony runs automatically the moment Phase 4 holds: capture the summary comment URL from `gh pr comment` stdout (`SUMMARY_URL=$(gh pr comment …)`), then rewrite the body with the Review-cycle line linking that URL.
2. Escalate/ambiguous comments never block the merge and never trigger a question — they are recorded in the summary comment (body + author + file context + the one-line outcome) and the merge proceeds.
3. The Review-cycle line in the rewritten body MUST contain that literal URL — a count with no link is not a pointer, and the quoted heredoc will not expand `$SUMMARY_URL`, so paste it.
4. Steps are ordered — the body needs the comment URL, so summary first, body second.
5. Do not sign the summary as AI-generated; body describes the change, comment records the review cycle — keep them distinct.
6. Do not run the ceremony or merge while CI is red or comments remain untriaged — the gate must hold first.
7. Auto-merge with `gh pr merge "$PR" --repo "$REPO" --merge --delete-branch` (NOT `--auto`) once CI is green AND every comment is triaged. Omit `--delete-branch` in a linked worktree; delete the remote head separately if stack-safe, leave the local branch for the worktree removal.
8. If the merge fails (branch protection, required reviews, stale base), surface the error in the conversation, stop the watch, and leave the PR open for manual handling — do not retry with different flags, do not force-push.
9. Never force long-lived branch updates; `--delete-branch` is the default (omitted only in linked worktrees). Post-merge hygiene runs unconditionally: remove the linked worktree (`git worktree remove <path>`), switch to `main`, and fast-forward-sync `main`/`develop` with origin — see `references/closeout.md` (After a successful merge).

Stop the watch after closeout completes.

## References

- **Review Loop**: `references/review-loop.md` - Watch script, size→INTERVAL table, triage agent prompt, verdict format, lifecycle/stop conditions
- **Closeout**: `references/closeout.md` - Summary comment, body rewrite, auto-merge, post-merge hygiene constraints
- **Commit Standards**: `references/commit-standards.md` - Commit message format for the inline git commit rounds
- **Repository Templates**: `references/repository-templates.md` - Contributing guidelines conformance for fixes
- **Examples**: `references/examples.md` - Commit message examples
