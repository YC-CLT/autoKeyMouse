# AGENTS.md

## 环境

- Python 3.11 + uv

## 关键文件

| 文件 | 作用 |
|------|------|
| `config.py` | 所有配置常量集中管理 |
| `main.py` | CLI 入口，argparse 子命令分发 |
| `engine/script.py` | Event/Script 数据模型 + JSON 存取 |
| `engine/capture.py` | PIL 截图 + 边缘裁剪 |
| `engine/matcher.py` | FFT NCC 模板匹配 |
| `engine/hooks.py` | pyWinhook 全局钩子封装 |
| `engine/logger.py` | 项目级日志，按日轮转 |
| `engine/recorder.py` | 录制调度器 |
| `engine/player.py` | 回放调度器 |
| `cli/commands.py` | 5 个子命令处理 (record/play/list/inspect/tui) |
| `tui/app.py` | Rich Live 交互菜单 |

## 参考文档

| 文件 | 内容 |
|------|------|
| `docs/2026-08-13-KeymouseGo-research.md` | KeymouseGo 参考项目调研（架构、脚本系统、回放引擎、插件系统） |

## 关键常量

所有常量在 `config.py`，修改后全量 grep 同步引用。

| 常量 | 默认值 | 说明 |
|------|--------|------|
| `STOP_HOTKEY` | `"f9"` | 全局停止热键 |
| `SHOT_RADIUS` | `50` | 截图裁剪半径 (px) |
| `MATCH_CONFIDENCE` | `0.85` | NCC 置信度阈值 |
| `MATCH_SEARCH_RADIUS` | `100` | 搜索 ROI 半径 (px) |
| `MOUSE_MOVE_INTERVAL_MS` | `200` | 鼠标移动事件最小间隔 |
| `DRAG_THRESHOLD_MS` | `300` | 按住多久判定为拖拽 |
| `SHOT_FORMAT` | `"PNG"` | 截图格式 |

## 规则

- **命令执行**：统一走 `cmd-exec-mcp`，必须先读 `./mcp_tools_summary.csv`
- **config 重命名全量 grep**：常量改名/移除后，搜索所有引用点确保同步更新
- **入口 DPI 感知**：`main.py` 必须调用 `SetProcessDPIAware()`，否则高 DPI 下坐标偏移
- **停止热键过滤**：录制端必须过滤停止热键，不写入脚本，否则回放自爆
- **实现前对照设计文档**：类名、方法签名、参数类型、返回值必须与设计文档一致

## 工具

- MCP 工具清单见 `../mcp_tools_summary.csv`
- 可并行的指令用 `parallel=True`
- 搜索通用知识/技术方案用 `WebSearch`；抓取特定网页完整内容用 `wet-mcp` 的 `extract`
- `wet-mcp extract` 可下载文件/抓取页面媒体组件
- `Read` 无法访问 `D:\Temp`，MCP 长输出需 `Copy-Item` 到项目根目录，正则替换 `\\n` 为 `\n`
- `write` 不支持 `replace_all`，用正则替换

## 经验/坑点

- **单例进程计数**：用 `os.path.abspath(__file__)` + `result.stdout.count(script)` 精确匹配，比 PID 文件更可靠，无残留
- **`uv sync` 不装 dev 依赖**：`uv sync` 只装 `[project.dependencies]`，pytest 在 `[project.optional-dependencies] dev` 里，需 `uv sync --extra dev` 才能安装
- **FFT NCC 积分图列偏移**：`integral[i+h, j+w]` 的列偏移是 `w`（模板宽度），不是 `1`。用 `1` 导致计算的是 h×1 区域而非 h×w 区域
- **`time.time()` 单位是秒**：内部计算 `duration_ms = int((end - start) * 1000)`，测试 mock 时间值时注意单位
- **Pillow 私有 API 会随版本移除**：`ImageGrab._grayscale_from_argb` 在 Pillow 12.3.0 被移除，改用 `Image.convert("L")`。依赖私有 API 时必须在 CI 中锁定版本上限
- **日志 handler 锁文件 + 全局状态污染**：`TimedRotatingFileHandler` 在 Windows 上持有日志文件句柄，`TemporaryDirectory` 清理时抛 `PermissionError`。`setup_logging()` 的 `_setup_done` 标志在测试间会污染。测试中需 `_reset_setup()` 关闭 handler 并重置标志，且在 `with` 块内调用
- **三档递进搜索策略**：原始+offset → 原始坐标 → 全屏 → 兜底，逐级降级确保不因单点匹配失败而整体回放中断
- **浮点时间比较需 `round()`**：`int((now - start) * 1000)` 在 `0.3 * 1000` 时产生 `299.999...` 而非 `300`，`int()` 截断导致 off-by-one。用 `int(round(...))` 修复
- **小模板全屏匹配假阳性**：100×100 模板在 1920×1200 屏幕上的 FFT NCC 全屏搜索容易找到高置信度但完全错误的匹配。模板匹配应默认关闭，仅作实验功能
- **Rich 反斜杠导致标记泄漏**：f-string 中文件路径末尾 `\` 会被 Rich 解析为转义 `\[`，使闭合标签 `[/bold cyan]` 变成纯文本。用 `rich.markup.escape()` 包裹用户输入

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