# Skills by Frad ![](https://img.shields.io/badge/Agent-Skills-blue)

[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT) [![Twitter Follow](https://img.shields.io/twitter/follow/FradSer?style=social)](https://twitter.com/FradSer)

**English** | [简体中文](README.zh-CN.md)

A collection of agent skills: specialized workflows and domain knowledge that can be used across agent runtimes.

## Available Skills

### [agent-browser](skills/agent-browser/)

Browser automation CLI for AI agents. Use for navigating pages, filling forms, taking screenshots, scraping data, testing web apps, or automating Electron desktop apps.

**Installation:**
```bash
npx skills add https://github.com/FradSer/skills --skill agent-browser
```

### [commit](skills/commit/)

Creates clean, conventional git commits using standard git. Use when the user asks to "commit", "git commit", or wants to commit staged or unstaged changes.

**Installation:**
```bash
npx skills add https://github.com/FradSer/skills --skill commit
```

### [commit-and-push](skills/commit-and-push/)

Creates conventional git commits and pushes them to the remote. Use when the user asks to "commit and push" or "push changes".

**Installation:**
```bash
npx skills add https://github.com/FradSer/skills --skill commit-and-push
```

### [create-issues](skills/create-issues/)

Creates GitHub issues following test-driven development principles and labeling conventions. Use when the user asks to "create an issue", "file a bug", or document new requirements, epics, or PR-scoped tasks.

**Installation:**
```bash
npx skills add https://github.com/FradSer/skills --skill create-issues
```

### [create-pr](skills/create-pr/)

Creates GitHub pull requests with automated quality validation and security scanning, then hands off to `review-pr` for CI monitoring and comment triage. Use when the user asks to "create a PR" or "submit a pull request".

**Installation:**
```bash
npx skills add https://github.com/FradSer/skills --skill create-pr
```

### [create-prd](skills/create-prd/)

Turns product ideas into Chinese PRD documents, with local Markdown output or Feishu/Lark document creation through `lark-cli`.

**Installation:**
```bash
npx skills add https://github.com/FradSer/skills --skill create-prd
```

### [finish-feature](skills/finish-feature/)

Finalizes a feature branch and merges it into develop using git-flow, then prunes stale branches and worktrees. Use when the user asks to "finish a feature" or "complete feature".

**Installation:**
```bash
npx skills add https://github.com/FradSer/skills --skill finish-feature
```

### [finish-hotfix](skills/finish-hotfix/)

Finalizes a hotfix and merges it into main and develop using git-flow, then prunes stale branches and worktrees. Use when the user asks to "finish a hotfix" or "complete hotfix".

**Installation:**
```bash
npx skills add https://github.com/FradSer/skills --skill finish-hotfix
```

### [finish-release](skills/finish-release/)

Finalizes a release and merges it into main and develop with a tag using git-flow, then prunes stale branches and worktrees. Use when the user asks to "finish a release" or "complete release".

**Installation:**
```bash
npx skills add https://github.com/FradSer/skills --skill finish-release
```

### [lark](skills/lark/)

Unified router for Lark/Feishu CLI operations via `lark-cli`. Routes intents to domain skills (docs, sheets, base, calendar, IM, mail, tasks, okr, drive, wiki, slides, whiteboard, apps/Miaoda, approval, attendance, contact, vc, minutes, note, events) via `lark-cli skills read <sub-skill>`.

**Installation:**
```bash
npx skills add https://github.com/FradSer/skills --skill lark
```

### [patent-architect](skills/patent-architect/)

Searches prior art via SerpAPI and generates Chinese patent application forms. Use when the user wants to protect technical innovations or mentions "patents" or "inventions".

**Installation:**
```bash
npx skills add https://github.com/FradSer/skills --skill patent-architect
```

### [resolve-issues](skills/resolve-issues/)

Resolves GitHub issues using isolated worktrees and test-driven development, then hands PR creation to `create-pr` so the quality gate and review loop always run. Use when the user asks to "resolve an issue" or "fix issue #123".

**Installation:**
```bash
npx skills add https://github.com/FradSer/skills --skill resolve-issues
```

### [review-pr](skills/review-pr/)

Reviews a pull request: runs a baseline review of the diff, monitors CI and incoming reviewer comments, triages each comment through a skeptical agent, applies only verified fixes, and commits until CI passes. Use when the user asks to "review a PR" or "watch CI on a pull request".

**Installation:**
```bash
npx skills add https://github.com/FradSer/skills --skill review-pr
```

### [start-feature](skills/start-feature/)

Starts a new feature branch using git-flow. Accepts either a branch name/version or a natural-language description. Use when the user asks to "start a feature" or "git flow feature start".

**Installation:**
```bash
npx skills add https://github.com/FradSer/skills --skill start-feature
```

### [start-hotfix](skills/start-hotfix/)

Starts a new hotfix branch using git-flow. Accepts either a branch name/version or a natural-language description. Use when the user asks to "start a hotfix" or "git flow hotfix start".

**Installation:**
```bash
npx skills add https://github.com/FradSer/skills --skill start-hotfix
```

### [start-release](skills/start-release/)

Starts a new release branch using git-flow. Accepts either a branch name/version or a natural-language description. Use when the user asks to "start a release" or "git flow release start".

**Installation:**
```bash
npx skills add https://github.com/FradSer/skills --skill start-release
```

### [substore-openclash](skills/substore-openclash/)

Manages the SubStore to OpenClash config pipeline for WeChat image direct routing and mihomo config fixes, and fixes homebridge-miot Xiaomi login errors. Use when the user says "wechat images not loading", "微信图片看不到", or reports TFO, fake-ip, proxy group, or MiCloud login failures.

**Installation:**
```bash
npx skills add https://github.com/FradSer/skills --skill substore-openclash
```

### [swiftui](skills/swiftui/)

Builds, refactors, and reviews modern SwiftUI. Prioritizes macOS 26 and iOS 26 Liquid Glass while covering view architecture, state, concurrency, navigation, accessibility, performance, and testing. Ships dedicated topic references (state, lists, layout, charts, macOS scenes, localization, previews), the authoritative [twostraws](https://github.com/twostraws/swiftui-agent-skill) review baseline, and Instruments trace tooling vendored from [AvdLee/SwiftUI-Agent-Skill](https://github.com/AvdLee/SwiftUI-Agent-Skill).

**Installation:**
```bash
npx skills add https://github.com/FradSer/skills --skill swiftui
```

### [tropes](skills/tropes/)

Detects and eliminates AI writing tropes that make text sound artificial or formulaic. Use when generating text content, writing documentation, creating code comments, or reviewing writing style.

**Source:** [tropes.fyi](https://tropes.fyi/tropes-md)

**Installation:**
```bash
npx skills add https://github.com/FradSer/skills --skill tropes
```

### [update-readme](skills/update-readme/)

Updates README.md and README.zh-CN.md to reflect the project's current state. Scans all skills, checks for stale entries, and writes both files with the correct header format and consistent bilingual content.

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
