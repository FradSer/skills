---
name: patent-architect
description: Draft a patent disclosure or application from a technical invention, or perform a source-traceable prior-art review when the user asks for patent drafting, invention disclosure, or prior-art analysis. Use the requested jurisdiction, language, format, and destination; do not use for general technical writing.
disable-model-invocation: true
---

# Patent drafting and prior-art analysis

Turn the user's technical disclosure into a traceable working draft: identify the technical problem, solution elements, effects, variants, assumptions, and open questions; then compare those elements with retrieved sources. This skill supports drafting and research. A patent attorney or the relevant patent office must make legal, filing, novelty, inventive-step, enablement, and claim-scope decisions.

## Route and authorization

Preserve the user's jurisdiction, language, output format, title, and requested scope. The bundled template and terminology reference are Chinese-oriented; read them for a Chinese draft and adapt rather than silently applying them to another jurisdiction.

If the user marks the disclosure confidential, says it contains unpublished trade-secret details, or restricts external sharing, use a redacted/local corpus or ask which safe search scope they want. Otherwise follow the user's request for retrieval. Do not expose credentials, private files, or unnecessary invention details in commands, logs, or citations. Do not make a filing, send a cloud document, or contact an attorney without explicit user authorization.

`$ARGUMENTS` may select:

| Argument | Mode |
| --- | --- |
| `--md` or no mode | Save a local Markdown draft when the user requested a file. Prefer an existing `docs/` or `patents/` directory. |
| `--lark` | Create or update a Feishu document only when the user requested that destination and the current Lark skill/CLI is available. |

In `--lark` mode accept at most one of `--folder-token`, `--wiki-node`, or `--wiki-space`, passing the selected token or URL through the current CLI. Verify the changed scope after writing and report the actual URL; never infer success from a command request alone. If a connector or permission is unavailable, provide the local draft or a clear blocked report instead.

## Workflow

1. **Disclosure map.** Extract the technical field, concrete problem, system or method elements, data/control flow, alternatives, measurable or observable effects, assumptions, and missing facts. Keep user facts, retrieved facts, and proposed drafting language distinguishable.
2. **Search plan.** Build queries from technical elements, effects, and alternatives. Use the retrieval tools actually available. When a patent database or API is available, record its name, query, date, result URL or publication number, and the fields actually inspected. Do not assume `SERPAPI_KEY`, `EXA_API_KEY`, `curl`, or a particular web-search command exists. If no retrieval is available, say so and produce a disclosure draft without a fabricated search result.
3. **Source ledger.** For each source retain the publication/application identifier, title, jurisdiction, kind code when available, priority/publication dates, applicant or assignee when available, URL, retrieval date, and the passage or claim supporting each comparison. Treat search snippets and generated summaries as leads until the source page or official record is checked.
4. **Comparison.** Compare the disclosed technical features with the closest sources feature by feature. Separate identical, overlapping, missing, and unverified elements. Use cautious wording such as “本次检索中未发现” or “需要进一步核实”; a search result cannot establish global novelty or inventive step.
5. **Draft.** For a Chinese application-style draft, read [references/template.md](references/template.md) and [references/reference.md](references/reference.md). Include only supported technical effects; label assumptions, alternatives, and unresolved claim decisions. Read [references/examples.md](references/examples.md) only when an example is useful, and treat its names, metrics, dates, and patent numbers as illustrative rather than evidence.
6. **Validate.** Check antecedent basis and consistent names, that claims do not introduce unsupported elements, that embodiments cover disclosed variants, and that every prior-art assertion has a source ledger entry. Report missing drawings, experiments, inventorship, ownership, jurisdiction, dates, or legal review as open items.

## Chinese draft guidance

Use the provided template's sections for background technology, search analysis, invention content, embodiments, and other alternatives/limitations. Use precise technical nouns and causal effects. Do not force three embodiments when the disclosure does not support them: offer clearly labelled implementation variants or mark the missing detail. Do not turn product names, UI labels, or marketing benefits into technical limitations without evidence. Avoid asserting that a draft is “ready for filing.”

The reference's terminology table is a drafting aid, not a universal legal rule. Preserve meaningful user terminology where changing it would alter scope, and define synonyms once. Distinguish an embodiment, an optional feature, and a claim limitation.

## Output and evidence report

For local Markdown, use `Patent-[ShortTitle]-[YYYYMMDD].md` only when the user has not supplied a filename, sanitize path separators, and do not overwrite an unrelated file. Report the path, search scope, source count, comparison limits, unresolved decisions, and whether the result is a disclosure draft, a working application draft, or an attorney-review draft. Never report “novel,” “patentable,” “grantable,” or “ready to file” as an established conclusion.

Supporting references:

- [reference.md](references/reference.md): Chinese terminology and source-ledger fields; read for Chinese drafting.
- [template.md](references/template.md): structural template; read when using the bundled Chinese application shape.
- [examples.md](references/examples.md): optional illustrative example; never treat its claims as source evidence.
