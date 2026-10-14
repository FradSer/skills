#!/usr/bin/env bash
# Fetch detail pages for top-ranked candidates and merge descriptions.
#
# Usage:
#   enrich-listings.sh --input listings.json --ranked ranked.json --output enriched.json [--top 5]
#
# --ranked: filter-recommendations.mjs output (uses .items sorted by score)
# Without --ranked: enriches first N items from --input (legacy, not recommended)
set -euo pipefail

INPUT=""
RANKED=""
OUTPUT=""
TOP=5
SESSION=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --input)   INPUT="$2"; shift 2 ;;
    --ranked)  RANKED="$2"; shift 2 ;;
    --output)  OUTPUT="$2"; shift 2 ;;
    --top)     TOP="$2"; shift 2 ;;
    --session) SESSION="$2"; shift 2 ;;
    --cdp)     export MISSAV_CDP_PORT="$2"; export MISSAV_USE_USER_CHROME=1; shift 2 ;;
    --user-chrome) export MISSAV_USE_USER_CHROME=1; shift ;;
    --no-user-chrome|--isolated) export MISSAV_USE_USER_CHROME=0; shift ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

[[ -n "$INPUT" && -n "$OUTPUT" ]] || {
  echo "Usage: enrich-listings.sh --input listings.json --ranked ranked.json --output enriched.json [--top 5]" >&2
  exit 1
}

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/browser-env.sh
source "$SCRIPT_DIR/lib/browser-env.sh"

[[ -n "$SESSION" ]] && MISSAV_SESSION="$SESSION" && export MISSAV_SESSION

# Reuse an existing session when --session is passed (e.g. run-recommend.sh).
# Only reset browser when no session was provided.
[[ -n "$SESSION" ]] || missav_browser_start

ENRICH_TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/missav-enrich.XXXXXX")"
trap 'rm -rf "$ENRICH_TMP_DIR"' EXIT
URLS_FILE="$ENRICH_TMP_DIR/urls.txt"
DETAILS_FILE="$ENRICH_TMP_DIR/details.jsonl"
: > "$DETAILS_FILE"

python3 <<PY > "$URLS_FILE"
import json

def load_items(path):
    data = json.load(open(path))
    if isinstance(data, dict) and "items" in data:
        return data["items"]
    if isinstance(data, list):
        return data
    return []

items = load_items("$RANKED") if "$RANKED" else json.load(open("$INPUT"))
items = sorted(items, key=lambda x: x.get("score", 0), reverse=True)
seen = set()
for item in items:
    href = item.get("href")
    if not href or href in seen:
        continue
    seen.add(href)
    print(href)
    if len(seen) >= int("$TOP"):
        break
PY

OK=0
FAIL=0

while IFS= read -r href; do
  [[ "$MISSAV_ACCESS_BLOCKED" -eq 1 ]] && break
  [[ -z "$href" ]] && continue
  if ! missav_open_page "$href" "detail"; then
    if [[ "$MISSAV_ACCESS_BLOCKED" -eq 1 ]]; then
      echo "STOP: $MISSAV_ACCESS_BLOCKED_MESSAGE" >&2
      break
    fi
    echo "SKIP: bad landing for $href" >&2
    FAIL=$((FAIL + 1))
    continue
  fi
  missav_ab find text "展开" click 2>/dev/null || missav_ab find text "更多" click 2>/dev/null || true
  missav_wait_page 1500
  TMP="$ENRICH_TMP_DIR/detail-$$.json"
  if _missav_ab_base eval --stdin < "$SCRIPT_DIR/extract-detail.js" | node "$SCRIPT_DIR/normalize-eval-output.mjs" --object "$TMP"; then
    if [[ -f "$TMP" ]] && python3 -c "import json, sys; d=json.load(open('$TMP')); sys.exit(0 if d.get('blockReason') == 'cloudflare' else 1)"; then
      missav_mark_access_blocked || true
      break
    fi
    if python3 -c "import json; d=json.load(open('$TMP')); exit(0 if d.get('description') and not d.get('blocked') else 1)"; then
      python3 -c "import json; print(json.dumps(json.load(open('$TMP')), ensure_ascii=False))" >> "$DETAILS_FILE"
      OK=$((OK + 1))
      continue
    fi
  fi
  if ! missav_stop_if_challenged; then
    break
  fi
  echo "SKIP: no description for $href" >&2
  FAIL=$((FAIL + 1))
done < "$URLS_FILE"

missav_browser_close

INPUT="$INPUT" OUTPUT="$OUTPUT" DETAILS_FILE="$DETAILS_FILE" python3 <<'PY'
import json, os
from pathlib import Path

listings = json.load(open(os.environ["INPUT"]))
details = []
for line in Path(os.environ["DETAILS_FILE"]).read_text().splitlines():
    if not line.strip():
        continue
    d = json.loads(line)
    if d.get("blocked") or not d.get("description"):
        continue
    details.append(d)

by_href = {d["href"]: d for d in details if d.get("href")}
merged = []
for item in listings:
    extra = by_href.get(item.get("href"), {})
    merged.append({**item, **{k: v for k, v in extra.items() if v not in (None, "", []) and k != "blocked"}})
json.dump(merged, open(os.environ["OUTPUT"], "w"), ensure_ascii=False, indent=2)
print(f"Merged {len(details)} descriptions into {os.environ['OUTPUT']}")
PY

echo "Detail fetch: ok=$OK fail=$FAIL" >&2
if [[ "$MISSAV_ACCESS_BLOCKED" -eq 1 ]]; then
  exit "$MISSAV_ACCESS_BLOCKED_EXIT"
fi
[[ "$OK" -gt 0 ]]
