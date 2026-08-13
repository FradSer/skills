# Skills by Frad ![](https://img.shields.io/badge/Agent-Skills-blue)

[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT) [![Twitter Follow](https://img.shields.io/twitter/follow/FradSer?style=social)](https://twitter.com/FradSer)

[English](README.md) | **简体中文**

面向多种 agent 运行环境的技能集合，包含专项工作流与领域知识。

## 可用技能

### [agent-browser](skills/agent-browser/)

面向 AI agent 的浏览器自动化 CLI。用于浏览页面、填写表单、截图、抓取数据、测试 Web 应用，或自动化 Electron 桌面应用。

**安装命令：**
```bash
npx skills add https://github.com/FradSer/skills --skill agent-browser
```

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

### [finish-feature](skills/finish-feature/)

使用 git-flow 完成功能分支并合并到 develop，随后清理过期分支与 worktree。当用户要求 "finish a feature" 或 "complete feature" 时使用。

**安装命令：**
```bash
npx skills add https://github.com/FradSer/skills --skill finish-feature
```

### [finish-hotfix](skills/finish-hotfix/)

使用 git-flow 完成 hotfix 并合并到 main 和 develop，随后清理过期分支与 worktree。当用户要求 "finish a hotfix" 或 "complete hotfix" 时使用。

**安装命令：**
```bash
npx skills add https://github.com/FradSer/skills --skill finish-hotfix
```

### [finish-release](skills/finish-release/)

使用 git-flow 完成 release 并以标签合并到 main 和 develop，随后清理过期分支与 worktree。当用户要求 "finish a release" 或 "complete release" 时使用。

**安装命令：**
```bash
npx skills add https://github.com/FradSer/skills --skill finish-release
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

### [start-feature](skills/start-feature/)

使用 git-flow 开启新的功能分支。接受分支名/版本号或自然语言描述。当用户要求 "start a feature" 或 "git flow feature start" 时使用。

**安装命令：**
```bash
npx skills add https://github.com/FradSer/skills --skill start-feature
```

### [start-hotfix](skills/start-hotfix/)

使用 git-flow 开启新的 hotfix 分支。接受分支名/版本号或自然语言描述。当用户要求 "start a hotfix" 或 "git flow hotfix start" 时使用。

**安装命令：**
```bash
npx skills add https://github.com/FradSer/skills --skill start-hotfix
```

### [start-release](skills/start-release/)

使用 git-flow 开启新的 release 分支。接受分支名/版本号或自然语言描述。当用户要求 "start a release" 或 "git flow release start" 时使用。

**安装命令：**
```bash
npx skills add https://github.com/FradSer/skills --skill start-release
```

### [substore-openclash](skills/substore-openclash/)

管理 SubStore 到 OpenClash 的配置管道，用于微信图片直连路由与 mihomo 配置修复，同时修复 homebridge-miot 小米登录错误。当用户提到 "微信图片看不到"、TFO、fake-ip、代理组或 MiCloud 登录失败时使用。

**安装命令：**
```bash
npx skills add https://github.com/FradSer/skills --skill substore-openclash
```

### [tropes](skills/tropes/)

检测并消除使文本显得生硬或公式化的 AI 写作套路。生成文本内容、编写文档、创建代码注释或审阅写作风格时使用。

**来源：** [tropes.fyi](https://tropes.fyi/tropes-md)

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
