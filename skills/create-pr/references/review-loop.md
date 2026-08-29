# Review Loop: Watch, Triage, Auto-Fix

A single bash script (`scripts/review-loop.sh`) drives the watch: it emits one tagged
stdout line per new event for BOTH CI checks and PR comments. Start each one-shot poll
with Pi's `monitor_start` tool, which returns its terminal result to the next turn. The
script is a plain executable emitting lines on stdout. Do not block on a manual `while
true` loop.

## Poll interval by PR size

Review comments on a PR typically come from **other agents** (automated linters, code-review
bots) and human reviewers. They arrive on no fixed schedule, so pick a poll interval matched
to the PR's size and pass it as `INTERVAL` (in seconds) to the script below.

| PR size | Lines changed (additions+deletions) | INTERVAL |
|---|---|---|
| Small | < 200 | 180 (3 min) |
| Medium | 200–1000 | 300 (5 min, recommended default) |
| Large | > 1000 | 480 (8 min) |

- Never poll faster than once per minute.
- Cap the total watch at ~2 hours (7200 s). After that, surface to the user that the PR is
  still unsettled rather than polling indefinitely.

Read size via `gh pr view <PR> --repo <REPO> --json additions,deletions` and pick the row.

## Start one Monitor for CI and Comments

Use one Pi `monitor_start` invocation per poll. The script below emits:

- `[ci] <name>: <bucket>` once per check reaching a terminal bucket (pass/fail/cancel/skipping)
- `[comment] issue node=<id> id=<n> @<user>: <body>` for new issue-level comments
- `[comment] inline node=<id> id=<n> @<user> <path>:<line>: <body>` for new inline review comments
- `[comment] review node=<id> id=<n> @<user> [<STATE>]: <body>` for new review summaries (approve / request-changes / comment)

Every `[comment]` line carries two IDs so the closeout steps never need a second API fetch:
- `node=<id>` — the comment's GraphQL `node_id`, used by `minimizeComment` (hide) and to match
  review threads for `resolveReviewThread`.
- `id=<n>` — the REST numeric id, used by the `/pulls/$PR/comments/<id>/replies` endpoint to
  reply to accepted/rejected inline comments. (For review summaries, `id` is the review's id,
  not a comment id — it does not feed the replies endpoint.)

The script lives at `<skill-dir>/scripts/review-loop.sh` (executable, `#!/usr/bin/env bash`). The skill runs in the PR's repository cwd, not the skill dir, so the bare path `scripts/review-loop.sh` does NOT resolve — always address the script by its absolute skill path.
Run it — it reads `PR`, `REPO`, and `INTERVAL` from env
(or `--pr`/`--repo`/`--interval` flags) and emits the tagged lines above.

```bash
# `monitor_start` command for one poll. Its result_pattern is
# __REVIEW_POLL__ (?<json>\{.*\}) and failure_pattern is
# __REVIEW_POLL_FAILED__ (?<json>\{.*\}).
# Capture stdout and embed every event line inside the sentinel JSON: such monitors
# surface only the matched result line, so events printed before it are dropped.
out=$(PR=<pr-number> REPO=<owner>/<repo> INTERVAL=<sec> bash <skill-dir>/scripts/review-loop.sh --once); rc=$?
payload=$(printf '%s\n' "$out" | jq -Rsc 'split("\n") | map(select(length > 0))')
if [ "$rc" -eq 0 ]; then
  printf '__REVIEW_POLL__ {"status":"ok","events":%s}\n' "$payload"
else
  printf '__REVIEW_POLL_FAILED__ {"status":"failed","exitCode":%s,"events":%s}\n' "$rc" "$payload"
  exit "$rc"
fi

```

Pass the wrapper above as `monitor_start.command`, parse every `events` entry from the
returned JSON, then invoke the next one-shot monitor only while the PR needs watching.
Stop scheduling monitors when the PR is settled — never leave a monitor running.

## Excluding already-triaged comments on restart

Every monitor run seeds `since` to the PR's creation time, so poll 1 re-surfaces the
ENTIRE comment history — including comments a previous watch run already triaged.
When restarting a watch mid-PR, pass the already-handled node ids so they are not
re-notified:

```bash
# ACK env: space-separated node ids acknowledged after triage. EXCLUDE is retained
# as an input alias for callers that already use it; both are persisted as ACKs.
PR=<n> REPO=<owner>/<repo> INTERVAL=<sec> \
  ACK="<handled-node-id> <handled-node-id>" \
  bash <skill-dir>/scripts/review-loop.sh --once
```

**CRITICAL: never filter the script's stdout through a `grep -v` / `sed` / `awk`
chain to drop handled comments.** Those tools block-buffer when their stdout is a
pipe, so every event — including later ones — stalls inside the filter's buffer
until ~4 KB accumulates or the pipeline exits: a streaming background monitor
delivers nothing until then. Observed live: a watch piped through `grep -v
node=...` delivered no events for 20+ minutes while a new reviewer comment had
already been emitted. (The re-entrant `--once` mode is unaffected — the buffer
flushes at exit before the output is read.) Exclusion is built into the script
for exactly this reason. If a downstream filter is ever truly unavoidable, make
it line-buffered (`grep --line-buffered`).

Behavior notes:
- `since` is seeded to the PR's **creation time** (not launch time), so comments posted
  before the skill started are surfaced on poll 1. It advances to `now` after each poll.
- Comments dedup client-side by `node_id` (GitHub's `?since=` is inclusive, so a comment
  posted in the boundary second could otherwise re-emit).
- Reviews are fetched without a `submitted_at` filter and deduped by `node_id` — the old
  client-side `submitted_at > since` string compare dropped reviews posted in the launch
  second.
- `|| true` / `2>/dev/null` on every API call keeps one transient failure from killing
  the watch; `INTERVAL` is floored at 60s.

Start one `monitor_start` `--once` poll with the unique terminal sentinel. After
processing that result, start the next poll in a new `monitor_start` invocation.
The script persists its cursor, emitted and acknowledged comment IDs, latest CI buckets,
head SHA, and deadline at the Git worktree path `review-pr-watch-<PR>.json` (override with
`STATE_FILE`); this path is safe for normal and linked worktrees. A restart resumes that
state instead of replaying the PR history. Stop scheduling polls when the PR is settled or
the deadline is reached — never leave a monitor running after stop.

## You do not have to adopt review comments

**CRITICAL**: Comments arriving on the PR are mostly from **other agents** and human
reviewers, not from you. They are suggestions to *consider*, not orders to apply. Default
to skepticism: verify each claim against the diff, and adopt only the comments that are
demonstrably correct and safe. Rejecting a comment (with a one-line reason) is the correct
and expected outcome for noise, false positives, or context misunderstandings.

The watch ends only when **every** comment received so far has been reflected on (triaged,
replied to, or fixed) and none remain worth adopting — not merely when the comment queue is
temporarily empty. Other agents may post more comments later.

## Baseline review agent

The skill's Phase 1 baseline review runs in an independent agent — the main context
authored the PR (or is otherwise biased) and should not judge it directly. The baseline
agent uses the same skeptical standard as the triage agent: it flags what is wrong or
unsafe, not every stylistic nit.

```bash
gh pr diff <PR> --repo <REPO>
```

**Baseline review agent prompt template:**

```
You are a skeptical code reviewer doing the baseline review of a pull request.
You did NOT write this code; you have no attachment to it.

Context:
- PR title/body: <paste from gh pr view>
- PR diff: <paste from gh pr diff>

Find real problems only — bugs, incorrectness, unsafe changes, missing edge
cases, clear violations of the project's documented conventions. Skip style
nits, naming preferences, and speculative improvements.

For each issue, return one line: `<path>:<line>: <issue>`
If the PR is clean, return `PASS`.
```

The findings are the **first `[comment]` batch** and go through the Phase 3 triage flow —
including the baseline agent's own claims — so a wrong or overzealous baseline finding is
rejected like any other comment.

## Reacting to Events

Each emitted line is a notification. Keep the Monitor running while you act, so apply
fixes, push, and let the same monitor re-emit the resulting CI lines.

### `[ci]` failure

```bash
gh run view <run-id> --log-failed          # failed step logs
gh run list --branch <branch> --json status,conclusion,name,databaseId
```

| Failure Type | Signal | Action |
|---|---|---|
| Lint error | `eslint`, `ruff`, `biome` non-zero | Run formatter/linter, commit, push |
| Type error | `tsc`, `mypy` non-zero | Read error, apply type fix, push |
| Test failure | `jest`, `pytest` output `FAIL` | Fix code or update test, push |
| Build error | `npm run build`, `cargo build` fails | Fix import/config, push |
| Format drift | `prettier --check`, `black --check` fails | Run formatter, commit, push |

Stop and report (do NOT auto-fix) for: permission/auth (`403`, `401`, `token expired`),
missing secret (`secret not found`, `env var missing`), flaky test (passes on retry),
infrastructure (`timeout`, `OOM`, `runner unavailable`).

### `[comment]` batch — spawn independent triage agent

**CRITICAL: Never evaluate comments in the main conversation.** The main loop authored the PR and is biased — it will either defensively reject criticism or over-correct to please reviewers. Both failure modes are harmful. Instead, spawn an **independent review-triage agent** with a clean context.

**Why independent evaluation:**
- The PR author context rationalizes ("this is intentional") or capitulates ("the reviewer must be right")
- A fresh agent reads the diff and comment without sunk-cost bias
- The comments mostly come from **other agents** (linters, code-review bots) and human reviewers — they can be wrong, overzealous, or misunderstand context. Only ~40-60% of automated review comments are actually valid in practice
- The triage agent's job is to be a **skeptical gatekeeper**, not a fix applicator. Not adopting a comment is a normal, correct outcome.

**Triage agent prompt template:**

```
You are a skeptical code reviewer evaluating PR comments on behalf of the PR author.
You did NOT write this code. You have no attachment to it.

The comments below come from OTHER agents (automated linters, code-review bots) and
human reviewers. They are suggestions to CONSIDER, not orders to apply. Default to
skepticism — most automated review comments are noise, false positives, or context
misunderstandings. You do NOT have to adopt them.

Your job: for each comment below, independently verify whether it is correct and
worth applying. Rejecting a comment (with a one-line reason) is the expected outcome
for anything that is wrong, overzealous, or would harm the code.

Context:
- PR diff: <paste relevant diff sections via `git diff main...HEAD -- <files>`>
- Comments to evaluate: <paste all [comment] lines from this batch>

For EACH comment, return one of:
- `fix` — the claim is verified correct AND the suggested fix is safe to apply
- `reject <reason>` — the claim is wrong, overzealous, or the fix would be harmful
- `escalate` — design disagreement, scope change, or needs human judgment

Evaluation criteria (ALL must be true for `fix`):
1. Points to a specific file/line or names a concrete change
2. The claim is actually correct when you read the diff (verify it!)
3. The fix does not change behavior or API surface
4. The fix would not introduce worse problems than it solves
5. Consistent with the surrounding code style and project conventions

Common reasons to REJECT:
- Comment says "use const not let" but the variable IS reassigned
- Comment says "add a test" for internal implementation detail
- Comment says "remove this comment" but it explains non-obvious logic
- Comment enforces a style preference that conflicts with project conventions
- Comment misunderstands the code's purpose or context
- Comment is a generic linter false-positive (unused variable that IS used downstream)
- Comment is from an automated bot applying a generic rule that does not fit this code

Be terse. One line per comment, verdict first.
```

**Verdict format (one line per comment):**
```
<comment-id or file:line>: fix
<comment-id or file:line>: reject <one-line reason>
<comment-id or file:line>: escalate
```

**After the triage agent returns:**
1. Parse verdicts — apply ONLY `fix` verdicts
2. Reply to each `reject` comment explaining why it was declined
3. Record each `escalate` verdict (comment body + author + file context) for the closeout
   summary comment — they are documented in the summary, never asked about and never
   blocking.
4. Commit and push all `fix` changes together in one round
5. **Close out resolved comments** — for each comment that is now fully addressed (a `fix`
   that you applied and pushed, OR a `reject` you replied to with a reason), hide it as
   `OUTDATED` and resolve its thread. This keeps the PR review clean: only genuinely open
   comments stay visible. See "Closing out resolved comments" below for the exact commands.
   `escalate` comments stay open; each one is recorded for the closeout summary.

Apply the validated fixes, commit and push them via inline git commands (`git add`, `git commit`, `git push`), then acknowledge each. **The reply endpoint depends on comment type** — the `/pulls/$PR/comments/<id>/replies` endpoint ONLY accepts inline review-comment ids; using it for an issue-level comment or a review summary hits the wrong resource and fails:

```bash
# Reply to an accepted/rejected INLINE review comment (id=<n> from the emitted line).
gh api repos/$REPO/pulls/$PR/comments/<comment-id>/replies -f body="Fixed in <commit-sha>."     # accepted
gh api repos/$REPO/pulls/$PR/comments/<comment-id>/replies -f body="<rejection reason>"        # rejected

# Reply to an ISSUE-LEVEL comment — there is no reply endpoint; post a new PR
# issue comment (the `id=<n>` from the emitted line can be referenced in the body
# but is not used in the URL).
gh pr comment "$PR" --repo "$REPO" --body="Re: <rejection reason or fix summary>"

# REVIEW SUMMARIES have no reply endpoint at all — skip the reply. If a summary
# raises a point worth addressing, reply to its inline sub-comments (handled as
# inline above) or post a single summary issue comment via `gh pr comment`.
```

### Closing out resolved comments

When a comment is fully addressed (fixed-and-pushed, or rejected with a reply), hide and
resolve it so the PR review only shows what is still open. Both use GraphQL via `gh api graphql`,
keyed on the comment's `node_id` (GitHub's `node_id`, NOT the REST numeric id).

**Minimize (hide) a comment** — works on issue-level AND inline review comments:

```bash
# $NODE_ID = the comment's node_id (from .node_id in the REST responses above)
gh api graphql -f query="mutation { minimizeComment(input: {subjectId: \"$NODE_ID\", classifier: OUTDATED}) { minimizedComment { isMinimized } } }"
```

**Resolve an inline review comment's thread** — inline comments only; issue-level comments
have no thread. Resolving requires the **thread node ID**, which is NOT the comment node_id.
Resolve only the thread containing each *top-level* inline comment you addressed (skip reply
comments — their thread is the parent's). Look up the thread IDs once per PR, then resolve:

```bash
# 1. Fetch every review thread with its node ID, line, path, and the first comment's
#    GraphQL `id` — which equals the REST `node_id` you just triaged on, so you can match
#    each thread to the comment node_ids from the [comment] batch. Loop on the cursor:
#    `first:100` alone would truncate at 100 threads (bot-heavy PRs can exceed that),
#    leaving addressed comments beyond the first page unresolvable.
threads=""
cursor=""
while :; do
  page=$(gh api graphql -f query='query($pr:Int!, $owner:String!, $name:String!, $c:String!) {
    repository(owner:$owner, name:$name) {
      pullRequest(number:$pr) {
        reviewThreads(first:100, after:$c) {
          nodes { id isResolved line path comments(first:1) { nodes { id fullDatabaseId } } }
          pageInfo { hasNextPage endCursor }
        }
      }
    }
  }' -F owner="${REPO%/*}" -F name="${REPO#*/}" -F pr="$PR" -F c="$cursor" 2>/dev/null || true)
  [ -z "$page" ] && break
  threads="$threads$(printf '%s' "$page" | jq -c '.data.repository.pullRequest.reviewThreads.nodes[]')"
  has_next=$(printf '%s' "$page" | jq -r '.data.repository.pullRequest.reviewThreads.pageInfo.hasNextPage')
  [ "$has_next" = "true" ] && cursor=$(printf '%s' "$page" | jq -r '.data.repository.pullRequest.reviewThreads.pageInfo.endCursor') || break
done
# `threads` now holds one JSON thread object per line; match by comments[0].id (== node_id).
# 2. For each thread whose first comment you fully addressed, resolve it:
gh api graphql -f query="mutation { resolveReviewThread(input: {threadId: \"$THREAD_ID\"}) { thread { isResolved } } }"
```

Order per comment: for inline comments, reply first, then resolve the thread, then minimize
the comment (minimize-after-resolve is fine; minimizing a comment does not resolve its thread).
For issue-level comments, reply then minimize (no thread to resolve). Do NOT hide or resolve
`escalate` comments — they stay open, and each is recorded for the closeout summary comment.

### `[comment]` ambiguous — record and defer

Ambiguous when ANY are true: questions a design decision; requests a scope change or new
feature; unclear intent; needs business context not in the diff; multiple valid readings.

Examples: "Why not use X instead of Y?", "This feels over-engineered",
"Can we also handle Z?", "I'm not sure this is the right approach".

For these: do not guess, reply, or hide. Post a one-line reply stating the point is deferred
(via the comment-type-appropriate reply endpoint above), record the comment (body + author +
file context) for the closeout summary comment, and continue. Never notify the user and wait
— the pipeline never pauses for user input.

## Lifecycle

- The monitor runs across turns; you keep working and react as lines arrive.
- A pushed fix triggers a fresh CI run that the same monitor re-emits — no need to relaunch it.
- A temporarily empty comment queue is NOT a stop signal — other agents may post more
  comments later. Keep the monitor running.
- Stop the monitor when EITHER holds:
  - **Normal stop (all three must hold)**:
    1. Every `[ci]` check is terminal AND passing.
    2. Every review comment received so far has been reflected on (triaged, replied to,
       or fixed) AND every fully-resolved one is hidden + its thread resolved. The only
       comments left visible on the PR are unresolved `escalate` items, each recorded for
       the closeout summary comment.
    3. The closeout summary and PR body are complete; the monitor is stopped while the
       workflow waits for the user's explicit merge confirmation.
  - **Hard cap (overrides the above)**: the ~2-hour max wall-clock is reached. Surface the
    unsettled state in the conversation first (state which of #1/#2 is still open), then
    stop — do NOT keep polling just because CI is still red or comments remain. The cap
    exists so a stuck PR (red CI the skill correctly won't auto-fix) cannot hold the watch
    open forever.
- Monitoring runs automatically. Once closeout is ready, stop monitoring and wait only
  for the user's explicit merge confirmation; never auto-merge.
