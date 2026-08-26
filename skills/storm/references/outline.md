# Phase 2 — Outline

Drafts an outline from the model's parametric knowledge, then refines it using the research conversations so the structure reflects what was actually learned.

Arguments consumed by this phase: `--output-dir PATH | --save`, `--force`.

## Prerequisites

- Read [engine.md](engine.md).
- `research/sources.json` MUST exist (phase 1 complete). If absent, stop and direct the user to run the research phase first — do not proceed with a parametric-only outline as the final artifact.

## Completion Contract

Complete iff `outline.md` exists with >=2 sections. If it exists and `--force` is not set, skip and exit early.

## Procedure

1. Resolve the output dir per the engine contract.
2. Read `research/conversations.jsonl` and `research/sources.json`. Concatenate the conversation histories as refinement input.
3. **Draft** — generate `outline-draft.md` from parametric knowledge alone using markdown `## Section` headings. This is the prior structure.
4. **Refine** — reorganize the draft using the conversation history: merge redundant sections, add sections the research surfaced that the draft missed, drop sections the research did not support. Write the result to `outline.md`.
5. Mark "Introduction", "Conclusion", "Summary" headings as placeholders if present — they are filled during polish, not here.
6. Verify `outline.md` has >=2 sections. Update `run-config.json`: `phases.outline = "completed"`, section count.

## Output

Report: draft section count, refined section count, sections added/removed during refinement, path to `outline.md`.
