# Agent-Browser Skill 同步说明

## 上游仓库

- **仓库**: [vercel-labs/agent-browser](https://github.com/vercel-labs/agent-browser)
- **路径**: `skills/agent-browser/`
- **上次同步**: 2026-04-16

## 同步内容

此 skill 通过 `git sparse-checkout` 从上游仓库整个目录同步，自动处理新增/变更/删除的文件。

当前同步的文件:

### 核心文件
- `SKILL.md` - 主技能文档

### 参考文档 (references/)
- `authentication.md` - 认证模式
- `commands.md` - 命令参考
- `profiling.md` - 性能分析
- `proxy-support.md` - 代理支持
- `session-management.md` - 会话管理
- `snapshot-refs.md` - 快照引用
- `video-recording.md` - 视频录制

### 模板脚本 (templates/)
- `authenticated-session.sh` - 认证会话模板
- `capture-workflow.sh` - 捕获工作流模板
- `form-automation.sh` - 表单自动化模板

## 同步方法

在仓库内使用 `git sparse-checkout` 同步整个目录（自动处理新增/删除文件）:

```bash
# 将 agent-browser 上游加入 sparse-checkout
# 以 vercel-labs/agent-browser 仓库为例：
#   git remote add upstream https://github.com/vercel-labs/agent-browser
#   git config core.sparseCheckout true
#   echo 'skills/agent-browser/' > .git/info/sparse-checkout
#   git pull upstream main
```

## 注意事项

- 使用 `git sparse-checkout` 同步整个目录，自动处理新增/删除文件
- 本地 `SYNC.md` 不会被上游覆盖
- 本地修改会在同步时被覆盖（其他文件）
- 同步前建议先备份本地修改，避免被上游覆盖
