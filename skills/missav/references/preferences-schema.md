# ~/.missav/ Preference Store

Persistent user taste profile for the missav skill. Updated every session from explicit settings and natural-language feedback.

## Preference dimensions

| Field | 中文 | Example | Notes |
|-------|------|---------|-------|
| `genres` | 类型 | `NTR`, `制服`, `中出` | Matched in title/slug text |
| `performers` | 男优/女优 | `枫ふうあ`, `Fuua Kaede` | Unified list for all cast |
| `labels` | 厂牌 | `SSIS`, `MIDV` | Prefix from番号 (`SSIS-825` → `SSIS`) |
| `keywords` | 关键词 | `english-subtitle` | Slug/title tokens |
| `codes` | 番号 | `SSIS-825` | Exact match |

Legacy v1 fields (`actresses`, `actors`, `series`) are auto-migrated on load.

## Directory layout

```
~/.missav/
├── preferences.json    # Current likes, dislikes, duration, search defaults
└── feedback.jsonl      # Append-only audit log (one JSON object per line)
```

Override location with `MISSAV_HOME` or `--dir` on CLI scripts.

## preferences.json schema

```json
{
  "version": 2,
  "updatedAt": "2026-07-09T13:00:00.000Z",
  "likes": {
    "genres": ["NTR", "制服"],
    "performers": ["枫ふうあ", "Fuua Kaede"],
    "labels": ["SSIS"],
    "keywords": ["english-subtitle"],
    "codes": ["SSIS-825"]
  },
  "dislikes": {
    "genres": [],
    "performers": [],
    "labels": ["MIDV"],
    "keywords": [],
    "codes": [],
    "hrefs": ["https://missav.ws/dm1/cn/example-slug"]
  },
  "duration": {
    "minMinutes": 90,
    "maxMinutes": null
  },
  "search": {
    "defaultKeyword": "ssis",
    "defaultFilter": "chinese-subtitle",
    "defaultCategory": "dm247"
  },
  "weights": {
    "code": 100,
    "label": 30,
    "performer": 40,
    "genre": 25,
    "keyword": 20,
    "durationOk": 10,
    "durationOut": -50,
    "dislikePenalty": -80
  },
  "limit": 10,
  "stats": {
    "likedCount": 3,
    "dislikedCount": 1,
    "sessions": 0
  }
}
```

## Signal extraction from listing items

When feedback includes an `--item` JSON file, the CLI auto-extracts:

| Signal | Source |
|--------|--------|
| `code` | `item.code` or parsed from title/slug |
| `labels` | prefix of code (`SSIS-825` → `SSIS`) |
| `performers` | names after ` - ` in title; comma-separated cast |
| `genres` | `item.genres[]` if present; otherwise set explicitly via CLI |
| `keywords` | slug tokens like `english-subtitle` |
| `href` | direct blocklist for `never_again` |

## Feedback types

| Type | Effect |
|------|--------|
| `like` / `more_like_this` | Add extracted signals to `likes.*` |
| `dislike` / `never_again` | Add to `dislikes.*`; block exact `href` |
| `too_short` | Set `duration.minMinutes` ≥ item duration + 5; dislike item |
| `too_long` | Set `duration.maxMinutes` ≤ item duration − 5; dislike item |

## CLI

```bash
node scripts/preferences.mjs init
node scripts/preferences.mjs show
node scripts/preferences.mjs set \
  --genres "NTR,制服" \
  --performers "枫ふうあ" \
  --labels "SSIS" \
  --min-duration 90
node scripts/preferences.mjs feedback like --item /tmp/item.json --note "很不错"
```

Aliases still accepted: `--actresses`, `--actors` → `performers`; `--series` → `labels`.

## Scoring integration

`filter-recommendations.mjs --prefs ~/.missav/preferences.json` loads likes as positive signals and dislikes as penalties. Blocked `hrefs` are excluded entirely.

All Node scripts are native ESM (`.mjs`) with zero npm dependencies.

Session CLI flags (`--genres`, `--performers`, `--labels`, etc.) merge on top of stored prefs for one-off overrides.
