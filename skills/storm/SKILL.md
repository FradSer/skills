---
name: storm
description: Generates Wikipedia-style long-form articles grounded in multi-perspective
  research and retrieval, porting Stanford STORM's four-phase pipeline (research,
  outline, write, polish). Each phase is independently runnable and resumable; runtime-neutral
  by design. Use when the user asks for a "storm article", a "wikipedia-style article",
  or to "research and write a long-form piece".
disable-model-invocation: true
---

# STORM — Long-Form Research Article Generation

Generate a Wikipedia-style long-form article on any topic via [Stanford STORM](https://github.com/stanford-oval/storm) (Synthesis of Topic Outlines through Retrieval and Multi-perspective Question Asking, NAACL'24/EMNLP'24). The output is grounded in retrieval, not parametric memory: multi-perspective simulated interviews collect sources first, then sections are written with inline `[n]` citations and a trailing References list.

## Pipeline

```
research  ->  outline  ->  write  ->  polish
  (persona      (draft +     (per-section,      (summary +
   discovery)    refine)      cited)             dedup)
```

Two invariants hold across every phase:

1. **Never skip research.** An article written from memory alone will hallucinate citations and miss the multi-perspective grounding that defines STORM.
2. **Never invent citations.** Every inline `[n]` maps to a source collected during research. A section without support is written uncited and flagged, never fabricated.

Read the shared contracts before running any phase: [engine](references/engine.md) defines the artifact layout, stage-gating, retrieval backend abstraction, citation hygiene, and persona discovery used by all four phases.

## Invocation

Run the whole pipeline end to end when asked to "write a storm article about X", "research and write a long-form piece on X", or similar:

```
storm <topic> [--max-perspective N] [--max-turns N] [--output-dir PATH | --save]
              [--docs DIR] [--docs-only] [--force] [--retriever mcp|web|local]
```

Each phase is also independently runnable and resumable — honor such requests ("run just the outline", "redo polish") by executing only that phase's workflow against an existing run directory:

| Phase | Workflow | Primary artifact |
|-------|----------|------------------|
| 1 | [references/research.md](references/research.md) | `research/sources.json` |
| 2 | [references/outline.md](references/outline.md) | `outline.md` |
| 3 | [references/write.md](references/write.md) | `article.md` |
| 4 | [references/polish.md](references/polish.md) | `article-polished.md` |

## Orchestration Procedure

1. If no topic was provided, ask the user for one through whatever prompting mechanism the runtime offers.
2. Read [engine](references/engine.md). Derive `<slug>`, resolve `<output_dir>` per the engine contract, and create the directory.
3. Write `run-config.json` snapshotting all parameters, including `started_at` from the runtime's current time.
4. For each phase in order — `research`, `outline`, `write`, `polish`:
   - Check the phase's completion artifact per the engine stage-gating contract.
   - If complete and not `--force`: mark `phases.<name>: "skipped"` in `run-config.json` and move on.
   - Otherwise execute the phase workflow from its reference file, then verify its artifact and record `"completed"` (or `"failed"` with the reason).
5. Read `article-polished.md` and report to the user: absolute path, word count, section count, number of cited sources, and the output directory (flag it prominently if temporary).

Phases run strictly sequentially — each depends on the previous phase's artifacts. Parallelism exists *inside* phases 1 and 3 (see their references), never across phases.

If a phase fails, stop and report. Do not proceed. Re-invocation without `--force` resumes from the failed phase because earlier completed phases are skipped.

## Portability Notes

This skill is runtime-neutral by design:

- **Subagents**: phases 1 and 3 benefit from running persona conversations / section writes in parallel. If the runtime can spawn subagents, do so; otherwise run the units sequentially in-context following the same role instructions.
- **Retrieval**: probe whatever search tooling the runtime exposes (MCP search servers, built-in web search/fetch, browser tools) per the engine's retrieval contract. `--docs DIR` grounds on local files instead of or in addition to the web.
- **Model routing**: if the runtime offers several models, run persona conversation turns on cheap/fast models and reserve the strongest available model for outline, section writing, and polish — mirroring upstream's cost/quality split.
- **User prompts**: use the runtime's native question/prompt mechanism when input is missing.
