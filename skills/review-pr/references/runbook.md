# Review-pr Operational Runbook

This is the operational map for runtimes that cannot dispatch a sibling skill
from inside another skill. It is not a skill entry point and must not be loaded
as a standalone skill.

## Inputs

- `PR`: normalized bare pull request number
- `REPO`: `<owner>/<repo>`
- `INTERVAL`: 180, 300, or 480 seconds based on PR size; minimum 60
- `STATE_FILE`: optional persistent state path
- `ACK`: space-separated node IDs acknowledged after triage

Resolve the installed skill directory once as `SKILL_DIR`. All script paths
must be absolute:

```bash
SKILL_DIR=/absolute/path/to/skills/review-pr
LOOP="$SKILL_DIR/scripts/review-loop.sh"
ARM="$SKILL_DIR/scripts/arm-closeout.sh"
CLEAR="$SKILL_DIR/scripts/clear-closeout.sh"
```

The create-pr fallback uses equivalent references under `references/` and
scripts under `scripts/`.

## Phase order

1. Normalize PR and resolve `REPO`.
2. Run the independent baseline review from `review-loop.md`.
3. Poll one cycle with `LOOP --once`.
4. Handle `[ci]`, `[comment]`, `[error]`, `[status]`, and `[watch]` events.
5. Pass acknowledged node IDs as `ACK` on the next poll. Never treat emitted
   events as acknowledged.
6. Schedule the next one-shot poll until the stop conditions hold.
7. Arm closeout, run the ceremony in `closeout.md`, then clear closeout state.

## Monitor contract

Run the review loop under a monitor started through the runtime's monitor facility —
never a manual foreground loop. Monitors with a terminal-result contract surface only
the matched result line, never the poll's preceding stdout; do not run the infinite
loop mode under one. Capture one-shot output and embed every emitted event line INSIDE
the sentinel payload:

```bash
events=$(PR="$PR" REPO="$REPO" INTERVAL="$INTERVAL" bash "$LOOP" --once); rc=$?
payload=$(printf '%s\n' "$events" | jq -Rsc 'split("\n") | map(select(length > 0))')
if [ "$rc" -eq 0 ]; then
  printf '__REVIEW_POLL__ {"status":"ok","events":%s}\n' "$payload"
else
  printf '__REVIEW_POLL_FAILED__ {"status":"failed","exitCode":%s,"events":%s}\n' "$rc" "$payload"
  exit "$rc"
fi
```

Parse the `events` array from the captured JSON and triage every line; never
treat an `ok` status as proof of no events. Then use:

```text
success matcher=__REVIEW_POLL__ (?<json>\{.*\})
failure matcher=__REVIEW_POLL_FAILED__ (?<json>\{.*\})
```

After processing the result, schedule the next invocation. Do not use a
foreground `while` loop.

## Stop and closeout

Stop only when CI is terminal and passing and all comments have been
acknowledged or recorded for escalation. An empty poll is not a stop signal.
The default deadline is 7200 seconds. A merged or closed PR stops immediately.

When the gate holds:

```bash
bash "$ARM" "$PR"
```

Run the ordered summary-comment, body-rewrite, and merge ceremony from
`closeout.md`. Clear state after merge or an unrecoverable merge failure:

```bash
bash "$CLEAR" "$PR"
```
