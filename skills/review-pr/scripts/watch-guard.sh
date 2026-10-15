#!/usr/bin/env bash
#
# Stall guard — detect a review watch that is armed with no wake source behind it.
#
# Background: the review-pr watch is a loop (poll, triage, fix, acknowledge, arm the
# next poll). On a host whose wake source is an asynchronous child, the loop closes
# only when the turn ends with that child pending. A turn that ends with nothing
# pending leaves the watch armed and unobserved: later reviewer comments are never
# triaged until the next user message. The loop state alone cannot show that, so
# review-loop.sh records the poll interval and the last poll time. This guard reports
# a watch that has not polled for three intervals while its deadline is still open.
#
# Usage:
#   bash watch-guard.sh --check      # report stale watches on stdout, exit 1 when any
#   <stop-hook payload> | bash watch-guard.sh   # emit one reminder per user turn
#
# Check mode is for any host: run it before ending a turn while the watch is armed.
# Hook mode follows the contract of closeout-stop.sh for hosts with compatible stop
# hooks, and fails open everywhere else.
#
# Guard rails (a Stop hook fires on EVERY turn end):
#   - Fails open: no jq, no git repo, no state file, a subagent stop, a still-fresh
#     poll, an expired deadline, or an unreadable state all pass.
#   - Yields to the user: a closeout state awaiting confirmation passes, because the
#     turn is ending for the human's reply.
#   - Fires at most once per user turn: stop_hook_active passes, so the reminder is
#     injected once and the turn can then end.
#
# Input (stdin JSON): a host stop-hook payload with a stop-hook-active flag.

set -uo pipefail

MODE=check
if [ "${1:-}" = "--check" ]; then
  MODE=check
elif [ "$#" -eq 0 ]; then
  MODE=hook
else
  echo "watch-guard.sh: usage: watch-guard.sh --check | <stop-hook payload> | watch-guard.sh" >&2
  exit 2
fi

command -v jq >/dev/null 2>&1 || exit 0

if [ "$MODE" = hook ]; then
  input=$(</dev/stdin)
  [ -n "$input" ] || exit 0
  # Subagent stops cannot arm a poll — enforcement is the main turn's job.
  [ -z "$(printf '%s' "$input" | jq -r '.agent_id // empty')" ] || exit 0
  stop_hook_active=$(printf '%s' "$input" | jq -r '.stop_hook_active // .stopHookActive // false')
  [ "$stop_hook_active" = "true" ] && exit 0
fi

# The watch state lives beside the worktree's gitdir, which `git rev-parse --git-path`
# resolves to for both normal and linked worktrees. Outside a git repo there is no watch.
GITDIR=$(git rev-parse --absolute-git-dir 2>/dev/null) || exit 0
[ -d "$GITDIR" ] || exit 0

# A presented approval question yields; the closeout guard owns that reminder.
CLOSEOUT="$GITDIR/review-pr-closeout.json"
if [ -f "$CLOSEOUT" ] && [ "$(jq -r '.awaiting_confirmation // false' "$CLOSEOUT" 2>/dev/null)" = "true" ]; then
  exit 0
fi

now=$(date +%s)
stale=""
stale_prs=""
for STATE in "$GITDIR"/review-pr-watch-*.json; do
  # An unmatched glob stays literal; read-side validation rejects anything else, so a
  # malformed or foreign file fails open instead of blocking the turn.
  [ -f "$STATE" ] || continue
  IFS=$'\t' read -r pr interval last_poll deadline < <(
    jq -r '[(.pr // ""), (.interval // ""), (.last_poll_epoch // ""), (.deadline_epoch // "")] | @tsv' \
      "$STATE" 2>/dev/null
  ) || continue
  [[ "$pr" =~ ^[0-9]+$ ]] && [[ "$interval" =~ ^[0-9]+$ ]] || continue
  [[ "$last_poll" =~ ^[0-9]+$ ]] && [[ "$deadline" =~ ^[0-9]+$ ]] || continue
  # An open deadline means the watch intends to continue; after it, the watch stops.
  [ "$now" -lt "$deadline" ] || continue
  threshold=$(( interval * 3 ))
  [ "$threshold" -lt 180 ] && threshold=180
  age=$(( now - last_poll ))
  [ "$age" -gt "$threshold" ] || continue
  stale="$stale$pr"$'\t'"$age"$'\t'"$interval"$'\n'
  stale_prs="$stale_prs #$pr"
done

[ -n "$stale" ] || exit 0

if [ "$MODE" = check ]; then
  while IFS=$'\t' read -r pr age interval; do
    [ -n "$pr" ] || continue
    echo "WATCH-STALE PR #$pr: no poll for ${age}s (interval ${interval}s). Arm the next poll through the host wake facility, or clear the watch when the PR merged or closed, or the user stopped watching."
  done <<<"$stale"
  exit 1
fi

SKILL_DIR="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
CLEAR_SCRIPT="$SKILL_DIR/scripts/clear-watch.sh"

msg="review-pr has a stale watch: no poll for three intervals on PR${stale_prs}. The watch is still armed, so its comment queue is unobserved. Arm the next poll through the host wake facility before this turn ends. If no facility exists, report that in the same turn. If the watch ended on purpose — the PR merged or closed, the user stopped watching, or the deadline passed — release it with bash ${CLEAR_SCRIPT} <PR> when the state is stale. Verify the current state first: gh pr view <PR> --json state,mergedAt, then read ${GITDIR}/review-pr-watch-<PR>.json."
msg="${msg} Procedure: ${SKILL_DIR}/references/runbook.md (Continuation contract)."

jq -n --arg c "$msg" '{hookSpecificOutput:{hookEventName:"Stop",additionalContext:$c}}'
exit 0