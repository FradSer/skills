# Browser Access Handling

## Cloudflare `Just a moment...`

A Cloudflare challenge is an explicit access-control signal, not a transient page-load condition.

| Symptom | Required behavior |
|---|---|
| Title is `Just a moment...`, `请稍候`, or `Checking your browser` | Stop the current workflow immediately. Do not navigate to another search or detail page. |
| A child script exits with status `42` | Treat it as `blocked_by_challenge`; preserve cleanup and report that a site-authorized API or access path is required. |

Do not retry challenges, rotate proxies or IPs, modify browser fingerprints, or use challenge-solving services. These are attempts to evade the site owner's access controls and are unsupported by this skill.

For repeatable automation, use an official API, a data export, or a dedicated endpoint and credentials granted by the site operator. Implement caching, deduplication, bounded concurrency, and `429`/`Retry-After` handling on that authorized channel.

## `daemon already running` / ignored `--executable-path`

**Cause:** A global `agent-browser` daemon can outlive a previous session and retain incompatible launch settings.

**Fix:**

- `missav_browser_start` closes both the named session and global daemon, then waits 2 seconds.
- Reuse a single named session with `--continue` while access remains available.
- Do not start a new browser session after an access challenge in the same workflow.

## Empty extraction `[]`

| Cause | Detection | Fix |
|---|---|---|
| Access challenge | title check | stop the workflow |
| Ad redirect `/pop?url=` | `missav_is_bad_url` | skip and log a warning |
| Search URL rejected on listing page | listing URL validation | allow `/search/` only for listing pages |
| Double-encoded JSON `"[]"` string | `normalize-eval-output.mjs` | always write a real JSON array |
| Non-video links in results | `isVideoHref()` in `extract-listings.js` | filter pop/search URLs |

## Detail page: empty description

| Cause | Fix |
|---|---|
| Redirect to ad (`missav.ws/pop`) | `extract-detail.js` sets `blocked: true, blockReason: ad-redirect` |
| Access challenge | stop the workflow; do not continue with the next candidate |
| Collapsed text | click 展开/更多 before evaluation |
| Wrong merge target | pass `--ranked` to `enrich-listings.sh` so it selects scored items |

## Duration `无码影片`

**Cause:** Badge text was parsed as duration.

**Fix:** `parseDuration` returns `minutes: null` for 无码/uncensored/leak labels.

## Authorized recommendation workflow

```bash
./skills/missav/scripts/run-recommend.sh --prefs ~/.missav/preferences.json
```

The workflow searches, merges, ranks, and enriches only while the site allows access. A Cloudflare challenge ends the run with exit status `42`; obtain a site-authorized API or access path before retrying automated access.
