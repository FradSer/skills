#!/usr/bin/env bash
# arm-closeout.sh — arm the review-pr closeout state for a PR.
#
# Writes .git/review-pr-closeout.json (resolved via `git rev-parse --git-dir`,
# so the script works from any cwd inside the repo). While that file exists,
# the skill must not end the turn: the automatic closeout (summary comment +
# body rewrite + auto-merge) is still pending. The state is cleared by
# clear-closeout.sh once the auto-merge completes or aborts.
#
# Usage:
#   bash arm-closeout.sh <PR>

set -u

PR="${1:-}"

# PR is a bare number (the skill normalizes it before arming); anything else
# would write invalid JSON that the adapter cannot parse and the clear script
# can never remove — reject it outright.
[[ "$PR" =~ ^[0-9]+$ ]] || { echo "arm-closeout.sh: usage: arm-closeout.sh <PR> (PR must be a number)" >&2; exit 2; }

GITDIR=$(git rev-parse --git-dir 2>/dev/null) || { echo "arm-closeout.sh: not a git repository" >&2; exit 1; }
case "$GITDIR" in
  /*) ;;
  *)  GITDIR="$PWD/$GITDIR" ;;
esac

jq -n --arg pr "$PR" '{pr:$pr}' \
  > "$GITDIR/review-pr-closeout.json" || { echo "arm-closeout.sh: cannot write state file" >&2; exit 1; }
echo "closeout armed for PR #$PR"
