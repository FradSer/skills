---
name: tropes
description: This skill should be used when generating any text content, writing documentation, creating code comments, or reviewing writing style. Provides guidance on avoiding common AI writing patterns and tropes that make text sound artificial or formulaic.
---

# AI Writing Tropes Detection

Scan generated text for common AI writing patterns that make content sound artificial or formulaic. This skill provides a systematic workflow for identifying and eliminating tropes.

Source: [tropes.fyi](https://tropes.fyi) by [ossama.is](https://ossama.is)

## Core Principle

**Write like a human: varied, imperfect, specific.**

A single pattern used once is usually fine. The problem occurs when multiple tropes cluster together or when the same trope repeats throughout the text.

## When to Check

Scan for tropes when:
- Generating any text content (documentation, comments, messages)
- Reviewing writing before committing or publishing
- Editing AI-generated drafts
- Responding to user questions or creating explanations

## Detection Workflow

### 1. Pattern Scan

Read through the text and identify:
- Repeated sentence structures or openings
- Formulaic transitions ("It's worth noting", "Here's the thing")
- Ornate vocabulary where simple words work better
- Rhetorical patterns that feel artificial

### 2. Cluster Check

Look for multiple tropes appearing together:
- 3+ patterns in a single paragraph = high risk
- Same pattern used 2+ times in a piece = needs revision
- Em-dashes appearing 5+ times = formatting issue

### 3. Revision Strategy

For each identified trope:
- **Word choice**: Replace with simpler, more direct language
- **Sentence structure**: Vary openings and lengths naturally
- **Transitions**: Remove filler phrases that signal nothing
- **Formatting**: Reduce em-dashes, remove bold-first bullets

### 4. Verification

After revision:
- Re-scan for remaining patterns
- Check that text sounds natural when read aloud
- Ensure specificity (concrete details vs vague attributions)

## Pattern Categories

The complete trope catalog is organized into six categories. Load specific references as needed:

1. **Word Choice** - `references/word-choice.md`
   Ornate vocabulary, magic adverbs, pompous constructions

2. **Sentence Structure** - `references/sentence-structure.md`
   Negative parallelism, rhetorical questions, formulaic patterns

3. **Paragraph Structure** - `references/paragraph-structure.md`
   Short fragments, listicle disguises

4. **Tone** - `references/tone.md`
   False suspense, pedagogical voice, vague attributions

5. **Formatting** - `references/formatting.md`
   Em-dash overuse, bold-first bullets, unicode decoration

6. **Composition** - `references/composition.md`
   Fractal summaries, dead metaphors, content duplication
