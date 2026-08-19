# Review-pr Operational Runbook

This is the operational map for hosts that cannot dispatch a sibling skill
from inside another skill. It is not a skill entry point and must not be
loaded as a standalone skill.

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

Pi's `monitor_start` requires a terminal result contract. Do not run the
infinite loop mode under it. Wrap one-shot polling with a unique sentinel:

```bash
if PR="$PR" REPO="$REPO" INTERVAL="$INTERVAL" STATE_FILE="$STATE_FILE" \
  bash "$LOOP" --once; then
  printf '__PI_REVIEW_POLL__ {"status":"ok"}\n'
else
  code=$?
  printf '__PI_REVIEW_POLL_FAILED__ {"status":"failed","exitCode":%s}\n' "$code"
  exit "$code"
fi
```

Use:

```text
result_pattern=__PI_REVIEW_POLL__ (?<json>\{.*\})
failure_pattern=__PI_REVIEW_POLL_FAILED__ (?<json>\{.*\})
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
