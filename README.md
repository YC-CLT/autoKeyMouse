# autokeymouse

[English](#english) | [中文](#中文)

Keyboard/mouse recording and playback tool for Windows — with optional screenshot-anchored positioning.

---

<a id="english"></a>

## Features

- **Record** keyboard, mouse clicks, wheel events, and drag (mouse movement by default)
- **Playback** with speed control, loop count, F9 emergency stop, and F8 pause/resume
- **Background execution** — replay scripts without stealing window focus via cua-driver
- **Drag support** — click-and-drag is recorded and replayed as a continuous sequence
- **Offset tracking** — window-moved detection via visual offset correction
- **Template matching** — (EXPERIMENTAL) FFT-based NCC screenshot-anchored positioning
- **TUI** — interactive terminal UI with Rich
- **CLI** — full argparse subcommands for scripting

## Requirements

- Windows only
- Python >= 3.11

## Installation

```bash
git clone https://github.com/YC-CLT/autokeymouse.git
cd autokeymouse
uv tool install -e .

# Or run directly in dev mode
uv sync --extra dev
uv run autokeymouse --help
```

## Quick Start

```bash
# Record (mouse movement enabled by default)
uv run autokeymouse record

# Record without mouse movement
uv run autokeymouse record --no-record-move

# Record to a custom directory
uv run autokeymouse record -o my_script

# Play back a recorded script
uv run autokeymouse play scripts/2026-08-14_1624

# Play back 5 times at 2x speed
uv run autokeymouse play scripts/2026-08-14_1624 -n 5 -s 2.0

# Play back with experimental template matching
uv run autokeymouse play scripts/2026-08-14_1624 --match

# Play back in background (no window focus needed)
uv run autokeymouse play scripts/2026-08-14_1624 --backend background

# Play back in background with foreground fallback
uv run autokeymouse play scripts/2026-08-14_1624 --backend background --backend-fallback

# List recorded scripts
uv run autokeymouse list

# Inspect a script
uv run autokeymouse inspect scripts/2026-08-14_1624

# Launch interactive TUI
uv run autokeymouse tui
```

## How It Works

### Recording

1. `F9` to stop recording
2. All key down/up events are captured via pyWinhook
3. Mouse clicks trigger a screenshot (100px radius crop) saved to `shots/NNNN.png`
4. Coordinates are stored as relative values [0~1] for resolution-independent playback
5. Mouse movement is recorded by default (use `--no-record-move` to disable)
6. Drag (click-hold-move-release) is detected by hold duration > 300ms, moves recorded at full rate
7. Script saved as `script.json` in the output directory

### Playback

1. Script is loaded from `script.json`
2. All events replay at original recorded coordinates (resolution-independent)
3. `--backend background` runs via cua-driver (no window focus needed); `--backend-fallback` auto-switches to foreground on failure
4. If `--match` is enabled, template matching attempts to locate the target on screen and corrects the position via a global offset
5. `F8` pauses/resumes playback, `F9` stops playback at any time

### Template Matching (EXPERIMENTAL)

FFT-based normalized cross-correlation (NCC) with pure numpy, no OpenCV dependency. Three-tier fallback: offset prediction → original position → full-screen search → raw coordinate. **Currently unreliable for small (100px) templates on large screens** — disabled by default. Use `--match` to enable at your own risk.

## Configuration

All constants in [config.py](config.py):

| Constant | Default | Description |
|----------|---------|-------------|
| `STOP_HOTKEY` | `"f9"` | Global stop hotkey |
| `PAUSE_HOTKEY` | `"f8"` | Pause/resume hotkey |
| `SHOT_RADIUS` | `192` | Screenshot crop radius (px) |
| `MATCH_CONFIDENCE` | `0.85` | NCC confidence threshold |
| `MATCH_SEARCH_RADIUS` | `100` | Search ROI radius (px) |
| `MOUSE_MOVE_INTERVAL_MS` | `200` | Min interval between move events (ms) |
| `DRAG_THRESHOLD_MS` | `300` | Hold duration to trigger drag (ms) |

## Project Structure

```
autokeymouse/
├── main.py              # CLI entry point
├── config.py            # All configuration constants
├── engine/              # Pure logic, no UI
│   ├── backend/         # Desktop driver abstraction
│   │   ├── base.py      # DesktopDriver ABC
│   │   ├── foreground.py # Foreground driver (win32api)
│   │   └── background.py # Background driver (cua-driver)
│   ├── script.py        # Event/Script model + save/load/validate
│   ├── capture.py       # Screenshot capture
│   ├── matcher.py       # FFT NCC template matching
│   ├── hooks.py         # pyWinhook hook manager
│   ├── logger.py        # Project-level logging (daily rotation)
│   ├── recorder.py      # Recording orchestrator
│   └── player.py        # Playback orchestrator
├── cli/                 # CLI layer
│   ├── commands.py      # Subcommand handlers
│   └── display.py       # Plain text output formatting
├── tui/                 # TUI layer
│   └── app.py           # Rich Live interactive menu
└── tests/               # pytest test suite (156 tests)
```

## License

MIT

---

<a id="中文"></a>

## 中文

Windows 键盘鼠标录制回放工具 — 支持可选截图锚定定位。

## 功能特性

- **录制** 键盘、鼠标点击、滚轮和拖拽事件（默认录制鼠标移动）
- **回放** 支持速度控制、循环次数、F9 紧急停止、F8 暂停/恢复
- **后台执行** — 通过 cua-driver 后台回放，无需窗口焦点
- **拖拽支持** — 点击拖拽操作录制为连续序列并完整回放
- **偏移追踪** — 窗口移动检测，通过视觉偏移修正定位
- **模板匹配** — （实验功能）基于 FFT 的 NCC 截图锚定定位
- **TUI** — 基于 Rich 的交互式终端界面
- **CLI** — 完整的 argparse 子命令，支持脚本化

## 环境要求

- 仅限 Windows
- Python >= 3.11

## 安装

```bash
git clone https://github.com/YC-CLT/autokeymouse.git
cd autokeymouse
uv tool install -e .

# 或者直接开发模式运行
uv sync --extra dev
uv run autokeymouse --help
```

## 快速上手

```bash
# 录制（默认开启鼠标移动录制）
uv run autokeymouse record

# 录制但不录鼠标移动
uv run autokeymouse record --no-record-move

# 录制到自定义目录
uv run autokeymouse record -o my_script

# 回放已录制的脚本
uv run autokeymouse play scripts/2026-08-14_1624

# 以 2 倍速循环播放 5 次
uv run autokeymouse play scripts/2026-08-14_1624 -n 5 -s 2.0

# 开启实验性模板匹配
uv run autokeymouse play scripts/2026-08-14_1624 --match

# 后台回放（无需窗口焦点）
uv run autokeymouse play scripts/2026-08-14_1624 --backend background

# 后台回放，失败时自动切回前台
uv run autokeymouse play scripts/2026-08-14_1624 --backend background --backend-fallback

# 列出已录制脚本
uv run autokeymouse list

# 查看脚本详情
uv run autokeymouse inspect scripts/2026-08-14_1624

# 启动交互式 TUI
uv run autokeymouse tui
```

## 工作原理

### 录制

1. `F9` 停止录制
2. 通过 pyWinhook 捕获所有按键按下/释放事件
3. 鼠标点击时触发截图（100px 半径裁剪），保存到 `shots/NNNN.png`
4. 坐标存储为相对值 [0~1]，保证不同分辨率下回放一致
5. 鼠标移动默认录制（用 `--no-record-move` 关闭）
6. 拖拽（按住超过 300ms 后移动）全量记录移动轨迹，不节流
7. 脚本保存为输出目录下的 `script.json`

### 回放

1. 从 `script.json` 加载脚本
2. 所有事件按原始录制坐标回放（分辨率无关）
3. `--backend background` 通过 cua-driver 后台运行（无需窗口焦点）；`--backend-fallback` 失败时自动切回前台
4. 若开启 `--match`，模板匹配尝试在屏幕上定位目标，通过全局偏移量修正位置
5. `F8` 暂停/恢复回放，`F9` 随时停止回放

### 模板匹配（实验功能）

纯 numpy 实现的 FFT 归一化互相关（NCC），无 OpenCV 依赖。三档递进搜索：偏移预测 → 原始坐标 → 全屏搜索 → 原始坐标兜底。**目前在小模板（100px）大屏幕上不够可靠**，默认关闭。用 `--match` 开启，风险自负。

## 配置项

所有常量在 [config.py](config.py) 中：

| 常量 | 默认值 | 说明 |
|------|--------|------|
| `STOP_HOTKEY` | `"f9"` | 全局停止热键 |
| `PAUSE_HOTKEY` | `"f8"` | 暂停/恢复热键 |
| `SHOT_RADIUS` | `192` | 截图裁剪半径（像素） |
| `MATCH_CONFIDENCE` | `0.85` | NCC 匹配置信度阈值 |
| `MATCH_SEARCH_RADIUS` | `100` | 搜索区域半径（像素） |
| `MOUSE_MOVE_INTERVAL_MS` | `200` | 鼠标移动事件最小间隔（毫秒） |
| `DRAG_THRESHOLD_MS` | `300` | 按住多久判定为拖拽（毫秒） |

## 项目结构

```
autokeymouse/
├── main.py              # CLI 入口
├── config.py            # 所有配置常量
├── engine/              # 纯逻辑，无 UI
│   ├── backend/         # 桌面驱动抽象层
│   │   ├── base.py      # DesktopDriver 抽象基类
│   │   ├── foreground.py # 前台驱动（win32api）
│   │   └── background.py # 后台驱动（cua-driver）
│   ├── script.py        # Event/Script 模型 + 保存/加载/校验
│   ├── capture.py       # 截图捕获
│   ├── matcher.py       # FFT NCC 模板匹配
│   ├── hooks.py         # pyWinhook 钩子管理
│   ├── logger.py        # 项目级日志（按日轮转）
│   ├── recorder.py      # 录制调度器
│   └── player.py        # 回放调度器
├── cli/                 # CLI 层
│   ├── commands.py      # 子命令处理
│   └── display.py       # 纯文本输出格式化
├── tui/                 # TUI 层
│   └── app.py           # Rich Live 交互菜单
└── tests/               # pytest 测试套件（156 个测试）
```

## 许可证

MIT