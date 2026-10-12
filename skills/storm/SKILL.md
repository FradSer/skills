---
name: storm
description: Research and write a Wikipedia-style long-form article with a resumable, multi-perspective STORM workflow when the user asks for a storm article, a Wikipedia-style article, or a researched long-form piece. Use available retrieval and local documents, preserve source provenance, and never invent citations. Do not use for ordinary creative writing or a simple summary.
disable-model-invocation: true
---

# STORM long-form research article

Use the four phase workflow from Stanford STORM: research, outline, write, and polish. The workflow is runtime-neutral and uses whatever search, fetch, prompt, and worker capabilities are actually available. Read [references/engine.md](references/engine.md) before any phase; it is the shared contract for artifacts, resumption, retrieval, and citations.

The default deliverable is a source-grounded article. A user-provided local corpus may be the only source pool when `--docs-only` is selected. A user who asks for an unsourced creative article should be routed to ordinary writing instead of using this skill.

## Invocation and phases

For a complete run, accept:

```text
storm <topic> [--max-perspective N] [--max-turns N]
  [--output-dir PATH | --save] [--docs DIR] [--docs-only]
  [--force] [--retriever mcp|web|local]
```

Honor a request for one phase (`research`, `outline`, `write`, or `polish`) and operate only on its existing run directory. The phase references define their arguments and prerequisites:

| Phase | Read | Primary artifact |
| --- | --- | --- |
| Research | [references/research.md](references/research.md) | `research/sources.json` |
| Outline | [references/outline.md](references/outline.md) | `outline.md` |
| Write | [references/write.md](references/write.md) | `article.md` |
| Polish | [references/polish.md](references/polish.md) | `article-polished.md` |

Phases are sequential because each consumes the prior artifact. Within research or writing, use workers only if the runtime supports them and only with the same source and output contracts; otherwise work sequentially. Do not claim parallel execution occurred when it did not.

## Model routing

If the runtime offers multiple models, use a cheaper or faster model for persona turns and the strongest available model for outline, section writing, and polish when that improves cost or quality. This is optional routing guidance, not a requirement to use a named provider or model.

## Invariants

- Every phase must have its prerequisite artifact. A missing research artifact stops outline/write/polish with a direction to run the prerequisite; do not produce a final parametric-only article.
- Reuse a completed artifact when `--force` is absent, and record `skipped`, `completed`, or `failed` in `run-config.json`. `--force` explicitly permits rerunning the selected pipeline against the same run directory.
- Every inline `[n]` must resolve to a collected source id. Never mint ids in outline, write, or polish. A claim without support stays uncited and is visibly flagged for review.
- The final References section is exactly the sources cited in the body. Preserve source title, URL, description, and retrieval/access date; strip citation markers embedded in retrieved snippets before reusing them as context.
- Keep topic, slug, output directory, parameters, and timestamps in `run-config.json`. Temporary output must be clearly reported and must not be described as published.

## Retrieval and reporting

Probe the runtime's actual search and fetch capabilities. Prefer a specialized retriever when available, otherwise use available web search/page fetching; with `--docs`, include local files, and with `--docs-only`, exclude the web. If retrieval is unavailable, stop or produce a clearly incomplete research artifact rather than silently relying on memory.

At completion, report the absolute run directory and final artifact, word and section counts, cited-source count, skipped phases, and unresolved citation or evidence flags. Read each changed artifact before reporting success. Do not imply peer review, publication, or factual completeness from a local run alone.
