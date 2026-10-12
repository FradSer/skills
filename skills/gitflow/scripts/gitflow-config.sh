#!/usr/bin/env bash
# Read git-flow-next topic/base configuration, retaining legacy AVH keys.

load_gitflow_config() {
  local type="$1" configured_type
  configured_type=$(git config --get "gitflow.branch.$type.type" 2>/dev/null || true)
  if [ -n "$configured_type" ]; then
    [ "$configured_type" = topic ] || { echo "gitflow: $type must be configured as a topic branch type" >&2; return 1; }
    PREFIX=$(git config --get "gitflow.branch.$type.prefix") || return 1
    MAIN_BRANCH=$(git config --get "gitflow.branch.$type.parent") || return 1
    START_BRANCH=$(git config --get "gitflow.branch.$type.startpoint" 2>/dev/null || printf '%s' "$MAIN_BRANCH")
    case "$type" in
      feature)
        DEVELOP_BRANCH="$MAIN_BRANCH"
        MAIN_BRANCH=$(git config --get "gitflow.branch.$DEVELOP_BRANCH.parent" 2>/dev/null || printf '%s' "$DEVELOP_BRANCH") ;;
      release) DEVELOP_BRANCH="$START_BRANCH" ;;
      hotfix)
        DEVELOP_BRANCH=$(git config --get gitflow.branch.feature.parent 2>/dev/null \
          || git config --get gitflow.branch.release.startpoint 2>/dev/null \
          || printf '%s' "$MAIN_BRANCH") ;;
    esac
    local base
    for base in "$START_BRANCH" "$MAIN_BRANCH" "$DEVELOP_BRANCH"; do
      [ "$(git config --get "gitflow.branch.$base.type" 2>/dev/null)" = base ] || {
        echo "gitflow: $base is not a configured base branch" >&2
        return 1
      }
    done
  else
    PREFIX=$(git config --get "gitflow.prefix.$type") || return 1
    MAIN_BRANCH=$(git config --get gitflow.branch.master) || return 1
    DEVELOP_BRANCH=$(git config --get gitflow.branch.develop) || return 1
    START_BRANCH="$DEVELOP_BRANCH"
    [ "$type" != hotfix ] || START_BRANCH="$MAIN_BRANCH"
  fi
  [ -n "$MAIN_BRANCH" ] && [ -n "$DEVELOP_BRANCH" ] && [ -n "$START_BRANCH" ] || return 1
}
