# missav DOM Selectors

Reference for listing-page extraction. Site markup may shift; fallbacks are ordered by reliability.

## Primary selectors (current layout)

### Title link

```css
a.text-secondary.group-hover:text-primary[href*="/cn/"]
```

Attributes: `href`, `alt`, text content.

### Duration badge

Inside the thumbnail anchor (same card container):

```css
span.absolute.bottom-1.right-1
/* fallback */
span[class*="bottom-1"][class*="right-1"]
```

Typical classes: `absolute bottom-1 right-1 rounded-lg px-2 py-1 text-xs text-nord5 bg-gray-800 bg-opacity-75`

### Thumbnail anchor

Shares `href` and `alt` with title link:

```css
a[href*="/cn/"][alt]:has(span.absolute.bottom-1)
```

## Card grouping

Title and thumbnail links share the same `href`. Group by `href` when duration is not in the title's immediate parent:

```javascript
const byHref = new Map();
document.querySelectorAll('a[href*="/cn/"][alt]').forEach(a => {
  const href = a.href;
  if (!byHref.has(href)) byHref.set(href, { href, slug: a.alt, title: '', duration: '' });
  const entry = byHref.get(href);
  if (a.classList.contains('text-secondary')) {
    entry.title = a.textContent.trim();
  }
  const dur = a.querySelector('span.absolute.bottom-1, span[class*="bottom-1"][class*="right-1"]');
  if (dur) entry.duration = dur.textContent.trim();
});
```

## Duration parsing

| Format | Example | Minutes |
|--------|---------|---------|
| `H:MM:SS` | `2:03:03` | 123 |
| `M:SS` | `45:30` | 45.5 |
| `MM:SS` | `03:45` | 3.75 |

## Code extraction

```javascript
const CODE_RE = /\b([A-Z]{2,10}-\d{2,5})\b/i;
const m = title.match(CODE_RE);
const code = m ? m[1].toUpperCase() : '';
```

Fallback from slug: `ssis-825-english-subtitle` → `SSIS-825`.

## Pagination and infinite scroll

missav listing pages often lazy-load on scroll. Before extraction:

1. `scroll down 1200` × 3–5 times
2. `wait 1500` between scrolls
3. Re-run extraction

Paged URLs (when present): `?page=2`, `?page=3`.

## Age verification

Common button texts (locale-dependent):

- `我已满 18 岁`
- `I am 18 or older`
- `Enter`

Use `agent-browser find text "<label>" click` or snapshot ref click.

## Search URL patterns

**Primary (keyword search):**

```
/cn/search/{keyword}
/cn/search/{keyword}?filters=chinese-subtitle
/cn/search/{keyword}?filters=english-subtitle
```

Examples:

- `https://missav.ws/cn/search/ssis` — 厂牌/番号前缀
- `https://missav.ws/cn/search/ssis` —番号前缀
- `https://missav.ws/cn/search/枫ふうあ` — 女优名

Build URLs with `scripts/build-search-url.mjs search <keyword> [--filter ...]`.

**Other listing paths:**

```
/cn/actresses/{slug}
/cn/genres/{slug}
/dm{category}/cn          # e.g. /dm247/cn
```

## Detail page — plot description

Primary description block (Vue/Alpine `:class` is stripped in live DOM):

```html
<div class="mb-1 text-secondary break-all line-clamp-none">
  那个蠢女人在网路上曝光了我，把我拖进了地狱。不如我们一起堕落吧？…
</div>
```

| Field | Selector / action |
|-------|-------------------|
| Description | `div.mb-1.text-secondary.break-all` → `textContent` |
| Expand collapsed | click `展开` / `更多` / `show more` first |
| Tags / genres | `a[href*="/cn/genres/"]`, `a[href*="/cn/tags/"]` |
| Performers | `a[href*="/cn/actresses/"]`, `a[href*="/cn/actors/"]` |
| Title | `h1` or `meta[property="og:title"]` |
| Code | from title or URL slug |

Extract with `scripts/extract-detail.js` (browser eval) or `extract-detail.sh`.

Analyze description against `~/.missav` prefs:

```bash
node scripts/analyze-description.mjs --item detail.json --prefs ~/.missav/preferences.json
```

Use description text to score **类型** (e.g. SM, NTR) — title/slug alone often miss theme keywords in plot summary.
