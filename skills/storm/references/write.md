# Phase 3 — Write

Writes each outline section grounded in the top-k most relevant sources from the research information table, with inline `[n]` citations.

Arguments consumed by this phase: `--retrieve-top-k N` (default 3), `--output-dir PATH | --save`, `--force`.

## Prerequisites

- Read [engine.md](engine.md).
- `research/sources.json` MUST exist (phase 1 complete). If absent, stop and direct the user to run the research phase first.
- `outline.md` MUST exist (phase 2 complete). If absent, stop and direct the user to run the outline phase first.

## Completion Contract

Complete iff `article.md` exists and every outline section (except Introduction/Conclusion/Summary placeholders) has body text. If satisfied and `--force` is not set, skip and exit early.

## Procedure

1. Resolve the output dir per the engine contract.
2. Read `outline.md` and `research/sources.json`. Index sources for retrieval (simple approach: rank by keyword/heading overlap with the section title).
3. **Identify sections** to write — skip any heading exactly named "Introduction", "Conclusion", or "Summary" (filled during polish).
4. **Write sections** — one unit of work per section, in parallel via subagents if the runtime supports spawning workers, otherwise sequentially in-context. Each unit receives the topic, section heading, top-k relevant sources (default `--retrieve-top-k` 3), and the full outline for context, then writes the section body per the citation rules below. A section with no relevant sources is written uncited and marked `<!-- TODO: no source -->`.
5. **Assemble** — concatenate sections in outline order under their headings into `article.md`, preserving the heading hierarchy.
6. Verify every non-placeholder section has body text. Update `run-config.json`: `phases.write = "completed"`, section count, TODO-flagged sections.

## Citation Rules

- Only cite `[n]` where `n` is an existing `id` in `sources.json`. Never mint a new id here.
- Place `[n]` immediately after the claim it supports; multi-source claims use `[1][2]`.
- Do not cite placeholder sections.

## Output

Report: sections written, citations used, sections flagged TODO (no source), path to `article.md`.
