# Skills by Frad

[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Twitter Follow](https://img.shields.io/twitter/follow/FradSer?style=social)](https://twitter.com/FradSer)

A repo for managing skills (specialized workflows and domain knowledge).

English | [简体中文](README.zh-CN.md)

## Available Skills

### [apple-events](skills/apple-events/)
Use when managing Apple Reminders or Calendars with the `event` CLI: create, view, update, delete reminders and calendar events (macOS).

**Installation:**
```bash
npx skills add https://github.com/FradSer/skills --skill apple-events
```

Install `event` CLI (required by apple-events) via Homebrew:

```bash
# Add tap
brew tap FradSer/brew

# Install
brew install event
```

## Adding a Skill

1. Create a directory under `skills/<skill-name>/`.
2. Add `SKILL.md` with YAML frontmatter (`name`, `description`) and the skill content.
3. Optionally add `evals/evals.json` for evaluation cases.
4. Update this README’s “Available Skills” table.
