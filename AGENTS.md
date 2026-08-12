# AGENTS.md

## 环境

- Python 3.11，uv 管理依赖
- config.py 集中配置所有常量，pyproject.toml 管理依赖

## 关键文件

## 参考文档

- 原版参考：`D:\CodeFile\Agent\KeymouseGo\README.md`

## 规则

- **config 重命名全量 grep**：常量改名/移除后，搜索所有引用点确保同步更新

## 工具

- 详见 `mcp_tools_summary.csv`
- 可并行的指令用 `parallel=True`有奇效
- `wet-mcp extract` 可下载文件/抓取页面媒体组件
- `Read` 无法访问 `D:\Temp`，MCP 长输出需 `Copy-Item` 到项目根目录，然后正则替换 `\\n` 为 `\n`，否则输出超长行
- 快速搜索优先 `WebSearch`（更快），深度内容再用 `wet-mcp`；提取网站内容必须用 `wet-mcp` 的 `extract`

## 经验/坑点

- **单例进程计数**：用 `os.path.abspath(__file__)` + `result.stdout.count(script)` 精确匹配，比 PID 文件更可靠，无残留。`Where-Object { ProcessId -ne }` 在 PowerShell 管道中可能失效，不如 Python 侧 `count()` 简单

## 工作流

0. 读AGENTS.md
1. 构想：调用 brainstorming → 产出 `docs/superpowers/specs/<date>-design.md`
2. 计划：调用 writing-plans → 产出 `docs/superpowers/plans/<date>-plan.md`
3. 发派：调用 dispatching-parallel-agents 产出给n号机（目前只有1，2号机）的提示词 `docs/superpowers/subprompts/<date>-plan-subprompt-n.md` ，用于手动发派（当前环境是win且不支持子代理，无法自动 dispatch），创建`docs/superpowers/subprompts/<date>-plan-process.md` 用于记录进度，防止冲突
4. 实施：调用 executing-plans
   - 先隔离，使用git创建新的dev分支（1号机）或者进入已有分支（2号机）  
   - 遇到 bug 自动触发 systematic-debugging（先找根因再修）
   - 写代码自动触发 test-driven-development（先写测试再实现）
5. 验证：调用 verification-before-completion → 跑验证命令确认完成
6. 记录：调用 writing-agents → 写CHANGELOG.md + 经验教训到AGENTS.md
7. 提交：调用 finishing-a-development-branch → 分组提交