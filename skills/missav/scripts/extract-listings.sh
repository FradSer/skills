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
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/browser-env.sh
source "$SCRIPT_DIR/lib/browser-env.sh"

[[ -n "$SESSION" ]] && MISSAV_SESSION="$SESSION" && export MISSAV_SESSION

if [[ -n "$OUTPUT" ]]; then
  _missav_ab_base eval --stdin < "$SCRIPT_DIR/extract-listings.js" \
    | node "$SCRIPT_DIR/normalize-eval-output.mjs" "$OUTPUT"
else
  _missav_ab_base eval --stdin < "$SCRIPT_DIR/extract-listings.js"
fi

if [[ -n "$OUTPUT" ]]; then
  COUNT="$(python3 -c "import json; print(len(json.load(open('$OUTPUT'))))")"
  if [[ "$COUNT" -eq 0 ]]; then
    echo "WARN: 0 listings (title=$(missav_page_title), url=$(missav_page_url))" >&2
    exit 1
  fi
fi
