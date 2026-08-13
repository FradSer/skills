#!/usr/bin/env bash
# start-branch.sh — mechanical steps of the git-flow start pipeline (feature/hotfix/release).
#
# Judgment stays in the skill: the agent decides the branch name / version bump
# semantics from the conversation or commit analysis. This script only executes
# the deterministic parts — clean-tree pre-flight, git-flow start, optional
# version-file bump commit, and push.
#
# Usage:
#   bash start-branch.sh --type feature --name <slug>
#   bash start-branch.sh --type hotfix --version <x.y.z>
#   bash start-branch.sh --type release --version <x.y.z>
#   bash start-branch.sh --type <type> --name <n> --version <v> --no-push
#
# Flags:
#   --type feature|hotfix|release   required
#   --name <slug>                   branch name for feature (or fallback for hotfix/release)
#   --version <x.y.z>               target version (hotfix/release; optional with --name)
#   --no-push                       do not push the branch to origin

set -uo pipefail

TYPE=""
NAME=""
VERSION=""
PUSH=1

while [ $# -gt 0 ]; do
  case "$1" in
    --type) TYPE="${2:-}"; shift 2 ;;
    --name) NAME="${2:-}"; shift 2 ;;
    --version) VERSION="${2:-}"; shift 2 ;;
    --no-push) PUSH=0; shift ;;
    -h|--help) sed -n '2,14p' "$0"; exit 0 ;;
    *) echo "start-branch.sh: unknown arg: $1" >&2; exit 2 ;;
  esac
done

case "$TYPE" in
  feature|hotfix|release) ;;
  *) echo "start-branch.sh: --type must be feature|hotfix|release" >&2; exit 2 ;;
esac

# Pre-flight: clean tree required before any git-flow start.
if [ -n "$(git status --porcelain)" ]; then
  echo "start-branch.sh: working tree is dirty — commit or stash before starting a branch" >&2
  exit 1
fi

# Resolve target name/version.
if [ -z "$NAME" ] && [ -z "$VERSION" ]; then
  echo "start-branch.sh: --name or --version is required" >&2
  exit 2
fi
if [ -z "$NAME" ]; then NAME="$VERSION"; fi

BRANCH="$TYPE/$NAME"
if git rev-parse --verify --quiet "$BRANCH" >/dev/null 2>&1; then
  echo "start-branch.sh: branch $BRANCH already exists" >&2
  exit 1
fi

echo "start-branch.sh: git flow $TYPE start $NAME"
if ! git flow "$TYPE" start "$NAME"; then
  echo "start-branch.sh: git flow start failed" >&2
  exit 1
fi

# hotfix/release: bump version files and commit in one step.
if [ -n "$VERSION" ]; then
  echo "start-branch.sh: bumping version to $VERSION"
  # Common version file locations; the agent may pass extra files via a follow-up commit.
  for f in package.json VERSION version.txt pyproject.toml Cargo.toml; do
    if [ -f "$f" ]; then
      sed -i.bak -E "s/\"version\": \"[0-9]+\.[0-9]+\.[0-9]+\"/\"version\": \"$VERSION\"/" "$f" 2>/dev/null \
        || sed -i.bak -E "s/^version *= *\"[0-9]+\.[0-9]+\.[0-9]+\"/version = \"$VERSION\"/" "$f" 2>/dev/null \
        || true
      rm -f "$f.bak"
    fi
  done
  if [ -n "$(git status --porcelain)" ]; then
    git add -u
    git commit -m "chore: bump version to $VERSION"
  fi
fi

if [ "$PUSH" = 1 ]; then
  echo "start-branch.sh: git push -u origin $BRANCH"
  git push -u origin "$BRANCH" || { echo "start-branch.sh: push failed" >&2; exit 1; }
fi

echo "start-branch.sh: branch $BRANCH ready"
