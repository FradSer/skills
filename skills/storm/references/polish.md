# Phase 4 — Polish

Adds a summary/intro section, removes duplicate content across sections, and verifies citation integrity between body and References.

Arguments consumed by this phase: `--remove-duplicate` (explicit form of the default-on duplicate removal), `--output-dir PATH | --save`, `--force`.

## Prerequisites

- Read [engine.md](engine.md).
- `article.md` MUST exist (phase 3 complete). If absent, stop and direct the user to run the write phase first.
- `research/sources.json` MUST exist. Citation integrity is checked against the collected sources; without them the References section cannot be verified.

## Completion Contract

Complete iff `article-polished.md` exists. If it exists and `--force` is not set, skip and exit early.

## Procedure

1. Resolve the output dir per the engine contract.
2. Read `article.md`, `outline.md`, and `research/sources.json`.
3. **Summary section** — if `outline.md` had an "Introduction" or "Summary" placeholder, write a summary synthesizing the article's main points (1-2 paragraphs). Introduce no new claims or citations beyond what the body already contains.
4. **Duplicate removal** (on by default) — detect near-duplicate paragraphs across sections and remove the later occurrence, keeping the copy in the more topically-appropriate section.
5. **Citation integrity** — collect the `[n]` keys present in the body. Append a `## References` section listing exactly those sources, numbered to match, each as `n. title — url (accessed YYYY-MM-DD)`. Replace any body `[n]` without a source with `<!-- TODO: missing source -->`. Drop sources that are never cited — References mirrors the body exactly.
6. Write `article-polished.md`.
7. Update `run-config.json`: `phases.polish = "completed"`, final word count, source count, integrity warnings.

## Output

Report: final word count, cited source count, duplicate paragraphs removed, integrity warnings (missing sources / TODO sections), absolute path to `article-polished.md`.
