# Phase 1 — Research

Discovers research personas, runs a simulated multi-turn conversation per persona (each grounded in retrieval), and produces the information table that downstream phases consume.

Arguments consumed by this phase: `--max-perspective N` (default 3), `--max-turns N` (default 3), `--retriever mcp|web|local`, `--docs DIR`, `--docs-only`, `--output-dir PATH | --save`, `--force`.

## Prerequisites

Read [engine.md](engine.md) — its Persona Discovery, Simulated Conversation, Retrieval, and Citation Hygiene sections govern this phase.

## Completion Contract

Complete iff `research/sources.json` exists with >=1 entry. If it exists and `--force` is not set, skip and exit early.

## Procedure

1. Resolve the output dir per the engine contract; ensure the `research/` subdir exists.
2. **Persona discovery** — follow the engine's Persona Discovery section: search for the topic + related concepts, extract real section headings from reference pages, propose `--max-perspective` personas (default 3) plus one "Basic fact writer". Write `research/personas.json`.
3. **Retrieval probe** — probe available search tooling per the engine's Retrieval Contract and record the chosen backend as `retriever` in `run-config.json`.
4. **Simulated conversations** — run one conversation per persona following the role spec below. Launch them in parallel via subagents if the runtime supports spawning workers; otherwise execute sequentially in-context with the same instructions.
5. **Merge** — collect all conversation records into `research/conversations.jsonl` (one JSON object per line). Deduplicate cited sources by URL into `research/sources.json`, assigning sequential `id`s. Strip inline `[n]` from snippets before storing (citation hygiene).
6. **Verify** — assert `sources.json` has >=1 entry and every persona produced >=1 turn. A persona that produced nothing is noted but does not fail the phase.
7. Update `run-config.json`: `phases.research = "completed"`, plus retriever and source count.

## Concurrency

If retrieval hits rate limits, reduce concurrency (e.g. 2 conversations at a time) rather than lowering `max_turns`.

## Persona Researcher Role Spec

Give each unit of work (subagent or sequential block) this role: *a single persona's researcher conducting a WikiWriter <-> TopicExpert dialogue about the topic.*

Inputs provided to each unit:
- `topic`, `persona` (`{name, perspective, rationale}`), `max_turns` (default 3), and the retrieval backend to use.

Procedure:
1. Adopt the persona's perspective. As the WikiWriter, pose a question about `topic` that this persona would ask.
2. As the TopicExpert, break the question into 1-3 search queries, retrieve via the configured backend, and answer grounded in the retrieved snippets, tracking which URL each claim came from.
3. Strip any inline `[n]` from retrieved snippets before storing them (citation hygiene).
4. Continue until the writer says "Thank you so much for your help!" or `max_turns` is reached.
5. Return ONLY a JSON array as the final output — one object per turn, no prose, no markdown fences:
   `[{"question", "queries", "snippets", "answer", "cited_sources": [{"title", "url", "description", "snippets"}]}]`. The merge step serializes these records into `conversations.jsonl`.

Constraints:
- Never fabricate sources or snippets. Every cited URL must come from an actual retrieval result; if nothing was retrieved, answer from parametric knowledge with `"cited_sources": []`.
- Stay in the persona's question category — other personas cover other perspectives.

## Output

Report: number of personas, total conversation turns, number of deduplicated sources, path to `research/sources.json`.
