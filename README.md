# Skills by Frad ![](https://img.shields.io/badge/Agent-Skills-blue)

[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT) [![Twitter Follow](https://img.shields.io/twitter/follow/FradSer?style=social)](https://twitter.com/FradSer)

**English** | [简体中文](README.zh-CN.md)

A collection of agent skills: specialized workflows and domain knowledge that can be used across agent runtimes.

The distributable catalog below contains 16 skills. The repository's internal
[skill-creator](.agents/skills/skill-creator/SKILL.md) supports authoring and validation.

## Invocation in Codex

`commit`, `lark`, and `swiftui` allow automatic matching to a task. The other
skills require an explicit mention, such as `$create-pr`. Select a skill with
`$` or `/skills` in Codex CLI and the IDE, or with `@` in the desktop app.

Each skill declares this policy in `agents/openai.yaml`; keep that directory
when installing or symlinking a skill. The existing `disable-model-invocation`
frontmatter is separate metadata for other runtimes. Restart Codex if the
updated invocation policy is not reflected in a new session.

## Available Skills

### [commit](skills/commit/)

Creates clean, conventional git commits using standard git. Use when the user asks to "commit", "git commit", or wants to commit staged or unstaged changes.

**Installation:**
```bash
npx skills add https://github.com/FradSer/skills --skill commit
```

### [commit-and-push](skills/commit-and-push/)

Creates conventional git commits and pushes them to the remote repository. Use when the user asks to "commit and push" or "push changes".

**Installation:**
```bash
npx skills add https://github.com/FradSer/skills --skill commit-and-push
```

### [create-issues](skills/create-issues/)

Drafts or creates GitHub issues with reproduction steps or acceptance criteria, following repository templates and existing labels.

**Installation:**
```bash
npx skills add https://github.com/FradSer/skills --skill create-issues
```

### [create-pr](skills/create-pr/)

Creates GitHub pull requests after relevant repository checks, then hands off once to `review-pr` for CI and feedback within the authorized scope.

**Installation:**
```bash
npx skills add https://github.com/FradSer/skills --skill create-pr
```

### [create-prd](skills/create-prd/)

Creates or revises PRDs while preserving supplied requirements and formats. Supports local Markdown and authorized Feishu/Lark document operations through `lark-cli`.

**Installation:**
```bash
npx skills add https://github.com/FradSer/skills --skill create-prd
```

### [gitflow](skills/gitflow/)

Starts or finishes feature, hotfix, and release branches in repositories configured for Git-flow. Includes changelog and version handling, with local-only execution available.

**Installation:**
```bash
npx skills add https://github.com/FradSer/skills --skill gitflow
```

### [lark](skills/lark/)

Routes Lark/Feishu requests through `lark-cli` and loads the relevant embedded domain guidance using `lark-cli skills read <sub-skill>`.

**Installation:**
```bash
npx skills add https://github.com/FradSer/skills --skill lark
```

### [loop](skills/loop/)

Repeats a prompt or skill on a fixed or variable interval using the host's supported scheduler, with a stopping condition and cancellation instructions.

**Installation:**
```bash
npx skills add https://github.com/FradSer/skills --skill loop
```

### [missav](skills/missav/)

Browses missav.ws listings with agent-browser, extracts listing and detail data, and ranks recommendations against user preferences. Preference persistence follows the user's request.

**Installation:**
```bash
npx skills add https://github.com/FradSer/skills --skill missav
```

### [patent-architect](skills/patent-architect/)

Researches prior art and drafts Chinese technical patent materials with traceable sources and explicit evidence limits.

**Installation:**
```bash
npx skills add https://github.com/FradSer/skills --skill patent-architect
```

### [resolve-issues](skills/resolve-issues/)

Implements tracked GitHub issues with acceptance scenarios, regression checks, and worktree isolation when needed. Hands off to `create-pr` when publication is requested.

**Installation:**
```bash
npx skills add https://github.com/FradSer/skills --skill resolve-issues
```

### [review-pr](skills/review-pr/)

Reviews PR changes, monitors CI and feedback, and applies verified fixes within the requested scope. Merge and cleanup require explicit authorization.

**Installation:**
```bash
npx skills add https://github.com/FradSer/skills --skill review-pr
```

### [storm](skills/storm/)

Researches and writes source-grounded long articles through resumable research, outline, write, and polish phases. Supports available retrieval tools or supplied sources.

**Installation:**
```bash
npx skills add https://github.com/FradSer/skills --skill storm
```

### [swiftui](skills/swiftui/)

Builds, refactors, and reviews SwiftUI for the project's deployment target. Covers state, concurrency, navigation, accessibility, performance, and Liquid Glass where available.

**Installation:**
```bash
npx skills add https://github.com/FradSer/skills --skill swiftui
```

### [tropes](skills/tropes/)

Reviews writing for formulaic phrasing while preserving the author's facts, voice, and format. Reads optional layered writing preferences without changing them.

**Installation:**
```bash
npx skills add https://github.com/FradSer/skills --skill tropes
```

### [update-readme](skills/update-readme/)

Updates the requested README files from repository evidence while preserving existing structure and supplied formatting. Keeps existing translations consistent when relevant.

**Installation:**
```bash
npx skills add https://github.com/FradSer/skills --skill update-readme
```

## Adding a Skill

1. Create a directory under `skills/<skill-name>/`.
2. Add `SKILL.md` with YAML frontmatter (`name`, `description`) and the skill body.
3. Optionally add `evals/evals.json` for evaluation cases.
4. Run the `update-readme` skill to sync both README files.

## Validation

Run the repository suite with `uv run --with pyyaml python -m unittest discover -s tests -v`.
The default suite uses temporary repositories and mocked services; it does not publish
issues or PRs, push to hosted remotes, or validate live accounts and devices. Installation
checks require an explicit opt-in documented in the corresponding test.

For authorized independent model testing, use the [Codex task runner](tools/skill_eval/README.md).
It invokes all 17 source skills in fresh CLI sessions across 22 local cases,
retains raw invocation and output evidence, and keeps external services in fixtures.
These cases check explicit task behavior; they do not establish implicit trigger
accuracy or live account integration.

Use concise descriptions and load supporting references only when relevant to the task.
Keep existing invocation policies when revising skills. See the
[official skill guide](https://learn.chatgpt.com/docs/build-skills) for authoring guidance.

## License

[MIT](LICENSE)
