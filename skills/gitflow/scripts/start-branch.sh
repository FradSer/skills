#!/usr/bin/env bash
# Start a configured Git-flow branch, optionally bumping package versions.
# Usage: bash start-branch.sh --type feature --name <slug> [--no-push]
#        bash start-branch.sh --type release|hotfix --version <semver> [--no-push]
# Publication remains enabled for existing callers; pass --no-push when only
# local work is authorized. This performs real local mutations, not a dry run.

set -euo pipefail
TYPE="" NAME="" VERSION="" PUSH=1
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
source "$SCRIPT_DIR/gitflow-config.sh"

require_value() {
  [ "$#" -ge 2 ] && [ -n "${2:-}" ] && [[ "$2" != --* ]] || {
    echo "start-branch.sh: $1 requires a value" >&2
    exit 2
  }
}
while [ $# -gt 0 ]; do
  case "$1" in
    --type) require_value "$@"; TYPE="$2"; shift 2 ;;
    --name) require_value "$@"; NAME="$2"; shift 2 ;;
    --version) require_value "$@"; VERSION="$2"; shift 2 ;;
    --no-push) PUSH=0; shift ;;
    -h|--help) sed -n '2,6p' "$0"; exit 0 ;;
    *) echo "start-branch.sh: unknown arg: $1" >&2; exit 2 ;;
  esac
done
case "$TYPE" in
  feature|hotfix|release) ;;
  *) echo "start-branch.sh: --type must be feature|hotfix|release" >&2; exit 2 ;;
esac
[ -n "$NAME" ] || NAME="$VERSION"
[ -n "$NAME" ] || { echo "start-branch.sh: --name or --version is required" >&2; exit 2; }

REPO_ROOT=$(git rev-parse --show-toplevel) || exit 1
cd -- "$REPO_ROOT"
STATUS=$(git status --porcelain) || exit 1
[ -z "$STATUS" ] || { echo "start-branch.sh: working tree is dirty; commit or stash before starting" >&2; exit 1; }
load_gitflow_config "$TYPE" || { echo "start-branch.sh: configure Git-flow before starting" >&2; exit 1; }
BRANCH="$PREFIX$NAME"
git check-ref-format --branch "$BRANCH" >/dev/null || exit 2
if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
  echo "start-branch.sh: branch $BRANCH already exists" >&2
  exit 1
fi
BASE="$START_BRANCH"
git show-ref --verify --quiet "refs/heads/$BASE" || { echo "start-branch.sh: base branch $BASE is missing" >&2; exit 1; }
[ "$PUSH" = 0 ] || git remote get-url origin >/dev/null || { echo "start-branch.sh: origin is required for publication" >&2; exit 1; }

# Refuse unsupported CLI versions before a start can change repository state.
HELP=$(git flow "$TYPE" start --help) || exit 1
[[ "$HELP" == *--no-fetch* && "$HELP" == *--no-worktree* ]] || {
  echo "start-branch.sh: Git-flow must support --no-fetch and --no-worktree; check the installed CLI" >&2
  exit 1
}
VERSION_FILES=()
if [ -n "$VERSION" ]; then
  command -v uv >/dev/null || { echo "start-branch.sh: uv is required for validated version updates" >&2; exit 1; }
  FILES=$(uv run --no-project --python '>=3.11' python "$SCRIPT_DIR/bump-version.py" --version "$VERSION" --check) || exit 1
  while IFS= read -r file; do VERSION_FILES+=("$file"); done <<< "$FILES"
fi

echo "start-branch.sh: starting $BRANCH"
git flow "$TYPE" start "$NAME" --no-fetch --no-worktree || { echo "start-branch.sh: git flow start failed" >&2; exit 1; }
if [ -n "$VERSION" ]; then
  uv run --no-project --python '>=3.11' python "$SCRIPT_DIR/bump-version.py" --version "$VERSION" >/dev/null || exit 1
  git add -- "${VERSION_FILES[@]}"
  if ! git diff --cached --quiet; then
    git commit -m "chore: bump version to $VERSION"
  fi
fi
if [ "$PUSH" = 1 ]; then
  git push -u origin "$BRANCH" || { echo "start-branch.sh: local branch exists but publication failed" >&2; exit 1; }
fi
echo "start-branch.sh: branch $BRANCH ready"
