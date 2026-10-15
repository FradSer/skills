#!/usr/bin/env bash
# clear-watch.sh — release the review-pr watch state for a PR.
#
# Removes this worktree's review-pr-watch-<PR>.json only when it belongs to $PR, so a
# watch for one PR never releases another. No-op (exit 0) when the state is absent or
# belongs to a different PR.
#
# Release a watch only when it ended on purpose: the PR merged or closed, the user
# stopped watching, or the deadline passed. The state holds the replay ledger for
# unacknowledged events, so removing it while the watch continues loses that replay.
# A lock left by a killed poll stays: rmdir that directory before a new watch starts.
#
# Usage:
#   bash clear-watch.sh <PR>

set -u

PR="${1:-}"
[[ "$PR" =~ ^[0-9]+$ ]] || { echo "clear-watch.sh: usage: clear-watch.sh <PR> (PR must be a number)" >&2; exit 2; }

GITDIR=$(git rev-parse --git-path "review-pr-watch-${PR}.json" 2>/dev/null) || exit 0
case "$GITDIR" in
  /*) ;;
  *)  GITDIR="$PWD/$GITDIR" ;;
esac

[ -f "$GITDIR" ] || exit 0
[ "$(jq -r '.pr // empty' "$GITDIR" 2>/dev/null)" = "$PR" ] || exit 0
rm -f "$GITDIR"
echo "watch released for PR #$PR"