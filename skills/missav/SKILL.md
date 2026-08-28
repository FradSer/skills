---
name: missav
description: Browse missav.ws AV listings with agent-browser, extract title/duration/url
  from listing cards, enrich detail-page plot descriptions for genre analysis, and
  rank recommendations against user preferences stored in ~/.missav/ (genres/types,
  performers, labels/studios, keywords, duration). Learns from user feedback each
  session. Use when finding AV on missav, searching /cn/search/{query}, analyzing
  plot descriptions, or getting personalized recommendations.
metadata:
  requires:
    bins:
    - agent-browser
disable-model-invocation: true
---

# missav

Browse [missav.ws](https://missav.ws) with **agent-browser**, extract listings, **enrich detail-page descriptions**, rank against `~/.missav/` preferences.

**Prerequisite:** the `agent-browser` skill must be installed, and read [`references/browser-troubleshooting.md`](references/browser-troubleshooting.md) when browser access fails.

Install: `npm i -g agent-browser && agent-browser install`

> **Authorized access only:** If the site presents a Cloudflare challenge, stop the workflow immediately. Do not retry challenges, alter browser fingerprints, rotate proxies, or use challenge-solving services. Use a site-authorized API or access path instead.

## Preference store (`~/.missav/`)

```bash
node skills/missav/scripts/preferences.mjs init
node skills/missav/scripts/preferences.mjs show
```

See [references/preferences-schema.md](references/preferences-schema.md).

| Dimension | Field | Example |
|-----------|-------|---------|
| 类型 | `likes.genres` | `SM`, `NTR` |
| 男优/女优 | `likes.performers` | 从标题或详情页提取 |
| 厂牌 | `likes.labels` | 番号前缀 `SSIS-825` → `SSIS` |
| 关键词 | `likes.keywords` | `english-subtitle` |

## Workflow (optimized)

Use **`run-recommend.sh`** for the full tested pipeline, or run steps manually.

The workflow is fail-closed: a Cloudflare challenge detected by title or body returns exit code `42`, stops all later searches/detail requests, and never presents a partial recommendation as a successful run. Public search results and community-maintained clients are not a site-authorized API; do not replace this behavior with fingerprint changes, proxy rotation, challenge solving, or unofficial bypasses.

```bash
chmod +x skills/missav/scripts/run-recommend.sh
./skills/missav/scripts/run-recommend.sh --prefs ~/.missav/preferences.json
```

This script: loads prefs → searches each liked **genre + label** → merges listings → ranks → enriches **top scored** detail pages → re-ranks with descriptions.

### Manual steps

```
Task Progress:
- [ ] Step 0: preferences.mjs init && show
- [ ] Step 1: missav_browser_start (once per task)
- [ ] Step 2: browse-page.sh URL --continue (for 2nd+ URLs)
- [ ] Step 3: extract-listings.sh → normalize-eval-output (built-in)
- [ ] Step 4: filter-recommendations.mjs → ranked.json
- [ ] Step 5: enrich-listings.sh --ranked ranked.json (top scored only)
- [ ] Step 6: filter again + present + feedback
- [ ] Step 7: missav_browser_close
```

### Browser rules (from testing)

1. **One** `missav_browser_start` per task — then `--continue` for more URLs
2. Always use the bundled browser defaults in `browser-env.sh`
3. Never use `wait --load networkidle`
4. Treat a Cloudflare challenge as terminal for the current workflow; do not issue another search or detail request
5. Validate URL after open — reject `/pop`, `/search/` redirects on detail pages
6. Pass `--ranked` to enrich, not raw listing order
7. Treat detail enrichment challenges as fatal; list-only fallback is reserved for ordinary missing-description/landing failures

### Step 0–1: Preferences + URLs

```bash
node skills/missav/scripts/preferences.mjs show

# Build one URL per liked label/genre (merge results later)
node skills/missav/scripts/build-search-url.mjs search "{label}"
node skills/missav/scripts/build-search-url.mjs search "{genre}"
```

Search pattern: `https://missav.ws/cn/search/{keyword}`

### Step 2: Browse + extract (use bundled browser defaults)

```bash
SESSION="missav-$(date +%s)"
export MISSAV_SESSION="$SESSION"
source skills/missav/scripts/lib/browser-env.sh
missav_browser_start

./skills/missav/scripts/browse-page.sh "https://missav.ws/cn/search/sm"
./skills/missav/scripts/extract-listings.sh --session "$SESSION" --output /tmp/listings-a.json

# 2nd query: reuse session, do NOT restart browser
./skills/missav/scripts/browse-page.sh "https://missav.ws/cn/search/omhd" --session "$SESSION" --continue
./skills/missav/scripts/extract-listings.sh --session "$SESSION" --output /tmp/listings-b.json || true
```

`browse-page.sh` handles: close stale daemon → open page → challenge detection → age gate → scroll. A detected challenge stops the workflow.

If extraction returns **0 listings**, read [browser-troubleshooting.md](references/browser-troubleshooting.md) and retry once.

### Step 3: Preliminary rank

```bash
node skills/missav/scripts/filter-recommendations.mjs \
  /tmp/missav-listings.json \
  --prefs ~/.missav/preferences.json \
  --limit 15 > /tmp/missav-prelim.json
```

### Step 4: Detail enrichment (description analysis)

For top candidates, open **detail pages** and extract plot description:

```html
<div class="mb-1 text-secondary break-all line-clamp-none">
  …剧情描述文本…
</div>
```

```bash
node skills/missav/scripts/filter-recommendations.mjs \
  /tmp/missav-merged.json \
  --prefs ~/.missav/preferences.json \
  --limit 10 > /tmp/missav-ranked.json
```

### Step 4: Detail enrichment (top **scored** items only)

```bash
./skills/missav/scripts/enrich-listings.sh \
  --input /tmp/missav-merged.json \
  --ranked /tmp/missav-ranked.json \
  --output /tmp/missav-enriched.json \
  --top 3 \
  --session "$SESSION"
```

Single detail page:

```bash
./skills/missav/scripts/browse-page.sh "https://missav.ws/dm1/cn/{slug}"
./skills/missav/scripts/extract-detail.sh --session "$SESSION" --output /tmp/detail.json
node skills/missav/scripts/analyze-description.mjs \
  --item /tmp/detail.json \
  --prefs ~/.missav/preferences.json
```

Description analysis matches user `likes.genres` (e.g. **SM**) against plot keywords: 绑、深喉、受虐、调教…

### Step 5: Final rank

```bash
node skills/missav/scripts/filter-recommendations.mjs \
  /tmp/missav-enriched.json \
  --prefs ~/.missav/preferences.json \
  --limit 10
```

Items with `description` get extra score via description ↔ preference matching.

### Step 6: Present + feedback

```markdown
## missav 推荐

| # | 番号 | 时长 | 匹配 | 标题 | 链接 |
|---|------|------|------|------|------|
| 1 | … | … | SM, 厂牌 | … | [打开](…) |

### 剧情摘要（Top 1）
{first 2 sentences of description}

### 偏好匹配
- 类型 SM：描述含「绑」「深喉」等
- 厂牌：{label}-xxx
```

On user feedback, persist with **full item including description**:

```bash
node skills/missav/scripts/preferences.mjs feedback like \
  --item /tmp/detail.json \
  --note "用户喜欢这类SM剧情"
```

`feedback like` auto-infers genres from description text into `likes.genres`.

### Cleanup

```bash
source skills/missav/scripts/lib/browser-env.sh
missav_browser_close
```

## Listing card DOM

```html
<a href="…" alt="ssis-825-english-subtitle">
  <span class="absolute bottom-1 right-1 …">2:03:03</span>
</a>
<a class="text-secondary group-hover:text-primary" href="…" alt="…">
  SSIS-825 … Fuua Kaede - 枫ふうあ
</a>
```

See [references/dom-selectors.md](references/dom-selectors.md).

## Error handling

| Symptom | Action |
|---------|--------|
| `Just a moment...` title or Cloudflare challenge body | Stop immediately with exit code `42`. Automated access requires a site-authorized API or access path. |
| `Executable doesn't exist` | Set `MISSAV_CHROME` to system Chrome |
| `daemon already running` | `agent-browser close` first |
| Empty `[]` extraction | Run `browse-page.sh`; check age gate + scroll |
| Empty description | Click 展开/更多; use `extract-detail.js` |
| JSON parse error | Use `parse-eval-json.mjs` (double-encoded fix) |

## Scripts

| Script | Purpose |
|--------|---------|
| [run-recommend.sh](scripts/run-recommend.sh) | **One-shot** full pipeline |
| [browse-page.sh](scripts/browse-page.sh) | Open URL (`--continue` for 2nd+ page) |
| [normalize-eval-output.mjs](scripts/normalize-eval-output.mjs) | Fix double-encoded eval JSON |
| [extract-listings.sh](scripts/extract-listings.sh) | Listing cards → JSON array |
| [extract-detail.sh](scripts/extract-detail.sh) | Detail page → description JSON |
| [enrich-listings.sh](scripts/enrich-listings.sh) | Batch detail fetch (`--ranked` required) |
| [analyze-description.mjs](scripts/analyze-description.mjs) | Description ↔ prefs analysis |
| [filter-recommendations.mjs](scripts/filter-recommendations.mjs) | Score + rank |
| [preferences.mjs](scripts/preferences.mjs) | ~/.missav/ CRUD + feedback |
| [build-search-url.mjs](scripts/build-search-url.mjs) | URL builder |

Browser-side eval: [extract-listings.js](scripts/extract-listings.js), [extract-detail.js](scripts/extract-detail.js)

Node `.mjs` scripts: zero npm dependencies.

References: [preferences-schema.md](references/preferences-schema.md), [browser-troubleshooting.md](references/browser-troubleshooting.md)
