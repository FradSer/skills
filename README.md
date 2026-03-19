# Skills by Frad ![](https://img.shields.io/badge/Claude-Skills-blue)

[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT) [![Twitter Follow](https://img.shields.io/twitter/follow/FradSer?style=social)](https://twitter.com/FradSer)

**English** | [简体中文](README.zh-CN.md)

A collection of skills (specialized workflows and domain knowledge) for Claude Code.

## Available Skills

### [apple-events](skills/apple-events/)

Use when managing Apple Reminders or Calendars with the `event` CLI: create, view, update, and delete reminders and calendar events (macOS only).

**Installation:**
```bash
npx skills add https://github.com/FradSer/skills --skill apple-events
```

Install the `event` CLI (required by apple-events) via Homebrew:

```bash
brew tap FradSer/brew
brew install event
```

### [tropes](skills/tropes/)

Use when generating any text content, writing documentation, creating code comments, or reviewing writing style. Provides guidance on avoiding common AI writing patterns that make text sound artificial or formulaic.

**Source:** [tropes.fyi](https://tropes.fyi/tropes-md)

**Installation:**
```bash
npx skills add https://github.com/FradSer/skills --skill tropes
```

### [update-readme](skills/update-readme/)

Use when you want to update README.md and README.zh-CN.md to reflect the current state of the project. Scans all skills, checks for stale entries, and writes both files with the correct header format and consistent bilingual content.

**Installation:**
```bash
npx skills add https://github.com/FradSer/skills --skill update-readme
```

## Adding a Skill

1. Create a directory under `skills/<skill-name>/`.
2. Add `SKILL.md` with YAML frontmatter (`name`, `description`) and the skill body.
3. Optionally add `evals/evals.json` for evaluation cases.
4. Run `/update-readme` to sync both README files.
