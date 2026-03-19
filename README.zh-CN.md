# Skills by Frad ![](https://img.shields.io/badge/Claude-Skills-blue)

[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT) [![Twitter Follow](https://img.shields.io/twitter/follow/FradSer?style=social)](https://twitter.com/FradSer)

[English](README.md) | **简体中文**

面向 Claude Code 的技能集合（专项工作流与领域知识）。

## 可用技能

### [apple-events](skills/apple-events/)

使用 `event` CLI 管理 Apple 提醒事项与日历时使用：创建、查看、更新、删除提醒与日历事件（仅限 macOS）。

**安装命令：**
```bash
npx skills add https://github.com/FradSer/skills --skill apple-events
```

通过 Homebrew 安装 `event` CLI（apple-events 依赖）：

```bash
brew tap FradSer/brew
brew install event
```

### [tropes](skills/tropes/)

生成文本内容、编写文档、创建代码注释或审阅写作风格时使用。提供避免常见 AI 写作模式的指导，使文本更自然、更少公式化。

**来源：** [tropes.fyi](https://tropes.fyi/tropes-md)

**安装命令：**
```bash
npx skills add https://github.com/FradSer/skills --skill tropes
```

### [update-readme](skills/update-readme/)

需要将 README.md 和 README.zh-CN.md 同步到项目最新状态时使用。自动扫描所有技能，检查过期条目，并按正确的头部格式输出双语文件。

**安装命令：**
```bash
npx skills add https://github.com/FradSer/skills --skill update-readme
```

## 添加新技能

1. 在 `skills/<skill-name>/` 下新建目录。
2. 添加 `SKILL.md`，包含 YAML frontmatter（`name`、`description`）及技能正文。
3. 可选：添加 `evals/evals.json` 作为评估用例。
4. 运行 `/update-readme` 同步两个 README 文件。

## License

[MIT](LICENSE)
