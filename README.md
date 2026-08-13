# Skills by Frad ![](https://img.shields.io/badge/Agent-Skills-blue)

[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT) [![Twitter Follow](https://img.shields.io/twitter/follow/FradSer?style=social)](https://twitter.com/FradSer)

**English** | [简体中文](README.zh-CN.md)

A collection of agent skills: specialized workflows and domain knowledge that can be used across agent runtimes.

## Available Skills

### [agent-browser](skills/agent-browser/)

Use when an agent needs to automate browser actions, test web apps, take screenshots, scrape pages, or control Electron apps through the `agent-browser` CLI.

**Installation:**
```bash
npx skills add https://github.com/FradSer/skills --skill agent-browser
```

### [create-prd](skills/create-prd/)

Use when turning product ideas into Chinese PRDs, with local Markdown output or Feishu/Lark document creation through `lark-cli`.

**Installation:**
```bash
npx skills add https://github.com/FradSer/skills --skill create-prd
```

### [lark](skills/lark/)

Use when operating Feishu/Lark resources with `lark-cli`, including docs, sheets, base, calendar, IM, mail, tasks, OKRs, drive, wiki, slides, whiteboards, approvals, attendance, contacts, meetings, and events.

**Installation:**
```bash
npx skills add https://github.com/FradSer/skills --skill lark
```

Install `lark-cli` separately before using this skill.

### [missav](skills/missav/)

Use when browsing missav.ws listing pages with `agent-browser`, extracting title/duration/url from cards, and ranking AV recommendations by user preferences (actress, code, keywords, duration).

**Installation:**
```bash
npx skills add https://github.com/FradSer/skills --skill missav
```

Install `agent-browser` separately before using this skill.

### [patent-architect](skills/patent-architect/)

Use when researching prior art and generating Chinese patent application forms for technical inventions.

**Installation:**
```bash
npx skills add https://github.com/FradSer/skills --skill patent-architect
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
4. Run the `update-readme` skill to sync both README files.

## License

[MIT](LICENSE)
