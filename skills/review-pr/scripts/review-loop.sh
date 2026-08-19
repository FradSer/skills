#!/usr/bin/env bash
# review-loop.sh — one-poll CI + PR-comment watch for review-pr.
#
# The script is intentionally one-shot when called with --once. State makes
# repeated invocations equivalent to a persistent watch while fitting hosts
# whose background monitor requires a terminal result contract.

set -u

PR="${PR:-}"
REPO="${REPO:-}"
INTERVAL="${INTERVAL:-}"
ONCE=0
ACK=" ${ACK:-} "
EXCLUDE=" ${EXCLUDE:-} "

while [ $# -gt 0 ]; do
  case "$1" in
    --pr)        [ $# -ge 2 ] || { echo "review-loop.sh: $1 requires a value" >&2; exit 2; }; [ -n "$PR" ] || PR="$2"; shift 2 ;;
    --repo)      [ $# -ge 2 ] || { echo "review-loop.sh: $1 requires a value" >&2; exit 2; }; [ -n "$REPO" ] || REPO="$2"; shift 2 ;;
    --interval)  [ $# -ge 2 ] || { echo "review-loop.sh: $1 requires a value" >&2; exit 2; }; [ -n "$INTERVAL" ] || INTERVAL="$2"; shift 2 ;;
    --ack)       [ $# -ge 2 ] || { echo "review-loop.sh: $1 requires a value" >&2; exit 2; }; ACK="$ACK$2 "; shift 2 ;;
    --exclude)   [ $# -ge 2 ] || { echo "review-loop.sh: $1 requires a value" >&2; exit 2; }; EXCLUDE="$EXCLUDE$2 "; shift 2 ;;
    --once)      ONCE=1; shift ;;
    -h|--help)   sed -n '2,16p' "$0"; exit 0 ;;
    *)            echo "review-loop.sh: unknown arg: $1" >&2; exit 2 ;;
  esac
done

INTERVAL="${INTERVAL:-300}"
if ! [[ "$INTERVAL" =~ ^[0-9]+$ ]]; then
  INTERVAL=300
elif [ "$INTERVAL" -lt 60 ]; then
  INTERVAL=60
fi

if [ -z "$PR" ] || [ -z "$REPO" ]; then
  echo "review-loop.sh: --pr and --repo (or PR/REPO env) are required" >&2
  exit 2
fi

WATCH_MAX_SECONDS="${WATCH_MAX_SECONDS:-7200}"
if ! [[ "$WATCH_MAX_SECONDS" =~ ^[0-9]+$ ]]; then
  WATCH_MAX_SECONDS=7200
fi

if [ -z "${STATE_FILE:-}" ]; then
  STATE_FILE=$(git rev-parse --git-path "review-pr-watch-${PR}.json" 2>/dev/null \
    || printf '%s/review-pr-watch-%s-%s.json' "${TMPDIR:-/tmp}" "${REPO//\//-}" "$PR")
fi
LOCK_DIR="${LOCK_DIR:-${STATE_FILE}.lock}"
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  echo "review-loop.sh: another watch already owns $LOCK_DIR" >&2
  exit 75
fi
cleanup_lock() { rmdir "$LOCK_DIR" 2>/dev/null || true; }
trap cleanup_lock EXIT INT TERM

# A state file is only accepted for this exact PR and repository. Invalid or
# mismatched state is ignored rather than allowing one PR to affect another.
state_matches=0
if [ -f "$STATE_FILE" ] && jq -e --arg pr "$PR" --arg repo "$REPO" \
    '.pr == $pr and .repo == $repo' "$STATE_FILE" >/dev/null 2>&1; then
  state_matches=1
fi

metadata=$(gh pr view "$PR" --repo "$REPO" --json createdAt,headRefOid,state,mergedAt 2>/dev/null) || {
  echo "review-loop.sh: unable to read PR metadata; cursor was not advanced" >&2
  exit 1
}
created_at=$(jq -r '.createdAt // empty' <<<"$metadata" 2>/dev/null) || created_at=""
head_sha=$(jq -r '.headRefOid // empty' <<<"$metadata" 2>/dev/null) || head_sha=""
pr_state=$(jq -r '.state // empty' <<<"$metadata" 2>/dev/null) || pr_state=""
if [ -z "$created_at" ] || [ -z "$head_sha" ]; then
  echo "review-loop.sh: PR metadata is incomplete; cursor was not advanced" >&2
  exit 1
fi

since=$(jq -r '.since // empty' "$STATE_FILE" 2>/dev/null || true)
[ "$state_matches" = 1 ] && [ -n "$since" ] || since="$created_at"
deadline_epoch=$(jq -r '.deadline_epoch // empty' "$STATE_FILE" 2>/dev/null || true)
if ! [[ "$deadline_epoch" =~ ^[0-9]+$ ]]; then
  deadline_epoch=$(($(date +%s) + WATCH_MAX_SECONDS))
fi

# emitted_comments records delivery history only. acknowledged_comments is the
# durable ack set. A delivered-but-unacknowledged comment must replay after a
# crash, so delivery is never treated as acknowledgement.
emitted_comments=" "
acknowledged_comments=" "
if [ "$state_matches" = 1 ]; then
  saved_emitted=$(jq -r '.emitted_comments[]? // .seen_comments[]? // empty' "$STATE_FILE" 2>/dev/null || true)
  saved_ack=$(jq -r '.acknowledged_comments[]? // empty' "$STATE_FILE" 2>/dev/null || true)
  while IFS= read -r node; do [ -n "$node" ] && emitted_comments="$emitted_comments$node "; done <<<"$saved_emitted"
  while IFS= read -r node; do [ -n "$node" ] && acknowledged_comments="$acknowledged_comments$node "; done <<<"$saved_ack"
fi

# Explicit ACK/EXCLUDE values represent triage performed by the caller. They
# are persisted so a subsequent invocation does not need to repeat them.
for value in $ACK $EXCLUDE; do
  [ -n "$value" ] || continue
  case "$acknowledged_comments" in *" $value "*) ;; *) acknowledged_comments="$acknowledged_comments$value ";; esac
done

# A changed head SHA starts a new CI lifecycle. Comment state remains valid,
# but check buckets from the old commit must not suppress new results.
last_ci=$'\n'
if [ "$state_matches" = 1 ]; then
  saved_head=$(jq -r '.head_sha // empty' "$STATE_FILE" 2>/dev/null || true)
  if [ -n "$saved_head" ] && [ "$saved_head" = "$head_sha" ]; then
    saved_ci=$(jq -r '.last_ci[]? // empty' "$STATE_FILE" 2>/dev/null || true)
    while IFS= read -r line; do [ -n "$line" ] && last_ci="$last_ci$line"$'\n'; done <<<"$saved_ci"
  fi
fi

set_ci_bucket() {
  local name="$1" bucket="$2" line tmp=$'\n'
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    [[ "$line" == "${name}="* ]] || tmp="$tmp$line"$'\n'
  done <<<"$last_ci"
  last_ci="${tmp}${name}=${bucket}"$'\n'
}

persist_state() {
  local state_dir tmp seen_json ack_json ci_json
  state_dir=$(dirname "$STATE_FILE")
  mkdir -p "$state_dir" || { echo "review-loop.sh: cannot create state directory $state_dir" >&2; return 1; }
  seen_json=$(printf '%s' "$emitted_comments" | jq -Rsc 'split(" ") | map(select(length > 0))') || return 1
  ack_json=$(printf '%s' "$acknowledged_comments" | jq -Rsc 'split(" ") | map(select(length > 0))') || return 1
  ci_json=$(printf '%s' "$last_ci" | jq -Rsc 'split("\n") | map(select(length > 0))') || return 1
  tmp=$(mktemp "${STATE_FILE}.tmp.XXXXXX") || { echo "review-loop.sh: cannot create temporary state file" >&2; return 1; }
  if ! jq -n \
    --arg pr "$PR" --arg repo "$REPO" --arg head_sha "$head_sha" \
    --arg since "$since" --argjson deadline_epoch "$deadline_epoch" \
    --argjson emitted_comments "$seen_json" --argjson acknowledged_comments "$ack_json" \
    --argjson last_ci "$ci_json" \
    '{version:2,pr:$pr,repo:$repo,head_sha:$head_sha,since:$since,deadline_epoch:$deadline_epoch,emitted_comments:$emitted_comments,acknowledged_comments:$acknowledged_comments,last_ci:$last_ci}' \
    > "$tmp"; then
    rm -f "$tmp"
    return 1
  fi
  mv "$tmp" "$STATE_FILE" || { rm -f "$tmp"; echo "review-loop.sh: cannot replace state file" >&2; return 1; }
}

if [ "$pr_state" = "MERGED" ] || [ "$pr_state" = "CLOSED" ]; then
  echo "[status] PR #$PR is $pr_state"
  persist_state || exit 1
  exit 0
fi

if [ "$(date +%s)" -ge "$deadline_epoch" ]; then
  echo "[watch] deadline reached for PR #$PR"
  persist_state || exit 1
  exit 0
fi

poll_seen=" "
emit_comment() {
  local id="$1" line="$2"
  [ -n "$id" ] || return
  case "$acknowledged_comments" in *" $id "*) return ;; esac
  case "$poll_seen" in *" $id "*) return ;; esac
  echo "$line"
  poll_seen="$poll_seen$id "
  case "$emitted_comments" in *" $id "*) ;; *) emitted_comments="$emitted_comments$id ";; esac
}

api_ok=true
checks=$(gh pr checks "$PR" --repo "$REPO" --json name,bucket 2>/dev/null) || {
  echo "[error] unable to read PR checks; retaining CI state" >&2
  api_ok=false
}
if [ -n "${checks:-}" ]; then
  while IFS=$'\t' read -r name bucket; do
    [ -z "$name" ] && continue
    case "$last_ci" in *$'\n'"${name}=${bucket}"$'\n'*) continue ;; esac
    echo "[ci] $name: $bucket"
    set_ci_bucket "$name" "$bucket"
  done < <(jq -r '.[] | select(.bucket!="pending") | "\(.name)\t\(.bucket)"' <<<"$checks" 2>/dev/null)
fi

issue_comments=$(gh api --paginate "repos/$REPO/issues/$PR/comments?since=$since" \
  --jq '.[] | "\(.node_id)\t[comment] issue node=\(.node_id) id=\(.id) @\(.user.login): \(.body | gsub("\\n";" "))"' 2>/dev/null) || {
  echo "[error] unable to read issue comments; retaining cursor" >&2
  api_ok=false
}
while IFS=$'\t' read -r id line; do emit_comment "$id" "$line"; done <<<"${issue_comments:-}"

inline_comments=$(gh api --paginate "repos/$REPO/pulls/$PR/comments?since=$since" \
  --jq '.[] | "\(.node_id)\t[comment] inline node=\(.node_id) id=\(.id) @\(.user.login) \(.path):\(.line // .original_line): \(.body | gsub("\\n";" "))"' 2>/dev/null) || {
  echo "[error] unable to read inline review comments; retaining cursor" >&2
  api_ok=false
}
while IFS=$'\t' read -r id line; do emit_comment "$id" "$line"; done <<<"${inline_comments:-}"

review_summaries=$(gh api --paginate "repos/$REPO/pulls/$PR/reviews" \
  --jq '.[] | select(.state != "PENDING") | "\(.node_id)\t[comment] review node=\(.node_id) id=\(.id) @\(.user.login) [\(.state)]: \(.body | gsub("\\n";" "))"' 2>/dev/null) || {
  echo "[error] unable to read review summaries; retaining cursor" >&2
  api_ok=false
}
while IFS=$'\t' read -r id line; do emit_comment "$id" "$line"; done <<<"${review_summaries:-}"

[ "$api_ok" = true ] && since=$(date -u +%Y-%m-%dT%H:%M:%SZ)
persist_state || exit 1

if [ "$ONCE" = 1 ]; then
  exit 0
fi
sleep "$INTERVAL"
exec "$0" --pr "$PR" --repo "$REPO" --interval "$INTERVAL" --ack "$ACK" --exclude "$EXCLUDE"
