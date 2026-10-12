---
name: update-readme
description: Update a README from current repository evidence when the user asks to update, sync, or audit a README. Use the named path and language; default to the repository root. Do not write a review unless the user asks for one.
disable-model-invocation: true
---

# README update

Bring the requested README file or files into agreement with the current project. A README update is a scoped documentation edit: identify the target path, inspect the repository as it exists now, preserve requested content and project voice, and write only the files the user named or clearly implied.

## Scope and routing

- If the user names a path, package, module, or nested README, use that path. Do not redirect it to a root README.
- If the user says “README” without a path, inspect the repository root and use its README as the default. Confirm the target when multiple plausible roots exist.
- Update both `README.md` and `README.zh-CN.md` only when the user requests bilingual synchronization or names both files. A single-language request changes only that file.
- Preserve an existing header, badge, language toggle, structure, and project-specific conventions unless the user requests a redesign. An existing README keeps its own structure and needs no skeleton, so a normal update reads no template.
- An existing README file is the target even when the user says “create a README”. Edit it and preserve its structure. Treat the work as new only when no README exists at the target path.
- A structural rewrite needs an explicit request: a redesign, a restructure, or a named profile to adopt. A request to update, sync, or audit is not a rewrite, so preserve the existing sections.
- Read [references/template.md](references/template.md) for a new README, or for a structural rewrite that the user requested. Choose the profile by repository shape: a collection repository or a single-artifact repository. A single-artifact repository must not receive a catalog section.
- Add a section from a profile only when the section has a real target. Never add a licence section, a badge, or a translation link that the repository does not already supply.
- A review, inventory, or suggested diff is read-only until the user asks to write.

## Ground truth

Before drafting, inspect the selected repository or package:

1. Read the target README(s), project manifest(s), and relevant source descriptors.
2. Enumerate components from the actual directory and descriptor files. Verify names, links, install commands, prerequisites, scripts, and versions before documenting them.
3. Use recent history only to identify likely stale claims; current files are authoritative. Treat generated, ignored, private, and unavailable resources as such.
4. Separate verified facts, user-provided claims, and suggested wording. Never invent component names, badges, metrics, releases, licenses, or installation steps.

Keep the English and Chinese files parallel when bilingual sync is requested: same components, section order, links, commands, and scope, with natural translations for prose and headings. Do not force all content into an invented bilingual template when the project intentionally has one language or an existing structure.

## Writing and editing

Describe what each component does and when to use it in concrete language. Keep commands copy-pasteable, use fenced blocks with a language tag, and preserve exact paths and flags. Remove stale statements only when current evidence shows they are stale; record uncertain items for the user instead of guessing. Keep badges only when their target is real and maintained, and preserve a user-supplied badge/header exactly unless asked to change it.

Use the smallest edit that makes the README accurate. Do not add promotional claims, generic “best practice” sections, a table of contents, or installation prerequisites merely because a template contains them. Do not modify source code, package metadata, nested docs, or generated files as part of a README update.

## Review before writing and report after writing

Check that every listed item exists, every command matches the project tooling, links resolve or are clearly marked, and bilingual files cover the same scope when requested. Re-read each changed file after writing and compare the diff against the requested target. Report the exact files changed, verified inventory, stale items removed or retained as uncertain, and checks that could not run. Do not claim publication, release, or successful installation from a documentation-only edit.
