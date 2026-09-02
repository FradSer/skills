# Skills by Frad ![](https://img.shields.io/badge/Agent-Skills-blue)

[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT) [![Twitter Follow](https://img.shields.io/twitter/follow/FradSer?style=social)](https://twitter.com/FradSer)

[English](README.md) | **简体中文**

面向多种 agent 运行环境的技能集合，包含专项工作流与领域知识。

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

遵循测试驱动开发原则和标签规范创建 GitHub issue。当用户要求 "create an issue"、"file a bug" 或记录新需求、epic、PR 范围内的任务时使用。

**安装命令：**
```bash
npx skills add https://github.com/FradSer/skills --skill create-issues
```

### [create-pr](skills/create-pr/)

创建 GitHub Pull Request，包含自动化质量校验与安全扫描，随后交给 `review-pr` 进行 CI 监控与评论分类处理。当用户要求 "create a PR" 或 "submit a pull request" 时使用。

**安装命令：**
```bash
npx skills add https://github.com/FradSer/skills --skill create-pr
```

### [create-prd](skills/create-prd/)

将产品想法转化为中文 PRD 文档，支持本地 Markdown 输出，也支持通过 `lark-cli` 创建飞书/Lark 文档。

**安装命令：**
```bash
npx skills add https://github.com/FradSer/skills --skill create-prd
```

### [gitflow](skills/gitflow/)

管理 Git-flow 分支生命周期：自动化启动或完成 feature、hotfix 和 release 分支，支持自动生成 changelog、版本号递增及分支清理。当用户要求启动/完成分支或提及 git-flow 时使用。

**安装命令：**
```bash
npx skills add https://github.com/FradSer/skills --skill gitflow
```

### [lark](skills/lark/)

飞书/Lark CLI 统一路由技能，基于 `lark-cli`。通过 `lark-cli skills read <sub-skill>` 将用户意图分发至各业务域技能（文档、电子表格、多维表格、日历、即时通讯、邮箱、任务、OKR、云空间、知识库、幻灯片、画板、妙搭应用、审批、考勤、通讯录、视频会议、妙记、纪要、实时事件等）。

**安装命令：**
```bash
npx skills add https://github.com/FradSer/skills --skill lark
```

### [loop](skills/loop/)

按固定或动态间隔再次执行提示词或技能，使用当前宿主提供的持久计时器、订阅机制或受监控的后台进程。

**安装命令：**
```bash
npx skills add https://github.com/FradSer/skills --skill loop
```

### [missav](skills/missav/)

使用 agent-browser 浏览 missav.ws 视频列表，提取标题/时长/链接，解析详情页剧情描述进行题材分析，并基于 ~/.missav/ 中的用户偏好进行个性化推荐与排序。

**安装命令：**
```bash
npx skills add https://github.com/FradSer/skills --skill missav
```

### [patent-architect](skills/patent-architect/)

通过 SerpAPI 检索现有技术并生成中文专利申请表。当用户想要保护技术创新或提到 "patents"、"inventions" 时使用。

**安装命令：**
```bash
npx skills add https://github.com/FradSer/skills --skill patent-architect
```

### [resolve-issues](skills/resolve-issues/)

使用隔离 worktree 和测试驱动开发解决 GitHub issue，随后交给 `create-pr` 创建 PR，确保质量关卡与 review 流程始终执行。当用户要求 "resolve an issue" 或 "fix issue #123" 时使用。

**安装命令：**
```bash
npx skills add https://github.com/FradSer/skills --skill resolve-issues
```

### [review-pr](skills/review-pr/)

审查 Pull Request：对 diff 进行基线审查、监控 CI 与评审评论、由独立 sceptic agent 分类处理每条评论、只应用已验证的修复，并持续提交直到 CI 通过。当用户要求 "review a PR" 或 "watch CI on a pull request" 时使用。

**安装命令：**
```bash
npx skills add https://github.com/FradSer/skills --skill review-pr
```

### [storm](skills/storm/)

基于多视角研究与检索生成维基百科风格的长文，移植了 Stanford STORM 的四阶段管道（research、outline、write、polish）。

**安装命令：**
```bash
npx skills add https://github.com/FradSer/skills --skill storm
```

### [swiftui](skills/swiftui/)

用于构建、重构和审查现代 SwiftUI。优先采用 macOS 26 与 iOS 26 的 Liquid Glass，同时涵盖视图架构、状态、并发、导航、无障碍、性能和测试。

**安装命令：**
```bash
npx skills add https://github.com/FradSer/skills --skill swiftui
```

### [tropes](skills/tropes/)

检测并消除使文本显得生硬或公式化的 AI 写作套路。生成文本内容、编写文档、创建代码注释或审阅写作风格时使用。

**安装命令：**
```bash
npx skills add https://github.com/FradSer/skills --skill tropes
```

### [update-readme](skills/update-readme/)

将 README.md 和 README.zh-CN.md 同步到项目最新状态。扫描所有技能、检查过期条目，并按正确的头部格式输出双语文件。

**安装命令：**
```bash
npx skills add https://github.com/FradSer/skills --skill update-readme
```

## 添加新技能

1. 在 `skills/<skill-name>/` 下新建目录。
2. 添加 `SKILL.md`，包含 YAML frontmatter（`name`、`description`）及技能正文。
3. 可选：添加 `evals/evals.json` 作为评估用例。
4. 运行 `update-readme` skill 同步两个 README 文件。

## License

[MIT](LICENSE)
