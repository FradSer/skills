#!/usr/bin/env bash
# Extract missav listing cards from the current agent-browser page.
# Usage: extract-listings.sh [--session NAME] [--output FILE]
set -euo pipefail

SESSION=""
OUTPUT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --session) SESSION="$2"; shift 2 ;;
    --output)  OUTPUT="$2"; shift 2 ;;
    --cdp)     export MISSAV_CDP_PORT="$2"; export MISSAV_USE_USER_CHROME=1; shift 2 ;;
    --user-chrome) export MISSAV_USE_USER_CHROME=1; shift ;;
    --no-user-chrome|--isolated) export MISSAV_USE_USER_CHROME=0; shift ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/browser-env.sh
source "$SCRIPT_DIR/lib/browser-env.sh"

[[ -n "$SESSION" ]] && MISSAV_SESSION="$SESSION" && export MISSAV_SESSION

if ! missav_stop_if_challenged; then
  exit "$MISSAV_ACCESS_BLOCKED_EXIT"
fi

TMP_RAW="$(mktemp "${TMPDIR:-/tmp}/missav-eval.XXXXXX")"
trap 'rm -f "$TMP_RAW"' EXIT

if _missav_ab_base eval --stdin < "$SCRIPT_DIR/extract-listings.js" > "$TMP_RAW"; then
  RAW_CONTENT="$(cat "$TMP_RAW")"
  if echo "$RAW_CONTENT" | grep -qiE 'just a moment|请稍候|checking your browser|attention required.*cloudflare|verifying you are human'; then
    missav_mark_access_blocked || true
    exit "$MISSAV_ACCESS_BLOCKED_EXIT"
  fi
  if [[ -n "$OUTPUT" ]]; then
    node "$SCRIPT_DIR/normalize-eval-output.mjs" "$OUTPUT" < "$TMP_RAW"
  else
    cat "$TMP_RAW"
  fi
else
  EVAL_STATUS=$?
  if ! missav_stop_if_challenged; then
    exit "$MISSAV_ACCESS_BLOCKED_EXIT"
  fi
  exit "$EVAL_STATUS"
fi

if ! missav_stop_if_challenged; then
  exit "$MISSAV_ACCESS_BLOCKED_EXIT"
fi

if [[ -n "$OUTPUT" ]]; then
  COUNT="$(python3 -c "import json; print(len(json.load(open('$OUTPUT'))))")"
  if [[ "$COUNT" -eq 0 ]]; then
    if ! missav_stop_if_challenged; then
      exit "$MISSAV_ACCESS_BLOCKED_EXIT"
    fi
    echo "WARN: 0 listings (title=$(missav_page_title), url=$(missav_page_url))" >&2
    exit 1
  fi
fi
