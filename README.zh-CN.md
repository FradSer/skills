# Skills by Frad

[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Twitter Follow](https://img.shields.io/twitter/follow/FradSer?style=social)](https://twitter.com/FradSer)

用于管理技能（专项工作流与领域知识）的仓库。

[English](README.md) | 简体中文

## 结构

```
skills/
├── README.md
├── README.zh-CN.md
└── skills/
    └── apple-events/
        ├── SKILL.md          # 必选 – 技能说明
        └── evals/
            └── evals.json    # 可选 – 评估用例
```

每个技能是一个目录，包含 `SKILL.md`（YAML frontmatter：`name`、`description`），以及可选的 `evals/evals.json`。

## 可用技能

| 技能 | 说明 |
|------|------|
| [apple-events](skills/apple-events/) | 使用 `event` CLI 管理 Apple 提醒事项与日历时使用：创建、查看、更新、删除提醒与日历事件（macOS）。 |

安装 `event` CLI（apple-events 依赖），使用 Homebrew：

```bash
# Add tap
brew tap FradSer/brew

# Install
brew install event
```

## 添加新技能

1. 在 `skills/<skill-name>/` 下新建目录。
2. 添加 `SKILL.md`，包含 YAML frontmatter（`name`、`description`）及技能正文。
3. 可选：添加 `evals/evals.json` 作为评估用例。
4. 在本 README 的「可用技能」表格中补充条目。
