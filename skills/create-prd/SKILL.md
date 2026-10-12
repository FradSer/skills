---
name: create-prd
description: Create, revise, simplify, or validate a product requirements document or service strategy table when the user asks for a PRD or product requirements document. Use the requested language, format, and destination; preserve existing business rules and clearly separate evidence, proposals, and unresolved decisions. Do not use for general product writing without a PRD request.
disable-model-invocation: true
---

# PRD creation and revision

Turn a product idea or an existing requirements document into a clear, testable PRD. A PRD is a product decision record: keep business intent and evidence visible, while leaving implementation choices open unless the user or a source has decided them.

## Route before writing

Read [prd-revision-rules.md](references/prd-revision-rules.md) before revising an existing PRD, strategy table, or requirements section. Classify material as:

- confirmed requirement or verified fact;
- proposed decision, which must stay labelled as a proposal until accepted;
- unresolved question or dependency, with the missing evidence and impact recorded.

“Fix all issues” authorizes repairs within the stated scope. It does not approve new thresholds, durations, priorities, triggers, actions, retention rules, or policy. Correct clear errors and broken references directly; ask or record a decision when behavior would change. If the user asks only for review, do not write files.

For an existing document, use the latest source as the baseline, patch the requested sections, update directly affected references, and preserve unrelated content and formatting. For a local or remote document, write only through the requested destination and report what was changed and read back. Follow the current Lark skill and CLI help for remote edits; do not assume a command or tool exists.

## Output and language

Honor the user's language, output format, filename, and location. If they have not specified a language, use the language of the request and ask only when the audience makes that choice material. Do not silently create a Markdown file or a cloud document during inspection or review.

`$ARGUMENTS` may select the output mode:

| Argument | Mode |
| --- | --- |
| `--md` or no mode | Save a local Markdown PRD when the user requested a file; prefer an existing `docs/` or `prd/` directory. |
| `--lark` | Create or update a Feishu document only when the user requested that destination and the Lark skill/CLI is available. |

In `--lark` mode, accept at most one of `--folder-token`, `--wiki-node`, or `--wiki-space`. A token or URL may be passed through to the current CLI. Report any unavailable connector or unresolved authorization instead of fabricating success. For an existing document, preserve unrelated blocks and read back the changed scope.

When a filename is not supplied for a new local document, use `PRD-[ProductName]-[YYYYMMDD].md`, choosing `docs/` or `prd/` if either exists. Sanitize path separators and do not overwrite an unrelated file without explicit instruction.

## Choose the smallest workflow

1. **New PRD:** inspect the project or user-provided source for relevant context, then choose Full, Brief, or One-pager from the user's request or the problem's complexity. Ask only for information that is missing and affects the document. Use the question bank in [prd-interview-questions.md](references/prd-interview-questions.md) as a menu, not a mandatory one-question-at-a-time script.
2. **Revision, simplification, or audit:** do not restart the creation interview. Read the current document and requested section, identify the smallest safe edit, and keep the existing format unless the user requests a new one.
3. **Template selection:** use [prd-template-full.md](references/prd-template-full.md), [prd-template-brief.md](references/prd-template-brief.md), or [prd-template-onepager.md](references/prd-template-onepager.md) only for a new document or when the user asks to reformat. Read [prd-best-practices.md](references/prd-best-practices.md) when a decision or writing problem needs its guidance; do not load every example by default.

## Content contract

- Start with the user problem, affected users, context, and available evidence. Mark unknowns as unknown; never invent survey results, baselines, targets, dates, costs, or vendor capabilities.
- State goals and success measures with an owner, population, calculation, baseline, target, and time window when those facts are known. If they are not known, record the measurement gap instead of manufacturing SMART values.
- Write each requirement as a discrete, observable behavior. Use Given/When/Then acceptance scenarios for behavior that needs testing, including relevant error and boundary cases.
- Keep business requirements separate from implementation tasks, architecture, schema, and agent work breakdowns. Include the three-layer agent boundary (autonomous / confirmation required / prohibited) only when the PRD will be consumed by an AI coding agent or the user asks for it.
- Distinguish delivery priority (P0–P3) from runtime ordering, recommendation ranking, or notification timing.
- State non-goals as scope constraints with a reason or dependency when known. Do not convert an unresolved issue into a prohibition.
- Preserve operators, time anchors, inclusivity, deduplication, actions, and exit conditions when reformatting rules. Check the same boundary inputs before and after a behavioral edit; if the behavior changes, cite its source or mark it for decision.

## Validation and handoff

Read [prd-validation-checklist.md](references/prd-validation-checklist.md) after drafting or changing a PRD. For a local file, verify headings, links, acceptance criteria, and the saved path. For a remote document, verify the changed values and formatting in the source system. Report evidence coverage, open decisions, actual changes, and any validation boundary. Suggest tickets or another review only when relevant; do not expand a localized edit into a new PRD.

Supporting references:

- [prd-revision-rules.md](references/prd-revision-rules.md): required for semantic-preserving revision.
- [prd-interview-questions.md](references/prd-interview-questions.md): questions to fill material gaps in a new PRD.
- [prd-best-practices.md](references/prd-best-practices.md): read for applicable product-writing guidance.
- [prd-validation-checklist.md](references/prd-validation-checklist.md): completion checks.
- The three templates: read only the selected template.
- [prd-examples.md](references/prd-examples.md): optional illustration; treat all names, metrics, dates, and claims as fictional examples.
