# Review-pr Handoff

`create-pr` creates the pull request. `review-pr` owns everything after
creation. This reference defines only the boundary between those workflows.

## Required handoff

After `gh pr create` succeeds:

1. Capture its returned URL in `PR_URL`.
2. Resolve the canonical PR number from GitHub:

   ```bash
   PR=$(gh pr view "$PR_URL" --json number --jq '.number')
   ```

3. Start standalone `review-pr` exactly once with `$ARGUMENTS="$PR"`.
4. Do not report success or return control before `review-pr` has ownership.

Use the host's real continuation or skill-dispatch mechanism. In Pi,
`/skill:review-pr <number>` is an input command, not a nested callable tool;
do not print it as if it executes. If the host cannot dispatch a sibling skill,
use the operational fallback under `references/` and `scripts/`, then
continue the review-pr procedure there. In Pi, that fallback MUST start every
review-loop poll through `monitor_start`, using the sentinel contract in
`references/runbook.md`; it must not run the poll in the foreground. The fallback
contains no nested `review-pr` directory or second `SKILL.md`.

## Ownership after handoff

`review-pr` owns:

- independent baseline review
- CI and review-comment polling
- persistent cursor and watch state
- comment acknowledgement and restart recovery
- skeptical triage and validated fixes
- closeout summary, body rewrite, and merge
- post-merge branch and worktree cleanup

`create-pr` must not duplicate those responsibilities or launch another monitor.

## Operational references

The operational references are synchronized from `skills/review-pr/`:

```bash
python3 tools/skill-sync/sync-review-pr-refs.py --check
```

Run the command without `--check` after changing the standalone review
references or scripts. The `references/` directory includes the important review references and
`scripts/` contains the review-pr executables. Both intentionally exclude the
standalone `SKILL.md` and any nested `review-pr` directory.
