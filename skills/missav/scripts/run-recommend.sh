#!/usr/bin/env bash
# End-to-end recommend workflow (tested defaults).
# Usage: run-recommend.sh [--prefs ~/.missav/preferences.json]
set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_PREFS="${HOME}/.missav/preferences.json"
PREFS="$DEFAULT_PREFS"
SESSION="missav-run-$(date +%s)"
export MISSAV_SESSION="$SESSION"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --prefs) PREFS="$2"; shift 2 ;;
    --cdp) export MISSAV_CDP_PORT="$2"; export MISSAV_USE_USER_CHROME=1; shift 2 ;;
    --user-chrome) export MISSAV_USE_USER_CHROME=1; shift ;;
    --no-user-chrome|--isolated) export MISSAV_USE_USER_CHROME=0; shift ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

if [[ "$PREFS" == "$DEFAULT_PREFS" ]]; then
  node "$SCRIPT_DIR/preferences.mjs" init --dir "$(dirname "$PREFS")" >/dev/null
elif [[ ! -f "$PREFS" ]]; then
  echo "FAIL: custom preferences file does not exist: $PREFS" >&2
  exit 2
fi

WORK_DIR="$(mktemp -d "${TMPDIR:-/tmp}/missav-run.XXXXXX")"
cleanup() {
  rm -rf "$WORK_DIR"
}
trap cleanup EXIT

QUERY_FILE="$WORK_DIR/queries"
PREFS_FILE="$PREFS" python3 -c "
import json
import os
p = json.load(open(os.environ['PREFS_FILE']))
q = []
for g in p.get('likes', {}).get('genres', []):
    q.append(g)
for l in p.get('likes', {}).get('labels', []):
    q.append(l.lower())
for pf in p.get('likes', {}).get('performers', []):
    q.append(pf)
dk = p.get('search', {}).get('defaultKeyword')
if dk and dk not in q:
    q.append(dk)
if not q:
    q = ['sm']
seen = set()
for item in q:
    value = str(item).strip()
    if value and value.lower() not in seen:
        seen.add(value.lower())
        print(value)
" > "$QUERY_FILE"

DEFAULT_FILTER="$(PREFS_FILE="$PREFS" python3 -c "
import json
import os
p = json.load(open(os.environ['PREFS_FILE']))
print(p.get('search', {}).get('defaultFilter') or '')
")"

# shellcheck source=lib/browser-env.sh
source "$SCRIPT_DIR/lib/browser-env.sh"
missav_browser_start

MERGED="$WORK_DIR/listings.json"
echo "[]" > "$MERGED"

QUERY_INDEX=0
while IFS= read -r q; do
  QUERY_INDEX=$((QUERY_INDEX + 1))
  [[ "$MISSAV_ACCESS_BLOCKED" -eq 1 ]] && break
  if [[ -n "$DEFAULT_FILTER" ]]; then
    URL="$(node "$SCRIPT_DIR/build-search-url.mjs" search "$q" --filter "$DEFAULT_FILTER")"
  else
    URL="$(node "$SCRIPT_DIR/build-search-url.mjs" search "$q")"
  fi
  echo "=== Query $QUERY_INDEX ===" >&2
  if "$SCRIPT_DIR/browse-page.sh" "$URL" --session "$SESSION" --continue; then
    TMP="$WORK_DIR/listings-$QUERY_INDEX.json"
    if "$SCRIPT_DIR/extract-listings.sh" --session "$SESSION" --output "$TMP"; then
      MERGED="$MERGED" TMP="$TMP" python3 <<PY
import json, os
merged = json.load(open(os.environ["MERGED"]))
add = json.load(open(os.environ["TMP"]))
by = {x["href"]: x for x in merged}
for x in add:
    if x.get("href"):
        by[x["href"]] = x
json.dump(list(by.values()), open(os.environ["MERGED"], "w"), ensure_ascii=False, indent=2)
print(f"merged total: {len(by)}")
PY
    else
      EXTRACT_STATUS=$?
      if [[ "$EXTRACT_STATUS" -eq "$MISSAV_ACCESS_BLOCKED_EXIT" ]]; then
        echo "STOP: $MISSAV_ACCESS_BLOCKED_MESSAGE" >&2
        MISSAV_ACCESS_BLOCKED=1
        break
      fi
      echo "WARN: no listings for query $QUERY_INDEX" >&2
    fi
  else
    BROWSE_STATUS=$?
    if [[ "$BROWSE_STATUS" -eq "$MISSAV_ACCESS_BLOCKED_EXIT" ]]; then
      echo "STOP: $MISSAV_ACCESS_BLOCKED_MESSAGE" >&2
      MISSAV_ACCESS_BLOCKED=1
      break
    fi
    echo "WARN: browse failed for query $QUERY_INDEX" >&2
  fi
done < "$QUERY_FILE"

missav_browser_close

if [[ "$MISSAV_ACCESS_BLOCKED" -eq 1 ]]; then
  exit "$MISSAV_ACCESS_BLOCKED_EXIT"
fi

TOTAL="$(python3 -c "import json; print(len(json.load(open('$MERGED'))))")"
if [[ "$TOTAL" -eq 0 ]]; then
  echo "FAIL: no listings from any query. See references/browser-troubleshooting.md" >&2
  exit 1
fi

RANKED="$WORK_DIR/ranked.json"
node "$SCRIPT_DIR/filter-recommendations.mjs" "$MERGED" --prefs "$PREFS" --limit 10 > "$RANKED"

export MISSAV_SESSION="${SESSION}-enrich"
missav_browser_start
ENRICHED="$WORK_DIR/enriched.json"
if "$SCRIPT_DIR/enrich-listings.sh" \
  --input "$MERGED" \
  --ranked "$RANKED" \
  --output "$ENRICHED" \
  --top 3 \
  --session "$MISSAV_SESSION"; then
  node "$SCRIPT_DIR/filter-recommendations.mjs" "$ENRICHED" --prefs "$PREFS" --limit 5
else
  ENRICH_STATUS=$?
  if [[ "$ENRICH_STATUS" -eq "$MISSAV_ACCESS_BLOCKED_EXIT" ]]; then
    echo "STOP: $MISSAV_ACCESS_BLOCKED_MESSAGE" >&2
    exit "$MISSAV_ACCESS_BLOCKED_EXIT"
  fi
  echo "WARN: detail enrichment failed, showing list-only results" >&2
  cat "$RANKED"
fi
