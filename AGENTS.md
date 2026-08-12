# AGENTS.md

## 环境

- Python 3.11，uv 管理依赖
- config.py 集中配置所有常量，pyproject.toml 管理依赖
- **命令执行**：统一走 `cmd-exec-mcp`，详见 `../mcp_tools_summary.csv`

## 关键文件

## 参考文档

- 原版参考：`D:\CodeFile\Agent\KeymouseGo\README.md`

## 规则

- **config 重命名全量 grep**：常量改名/移除后，搜索所有引用点确保同步更新

## 工具

- 详见 `../mcp_tools_summary.csv`
- 可并行的指令用 `parallel=True`有奇效
- `wet-mcp extract` 可下载文件/抓取页面媒体组件
- `Read` 无法访问 `D:\Temp`，MCP 长输出需 `Copy-Item` 到项目根目录，然后正则替换 `\\n` 为 `\n`，否则输出超长行
- 快速搜索优先 `WebSearch`（更快），深度内容再用 `wet-mcp`；提取网站内容必须用 `wet-mcp` 的 `extract`

## 经验/坑点

- **单例进程计数**：用 `os.path.abspath(__file__)` + `result.stdout.count(script)` 精确匹配，比 PID 文件更可靠，无残留。`Where-Object { ProcessId -ne }` 在 PowerShell 管道中可能失效，不如 Python 侧 `count()` 简单
- **`uv sync` 不装 dev 依赖**：`uv sync` 只装 `[project.dependencies]`，pytest 在 `[project.optional-dependencies] dev` 里，需 `uv sync --extra dev` 才能安装
- **FFT NCC 积分图列偏移**：`integral[i+h, j+w]` 的列偏移是 `w`（模板宽度），不是 `1`。用 `1` 导致计算的是 h×1 区域而非 h×w 区域
- **卡尔曼静态模型收敛**：静态目标模型 + 低过程噪声时，协方差快速收敛到接近零，Kalman Gain 极小，滤波器不再信任观测。测试需从真实值附近初始化，或增大过程噪声
- **`time.time()` 单位是秒**：内部计算 `duration_ms = int((end - start) * 1000)`，测试 mock 时间值时注意单位
- **实现前必须对照设计文档**：类名、方法签名、参数类型、返回值类型必须与设计文档一致，否则后续环节（如 player 依赖 kalman）会连锁报错
- **`_pos_match` 多路径测试需 mock 多个内部方法**：`_pos_match` 有多个 fallback 路径（shot 文件不存在→原始坐标、匹配失败→卡尔曼预测值），测试匹配成功/失败路径时需同时 mock `_load_shot` 和 `_capture_screen`，否则静默走 fallback

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