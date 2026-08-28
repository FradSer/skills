#!/usr/bin/env bash
# finish-branch.sh — mechanical steps of the git-flow finish pipeline (feature/hotfix/release).
#
# Judgment stays in the skill: the agent runs tests, writes the changelog, and
# drafts GitHub releases. This script only executes the deterministic parts —
# clean-tree/branch-type pre-flight, git-flow finish, push, return to develop,
# and stale branch/worktree cleanup.
#
# Usage:
#   bash finish-branch.sh --type feature --name <slug>
#   bash finish-branch.sh --type hotfix --version <x.y.z> [--tagname v<x.y.z>]
#   bash finish-branch.sh --type release --version <x.y.z> [--tagname v<x.y.z>]
#
# Flags:
#   --type feature|hotfix|release   required
#   --name <slug>                   branch name (feature)
#   --version <x.y.z>               version (hotfix/release; used for --tagname default)
#   --tagname <tag>                 tag name, default "v$VERSION"
#   --message <msg>                 tag message (hotfix/release)

set -uo pipefail

TYPE=""
NAME=""
VERSION=""
TAGNAME=""
MESSAGE="Release"

while [ $# -gt 0 ]; do
  case "$1" in
    --type) TYPE="${2:-}"; shift 2 ;;
    --name) NAME="${2:-}"; shift 2 ;;
    --version) VERSION="${2:-}"; shift 2 ;;
    --tagname) TAGNAME="${2:-}"; shift 2 ;;
    --message) MESSAGE="${2:-}"; shift 2 ;;
    -h|--help) sed -n '2,14p' "$0"; exit 0 ;;
    *) echo "finish-branch.sh: unknown arg: $1" >&2; exit 2 ;;
  esac
done

case "$TYPE" in
  feature|hotfix|release) ;;
  *) echo "finish-branch.sh: --type must be feature|hotfix|release" >&2; exit 2 ;;
esac

# Pre-flight: clean tree + correct branch type.
if [ -n "$(git status --porcelain)" ]; then
  echo "finish-branch.sh: working tree is dirty — commit or stash before finishing" >&2
  exit 1
fi
CURRENT=$(git branch --show-current)
case "$CURRENT" in
  "$TYPE"/*) ;;
  *) echo "finish-branch.sh: current branch $CURRENT is not $TYPE/*" >&2; exit 1 ;;
esac

if [ "$TYPE" = "feature" ]; then
  [ -n "$NAME" ] || NAME="${CURRENT#feature/}"
  echo "finish-branch.sh: git flow feature finish $NAME"
  git flow feature finish "$NAME" || { echo "finish-branch.sh: git flow finish failed" >&2; exit 1; }
  git push origin develop
else
  [ -n "$VERSION" ] || VERSION="${CURRENT#$TYPE/}"
  [ -n "$TAGNAME" ] || TAGNAME="v$VERSION"
  echo "finish-branch.sh: git flow $TYPE finish $VERSION --tagname $TAGNAME"
  git flow "$TYPE" finish "$VERSION" --tagname "$TAGNAME" -m "$MESSAGE" \
    || { echo "finish-branch.sh: git flow finish failed" >&2; exit 1; }
  git push origin main develop --tags
  # git-flow leaves the repo on main after hotfix/release; return to develop.
  git checkout develop && git pull --ff-only origin develop
fi

echo "finish-branch.sh: cleanup"
git fetch --prune
git worktree prune

# Sweep merged local branches (feature/hotfix/release), keeping long-lived ones.
for b in $(git branch --merged develop | sed 's/^[* ] //' | grep -E '^(feature|hotfix|release)/' || true); do
  git branch -d "$b" 2>/dev/null || true
done

echo "finish-branch.sh: $TYPE/$NAME finished"
