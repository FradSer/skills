#!/usr/bin/env bash
# End-to-end recommend workflow (tested defaults).
# Usage: run-recommend.sh [--prefs ~/.missav/preferences.json]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PREFS="${HOME}/.missav/preferences.json"
SESSION="missav-run-$(date +%s)"
export MISSAV_SESSION="$SESSION"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --prefs) PREFS="$2"; shift 2 ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

node "$SCRIPT_DIR/preferences.mjs" init >/dev/null

QUERIES="$(python3 -c "
import json
p = json.load(open('$PREFS'))
q = []
for g in p.get('likes', {}).get('genres', []):
    q.append(g)
for l in p.get('likes', {}).get('labels', []):
    q.append(l.lower())
dk = p.get('search', {}).get('defaultKeyword')
if dk and dk not in q:
    q.append(dk)
if not q:
    q = ['sm']
print(' '.join(q))
")"

# shellcheck source=lib/browser-env.sh
source "$SCRIPT_DIR/lib/browser-env.sh"
missav_browser_start

MERGED="/tmp/missav-run-listings.json"
echo "[]" > "$MERGED"

for q in $QUERIES; do
  [[ "$MISSAV_ACCESS_BLOCKED" -eq 1 ]] && break
  URL="$(node "$SCRIPT_DIR/build-search-url.mjs" search "$q")"
  echo "=== Query: $q → $URL ===" >&2
  if "$SCRIPT_DIR/browse-page.sh" "$URL" --session "$SESSION" --continue; then
    TMP="/tmp/missav-run-$q.json"
    if "$SCRIPT_DIR/extract-listings.sh" --session "$SESSION" --output "$TMP"; then
      python3 <<PY
import json
merged = json.load(open("$MERGED"))
add = json.load(open("$TMP"))
by = {x["href"]: x for x in merged}
for x in add:
    if x.get("href"):
        by[x["href"]] = x
json.dump(list(by.values()), open("$MERGED", "w"), ensure_ascii=False, indent=2)
print(f"merged total: {len(by)}")
PY
    else
      echo "WARN: no listings for query $q" >&2
    fi
  else
    BROWSE_STATUS=$?
    if [[ "$BROWSE_STATUS" -eq "$MISSAV_ACCESS_BLOCKED_EXIT" ]]; then
      echo "STOP: $MISSAV_ACCESS_BLOCKED_MESSAGE" >&2
      MISSAV_ACCESS_BLOCKED=1
      break
    fi
    echo "WARN: browse failed for $q" >&2
  fi
done

missav_browser_close

if [[ "$MISSAV_ACCESS_BLOCKED" -eq 1 ]]; then
  exit "$MISSAV_ACCESS_BLOCKED_EXIT"
fi

TOTAL="$(python3 -c "import json; print(len(json.load(open('$MERGED'))))")"
if [[ "$TOTAL" -eq 0 ]]; then
  echo "FAIL: no listings from any query. See references/browser-troubleshooting.md" >&2
  exit 1
fi

RANKED="/tmp/missav-run-ranked.json"
node "$SCRIPT_DIR/filter-recommendations.mjs" "$MERGED" --prefs "$PREFS" --limit 10 > "$RANKED"

export MISSAV_SESSION="${SESSION}-enrich"
missav_browser_start
ENRICHED="/tmp/missav-run-enriched.json"
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
