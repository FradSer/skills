---
name: tropes
description: Review a supplied draft for repetitive, formulaic, or AI-associated writing patterns and suggest or apply context-aware edits when the user asks for a style review, trope removal, or documentation-tone refinement. Preserve facts, meaning, author voice, quotations, code, and requested format; do not trigger for ordinary code generation or an initial document draft.
---

# AI writing trope review

Review the text or file the user places in scope for patterns that make prose sound formulaic, artificial, overly casual, or needlessly ornate. The target is clear writing in the author's intended voice, not a fixed “human” style. A single occurrence may be deliberate; judge repetition, clustering, context, audience, and the user's preferences.

## Route the request

- For an audit or critique, report findings and examples without changing the source.
- For “rewrite”, “remove”, or an explicitly requested edit, apply only supported changes and preserve factual claims, citations, examples, terminology, code, quoted speech, and the requested language and output format.
- Do not mechanically replace every flagged word or pattern. Explain material changes when a rewrite could alter emphasis, register, attribution, or meaning. Ask when the user's desired tone is unclear.
- Do not treat a trope catalogue as a ban list. Code blocks, commands, titles, required terminology, cited quotations, and intentional rhetorical devices are excluded or reviewed separately unless the user asks otherwise.

## Progressive scan

Read only the category references relevant to the text. Use the seven categories as a routing guide:

1. [word-choice.md](references/word-choice.md): ornate vocabulary, filler adverbs, and pompous constructions.
2. [sentence-structure.md](references/sentence-structure.md): repetitive openings, negative parallelism, and rhetorical questions.
3. [paragraph-structure.md](references/paragraph-structure.md): fragments, listicle disguises, and pacing.
4. [tone.md](references/tone.md): false suspense, unexplained authority, and pedagogical or promotional voice.
5. [formatting.md](references/formatting.md): em dashes, bold-first bullets, and decorative Unicode.
6. [composition.md](references/composition.md): duplicated summaries, dead metaphors, and repeated ideas.
7. [professional-balance.md](references/professional-balance.md): both colloquial “humanisms” and obscure AI-isms.

Start with a light read for repetitions and clusters. Use stricter thresholds only when the user requests a strict lint or a preference sets them. A useful finding names the location, pattern, reason it is a problem in this context, and a minimally invasive option; it does not claim that a phrase is always wrong.

## Preferences

User preferences are optional. If the user asks to use or inspect them, or if the target project contains one, run:

```bash
bash <skill-dir>/scripts/load-preferences.sh
```

Read [preferences-schema.md](references/preferences-schema.md) for the four-tier `office.*.json` format and merge semantics. If no preferences exist, use the default category guidance without creating a file. Preference files are local configuration, not evidence about the draft. `skip_categories`, language-specific terms, thresholds, tone, dead-metaphor caps, pattern caps, rhetorical bans, and principles may narrow or extend the review; preserve intentional exceptions such as quoted speech where configured.

If the user asks to save a new preference, show a diff preview with the target file, field, and merged value before writing. Write only after confirmation to the requested global/project and shared/local path. Never silently modify preference files.

## Revision and verification

For each approved change, prefer a local rewrite that keeps the original fact and attribution. Re-read the revised passage in context, then check that:

- facts, numbers, links, citations, names, and speaker attribution are unchanged unless the user requested a content edit;
- the author's point of view, level of formality, rhythm, and intentional repetition remain appropriate;
- required headings, list structure, code, and output format remain valid;
- the proposed replacement does not introduce a new trope or stronger claim;
- any remaining flagged pattern is either intentional, required, or clearly reported as unresolved.

Report the reviewed scope, categories applied, changes made or proposed, and any exclusions or uncertainty. Do not describe a style pass as factual, legal, or editorial approval.
