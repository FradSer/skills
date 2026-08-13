# Closeout: Ceremony and Auto-Merge

Once the PR is merge-ready (all `[ci]` checks terminal and passing, every comment either
fixed, rejected-with-reply, or escalated-and-documented, and resolved comments hidden +
their threads resolved), run the closeout ceremony and auto-merge. There is no merge
question — the pipeline is fully automatic and never pauses for user input.

## Merge gate — must hold before anything else

The closeout runs only when the Phase 4 gate holds:

1. Every `[ci]` check is terminal AND passing.
2. Every comment is reflected on: `fix` pushed, `reject` replied, resolved ones hidden +
   threads resolved. `escalate` items may remain visible, but each one is recorded (body +
   author + file context) for the summary comment — they are documented, not asked about.

Escalate/ambiguous comments never block the merge. They are recorded in the summary
comment with their one-line outcome and the merge proceeds. The merge is automatic; the
only deviations are a merge failure (surface the error, stop, leave the PR open) or a
hard-cap stop (see `review-loop.md`).

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

## The merge

Run the ceremony first (summary comment + body rewrite, above), so the record is on the PR
before the merge lands. Then auto-merge:

```bash
gh pr merge "$PR" --repo "$REPO" --merge --delete-branch
```

- `--merge` is the fixed strategy — a merge commit, never squash/rebase (no user choice
  exists; keep the review-cycle history intact). Never `--auto` (GitHub's background
  auto-merge feature fires whenever it can and bypasses this gate).
- `--delete-branch` is safe only in the main worktree when no open PR still bases on that
  head. In a linked worktree, omit `--delete-branch` — delete the remote head separately if
  stack-safe, leave the local branch for the worktree removal (`git worktree remove <path>`).
- Report the merge in the conversation (one line, e.g. "PR #<n>: CI green, comments triaged —
  merged."). This is a notification, not a question.

**If the merge fails** (branch protection, required reviews, stale base): surface the error
in the conversation, stop the watch, and leave the PR open for manual handling. Do not retry
with different flags, do not force-push, do not re-run the ceremony.

## After a successful merge

Default cleanup — run all of these unconditionally:

1. **Remove the linked worktree first, before any switch.** Detect whether the closeout is
   running in a linked worktree (`resolve-issues`):
   ```bash
   [ "$(git rev-parse --git-dir)" != "$(git rev-parse --git-common-dir)" ] && echo "linked worktree"
   ```
   If linked, remove the worktree with `git worktree remove <path>` (or the runtime's own
   worktree-exit mechanism) — it deletes the worktree and its local branch
   and returns the session to the main worktree. If it refuses (uncommitted changes), stop
   and report rather than discarding work. Then delete the remote head separately if
   stack-safe (no open PR still bases on it).
2. **Switch to `main` and sync.** Now in the main worktree, run:
   ```bash
   git fetch --prune
   git checkout main && git pull --ff-only
   ```
   Repeat the `--ff-only` pull for `develop` and the PR's `baseRefName` when present on
   origin (check each out first, then land back on `main`). Never force long-lived branches.
3. Delete every local branch already merged into `main`/`develop` (except the current branch).
   ```bash
   git branch --merged main | grep -v '^\*\|main\|develop' | xargs -r git branch -d
   ```
4. `git worktree prune` to remove stale administrative records.
5. Scan `.agents/worktrees/` for stale worktree directories whose branch is already merged
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
2. Hide + resolve the fully-addressed comments (Phase 3 closeout) **first** — the summary
   comment should land on a clean PR. Re-sweep if a final CI push landed after the last
   closeout pass.
3. Post the summary comment, capturing its URL.
4. Rewrite the title/body, linking the Review-cycle line to that URL.
5. Auto-merge with `gh pr merge --merge --delete-branch` (omitting `--delete-branch` in a
   linked worktree, same rule as above).
6. After a successful merge: remove the linked worktree (with `git worktree remove <path>` or
   the runtime's own mechanism) + switch to `main` + sync `main`/`develop` + delete merged
   local branches + `git worktree prune` + scan stale worktrees (see "After a successful
   merge" above).
7. Stop the watch.

Steps 2–4 (the ceremony) are idempotent: re-running `gh pr edit` with the same title/body is
a no-op, and the marker lookup patches the existing summary rather than duplicating it (which
also recovers `SUMMARY_URL` after an interrupt). Steps 5 and 6 are NOT idempotent — run them
once, when the gate holds. If an interrupt left the pipeline mid-closeout and you resume,
skip steps already completed; if the merge already landed, verify the post-merge hygiene and
stop. Do not re-ask anything — the pipeline never asks.

## Do not

- Do not run the ceremony or merge while comments are still open or CI is still red — the
  gate must hold first, and the summary would claim a merge-ready state that is not true.
- Do not ask the user whether to merge, which strategy to use, or how to handle an escalate
  or ambiguous comment. The pipeline is fully automatic; escalate items are documented in
  the summary comment with their one-line outcome.
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
  whenever it can and bypasses your own gate); use `gh pr merge --merge`, a direct merge you
  execute only when the gate holds. Do not merge with squash/rebase — the strategy is fixed
  to a merge commit.
- Do not merge past unresolved `escalate` comments silently — they are recorded in the
  summary comment, which is the audit trail. Merging with open escalate items is expected;
  merging without documenting them is not.
