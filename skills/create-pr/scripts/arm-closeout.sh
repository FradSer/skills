#!/usr/bin/env bash
# arm-closeout.sh — arm the review-pr closeout state for a PR.
#
# Writes .git/review-pr-closeout.json (resolved via `git rev-parse --git-dir`,
# so the script works from any cwd inside the repo). The state tracks unfinished
# preparation or a presented explicit user merge confirmation. Awaiting
# confirmation permits the turn to yield for the human decision. The state is
# cleared by clear-closeout.sh once the user declines, the merge aborts, or the confirmed
# merge and all required cleanup complete.
#
# Usage:
#   bash arm-closeout.sh <PR> [--awaiting-confirmation]

set -u

PR="${1:-}"
AWAITING_CONFIRMATION=false
if [ "$#" -gt 2 ] || { [ "$#" -eq 2 ] && [ "$2" != --awaiting-confirmation ]; }; then
  echo "arm-closeout.sh: usage: arm-closeout.sh <PR> [--awaiting-confirmation]" >&2
  exit 2
fi
[ "${2:-}" != --awaiting-confirmation ] || AWAITING_CONFIRMATION=true

# PR is a bare number (the skill normalizes it before arming); anything else
# would write invalid JSON that the adapter cannot parse and the clear script
# can never remove — reject it outright.
[[ "$PR" =~ ^[0-9]+$ ]] || { echo "arm-closeout.sh: usage: arm-closeout.sh <PR> (PR must be a number)" >&2; exit 2; }

GITDIR=$(git rev-parse --git-dir 2>/dev/null) || { echo "arm-closeout.sh: not a git repository" >&2; exit 1; }
case "$GITDIR" in
  /*) ;;
  *)  GITDIR="$PWD/$GITDIR" ;;
esac

jq -n --arg pr "$PR" --argjson awaiting_confirmation "$AWAITING_CONFIRMATION" '{pr:$pr,awaiting_confirmation:$awaiting_confirmation}' \
  > "$GITDIR/review-pr-closeout.json" || { echo "arm-closeout.sh: cannot write state file" >&2; exit 1; }
echo "closeout armed for PR #$PR"
