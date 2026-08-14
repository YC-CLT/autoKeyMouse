# CHANGELOG

## 2026-08-14 — 移动事件压缩

### 改动

- **engine/script.py**: Event 新增 `positions`/`delays` 字段，`save()`/`load()` 仅非 None 时序列化
- **engine/recorder.py**: 新增 `_move_buffer` 缓冲连续 move 事件，`_flush_move_buffer()` 合并为压缩事件
  - 普通 move → `positions` 数组，`delays` 为 None
  - 拖拽 move → `positions` + `delays` 数组，保留原始时间间隔
  - 拖拽与普通 move 不混合，缓冲区遇非 move 事件或类型切换时刷新
  - `compress=False` 时关闭压缩，退化为逐事件记录
- **engine/player.py**: `play()` 检测 `event.positions` 展开压缩事件
  - 普通 move：首点 `delay_ms` + 后续点 `MOUSE_MOVE_INTERVAL_MS`
  - 拖拽 move：首点 `delay_ms` + 后续点按 `delays[i]` 间隔
  - 无 `positions` 字段的旧脚本回退到原有单事件逻辑
  - 新增 `_pos_match_for_pos`/`_execute_mouse_event_at` 辅助方法
- **cli/commands.py**: `record` 子命令新增 `--no-compress` 参数
- **tui/app.py**: 录制交互新增 `Compress move events? [y/n]` 选项
- **cli/display.py**: `print_event_list` 连续 move 事件合并显示为一行 `xN 起点→终点`
- **tests**: 新增 10 个测试（recorder 压缩 5 + player 解压 3 + CLI 2）

### 原因

- 录制脚本中连续鼠标移动占事件量 60%+，坐标相邻、时间间隔固定，冗余度高
- 压缩后脚本体积显著减小，回放时展开逐点执行，用户无感知

---

## 2026-08-14 — 硬编码消除 + 配置统一

### 改动

- **cli/commands.py**: `--shot-radius`/`--move-interval` 默认值从硬编码改为从 `config.py` 导入
- **tui/app.py**: `shot_radius` 从 `50` 改为 `SHOT_RADIUS`；新增 `record_move`/`move_interval` 交互选项；inspect 增加事件列表展示
- **config.py**: 移除未使用的 `SHOT_FORMAT`
- **tests/test_cli.py**: 默认值断言从硬编码改为引用 config 常量
- **README.md/AGENTS.md**: 同步 `SHOT_RADIUS=192`，移除 `SHOT_FORMAT`

---

## 2026-08-14 — 匹配默认关闭 + 显示修复

### 改动

- **engine/player.py**: `use_match` 默认 `True` → `False`，回放默认纯坐标
- **cli/commands.py**: `--nomatch` → `--match`（opt-in），开启时打印实验功能警告
- **cli/display.py**: `script_name` 用 `rich.markup.escape()` 防反斜杠导致标记泄漏
- **tui/app.py**: 匹配开关默认 `n`，标注 `[EXPERIMENTAL]`
- **tests/test_cli.py/test_player.py**: 默认值断言同步更新

### 原因

- 模板匹配（FFT NCC）在 100×100 小模板 + 1920×1200 屏幕上容易假阳性
- 全屏搜索回退曾将 `left_up` 匹配到完全错误的位置 `(1293,865)`（正确为 `(1570,0)`）
- 匹配功能降级为实验功能，默认关闭

---

## 2026-08-13 — 鼠标拖拽支持

### 新增

- **config.py**: `DRAG_THRESHOLD_MS = 300` — 按住多久判定为拖拽
- **engine/recorder.py**: `_on_mouse_callback` 重写拖拽逻辑
  - `left_down` 记录 `_drag_button` / `_drag_start_time` / `_drag_move_count`
  - `move` 分两路：拖拽中全量记录（不节流、不截图），普通移动仍节流 200ms
  - `left_up` 区分拖拽终点（有截图）vs 普通点击（不截图）
  - 浮点精度修复：`int(round(...))` 替代 `int()` 避免 `0.3 * 1000 = 299.999...`

### 测试

- 111 tests passed (104 原有 + 7 新增 `tests/test_recorder_drag.py`)

---

## 2026-08-13 — KeymouseGo 参考项目调研

### 调研

- 产出 [docs/2026-08-13-KeymouseGo-research.md](docs/2026-08-13-KeymouseGo-research.md)
- KeymouseGo v5.2 是成熟的开源键鼠录制回放工具（Python + PySide6，Win/Linux/macOS）
- 架构亮点：平台抽象层（Event/Recorder 通过 `platform.system()` 做策略分发）
- 脚本系统：json5 格式，支持 if/else、goto、sequence、subroutine、插件扩展
- 回放引擎：QThread + QWaitCondition 实现可中断的精确时序控制
- 与 autoKeyMouse 对比：KeymouseGo 靠事件录制回放，autoKeyMouse 靠视觉定位，互补关系

---
## 2026-08-13 — 识图定位修复

### 修复

- **移除**：卡尔曼滤波（`engine/kalman.py`），替换为简易 offset 追踪
- **修复**：三档递进搜索策略（原始+offset → 原始 → 全屏 → 兜底），消除死亡螺旋
- **修复**：`_pos_match` 签名简化，不再接受 kalman 参数

---
## 2026-08-13 — 日志系统

### 新增

- **engine/logger.py**: 日志核心模块
  - `setup_logging(level)` — 初始化日志系统，TimedRotatingFileHandler 按天轮转，30 天保留
  - `get_logger(name)` — 获取 `autokeymouse.<name>` 命名空间的 logger
  - 日志只输出到 `logs/autokeymouse.log`，不打印到终端
  - 格式：`2026-08-13 14:30:01 [INFO] engine.player: ...`
  - `setup_logging()` 幂等，重复调用不创建重复 handler
- **main.py**: `--debug` 全局标志，切换到 DEBUG 级别
- **所有模块** 添加 INFO/DEBUG/WARNING/ERROR 级别日志

### 日志覆盖

| 模块 | 日志要点 |
|------|---------|
| engine/hooks.py | 钩子启动、键盘/鼠标事件 DEBUG、启动失败 ERROR |
| engine/recorder.py | 录制开始/停止、鼠标移动节流、截图失败 |
| engine/player.py | 回放开始/完成、周期进度、事件执行、模板匹配结果、执行异常 |
| engine/matcher.py | ROI 过小 WARNING、置信度低于阈值 DEBUG |
| cli/commands.py | 命令入口（record/play/list/inspect） |
| tui/app.py | TUI 录制/回放入口 |

### 测试

- 117 tests passed (原有 111 + 新增 6)

---

## 2026-08-13 — 录制回放 Bug 修复

### 修复

- **script.json 未保存**：`handle_record` / `_tui_record` 未调用 `save()`，只有截图 PNG 写入磁盘，脚本数据丢失
- **F9 停止热键不起效**：录制循环只捕获 `KeyboardInterrupt`，不检查 `stop_flag`。TUI 改用 `msvcrt` 非阻塞轮询
- **图片重复**：鼠标 down/up 各截一张图，位置相同内容几乎一样。改为只在 down 事件截图
- **Pillow 12.3.0 兼容**：`_grayscale_from_argb` 私有 API 被移除，改用 `Image.convert("L")`
- **F9 自爆**：停止热键的 keydown/keyup 被写入脚本，回放时模拟 F9 触发 player 自身 hook 导致回放中止。录制端过滤停止热键
- **Windows DPI 坐标偏移**：高 DPI 下 `ImageGrab.grab()` 与 `SetCursorPos` 坐标系不一致。入口加 `SetProcessDPIAware()`

### 测试

- 111 tests passed

---

## 2026-08-13 — pyproject.toml 完善 + README 双语

### 新增

- **pyproject.toml**: `[project.scripts]` 入口点 (`autokeymouse` 命令), `[build-system]` hatchling, `[tool.hatch.build.targets.wheel]` flat layout 配置, `[tool.uv] package = true`, 项目元数据 (license/authors/keywords/classifiers/urls)
- **README.md**: 上半英文 + 下半中文双语, 语言切换锚点, 安装/快速上手/工作原理/配置表/项目结构

### 修复

- 支持 `uv tool install -e .` 安装后直接 `autokeymouse` 命令

---

## 2026-08-13 — 录制引擎核心 (Task 1~8)

### 新增

- **config.py**: 集中配置常量 (STOP_HOTKEY, SHOT_RADIUS, MATCH_CONFIDENCE, KALMAN_*, MOUSE_MOVE_INTERVAL_MS)
- **engine/script.py**: Event/Meta/Script 数据类 + JSON load/save/validate
- **engine/capture.py**: PIL ImageGrab 截图 + 边缘裁剪 + PNG 保存
- **engine/matcher.py**: FFT 归一化互相关模板匹配 (Lewis 1995 算法)
- **engine/kalman.py**: 2D 静态目标卡尔曼滤波 (predict/update/reset/staleness)
- **engine/hooks.py**: pyWinhook HookManager 封装 (键盘+鼠标全局钩子)
- **engine/recorder.py**: 录制器 (钩子回调→事件构建→截图→脚本输出)

### 测试

- 70 tests passed (config 27 + script 15 + capture 6 + matcher 6 + kalman 8 + recorder 8)

### 修复

- matcher 积分图列偏移 bug: `1:1+valid_cols` → `w:w+valid_cols`

## 2026-08-13 — Recorder 参数接入

### 新增

- **Recorder** 接入 `--record-move` / `--move-interval` / `--shot-radius` / `--no-shot` 参数
- `no_shot=True` 时跳过截图，`shot` 字段为 `None`
- `record_move=False`（默认）时丢弃鼠标移动事件
- `_shot_radius` / `_move_interval` 覆盖 config 默认值

### 测试

- 106 tests passed (recorder 新增 6 tests)

## 2026-08-13 — 对齐设计文档偏差修复

### 修复

- **Task 6 kalman**: `KalmanFilter` → `PositionKalman`, `__init__(x,y)` 替代 `reset()`, `predict()/update()` → `np.ndarray`, 新增 `is_stale()`
- **Task 7 hooks**: 从队列模式改为回调模式 (`__init__(key_callback, mouse_callback)`), 规范化回调 dict, F9 检测 + stop_flag
- **Task 8 recorder**: `start()` 获取屏幕尺寸, 新增 `is_recording()`, `_relative_pos()`, `_map_mouse_action()`, 位置改为相对坐标 [0~1]
- **Task 9 player**: 移除 `STOP_HOTKEY` 死代码, 适配新 kalman/hooks API, 鼠标事件执行改为 `left_down/left_up` 等独立动作

### 测试

- 111 tests passed

## 2026-08-13 — 回放器 + CLI + TUI (Task 9~11)

### 新增

- **engine/player.py**: Player 回放器 + PlayerResult 数据类
  - 模板匹配+卡尔曼定位管线 (`_pos_match`)
  - win32api 鼠标/键盘/文本模拟 (`_execute_mouse_event`, `_execute_key_event`, `_execute_text_event`)
  - F9 热键停止监听 (`_start_stop_listener` / `_check_stop`)
  - 速度控制 (`_calc_delay`: delay_ms/speed, 最小 1ms)
  - 相对坐标→绝对坐标转换 (`_rel_to_abs`)
- **cli/commands.py**: 5 个子命令处理器 (record/play/list/inspect/tui)
- **cli/display.py**: Rich 格式化输出 (表格/面板/进度条)
- **main.py**: argparse 入口, 子命令分发
- **tui/app.py**: Rich 交互菜单界面 (录制/回放/列表/检查)

### 测试

- 30 tests passed (player 19 + cli 11), 全量 100 tests

### 实现细节

- Player 回放循环: for cycle → for event → sleep(delay) → check F9 → execute
- 坐标匹配: 卡尔曼 predict → 模板匹配 → 更新(成功) or 预测值(失败)
- 鼠标事件: SetCursorPos + mouse_event (down/up 配对)
- 文本事件: 剪贴板 OpenClipboard → SetClipboardText → Ctrl+V
- 速度 clamp: 最小 0.01, 防止除零