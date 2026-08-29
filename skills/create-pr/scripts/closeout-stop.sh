#!/usr/bin/env bash
#
# Stop-hook adapter — enforce the review-pr closeout on hosts with compatible stop hooks.
# The default enforcement is in-prompt (see SKILL.md Runtime notes): never end the
# turn while the closeout state is armed. On hosts that provide a compatible stop
# hook, wire this script into that hook so the rule is enforced mechanically; on
# hosts without hooks, apply the same rule in the prompt. The script fails open
# everywhere else.
#
# Background: the review-pr skill runs on prompt alone, so the closeout
# (summary comment + body rewrite + explicit user merge confirmation) can be skipped
# by a hallucinated or premature stop. The skill arms a state file
# (.git/review-pr-closeout.json) the moment Phase 4's stop conditions hold and
# clears it once the user declines, the merge aborts, or the confirmed merge and all
# required cleanup complete. While the file exists, this adapter blocks one turn-end per
# user turn with a message naming the PR
# and the pending step — the closeout cannot silently vanish, and it does not loop:
# after the single block the turn ends.
#
# Guard rails (a Stop hook fires on EVERY turn end — Stop has no matcher):
#   - Fails open: no jq, no git repo, no state file, or a subagent stop
#     (agent_id present in the input) all pass.
#   - Fires at most once per user turn: stop_hook_active is true when the turn
#     is already continuing from a stop-hook block — pass through so the turn
#     can end. The single block injects the reminder once; resolving the
#     closeout (running it, then clear-closeout.sh) is what removes the state
#     file.
#   - Blocks via the host hook's context channel (exit 0 + JSON): the message is
#     fed back to the model and the turn continues. Hosts that do not understand
#     this output fail open.
#
# Input (stdin JSON): a host stop-hook payload with a stop-hook-active flag.
# Hosts with a different payload or no stop hook fail open.

set -uo pipefail

input=$(</dev/stdin)

# Fail open: without jq there is nothing to parse.
command -v jq >/dev/null 2>&1 || exit 0
[ -n "$input" ] || exit 0

# Subagent stops cannot run the closeout — enforcement is the main turn's job.
agent_id=$(printf '%s' "$input" | jq -r '.agent_id // empty')
[ -z "$agent_id" ] || exit 0

# At most one reminder per user turn. stop_hook_active is true when the turn is
# already continuing from a stop-hook block — passing through lets the turn end
# instead of re-blocking every end attempt. The reminder was already injected
# once; running the closeout (then clear-closeout.sh) is what clears the state
# file on its own schedule.
stop_hook_active=$(printf '%s' "$input" | jq -r '.stop_hook_active // .stopHookActive // false')
[ "$stop_hook_active" = "true" ] && exit 0

# The state file lives in the repo's gitdir; resolve it from the hook cwd
# (the session's working directory). Outside a git repo there is no closeout.
GITDIR=$(git rev-parse --git-dir 2>/dev/null) || exit 0
case "$GITDIR" in
  /*) ;;
  *)  GITDIR="$PWD/$GITDIR" ;;
esac

STATE="$GITDIR/review-pr-closeout.json"
[ -f "$STATE" ] || exit 0

# Read-side validation: only a well-formed, digits-PR state may block. Anything
# else (malformed file, foreign content) fails open — the file was not written
# by the skill's arm script, so it is not a closeout this hook should enforce.
PR=$(jq -r '.pr // empty' "$STATE")
[[ "$PR" =~ ^[0-9]+$ ]] || exit 0

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CLEAR_SCRIPT="$SKILL_DIR/scripts/clear-closeout.sh"

msg="review-pr closeout for PR #${PR} is pending: post the summary comment and rewrite the title/body if they are not complete, then present the closeout result and request explicit user confirmation before running gh pr merge --merge. Do not merge without that confirmation. First verify the pending closeout is real: the state file is stale (a false alarm) if the closeout was already resolved — the user declined and state was cleared, or the PR already merged. Judge simple checks directly (e.g. gh pr view --json state,mergedAt, the <!-- review-pr:summary --> marker lookup); for complex or ambiguous situations spawn an independent subagent with clean context to verify. If the state is stale, the user declined, or the merge failed and the PR is left open for manual handling, run bash ${CLEAR_SCRIPT} ${PR} to release the closeout."
msg="${msg} Full verification procedure: ${SKILL_DIR}/references/closeout.md (When enforcement fires)."

jq -n --arg c "$msg" '{hookSpecificOutput:{hookEventName:"Stop",additionalContext:$c}}'
exit 0
