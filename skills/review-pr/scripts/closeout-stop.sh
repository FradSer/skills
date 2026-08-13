#!/usr/bin/env bash
#
# Stop-hook adapter — enforce the review-pr closeout on runtimes with stop hooks.
# The DEFAULT enforcement is in-prompt (see SKILL.md Runtime notes): never end
# the turn while the closeout state is armed. On runtimes that provide stop
# hooks (e.g. Claude Code), wire this script as the Stop hook so the rule is
# enforced mechanically; on runtimes without hooks, apply the same rule in the
# prompt. The script fails open everywhere else.
#
# Background: the review-pr skill runs on prompt alone, so the automatic
# closeout (summary comment + body rewrite + auto-merge, no user question) can
# be skipped by a hallucinated or premature stop. The skill arms a state file
# (.git/review-pr-closeout.json) the moment Phase 4's stop conditions hold and
# clears it once the auto-merge completes or aborts. While the file exists, this
# adapter blocks one turn-end per user turn with a message naming the PR and the
# pending step — the closeout cannot silently vanish, and it does not loop:
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
#   - Blocks via hookSpecificOutput.additionalContext (exit 0 + JSON): the
#     message is fed back to the model as "Stop hook feedback" and the turn
#     continues — same loop protections as a decision:block, without the
#     hook-error label.
#
# Input (stdin JSON): Stop common fields + stop_hook_active,
#   last_assistant_message, background_tasks, session_crons.

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
# file on its own schedule. Official anti-loop pattern per
# https://code.claude.com/docs/en/hooks-guide.md.
stop_hook_active=$(printf '%s' "$input" | jq -r '.stop_hook_active // false')
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

msg="review-pr closeout for PR #${PR} is pending: the automatic closeout has not run yet. Run it now — post the summary comment, rewrite the title/body, then gh pr merge --merge — and clear the state with bash ${CLEAR_SCRIPT} ${PR}. First verify the pending closeout is real: the state file is stale (a false alarm) if the closeout was already resolved — summary already posted, or the PR already merged. Judge simple checks directly (e.g. gh pr view --json state,mergedAt, the <!-- review-pr:summary --> marker lookup); for complex or ambiguous situations spawn an independent subagent with clean context to verify. If the state is stale, or the merge already failed and the PR is left open for manual handling, run bash ${CLEAR_SCRIPT} ${PR} to release the closeout. Never ask the user whether to merge — the pipeline is fully automatic."
msg="${msg} Full verification procedure: ${SKILL_DIR}/references/closeout.md (When enforcement fires)."

jq -n --arg c "$msg" '{hookSpecificOutput:{hookEventName:"Stop",additionalContext:$c}}'
exit 0
