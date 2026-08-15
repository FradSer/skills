#!/usr/bin/env bash
# Extract detail page metadata + description from current agent-browser page.
# Usage: extract-detail.sh [--session NAME] [--output FILE]
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
  _missav_ab_base eval --stdin < "$SCRIPT_DIR/extract-detail.js" \
    | node "$SCRIPT_DIR/normalize-eval-output.mjs" --object "$OUTPUT"
  python3 -c "
import json, sys
d = json.load(open('$OUTPUT'))
if d.get('blocked'):
    print(f\"WARN: detail blocked ({d.get('blockReason')}) url={d.get('href')}\", file=sys.stderr)
    sys.exit(1)
if not d.get('description'):
    print('WARN: empty description', file=sys.stderr)
    sys.exit(1)
" || exit 1
else
  _missav_ab_base eval --stdin < "$SCRIPT_DIR/extract-detail.js"
fi
