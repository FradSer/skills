---
name: create-prd
description: This skill should be used when the user asks to "create PRD", "write
  product requirements document", revise or simplify an existing PRD or service
  strategy table, or mentions "PRD", "product requirements document".
disable-model-invocation: true
---

# PRD Creation

Transform product ideas into a usable PRD, or revise an existing one without inventing policy. All PRD content is written in Chinese (the target audience is Chinese-speaking teams).

## Route and Evidence First

Read `references/prd-revision-rules.md` before drafting or changing requirements. Separate sourced requirements, proposed decisions and unresolved dependencies. Broad repair requests do not approve arbitrary new business rules.

For an existing document, audit, simplification or targeted replacement, do not restart the creation interview. Use the user's stated scope and format; read the latest source, patch the relevant section, and validate the result. Inspection alone does not authorize writing. Follow Phases 0–4 for new documents; ask only questions not already answered by the conversation or source.

## Output Mode

Determine output mode from `$ARGUMENTS`:

| Argument | Mode | Output |
|----------|------|--------|
| `--md` (default) | Local Markdown | Save as `.md` file to project directory |
| `--lark` | Feishu Cloud Doc | Create via `lark-cli` using Lark rich-text features |

`--lark` mode accepts optional location arguments (mutually exclusive), supporting token or Feishu URL:
- `--folder-token` — Target folder (token or URL)
- `--wiki-node` — Target wiki node (token or URL)
- `--wiki-space` — Target wiki space root (ID or URL, or `my_library`)

Pass URL directly to `lark-cli` — no manual token extraction needed. Defaults to user's personal space root when no location specified.

## Phase 0: Import Context

Check for existing design or requirements documents:

1. Search for `docs/`, `prd/` directories or user-specified files
2. If found, extract key information (problem statement, target users, core features) as pre-filled content
3. If nothing found, skip this phase

## Phase 1: Determine PRD Type

Ask the user which PRD type they need:

- **Full** (recommended): All standard sections, suitable for complex features
- **Brief**: Core sections only, suitable for small features or quick iteration
- **One-pager**: Single-page summary, suitable for concept validation and executive reporting

## Phase 2: Gather Information

Follow the interview questions in `references/prd-interview-questions.md`, one question at a time. Wait for the answer before continuing.

- Basic info (7 items): required for all types
- Full version extras (5 items): full type only
- AI Agent boundaries: needed when the PRD will be consumed by AI coding agents

If Phase 0 found pre-filled content, show it to the user for confirmation and skip covered questions.

## Phase 3: Generate PRD Document

1. **Select template**:
   - Full: `references/prd-template-full.md`
   - Brief: `references/prd-template-brief.md`
   - One-pager: `references/prd-template-onepager.md`

2. **Fill content**: Use gathered information for each section, following `references/prd-best-practices.md` writing principles

3. **AI Agent consumability**:
   - Write each requirement as a discrete, verifiable item (lists over long paragraphs)
   - Express non-goals as positive constraints
   - Keep implementation task breakdowns separate from business requirements; add them only when requested
   - Full version includes a three-layer boundary framework: autonomous / needs confirmation / prohibited

4. **Quality requirements**:
   - Problem statement backed by available data or research; label missing evidence instead of inventing it
   - Goals follow SMART principles
   - Success metrics are quantifiable
   - Avoid vague terms ("approximately", "maybe", "try to")
   - Use active voice and concrete verbs

5. **Format**:
   - `--md` mode: Standard Markdown with clear heading hierarchy
   - `--lark` mode: Follow the current Lark document skill for supported rich-text syntax

## Phase 4: Validate and Save

Run validation per `references/prd-validation-checklist.md` — completeness, SMART goals, content quality, BDD acceptance criteria.

### `--md` Mode

Save file after validation:
- Filename: `PRD-[ProductName]-[YYYYMMDD].md`
- Prefer `docs/` or `prd/` directory, otherwise current working directory
- Report path and file summary

### `--lark` Mode

1. Load the current `lark-doc` skill and its create or update reference, plus the matching format guide. For spreadsheet content use `lark-sheets`. Discover supported flags from current CLI help instead of copying syntax from this skill.
2. For existing documents, record the latest revision and targeted changes before local block/cell edits. Preserve unrelated content and resources; do not create a replacement document unless requested.
3. Choose the smallest useful format: tables for parallel business rules, multiline boolean conditions for triggers, diagrams only for meaningful branching or an explicit user request. No mandatory decorative grids or empty whiteboards.
4. Read back the changed scope. Check actual values, formatting, resources and dependent acceptance examples; report the URL, actual changes and any unresolved decisions.

## Phase 5: Next Steps

After saving, report the result concisely. Suggest implementation tickets or additional review only when relevant; do not expand a localized edit into another full PRD workflow.

## Format Principles

- Use at most four heading levels and avoid duplicating the document title.
- Prefer a business table and a few shared rules over paragraphs repeating the same policy.
- Respect the user's latest format choice; replacement removes the superseded section rather than appending another explanation.
- Keep one authoritative location per rule. Use descriptive references, not mutable spreadsheet row numbers as the rule itself.

## Quality Principles

- **Data-driven**: Support problem statements with specific data and user research
- **SMART goals**: Specific, Measurable, Achievable, Relevant, Time-bound
- **Concise and clear**: Avoid verbosity; descriptions must be clear enough for dev teams to implement directly
- **Collaboration-oriented**: PRD is a collaboration tool; tone promotes discussion, not command
- **Dual-audience design**: Serve both human teams and AI coding agents

## Supporting Files

- `references/prd-interview-questions.md` — Information gathering questionnaire
- `references/prd-validation-checklist.md` — Validation checklist
- `references/prd-template-full.md` — Full version template
- `references/prd-template-brief.md` — Brief version template
- `references/prd-template-onepager.md` — One-pager template
- `references/prd-best-practices.md` — Best practices guide
- `references/prd-examples.md` — High-quality PRD examples
- Standalone `lark` plugin — Lark CLI skills (`--lark` mode)
