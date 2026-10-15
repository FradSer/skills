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
GUARD="$SKILL_DIR/scripts/watch-guard.sh"
RELEASE="$SKILL_DIR/scripts/clear-watch.sh"
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
6. Re-arm the next one-shot poll through the same facility after each processed
   batch, until a stop condition holds.
7. Arm closeout, run the ceremony in `closeout.md`, then clear closeout state.

## Continuation contract

Discover how this host wakes the agent with a poll result before the first poll. Use the
first facility the host exposes, in this order:

1. A facility that returns a bounded command's output in a later turn. In Pi, start one
   asynchronous subagent per poll with `tools: ["bash"]`; its answer arrives in a later
   turn and resumes this session.
2. A cancellable host monitor that surfaces one terminal result line for a matched
   sentinel.
3. A bounded `--once` poll that this turn waits for, when (1) and (2) are absent. State in
   the report that the watch needs another turn.

Never name a tool the host may not have, never use a manual foreground loop, and never
claim a tool ran. If the host exposes no facility, report that ongoing monitoring could
not be established and stop after one bounded poll.

Give a poll child these instructions, and pass `ACK` with the node IDs you triaged:

```
Run exactly one command and print its complete stdout verbatim. Then stop. Do not read
files, edit anything, or start other agents.
<the bounded poll command below>
```

Arm one poll child per cycle. Read its answer, triage every `events` entry, apply the
verified fixes, then arm the next poll child with the updated `ACK` list. Do not leave a
child running after a stop condition holds.

### Stall guard

A watch can outlive its wake source: a turn that ends with nothing armed leaves the comment
queue unobserved. The state file records `interval` and `last_poll_epoch`, so this stall is
detectable. Before you end a turn while the watch stays open, confirm the next poll is armed.
On stop-hook hosts, wire the guard into that hook the same way as `closeout-stop.sh`. On any
host, run one check:

```bash
bash "$GUARD" --check   # exit 1 names a watch that has not polled for three intervals
```

Do not treat a fresh poll as a stop signal: a watch that is armed but idle is normal, and a
stale watch needs the next poll, not a hidden comment queue. Release a watch that ended on
purpose — merged, closed, stopped by the user, or past the deadline — with:

```bash
bash "$RELEASE" "$PR"
```

A host monitor with a terminal-result contract surfaces only
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

After you process a result, arm another bounded poll through the same facility, no faster
than INTERVAL. Repeat: poll, triage, fix, acknowledge, arm the next poll. Do not use a
foreground `while` loop. A host monitor uses the wrapper above as its command, with
`result_pattern='__REVIEW_POLL__ (?<json>\\{.*\\})'` and
`failure_pattern='__REVIEW_POLL_FAILED__ (?<json>\\{.*\\})'`; parse every entry in
its returned `events` array before arming the next poll.

## Stop and closeout

Keep the watch armed while the PR stays open. Stop only when the PR merges or closes, when
the user stops watching, or when the default 7200-second deadline expires. A terminal
passing CI and a handled comment queue show a settled gate, not a finished review; an empty
poll is not a stop signal. Resolve material escalations before you declare the gate ready.

The ~2-hour cap bounds a stuck PR. When the cap expires, surface whether CI is still red or
comments remain, then stop.

When the gate holds, prepare closeout and keep polling:

```bash
bash "$ARM" "$PR"
```

Run the ordered summary-comment and body-rewrite ceremony from `closeout.md`.
Present its result and request any missing explicit user confirmation. Mark awaiting
confirmation with `arm-closeout.sh "$PR" --awaiting-confirmation` and yield. Merge
only after confirmation. New commits or new comments invalidate the approved result:
triage, fix, and request the missing authorization again. Clear state after merge and
authorized cleanup, after an unrecoverable merge failure, or when the user declines both
the merge and further watching:

```bash
bash "$CLEAR" "$PR"
```

When confirmation arrives, run `bash "$ARM" "$PR"` before rechecking and merging.
This clears the awaiting-confirmation flag and restores the reminder until the approved
operation and authorized cleanup are complete.
