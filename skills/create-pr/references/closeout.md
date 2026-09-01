# Closeout: Ceremony and Confirmed Merge

Once the PR is merge-ready (all `[ci]` checks terminal and passing, every comment either
fixed, rejected-with-reply, or escalated-and-documented, and resolved comments hidden +
their threads resolved), run the closeout ceremony and ask the user to confirm the merge.
Do not merge unless the user gives explicit confirmation.

## Merge gate — must hold before anything else

The closeout runs only when the Phase 4 gate holds:

1. Every `[ci]` check is terminal AND passing.
2. Every comment is reflected on: `fix` pushed, `reject` replied, resolved ones hidden +
   threads resolved. `escalate` items may remain visible, but each one is recorded (body +
   author + file context) for the summary comment — they are documented, not asked about.

Escalate/ambiguous comments never block a confirmed merge. They are recorded in the
summary comment with their one-line outcome. The only deviations are a user declining
the merge, a merge failure (surface the error, stop, leave the PR open), or a hard-cap
stop (see `review-loop.md`).

### Arm the closeout state first

The moment the Phase 4 gate holds, arm the closeout state **before anything else**:

```bash
bash <skill-dir>/scripts/arm-closeout.sh "$PR"
```

Arming writes `.git/review-pr-closeout.json` (resolved via `git rev-parse --git-dir`, so it
works from any cwd in the repo). While the file exists, the runtime must not end the turn
until the closeout is resolved. On runtimes with stop hooks, `scripts/closeout-stop.sh`
blocks one turn-end per user turn with a message naming the PR and the pending closeout;
on runtimes without hooks, the agent enforces the same rule in-prompt: never end the turn
while the state file exists — the reminder must not loop, so it fires once per turn. A
user interrupt also bypasses it — the message always names the clear script as the escape
hatch.

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
  (a MERGED PR means the closeout is done and the state is stale), or the
  `<!-- review-pr:summary -->` marker lookup (a posted summary means the ceremony already
  ran).
- **Complex or ambiguous situations — spawn an independent subagent with clean context.**
  e.g. reconstructing whether the ceremony ran earlier in the session, or whether the gate
  (CI green, every comment triaged) still holds after events that landed after arming.

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

Run the ceremony first (summary comment + body rewrite, above), so the record is on the PR
before the merge lands. Stop the monitor and present the summary URL, passing CI status, and
comment-triage outcome. Ask the user whether to merge. Only an explicit confirmation permits
the merge; if the user declines, clear closeout state and leave the PR open.

After explicit user confirmation, merge:

```bash
gh pr merge "$PR" --repo "$REPO" --merge --delete-branch
```

- `--merge` is the fixed strategy — a merge commit, never squash/rebase. Never `--auto`
  (GitHub's background auto-merge feature fires whenever it can and bypasses this gate).
- `--delete-branch` is safe only in the main worktree when no open PR still bases on that
  head. In a linked worktree, omit `--delete-branch` — delete the remote head separately if
  stack-safe. Capture the current local PR branch as `HEAD_BRANCH` before removing its
  worktree, then explicitly delete that local branch after synchronizing the base branch.
- After the confirmed merge lands, run every cleanup step below before reporting success.
- Keep closeout state armed until cleanup completes. Then clear it with
  `clear-closeout.sh "$PR"`; if cleanup fails, leave it armed and report the failure.

**If the merge fails** (branch protection, required reviews, stale base): surface the error
in the conversation, clear the closeout state (`clear-closeout.sh "$PR"`), stop the watch,
and leave the PR open for manual handling. Do not retry with different flags, do not
force-push, do not re-run the ceremony.

## After a successful merge

Default cleanup — run all of these unconditionally. It must complete before reporting success:

1. **Capture the PR branch and remove the linked worktree from the main worktree.** In the
   PR worktree, set `HEAD_BRANCH=$(git branch --show-current)`, `WORKTREE_PATH=$(pwd)`, and
   `MAIN_WORKTREE=$(git worktree list --porcelain | awk '$1 == "worktree" { print $2; exit }')`.
   Detect a linked worktree:
   ```bash
   [ "$(git rev-parse --git-dir)" != "$(git rev-parse --git-common-dir)" ] && echo "linked worktree"
   ```
   If linked, remove it without deleting the current directory:
   ```bash
   git -C "$MAIN_WORKTREE" worktree remove "$WORKTREE_PATH"
   cd "$MAIN_WORKTREE"
   ```
   `git worktree remove` does **not** delete the local branch. If removal refuses because of
   uncommitted changes, stop and report rather than discarding work. Delete the remote head
   separately only when stack-safe (no open PR still bases on it).
2. **Switch to `main` and explicitly synchronize it with origin.** From `$MAIN_WORKTREE`, run:
   ```bash
   git fetch origin --prune
   git checkout main && git merge --ff-only origin/main
   ```
   Do not rely on an implicit upstream: branch deletion must be based on the fetched
   `origin/main`. If `refs/remotes/origin/develop` exists, create or check out `develop` from
   that remote ref and fast-forward it before using it as an integration branch:
   ```bash
   if git show-ref --verify --quiet refs/remotes/origin/develop; then
     if git show-ref --verify --quiet refs/heads/develop; then
       git checkout develop && git merge --ff-only origin/develop
     else
       git checkout --track origin/develop
     fi
     DEVELOP_SYNCED=1
   else
     DEVELOP_SYNCED=0
   fi
   git checkout main
   ```
   Synchronize the PR's `baseRefName` similarly when it exists on origin. Never force
   long-lived branches.
3. **Explicitly delete the PR's local branch.** After its base is synchronized, run:
   ```bash
   git branch -d "$HEAD_BRANCH"
   ```
   Verify `git show-ref --verify --quiet "refs/heads/$HEAD_BRANCH"` fails. If the branch
   remains, stop and report cleanup failure; do not report success.
4. **Prune every other local branch already merged into either synchronized integration
   branch.** A branch may have merged through `develop` without yet appearing in `main`, so
   derive the deletion candidates from both branches. Exclude the checked-out branch and the
   protected integration branches:
   ```bash
   CURRENT_BRANCH=$(git branch --show-current)
   {
     git branch --merged main
     [ "${DEVELOP_SYNCED:-0}" = "1" ] && git branch --merged develop
   } | sed 's/^[* ]*//' | sort -u | while IFS= read -r branch; do
     [ -n "$branch" ] || continue
     [ "$branch" = "$CURRENT_BRANCH" ] && continue
     [ "$branch" = "main" ] && continue
     [ "$branch" = "develop" ] && continue
     git branch -d "$branch"
   done
   ```
   This runs only after `main` and, when available, `develop` have been synchronized from
   their corresponding `origin/*` refs, so branch deletion never relies on stale local
   integration history.
5. `git worktree prune` to remove stale administrative records.
6. Scan `.agents/worktrees/` for stale worktree directories whose branch is already merged
   or no longer exists. Report them to the user and suggest manual `rm -rf` removal.

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

1. The Phase 4 gate holds (CI green, every comment reflected on). Escalate items are
   recorded for the summary; they do not block.
2. **Arm the closeout state** (`arm-closeout.sh "$PR"`).
3. Hide + resolve the fully-addressed comments (Phase 3 closeout) **first** — the summary
   comment should land on a clean PR. Re-sweep if a final CI push landed after the last
   closeout pass.
4. Post the summary comment, capturing its URL.
5. Rewrite the title/body, linking the Review-cycle line to that URL.
6. Stop the watch (monitor), present the closeout result, and wait for explicit user
   confirmation. If declined, clear closeout state and leave the PR open.
7. After confirmation, merge with `gh pr merge --merge --delete-branch` (omitting
   `--delete-branch` in a linked worktree). Keep closeout state armed.
8. After a successful merge: remove the linked worktree (with `git worktree remove <path>` or
   the runtime's own mechanism) + delete its merged local branch + switch to `main` + sync
   `main`/`develop` + delete merged local branches + `git worktree prune` + scan stale
   worktrees (see "After a successful merge"). Complete this before reporting success, then
   clear closeout state. If cleanup fails, leave closeout state armed and report the failure.

Steps 2–4 (the ceremony) are idempotent: re-running `gh pr edit` with the same title/body is
a no-op, and the marker lookup patches the existing summary rather than duplicating it (which
also recovers `SUMMARY_URL` after an interrupt). Steps 5 and 6 are NOT idempotent — run them
once, when the gate holds. If an interrupt left the pipeline mid-closeout and you resume,
skip steps already completed; if the merge already landed, verify the post-merge hygiene and
stop. Do not re-run the confirmation unless a new closeout is necessary.

## Do not

- Do not run the ceremony or merge while comments are still open or CI is still red — the
  gate must hold first, and the summary would claim a merge-ready state that is not true.
- Do not choose the merge strategy or ask how to handle an escalate or ambiguous comment.
  The merge question is required: request explicit user confirmation after the closeout
  summary is posted. Escalate items are documented in that summary.
- Do not end the turn with the closeout state armed — enforcement blocks it. Clear it
  (`clear-closeout.sh "$PR"`) after a user decline, merge failure/abort, or only after a
  confirmed merge **and all required cleanup** complete; while it stays armed, one turn-end
  per user turn is blocked with a message naming the PR and the pending closeout.
- Do not run the ceremony (summary comment + body rewrite) before the gate holds.
- Do not rewrite the title/body to claim something the diff does not deliver.
- Do not include the closeout summary inside the PR body AND as a comment — the body
  describes the change; the comment records the review cycle. They are different records.
- Do not ship a Review-cycle line without the summary comment's URL. Counts alone strand the
  audit trail somewhere in a long comment thread.
- Do not edit the summary with `gh pr comment --edit-last` — it targets whatever you commented
  last, not the summary. Find it by its `<!-- review-pr:summary -->` marker.
- Do not write the summary in the AI's voice or sign it as AI-generated; the user asked for
  it in their name.
- Do not use `gh pr merge --auto` (GitHub's background auto-merge feature, which fires
  whenever it can and bypasses your own gate); use `gh pr merge --merge`, a direct merge only
  after the gate holds and the user explicitly confirms. Do not merge with squash/rebase —
  the strategy is fixed to a merge commit.
- Do not merge past unresolved `escalate` comments silently — they are recorded in the
  summary comment, which is the audit trail. Merging with open escalate items is expected;
  merging without documenting them is not.
