# Closeout: Ceremony and Confirmed Merge

## Contents

Find the relevant section by heading:

- Merge gate — must hold before anything else
- The ceremony
- Confirmation and merge
- After a successful merge
- Stacked / chained PRs (base branch is a shared dependency)
- Order and idempotency
- Do not

Once the PR is merge-ready (all `[ci]` checks terminal and passing, every comment either
fixed, rejected-with-reply, or explicitly accepted/deferred under the gate below, and resolved comments hidden +
their threads resolved), run the closeout ceremony and ask the user to confirm the merge.
Do not merge unless the user gives explicit confirmation.

## Merge gate — must hold before anything else

The closeout runs only when the Phase 4 gate holds:

1. Every `[ci]` check is terminal AND passing.
2. Every comment is reflected on: `fix` pushed, `reject` replied, resolved ones hidden +
   threads resolved. Record each escalation's body, author, context, and decision.
3. Resolve escalations affecting correctness, authorization, scope, or a repository merge
   requirement before declaring readiness. Ask for the missing decision while continuing
   independent work. Optional suggestions may remain open when explicitly deferred by
   the user or permitted by repository policy; document that decision.

Escalate/ambiguous comments remain visible until resolved. Documentation alone does not
resolve a material issue or supply approval. Apply repository policy and the user's actual
decision, and include accepted limitations in the concrete merge proposal. A merge still requires explicit user confirmation, and a merge
failure or hard-cap stop leaves the PR open.

### Arm the closeout state first

The moment the Phase 4 gate holds, arm the closeout state **before anything else**:

```bash
bash <skill-dir>/scripts/arm-closeout.sh "$PR"
```

Arming writes `.git/review-pr-closeout.json` (resolved via `git rev-parse --git-dir`, so it
works from any cwd in the repo). On compatible stop-hook runtimes,
`scripts/closeout-stop.sh` emits at most one reminder per turn for unfinished preparation.
After presenting the concrete merge question, mark the state as awaiting confirmation:

```bash
bash <skill-dir>/scripts/arm-closeout.sh "$PR" --awaiting-confirmation
```

This permits yielding for the user's reply while preserving the pending decision. On
runtimes without hooks, track the same state in the task. Never invent a hook or keep
working around a required human decision. A state file is not merge authorization.

Clear it the moment the closeout is resolved:

```bash
bash <skill-dir>/scripts/clear-closeout.sh "$PR"
```

Clear after the user declines, after a merge failure or abort, after the gate no longer
holds, or after a confirmed merge **and all required cleanup** complete. Leaving it armed
blocks the next stop; the enforcement message repeats the clear path as the escape hatch. The clear script only removes state matching `$PR`, so an
interrupted closeout for one PR never deletes a pending one for another.

### When enforcement fires: verify the problem is real

Enforcement blocks on the state file alone — it cannot know whether the closeout was
already resolved and the clear step was simply missed. That happens after an interrupt (the
closeout ran, then the turn died before the clear), a resumed session, a summary already
posted, or a merge that already landed. So before acting on a block, **verify the pending
closeout actually exists**:

- **Simple checks — judge directly.** e.g. `gh pr view "$PR" --repo "$REPO" --json state,mergedAt`
  (a MERGED PR means the merge landed; verify authorized cleanup separately), or the
  `<!-- review-pr:summary -->` marker lookup (a posted summary means the ceremony already
  ran).
- **Complex or ambiguous situations — spawn an independent subagent with clean context.**
  e.g. reconstructing whether the ceremony ran earlier in the session, or whether the gate
  (CI green, every comment triaged) still holds after events that landed after arming. When
  the host cannot spawn a worker, re-read the state file and the `gh pr view` output
  yourself, and state that the check shared the main context.

A verified-stale state means the enforcement already did its job: clear it
(`clear-closeout.sh "$PR"`) and end the turn — do not re-run the ceremony or the merge. A
verified-real state: proceed with the closeout as below.

## The ceremony

The PR page should read as an accurate, self-contained record of the change: a summary
comment in the user's voice recording the review cycle, and a rewritten title/body
describing what is actually being merged.

### What the summary must cover

1. **What was changed** — the substantive code/config changes across the review cycle
   (each `fix` round, summarized by commit). Not a git-log dump: group related commits and
   say what each group accomplished and why.
2. **What review surfaced and what was done about it** — for each comment batch, the
   outcome: adopted (with the fix), rejected (with the one-line reason), or escalated
   (and how it was resolved or deferred). This is the audit trail a reader needs to trust
   the merge.

Write it in the user's voice and first person ("I changed…", "Review flagged…, I fixed…").
No emojis, no marketing tone. Terse but complete.

### Write the summary comment

The body opens with the marker `<!-- review-pr:summary -->`. GitHub renders HTML comments as
nothing, and it makes the summary findable later without guessing which comment it was.

`gh pr comment` prints the new comment's URL on stdout — capture it. The PR body's Review-cycle
line links to that URL, which is why the comment must be posted *before* the body is rewritten.

```bash
SUMMARY_URL=$(gh pr comment "$PR" --repo "$REPO" --body-file - <<'EOF'
<!-- review-pr:summary -->
Summary of the review cycle on this PR.

## Changes made
- <group 1: what changed and why, in one or two lines>
- <group 2: ...>

## Review findings and resolution
- <Adopted> @<reviewer> on <path>:<line> — <what the comment was> → fixed in <sha>.
- <Rejected> @<reviewer> on <path>:<line> — <comment> → declined: <one-line reason>.
- <Escalated> @<reviewer> — <comment> → deferred: <one-line outcome>.

All CI checks are green and no comments remain worth adopting. This PR is ready to merge.
EOF
)
```

`--body-file -` reads the heredoc from stdin, so multi-line bodies (and the user's actual
commit/review data pasted into the placeholders) work without shell-escaping pain. Replace
the placeholders with the real data gathered during Phases 1–4 before running.

#### Updating an existing summary

If a summary was already posted (a resumed session, a re-run after an interrupt), edit that
comment in place rather than posting a duplicate. Do NOT use `gh pr comment --edit-last`: it
edits your *most recent* comment on the PR, which may be a Phase 3 reject reply rather than
the summary, and overwrites it. Look the summary up by its marker and patch that exact id:

```bash
# `--paginate` runs the jq filter per page, so `.[] | select(...)` sees every page.
SUMMARY_ID=$(gh api --paginate "repos/$REPO/issues/$PR/comments" \
  --jq '.[] | select(.body | startswith("<!-- review-pr:summary -->")) | .id' | head -1)

# An empty SUMMARY_ID means no summary exists yet — post one with the block above instead.
SUMMARY_URL=$(gh api --method PATCH "repos/$REPO/issues/comments/$SUMMARY_ID" \
  -F body=@- --jq .html_url <<'EOF'
<!-- review-pr:summary -->
...same template, updated...
EOF
)
```

`-F body=@-` sends stdin verbatim as a string: the `@` prefix short-circuits gh's type coercion
and its `{owner}`/`{repo}`/`{branch}` placeholder expansion, so markdown passes through intact.

### Rewrite the PR title and body

The original PR title/body were written before the review cycle; by closeout the change may
have shifted scope, merged batches, or dropped approaches. Rewrite both so the PR page reads
as an accurate, self-contained description of what is actually being merged.

```bash
# Body is always rewritten. Title is rewritten ONLY if the current one no longer matches
# the merged change (see Title guidance below); drop --title when the title is already
# accurate.
gh pr edit "$PR" --repo "$REPO" \
  --title "<imperative, lowercase, conventional-commits if the repo uses them>" \
  --body-file - <<'EOF'
## What
<one-paragraph statement of what this PR changes>

## Why
<the problem or motivation; link issues if any>

## Changes
- <logical change 1>
- <logical change 2>

## Review cycle
<N> comments triaged over <R> rounds, <M> adopted, <K> rejected; all CI green.
Full breakdown: <paste $SUMMARY_URL here, e.g. https://github.com/owner/repo/pull/4#issuecomment-4930992385>

## Verification
- <test commands run and their results>
- <manual checks performed>
EOF
```

**The Review-cycle line MUST carry the summary comment's URL.** A count with no link is not a
pointer — the whole point is that a reader landing on the PR can reach the audit trail in one
click. The heredoc is quoted (`<<'EOF'`), so `$SUMMARY_URL` will NOT expand inside it: read the
URL that the previous command printed and paste it as a literal. Do not switch to an unquoted
heredoc to interpolate it — PR bodies contain backticks and `$` in code references, and an
unquoted heredoc would run them as command substitution.

#### Title guidance

Rewrite the title only when the current one no longer matches the merged change (scope
drifted, the feature was renamed, the original was a WIP stub). If the title is already
accurate, leave it — **drop the `--title` flag from the command above and just rewrite the
body**; do not churn the title for style. When rewriting:
- Imperative mood, lowercase, under ~70 chars.
- Match the repo's conventions (conventional-commits prefix like `feat(scope):` if the
  repo's history uses it; plain imperative otherwise).
- The PR title does not need the commit-message body rules — it is a UI title, not a commit.

#### Body guidance

The body is the durable record. Lead with **What** and **Why** (a reviewer who never read
the comments should understand the PR from the body alone), then **Changes** (the logical
units, not commit-by-commit), then a one-line **Review cycle** pointer *linking to the summary
comment*, then **Verification** (real commands + results, not claims). Keep it scannable —
headings and bullets, not prose walls.

The pointer is what makes the pair work: the body stays short and describes the merged change,
the linked comment holds the full comment-by-comment audit trail, and neither repeats the other.

## Confirmation and merge

Run the ceremony first so the PR record is ready for review. Keep the watch armed, present
the summary URL, verified CI/review state, any accepted limitations, merge strategy, and
the exact optional cleanup targets. Request explicit user confirmation after preparation.
Reuse an existing authorization for this same reviewed merge; do not ask again.

A bare authorization to merge does not authorize deleting unrelated branches or worktrees.
Include any desired deletion of this PR's head or pre-existing checkout in the concrete
proposal, or leave it in place. Check downstream PR dependencies before proposing deletion.

Mark the pending question with `arm-closeout.sh "$PR" --awaiting-confirmation` and yield.
After confirmation, run `arm-closeout.sh "$PR"` to leave awaiting-confirmation state and
rearm the pending-operation reminder, then recheck the current head, CI, and review gate. If new changes invalidate
the approved result, complete review again and obtain the missing authorization.

For the skill's default merge strategy, subject to the repository and user requirements:

```bash
gh pr merge "$PR" --repo "$REPO" --merge
```

Use `--delete-branch` only when that exact deletion was authorized, is stack-safe, and the
host can safely handle the local checkout. In a linked worktree, handle the head/worktree
separately after merge. Never enable `--auto` or bypass branch protections.

If merge fails, surface the error, clear closeout state, stop the watch, and leave the PR
open. Do not retry with a different strategy, force-push, or repeat the ceremony to hide
the failure.

## After a successful merge

Verify the merged head is contained in the PR's actual base. Any authorized cleanup
must complete before reporting success for cleanup; distinguish a landed merge from
unfinished local cleanup.

1. Record `HEAD_BRANCH`, `BASE_BRANCH` from PR metadata, `WORKTREE_PATH`, and
   `MAIN_WORKTREE` before changing or removing the checkout. Parse worktree metadata
   without splitting paths on spaces.
2. Remove this PR's linked worktree only when it was created by this task and no longer
   needed, or its exact removal was authorized. Preserve local changes. Prefer the host's
   managed-worktree lifecycle tool for managed checkouts. For an authorized plain checkout:
   ```bash
   git -C "$MAIN_WORKTREE" worktree remove "$WORKTREE_PATH"
   cd "$MAIN_WORKTREE"
   ```
   If removal refuses, report it and preserve the checkout; never force-remove.
3. When local base synchronization is in scope, fetch only the actual base ref and
   fast-forward its clean local checkout:
   ```bash
   git fetch origin "$BASE_BRANCH"
   git checkout "$BASE_BRANCH"
   git merge --ff-only "origin/$BASE_BRANCH"
   ```
   Use the base's existing worktree if it is checked out elsewhere. If the base is missing,
   diverged, dirty, or needed by a PR stack, report the condition rather than resetting it.
4. When deletion of this PR's local branch was authorized, verify it is fully merged into
   the fetched base, is not an integration branch, and is not checked out elsewhere:
   ```bash
   git branch -d "$HEAD_BRANCH"
   ```
   Verify the ref is gone and report a refusal. Delete the exact remote head only when
   separately authorized and no dependent PR still needs it.
5. Preserve every other branch, checkout, and worktree record. Broader branch sweeps,
   `git worktree prune`, and stale-directory removal require separate explicit authorization
   with enumerated targets. Do not scan for unrelated cleanup or suggest blanket deletion.

Clear this PR's closeout state after the confirmed merge and authorized cleanup complete.
If cleanup is blocked, report the landed merge and the exact unfinished action; retain
recoverable state and do not claim cleanup succeeded.

## Stacked / chained PRs (base branch is a shared dependency)

When several PRs depend on each other — PR-B's `--base` is PR-A's head branch, not
`main` — **the base branch is a load-bearing dependency**, not a scratch branch. A
chain breaks in a specific, silent way that is easy to miss:

- PR-A merges into `main` with `--delete-branch`. Its head branch is deleted.
- PR-B (and PR-C, …) had `--base = <PR-A head branch>`. When that branch is deleted,
  GitHub auto-retargets their base to `main`, **but their merge commits were created
  against the now-deleted branch and become dangling** — the content of PR-B/C lands
  on **nothing**, and `main` advances with only PR-A's changes. The PRs show `MERGED`
  on GitHub, which is the trap: the merge state lies. The only reliable check is
  `git branch -r --contains <head-sha>` against `origin/main` — if it says no, the
  content is not on `main` despite the MERGED badge.

**Two safe patterns for a stack:**

1. **All PRs base on `main` directly** (no inter-PR base). Land them in order; each
   merge advances `main` and the next PR's base is already current. Simplest; prefer
   this unless the intermediate state is genuinely unreviewable on its own.
2. **Keep the base branch alive until every downstream PR is merged.** Merge the
   stack top-down (or in dependency order); do not delete a head that open PRs still
   base on.

If you suspect a stack already broke (PRs MERGED but content absent from `main`):
open one repair PR off `origin/main` that cherry-picks each missing head commit, and
link the dangling PRs in the body. Verify the repair with `git branch -r --contains
<sha> origin/main` before merging.

**Don't pre-announce implementation-detail strings in docs a parallel agent will
write.** When a stack splits docs (PR-E) from the code that emits a string
(PR-B), the docs author will name the string from intuition — `manual-blocks-initial`
— instead of the real `manual-skips-initial`. The review bots catch it, but it costs
a round-trip. If a downstream PR documents a value another PR produces, put the
exact literal in the upstream agent's prompt and have it referenced verbatim, or
land docs after the code PR merges so the author can grep the real value.

## Order and idempotency

1. Verify the merge gate, including material escalations.
2. Arm closeout, finish verified-comment handling, and prepare the summary/title/body.
3. Find the existing `<!-- review-pr:summary -->` marker before posting another summary;
   update that record and recover its URL after an interruption.
4. Present the concrete result, keep the watch armed, and request only missing merge/cleanup
   authorization. Mark awaiting-confirmation state and yield for the decision.
5. After confirmation, rearm with `arm-closeout.sh "$PR"`, recheck the head and gate, merge once, verify it, and complete
   only the authorized cleanup. Clear state when complete, after decline and stop-watching,
   or after merge failure. A new head or a new comment invalidates the approval: redo the
   gate before merging. Release the watch with `clear-watch.sh "$PR"` when the watch ended
   on purpose — merged, closed, stopped by the user, or past the deadline.

Resume from observed state. A summary comment proves the summary was posted, not that the
merge or cleanup occurred. A MERGED badge proves a merge event; stacked PRs still need
base/head containment verification. Never repeat an already completed mutation or ask
again for authorization that still applies to the same reviewed result.

## Do not

- Declare readiness with failed/pending required CI or a material unresolved escalation.
- Treat documenting an escalation as resolution or approval.
- End before presenting the prepared closeout, or block the turn after asking the user
  for the required decision.
- Rewrite title/body to claim behavior or checks the diff and evidence do not support.
- Duplicate the review-cycle record in the body and summary comment; link the summary.
- Edit whichever comment happened to be last; find the summary by its marker.
- Bypass protections, enable automatic merge, or change the approved strategy on failure.
- Delete unrelated branches/worktrees or discard local changes as post-merge cleanup.
- Claim that all cleanup succeeded because GitHub shows the PR as merged.
