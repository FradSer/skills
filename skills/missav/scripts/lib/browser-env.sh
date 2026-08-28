# Shared agent-browser defaults for missav (source, do not execute).

MISSAV_CHROME="${MISSAV_CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
MISSAV_SESSION="${MISSAV_SESSION:-missav-$(date +%s)}"
MISSAV_ACCESS_BLOCKED=0
MISSAV_ACCESS_BLOCKED_MESSAGE="Automated access stopped after a Cloudflare challenge. Authorized API or site-owner access is required."
export MISSAV_CHROME MISSAV_SESSION MISSAV_ACCESS_BLOCKED MISSAV_ACCESS_BLOCKED_MESSAGE

MISSAV_ACCESS_BLOCKED_EXIT=42

_missav_ab_base() {
  local -a args=()
  if [[ -f "$MISSAV_CHROME" ]]; then
    args+=(--executable-path "$MISSAV_CHROME")
  fi
  args+=(--headed --session "$MISSAV_SESSION")
  agent-browser "${args[@]}" "$@"
}

missav_ab() {
  _missav_ab_base "$@"
}

# Kill global daemon AND session-scoped state. Call once at task start.
missav_browser_start() {
  agent-browser --session "$MISSAV_SESSION" close 2>/dev/null || true
  agent-browser close 2>/dev/null || true
  sleep 2
}

missav_browser_close() {
  agent-browser --session "$MISSAV_SESSION" close 2>/dev/null || true
}

missav_wait_page() {
  local ms="${1:-8000}"
  missav_ab wait "$ms"
}

missav_page_title() {
  missav_ab get title 2>/dev/null || echo ""
}

missav_page_url() {
  missav_ab get url 2>/dev/null || echo ""
}

missav_is_cloudflare_title() {
  echo "$1" | grep -qiE 'just a moment|请稍候|checking your browser|performing security verification|attention required.*cloudflare|verify you are human'
}

missav_is_cloudflare_body() {
  echo "$1" | grep -qiE 'enable javascript and cookies to continue|verifying you are human|performing security verification|checking your browser before accessing|attention required.*cloudflare'
}

missav_is_bad_url() {
  local url="$1"
  local kind="${2:-page}"
  echo "$url" | grep -qE '/pop(\?|$)|tsyndicate|bit\.ly' && return 0
  if [[ "$kind" == "detail" ]]; then
    echo "$url" | grep -qE '/search/|/actresses/|/genres/|/tags/' && return 0
    echo "$url" | grep -qE 'missav\.(ws|com)/cn/[a-z0-9][a-z0-9-]*[a-z0-9](/|$|\?)' && return 1
    return 0
  fi
  # listing/search pages: allow /search/ but reject ad popups
  echo "$url" | grep -qE 'missav\.(ws|com)/' && return 1
  return 0
}

missav_mark_access_blocked() {
  MISSAV_ACCESS_BLOCKED=1
  export MISSAV_ACCESS_BLOCKED
  printf '%s\n' "$MISSAV_ACCESS_BLOCKED_MESSAGE" >&2
  return "$MISSAV_ACCESS_BLOCKED_EXIT"
}

missav_stop_if_challenged() {
  local title body
  title="$(missav_page_title)"
  if missav_is_cloudflare_title "$title"; then
    missav_mark_access_blocked
    return "$MISSAV_ACCESS_BLOCKED_EXIT"
  fi

  body="$(missav_ab get text body 2>/dev/null || true)"
  if missav_is_cloudflare_body "$body"; then
    missav_mark_access_blocked
    return "$MISSAV_ACCESS_BLOCKED_EXIT"
  fi
  return 0
}

missav_handle_age_gate() {
  missav_ab find text "我已满 18 岁" click 2>/dev/null \
    || missav_ab find text "I am 18" click 2>/dev/null \
    || missav_ab find text "Enter" click 2>/dev/null \
    || true
  missav_wait_page 3000
}

missav_scroll_load() {
  local rounds="${1:-4}"
  local i
  for ((i = 1; i <= rounds; i++)); do
    missav_ab scroll down 1200
    missav_wait_page 2000
  done
}

# Open a video/listing URL and verify we landed on a real page (not CF/ad redirect).
missav_open_page() {
  local url="$1"
  local kind="${2:-page}"
  echo "Opening $kind: $url" >&2
  missav_ab open "$url"
  missav_wait_page 8000
  missav_stop_if_challenged || return $?
  missav_handle_age_gate
  missav_stop_if_challenged || return $?
  local final_url
  final_url="$(missav_page_url)"
  if missav_is_bad_url "$final_url" "$kind"; then
    echo "WARN: redirected to bad URL ($kind): $final_url" >&2
    return 1
  fi
  return 0
}
