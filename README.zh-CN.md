# Skills by Frad ![](https://img.shields.io/badge/Agent-Skills-blue)

[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT) [![Twitter Follow](https://img.shields.io/twitter/follow/FradSer?style=social)](https://twitter.com/FradSer)

[English](README.md) | **简体中文**

面向多种 agent 运行环境的技能集合，包含专项工作流与领域知识。

## 可用技能

### [agent-browser](skills/agent-browser/)

当 agent 需要自动化浏览器操作、测试 Web 应用、截图、抓取页面或通过 `agent-browser` CLI 控制 Electron 应用时使用。

**安装命令：**
```bash
npx skills add https://github.com/FradSer/skills --skill agent-browser
```

### [create-prd](skills/create-prd/)

将产品想法转化为中文 PRD 时使用，支持输出本地 Markdown，也支持通过 `lark-cli` 创建飞书/Lark 文档。

**安装命令：**
```bash
npx skills add https://github.com/FradSer/skills --skill create-prd
```

### [lark](skills/lark/)

使用 `lark-cli` 操作飞书/Lark 资源时使用，覆盖文档、表格、多维表格、日历、消息、邮箱、任务、OKR、云盘、知识库、幻灯片、白板、审批、考勤、通讯录、会议和事件等场景。

**安装命令：**
```bash
npx skills add https://github.com/FradSer/skills --skill lark
```

使用此技能前需单独安装 `lark-cli`。

### [missav](skills/missav/)

使用 `agent-browser` 浏览 missav.ws 列表页，从卡片提取标题/时长/链接，并根据用户偏好（女优、番号、关键词、时长）排序推荐 AV。

**安装命令：**
```bash
npx skills add https://github.com/FradSer/skills --skill missav
```

使用此技能前需单独安装 `agent-browser`。

### [patent-architect](skills/patent-architect/)

为技术发明检索现有技术并生成中文专利申请表时使用。

**安装命令：**
```bash
npx skills add https://github.com/FradSer/skills --skill patent-architect
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
4. 运行 `update-readme` skill 同步两个 README 文件。

## License

[MIT](LICENSE)
