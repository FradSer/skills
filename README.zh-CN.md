# Skills by Frad ![](https://img.shields.io/badge/Agent-Skills-blue)

[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT) [![Twitter Follow](https://img.shields.io/twitter/follow/FradSer?style=social)](https://twitter.com/FradSer)

[English](README.md) | **简体中文**

面向多种 agent 运行环境的技能集合，包含专项工作流与领域知识。

以下发布目录包含 18 个技能；仓库内部的
[skill-creator](.agents/skills/skill-creator/SKILL.md) 用于编写和验证技能。

## Codex 中的触发方式

`commit`、`design-engineering`、`lark`、`marketing` 和 `swiftui` 允许根据任务自动匹配，其他技能需要明确点名，例如
`$create-pr`。在 Codex CLI 和 IDE 中使用 `$` 或 `/skills` 选择技能，在桌面应用中使用 `@`。

每个技能通过 `agents/openai.yaml` 声明触发策略；安装或建立软链接时应保留这个目录。
原有的 `disable-model-invocation` frontmatter 是其他运行时的独立元数据。
若新会话未反映更新后的触发策略，请重启 Codex。

## 可用技能

### [commit](skills/commit/)

使用标准 git 创建规范、原子的 Conventional Commit。当用户要求 "commit"、"git commit" 或提交已暂存/未暂存的更改时使用。

**安装命令：**
```bash
npx skills add https://github.com/FradSer/skills --skill commit
```

### [commit-and-push](skills/commit-and-push/)

创建 Conventional Commit 并推送到远程仓库。当用户要求 "commit and push" 或 "push changes" 时使用。

**安装命令：**
```bash
npx skills add https://github.com/FradSer/skills --skill commit-and-push
```

### [create-issues](skills/create-issues/)

起草或创建 GitHub issue，包含复现步骤或验收条件，并遵循仓库模板和现有标签。

**安装命令：**
```bash
npx skills add https://github.com/FradSer/skills --skill create-issues
```

### [create-pr](skills/create-pr/)

完成相关仓库检查后创建 GitHub PR，随后单次交接给 `review-pr`，在授权范围内监控 CI 和处理反馈。

**安装命令：**
```bash
npx skills add https://github.com/FradSer/skills --skill create-pr
```

### [create-prd](skills/create-prd/)

创建或修订 PRD，保留已有需求和指定格式。支持本地 Markdown，以及经授权通过 `lark-cli` 操作飞书/Lark 文档。

**安装命令：**
```bash
npx skills add https://github.com/FradSer/skills --skill create-prd
```

### [design-engineering](skills/design-engineering/)

以统一的视觉品味、有目的性的动效、无障碍与可用性来设计、实现、打磨和审查产品界面；保留上游的界面质量与设计工程工作流作为参考资料。

**安装命令：**
```bash
npx skills add https://github.com/FradSer/skills --skill design-engineering
```

### [gitflow](skills/gitflow/)

在已配置 Git-flow 的仓库中启动或完成 feature、hotfix 和 release 分支，包含 changelog 和版本处理，支持仅在本地执行。

**安装命令：**
```bash
npx skills add https://github.com/FradSer/skills --skill gitflow
```

### [lark](skills/lark/)

通过 `lark-cli` 路由飞书/Lark 请求，并使用 `lark-cli skills read <sub-skill>` 按需加载内置业务域指引。

**安装命令：**
```bash
npx skills add https://github.com/FradSer/skills --skill lark
```

### [loop](skills/loop/)

使用宿主支持的调度机制，按固定或动态间隔重复执行提示词或技能，并提供停止条件和取消方式。

**安装命令：**
```bash
npx skills add https://github.com/FradSer/skills --skill loop
```

### [marketing](skills/marketing/)

把营销请求路由到 50 个内置工作流，覆盖定位、文案、SEO 与 AI 搜索、转化优化、广告、生命周期邮件、定价、发布、分析与增长，同时只暴露一个技能。

**安装命令：**
```bash
npx skills add https://github.com/FradSer/skills --skill marketing
```

### [missav](skills/missav/)

使用 agent-browser 浏览 missav.ws 列表，提取列表和详情数据，结合用户偏好进行推荐排序；按用户要求决定是否保存偏好。

**安装命令：**
```bash
npx skills add https://github.com/FradSer/skills --skill missav
```

### [patent-architect](skills/patent-architect/)

检索现有技术并起草中文专利技术材料，保留可追溯来源并说明证据边界。

**安装命令：**
```bash
npx skills add https://github.com/FradSer/skills --skill patent-architect
```

### [resolve-issues](skills/resolve-issues/)

通过验收场景和回归检查实现 GitHub issue，按需使用 worktree 隔离；用户要求发布时交接给 `create-pr`。

**安装命令：**
```bash
npx skills add https://github.com/FradSer/skills --skill resolve-issues
```

### [review-pr](skills/review-pr/)

审查 PR 改动、监控 CI 和反馈，并在请求范围内应用已验证的修复；合并和清理需要明确授权。

**安装命令：**
```bash
npx skills add https://github.com/FradSer/skills --skill review-pr
```

### [storm](skills/storm/)

通过可续跑的研究、提纲、写作和润色阶段生成有来源支撑的长文，支持可用检索工具或用户提供的材料。

**安装命令：**
```bash
npx skills add https://github.com/FradSer/skills --skill storm
```

### [swiftui](skills/swiftui/)

根据项目部署目标构建、重构和审查 SwiftUI，涵盖状态、并发、导航、无障碍、性能，以及可用平台上的 Liquid Glass。

**安装命令：**
```bash
npx skills add https://github.com/FradSer/skills --skill swiftui
```

### [tropes](skills/tropes/)

审查公式化写作表达，保留作者事实、语气和格式；可读取分层写作偏好，不修改偏好文件。

**安装命令：**
```bash
npx skills add https://github.com/FradSer/skills --skill tropes
```

### [update-readme](skills/update-readme/)

依据仓库事实更新指定的 README，保留已有结构和指定格式；存在相关译本时保持内容一致。

**安装命令：**
```bash
npx skills add https://github.com/FradSer/skills --skill update-readme
```

## 添加新技能

1. 在 `skills/<skill-name>/` 下新建目录。
2. 添加 `SKILL.md`，包含 YAML frontmatter（`name`、`description`）及技能正文。
3. 可选：添加 `evals/evals.json` 作为评估用例。
4. 运行 `update-readme` skill 同步两个 README 文件。

## 验证

运行仓库测试：`uv run --with pyyaml python -m unittest discover -s tests -v`。
默认测试使用临时仓库和模拟服务，不发布 issue 或 PR、不向托管远端推送，也不验证真实账号或设备。
安装检查需按对应测试的说明显式开启。

用户授权独立模型测试后，可使用 [Codex 任务评估器](tools/skill_eval/README.md)。
它通过全新 CLI 会话调用全部 18 个源 skill，执行 23 个本地用例，保留原始调用与产物证据；
外部服务使用 fixture。这些用例验证显式任务行为，不代表隐式触发准确率或真实账号集成已通过。

使用简洁的触发描述，仅在任务需要时加载参考资料。修订技能时保留已有触发策略。
编写指引见[官方 skill 文档](https://learn.chatgpt.com/docs/build-skills)。

## License

[MIT](LICENSE)
