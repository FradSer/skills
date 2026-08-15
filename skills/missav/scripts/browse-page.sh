#!/usr/bin/env bash
# Open a missav URL with tested browser defaults.
# Usage: browse-page.sh <url> [--session NAME] [--continue]
set -euo pipefail

URL="${1:?Usage: browse-page.sh <url> [--session NAME] [--continue]}"
shift || true

CONTINUE=0
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/browser-env.sh
source "$SCRIPT_DIR/lib/browser-env.sh"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --session) MISSAV_SESSION="$2"; export MISSAV_SESSION; shift 2 ;;
    --continue) CONTINUE=1; shift ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

[[ "$CONTINUE" -eq 1 ]] || missav_browser_start

if missav_open_page "$URL" "listing"; then
  :
else
  BROWSE_STATUS=$?
  echo "FAIL: could not load $URL" >&2
  if [[ "$BROWSE_STATUS" -eq "$MISSAV_ACCESS_BLOCKED_EXIT" ]]; then
    exit "$MISSAV_ACCESS_BLOCKED_EXIT"
  fi
  exit 1
fi

missav_scroll_load 4
missav_page_title
