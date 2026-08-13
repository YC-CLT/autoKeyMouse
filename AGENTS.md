# AGENTS.md

## 环境

- Python 3.11 + uv
- **命令执行**：统一走 `cmd-exec-mcp`，必须先读 `./mcp_tools_summary.csv`

## 关键文件

| 文件 | 作用 |
|------|------|
| `config.py` | 所有配置常量集中管理 |
| `main.py` | CLI 入口，argparse 子命令分发 |
| `engine/script.py` | Event/Script 数据模型 + JSON 存取 |
| `engine/capture.py` | PIL 截图 + 边缘裁剪 |
| `engine/matcher.py` | FFT NCC 模板匹配 |
| `engine/kalman.py` | 2D 卡尔曼滤波 |
| `engine/hooks.py` | pyWinhook 全局钩子封装 |
| `engine/recorder.py` | 录制调度器 |
| `engine/player.py` | 回放调度器 |
| `cli/commands.py` | 5 个子命令处理 (record/play/list/inspect/tui) |
| `tui/app.py` | Rich Live 交互菜单 |

## 关键常量

所有常量在 `config.py`，修改后全量 grep 同步引用。

| 常量 | 默认值 | 说明 |
|------|--------|------|
| `STOP_HOTKEY` | `"f9"` | 全局停止热键 |
| `SHOT_RADIUS` | `50` | 截图裁剪半径 (px) |
| `MATCH_CONFIDENCE` | `0.85` | NCC 置信度阈值 |
| `MATCH_SEARCH_RADIUS` | `100` | 搜索 ROI 半径 (px) |
| `KALMAN_PROCESS_NOISE` | `1e-2` | 卡尔曼过程噪声 |
| `KALMAN_MEASURE_NOISE` | `1e-1` | 卡尔曼观测噪声 |
| `KALMAN_MAX_CONSECUTIVE_MISS` | `5` | 连续失配判定失效阈值 |
| `MOUSE_MOVE_INTERVAL_MS` | `200` | 鼠标移动事件最小间隔 |

## 规则

- **config 重命名全量 grep**：常量改名/移除后，搜索所有引用点确保同步更新
- 可并行的指令用 `parallel=True`
- `wet-mcp extract` 可下载文件/抓取页面媒体组件
- `Read` 无法访问 `D:\Temp`，MCP 长输出需 `Copy-Item` 到项目根目录，然后正则替换 `\\n` 为 `\n`，否则输出超长行
- `write` 无法使用`replace_all`，使用正则替换
- 快速搜索优先 `WebSearch`（更快），深度内容再用 `wet-mcp`；提取网站内容必须用 `wet-mcp` 的 `extract`

## 工具

- MCP类见 `../mcp_tools_summary.csv`

## 经验/坑点

- **单例进程计数**：用 `os.path.abspath(__file__)` + `result.stdout.count(script)` 精确匹配，比 PID 文件更可靠，无残留。`Where-Object { ProcessId -ne }` 在 PowerShell 管道中可能失效，不如 Python 侧 `count()` 简单
- **`uv sync` 不装 dev 依赖**：`uv sync` 只装 `[project.dependencies]`，pytest 在 `[project.optional-dependencies] dev` 里，需 `uv sync --extra dev` 才能安装
- **FFT NCC 积分图列偏移**：`integral[i+h, j+w]` 的列偏移是 `w`（模板宽度），不是 `1`。用 `1` 导致计算的是 h×1 区域而非 h×w 区域
- **卡尔曼静态模型收敛**：静态目标模型 + 低过程噪声时，协方差快速收敛到接近零，Kalman Gain 极小，滤波器不再信任观测。测试需从真实值附近初始化，或增大过程噪声
- **`time.time()` 单位是秒**：内部计算 `duration_ms = int((end - start) * 1000)`，测试 mock 时间值时注意单位
- **实现前必须对照设计文档**：类名、方法签名、参数类型、返回值类型必须与设计文档一致，否则后续环节（如 player 依赖 kalman）会连锁报错
- **`_pos_match` 多路径测试需 mock 多个内部方法**：`_pos_match` 有多个 fallback 路径（shot 文件不存在→原始坐标、匹配失败→卡尔曼预测值），测试匹配成功/失败路径时需同时 mock `_load_shot` 和 `_capture_screen`，否则静默走 fallback
- **Pillow 私有 API 会随版本移除**：`ImageGrab._grayscale_from_argb` 在 Pillow 12.3.0 被移除，改用 `Image.convert("L")`。依赖私有 API 时必须在 CI 中锁定版本上限
- **停止热键会自爆**：录制时 F9 停止热键的 keydown/keyup 被写入脚本，回放时模拟 F9 会触发 player 自身 hook 的 stop_flag，导致回放立即中止。录制端必须过滤停止热键，不要写入脚本
- **Windows DPI 缩放导致坐标偏移**：高 DPI 下 `ImageGrab.grab()` 返回虚拟化尺寸，但 `SetCursorPos` 用物理像素，坐标换算错位。入口处调用 `SetProcessDPIAware()` 强制物理像素坐标系

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