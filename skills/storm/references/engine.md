# STORM Engine — Shared Contracts

Methodology ported from Stanford STORM. Every phase reads this file first: it defines the artifact layout, stage-gating, retrieval abstraction, citation hygiene, and persona discovery that all phases share.

## Two-Stage Pipeline

```
Stage 1 (Pre-writing)        Stage 2 (Writing)
  research  --------->  outline  --------->  write  --------->  polish
   (persona               (draft +            (per-section,        (summary +
    discovery,            refine from         cited, parallel)     dedup)
    simulated Q&A,        research)
    information table)
```

**NEVER skip stage 1.** If `research/` is absent, run the research phase first.

**NEVER invent citations.** Every inline `[n]` must map to an entry in `research/sources.json`. If a section has no supporting sources, write it without citations and flag the gap in polish — do not fabricate a reference.

## Artifact Layout

All phases read from and write to a single per-topic directory:

```
<output_dir>/<slug>/
  research/
    personas.json          # discovered personas (name + perspective + rationale)
    conversations.jsonl    # one record per (persona, turn): question, queries, snippets, answer
    sources.json           # deduplicated sources: {id, title, url, description, snippets}
  outline.md               # refined outline (markdown headings)
  outline-draft.md         # pre-research draft (kept for reference)
  article.md               # per-section draft with inline [n] citations
  article-polished.md      # final polished article
  run-config.json          # snapshot of run parameters
```

## Stage-Gating Contract

A phase is complete when its primary artifact exists and is non-empty:

- `research` complete iff `research/sources.json` exists with >=1 entry.
- `outline` complete iff `outline.md` exists with >=2 sections.
- `write` complete iff `article.md` exists and every outline section (except Introduction/Conclusion/Summary) has body text.
- `polish` complete iff `article-polished.md` exists.

If complete and the user did not pass `--force`, skip the phase, read its artifact, and log what was skipped. Mark skipped/completed/failed per phase in `run-config.json`.

## Slug Derivation

Lowercase the topic, replace non-alphanumeric runs with `-`, trim leading/trailing `-`, truncate to 60 chars. If the directory already exists for a *different* topic (per its `run-config.json`), append `-2`, `-3`, etc.

## Output Directory Resolution

1. `--output-dir <path>` given -> use `<path>/<slug>/`.
2. Else if `--save` given -> use `docs/storm/<slug>/` relative to cwd (create if missing).
3. Else -> use a temporary directory (`mktemp -d` or equivalent): `<tmp>/storm-<slug>/`. Write `"temporary": true` into `run-config.json` and surface the absolute path to the user so artifacts can be rescued. Temporary dirs are not auto-cleaned by the skill; resumption within the session still works.

## Retrieval Contract

Prefer specialized retrieval tooling when available; fall back to generic web search:

1. Probe the runtime's tool set for search-capable tools — e.g. MCP search servers (an exa-style server may offer code, research-paper, company, financial-report, or social search variants) or any built-in web search / page fetch capability.
2. If specialized tools exist, pick the most relevant type per query (research-paper search for academic topics, company search for organizations).
3. Otherwise fall back to built-in web search plus page fetching.
4. With `--docs <dir>`, ingest local files as an additional source pool alongside web results — as the only pool with `--docs-only`.

**Source shape** (mirrors upstream `Information`): every source is normalized to

```json
{"id": 1, "title": "...", "url": "...", "description": "...", "snippets": ["..."]}
```

Assign sequential `id`s as sources are added; the `id` is the citation key used in inline `[n]`.

## Citation Hygiene

- Inline citations use `[1]` / `[1][2]`, placed immediately after the claim they support.
- The trailing `## References` section lists every cited source, numbered to match, as `title — url (accessed YYYY-MM-DD)`.
- Before reusing a snippet from an existing source as context for follow-up questions, apply `strip_citations(text) -> text`, removing every `[n]` and `[n][m]` pattern the snippet itself contained — this prevents multi-hop citation confusion.
- References = exactly the set of `[n]` keys present in the body. Uncited sources stay in research but never appear in References.
- A genuinely unsupported section is written uncited and marked `<!-- TODO: no source -->` so polish can flag it.

## Persona Discovery

Ground personas in real structure, not hallucination — mirrors upstream's "scrape related Wikipedia TOCs" step:

1. Search for the topic plus 2-3 closely related concepts.
2. For top results that look like reference pages (encyclopedia entries, handbooks, surveys), fetch them and extract their table of contents / section headings.
3. Feed those real headings as inspiration for persona generation: propose N perspectives (default 3) such that each persona asks a different category of question about the topic. Always include one "Basic fact writer" persona.
4. Each record: `{"name": "...", "perspective": "...", "rationale": "..."}`.

## Simulated Conversation (per persona)

Each persona drives a multi-turn dialogue between a WikiWriter (asks questions) and a TopicExpert (answers, grounded in retrieval):

1. Writer poses a question from the persona's angle.
2. Expert breaks the question into 1-3 search queries, retrieves per the contract above, and answers with inline source attribution.
3. The conversation ends when the writer says "Thank you so much for your help!" or `max_turns` (default 3) is reached.
4. Collect every `(question, queries, snippets, answer)` tuple into `conversations.jsonl` and every cited source into `sources.json` (deduplicated by URL).

## Run Config

`run-config.json` always contains:

```json
{
  "topic": "<original topic>",
  "slug": "<derived>",
  "temporary": false,
  "output_dir": "<absolute>",
  "max_perspective": 3,
  "max_turns": 3,
  "search_top_k": 3,
  "retrieve_top_k": 3,
  "retriever": "mcp | web | local",
  "started_at": "<ISO timestamp from the runtime>",
  "phases": {"research": "completed|skipped|pending", "outline": "...", "write": "...", "polish": "..."}
}
```
