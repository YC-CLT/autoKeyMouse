# autokeymouse

[English](#english) | [中文](#中文)

Keyboard/mouse recording and playback tool for Windows — with screenshot-anchored template matching and Kalman-filtered positioning.

---

<a id="english"></a>

## Features

- **Record** keyboard, mouse clicks, and wheel events (optional mouse movement)
- **Playback** with speed control, loop count, and F9 emergency stop
- **Template matching** — screenshot-anchored replay via FFT-based NCC (no OpenCV needed)
- **Kalman filter** — smooths target position, handles transient mismatches
- **TUI** — interactive terminal UI with Rich
- **CLI** — full argparse subcommands for scripting

## Requirements

- Windows only
- Python >= 3.11

## Installation

```bash
# Install from local source (editable)
git clone https://github.com/YC-CLT/autokeymouse.git
cd autokeymouse
uv tool install -e .

# Or run directly in dev mode
uv sync --extra dev
uv run autokeymouse --help
```

## Quick Start

```bash
# Record keystrokes and mouse clicks (default: no mouse movement)
uv run autokeymouse record

# Record with mouse movement
uv run autokeymouse record --record-move

# Record to a custom directory
uv run autokeymouse record -o my_script

# Play back a recorded script
uv run autokeymouse play scripts/2026-08-13_1430

# Play back 5 times at 2x speed, no template matching
uv run autokeymouse play scripts/2026-08-13_1430 -n 5 -s 2.0 --nomatch

# List recorded scripts
uv run autokeymouse list

# Inspect a script
uv run autokeymouse inspect scripts/2026-08-13_1430

# Launch interactive TUI
uv run autokeymouse tui
```

## How It Works

### Recording

1. `F9` or `Ctrl+C` to start recording
2. All key down/up events are captured via pyWinhook
3. Mouse clicks trigger a screenshot (50px radius crop) saved to `shots/NNNN.png`
4. Coordinates are stored as relative values [0~1] for resolution-independent playback
5. Script saved as `script.json` in the output directory

### Playback

1. Script is loaded from `script.json`
2. For each mouse event with a screenshot, template matching locates the target on screen
3. Kalman filter smooths the position across consecutive frames
4. If matching fails, falls back to the last predicted position
5. `F9` stops playback at any time

### Template Matching

Pure numpy FFT-based normalized cross-correlation (NCC), no OpenCV dependency. Searches within a radius around the expected position for efficiency.

### Kalman Filter

A 2D static-target Kalman filter: `predict()` increments uncertainty, `update()` fuses a measurement. If no match for 5 consecutive frames, the filter is considered stale.

## Configuration

All constants in [config.py](config.py):

| Constant | Default | Description |
|----------|---------|-------------|
| `STOP_HOTKEY` | `"f9"` | Global stop hotkey |
| `SHOT_RADIUS` | `50` | Screenshot crop radius (px) |
| `MATCH_CONFIDENCE` | `0.85` | NCC confidence threshold |
| `MATCH_SEARCH_RADIUS` | `100` | Search ROI radius (px) |
| `KALMAN_PROCESS_NOISE` | `1e-2` | Kalman process noise |
| `KALMAN_MEASURE_NOISE` | `1e-1` | Kalman measurement noise |
| `KALMAN_MAX_CONSECUTIVE_MISS` | `5` | Max misses before stale |
| `MOUSE_MOVE_INTERVAL_MS` | `200` | Min interval between move events |

## Project Structure

```bash
autokeymouse/
├── main.py              # CLI entry point
├── config.py            # All configuration constants
├── engine/              # Pure logic, no UI
│   ├── script.py        # Event/Script model + save/load/validate
│   ├── capture.py       # Screenshot capture
│   ├── matcher.py       # FFT NCC template matching
│   ├── kalman.py        # 2D Kalman filter
│   ├── hooks.py         # pyWinhook hook manager
│   ├── recorder.py      # Recording orchestrator
│   └── player.py        # Playback orchestrator
├── cli/                 # CLI layer
│   ├── commands.py      # Subcommand handlers
│   └── display.py       # Rich output formatting
├── tui/                 # TUI layer
│   └── app.py           # Rich Live interactive menu
└── tests/               # pytest test suite (111 tests)
```

## License

MIT

---

<a id="中文"></a>

## 中文

Windows 键盘鼠标录制回放工具 — 基于截图锚定的模板匹配 + 卡尔曼滤波定位。

## 功能特性

- **录制** 键盘、鼠标点击和滚轮事件（可选录制鼠标移动）
- **回放** 支持速度控制、循环次数、F9 紧急停止
- **模板匹配** — 基于 FFT 的 NCC 截图锚定回放（无需 OpenCV）
- **卡尔曼滤波** — 平滑目标位置，容忍短暂匹配失败
- **TUI** — 基于 Rich 的交互式终端界面
- **CLI** — 完整的 argparse 子命令，支持脚本化

## 环境要求

- 仅限 Windows
- Python >= 3.11

## 安装

```bash
# 从本地源码安装（可编辑模式）
git clone https://github.com/YC-CLT/autokeymouse.git
cd autokeymouse
uv tool install -e .

# 或者直接开发模式运行
uv sync --extra dev
uv run autokeymouse --help
```

## 快速上手

```bash
# 录制键盘和鼠标点击（默认不录制鼠标移动）
uv run autokeymouse record

# 录制鼠标移动
uv run autokeymouse record --record-move

# 录制到自定义目录
uv run autokeymouse record -o my_script

# 回放已录制的脚本
uv run autokeymouse play scripts/2026-08-13_1430

# 以 2 倍速循环播放 5 次，关闭模板匹配
uv run autokeymouse play scripts/2026-08-13_1430 -n 5 -s 2.0 --nomatch

# 列出已录制脚本
uv run autokeymouse list

# 查看脚本详情
uv run autokeymouse inspect scripts/2026-08-13_1430

# 启动交互式 TUI
uv run autokeymouse tui
```

## 工作原理

### 录制

1. `F9` 或 `Ctrl+C` 停止录制
2. 通过 pyWinhook 捕获所有按键按下/释放事件
3. 鼠标点击时触发截图（50px 半径裁剪），保存到 `shots/NNNN.png`
4. 坐标存储为相对值 [0~1]，保证不同分辨率下回放一致
5. 脚本保存为输出目录下的 `script.json`

### 回放

1. 从 `script.json` 加载脚本
2. 对每个带截图的鼠标事件，用模板匹配在屏幕上定位目标
3. 卡尔曼滤波平滑连续帧之间的位置
4. 匹配失败时回退到上一次预测位置
5. `F9` 随时停止回放

### 模板匹配

纯 numpy 实现的 FFT 归一化互相关（NCC），无 OpenCV 依赖。在预期位置附近的搜索半径内高效匹配。

### 卡尔曼滤波

二维静态目标卡尔曼滤波：`predict()` 增加不确定性，`update()` 融合观测值。连续 5 帧匹配失败则判定为失效。

## 配置项

所有常量在 [config.py](config.py) 中：

| 常量 | 默认值 | 说明 |
|----------|---------|-------------|
| `STOP_HOTKEY` | `"f9"` | 全局停止热键 |
| `SHOT_RADIUS` | `50` | 截图裁剪半径（像素） |
| `MATCH_CONFIDENCE` | `0.85` | NCC 匹配置信度阈值 |
| `MATCH_SEARCH_RADIUS` | `100` | 搜索区域半径（像素） |
| `KALMAN_PROCESS_NOISE` | `1e-2` | 卡尔曼过程噪声 |
| `KALMAN_MEASURE_NOISE` | `1e-1` | 卡尔曼观测噪声 |
| `KALMAN_MAX_CONSECUTIVE_MISS` | `5` | 连续匹配失败阈值 |
| `MOUSE_MOVE_INTERVAL_MS` | `200` | 鼠标移动事件最小间隔（毫秒） |

## 项目结构

```bash
autokeymouse/
├── main.py              # CLI 入口
├── config.py            # 所有配置常量
├── engine/              # 纯逻辑，无 UI
│   ├── script.py        # Event/Script 模型 + 保存/加载/校验
│   ├── capture.py       # 截图捕获
│   ├── matcher.py       # FFT NCC 模板匹配
│   ├── kalman.py        # 二维卡尔曼滤波
│   ├── hooks.py         # pyWinhook 钩子管理
│   ├── recorder.py      # 录制调度器
│   └── player.py        # 回放调度器
├── cli/                 # CLI 层
│   ├── commands.py      # 子命令处理
│   └── display.py       # Rich 输出格式化
├── tui/                 # TUI 层
│   └── app.py           # Rich Live 交互菜单
└── tests/               # pytest 测试套件（111 个测试）
```

## 许可证

MIT
