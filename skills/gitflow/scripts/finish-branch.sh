#!/usr/bin/env bash
# Finish only the exact current configured Git-flow branch.
# Usage: bash finish-branch.sh --type feature --name <slug> [--no-push]
#        bash finish-branch.sh --type release|hotfix --version <semver>
#          [--tagname <tag>] [--message <text>] [--no-push]
# --no-push disables remote operations but still merges, tags, and deletes the
# operation's local branch. Obtain authorization for those local finish actions.

set -euo pipefail
TYPE="" NAME="" VERSION="" TAGNAME="" MESSAGE="Release" PUSH=1
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
source "$SCRIPT_DIR/gitflow-config.sh"
require_value() {
  [ "$#" -ge 2 ] && [ -n "${2:-}" ] && [[ "$2" != --* ]] || {
    echo "finish-branch.sh: $1 requires a value" >&2
    exit 2
  }
}
while [ $# -gt 0 ]; do
  case "$1" in
    --type) require_value "$@"; TYPE="$2"; shift 2 ;;
    --name) require_value "$@"; NAME="$2"; shift 2 ;;
    --version) require_value "$@"; VERSION="$2"; shift 2 ;;
    --tagname) require_value "$@"; TAGNAME="$2"; shift 2 ;;
    --message) require_value "$@"; MESSAGE="$2"; shift 2 ;;
    --no-push) PUSH=0; shift ;;
    -h|--help) sed -n '2,7p' "$0"; exit 0 ;;
    *) echo "finish-branch.sh: unknown arg: $1" >&2; exit 2 ;;
  esac
done
case "$TYPE" in
  feature|hotfix|release) ;;
  *) echo "finish-branch.sh: --type must be feature|hotfix|release" >&2; exit 2 ;;
esac
REPO_ROOT=$(git rev-parse --show-toplevel) || exit 1
cd -- "$REPO_ROOT"
STATUS=$(git status --porcelain) || exit 1
[ -z "$STATUS" ] || { echo "finish-branch.sh: working tree is dirty; commit or stash before finishing" >&2; exit 1; }
CURRENT=$(git branch --show-current) || exit 1
load_gitflow_config "$TYPE" || { echo "finish-branch.sh: configure Git-flow before finishing" >&2; exit 1; }
[ "$CURRENT" != "$MAIN_BRANCH" ] && [ "$CURRENT" != "$DEVELOP_BRANCH" ] || { echo "finish-branch.sh: cannot finish an integration branch" >&2; exit 1; }
[[ -n "$CURRENT" && "$CURRENT" == "$PREFIX"* && "$CURRENT" != "$PREFIX" ]] || {
  echo "finish-branch.sh: current branch $CURRENT does not match $PREFIX<name>" >&2
  exit 1
}
if [ "$TYPE" = feature ]; then
  [ -z "$VERSION" ] || { echo "finish-branch.sh: use --name for a feature" >&2; exit 2; }
  [ -n "$NAME" ] || NAME="${CURRENT#"$PREFIX"}"
else
  [ -n "$NAME" ] || NAME="$VERSION"
  [ -n "$NAME" ] || NAME="${CURRENT#"$PREFIX"}"
  [ -n "$VERSION" ] || VERSION="$NAME"
  [ -n "$TAGNAME" ] || TAGNAME="v$VERSION"
  git check-ref-format "refs/tags/$TAGNAME" >/dev/null || exit 2
  if git show-ref --verify --quiet "refs/tags/$TAGNAME"; then
    echo "finish-branch.sh: tag $TAGNAME already exists" >&2
    exit 1
  fi
fi
BRANCH="$PREFIX$NAME"
[ "$CURRENT" = "$BRANCH" ] || { echo "finish-branch.sh: requested $BRANCH differs from current $CURRENT" >&2; exit 1; }
git show-ref --verify --quiet "refs/heads/$DEVELOP_BRANCH" || exit 1
[ "$TYPE" = feature ] || git show-ref --verify --quiet "refs/heads/$MAIN_BRANCH" || exit 1
[ "$PUSH" = 0 ] || git remote get-url origin >/dev/null || { echo "finish-branch.sh: origin is required for publication" >&2; exit 1; }
HELP=$(git flow "$TYPE" finish --help) || exit 1
for option in --no-fetch --no-push --no-pushtag --keepremote; do
  [[ "$HELP" == *"$option"* ]] || { echo "finish-branch.sh: installed Git-flow lacks $option; no finish performed" >&2; exit 1; }
done
FLOW_ARGS=("$NAME" --no-fetch --no-push --no-pushtag --keepremote)
[[ "$HELP" != *--keep-worktree* ]] || FLOW_ARGS+=(--keep-worktree)
if [ "$TYPE" != feature ]; then
  [[ "$HELP" == *--tagname* ]] || exit 1
  FLOW_ARGS+=(--tagname "$TAGNAME" -m "$MESSAGE")
fi
echo "finish-branch.sh: finishing $BRANCH locally"
git flow "$TYPE" finish "${FLOW_ARGS[@]}" || { echo "finish-branch.sh: git flow finish failed; inspect repository state" >&2; exit 1; }
if [ "$PUSH" = 1 ]; then
  REFS=("$DEVELOP_BRANCH")
  if [ "$TYPE" != feature ]; then
    [ "$MAIN_BRANCH" = "$DEVELOP_BRANCH" ] || REFS+=("$MAIN_BRANCH")
    REFS+=("refs/tags/$TAGNAME")
  fi
  git push origin "${REFS[@]}" || { echo "finish-branch.sh: local finish completed but publication failed" >&2; exit 1; }
fi
AFTER_BRANCH=$(git branch --show-current) || exit 1
if [ -z "$AFTER_BRANCH" ]; then
  echo "finish-branch.sh: retained worktree remains detached"
else
  git checkout "$DEVELOP_BRANCH" || exit 1
fi
echo "finish-branch.sh: $BRANCH finished"
