# CHANGELOG

## 2026-08-13 — 1号机：录制引擎核心 (Task 1~8)

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

## 2026-08-13 — 1号机：Recorder 参数接入

### 新增
- **Recorder** 接入 `--record-move` / `--move-interval` / `--shot-radius` / `--no-shot` 参数
- `no_shot=True` 时跳过截图，`shot` 字段为 `None`
- `record_move=False`（默认）时丢弃鼠标移动事件
- `_shot_radius` / `_move_interval` 覆盖 config 默认值

### 测试
- 106 tests passed (recorder 新增 6 tests)

## 2026-08-13 — 2号机：回放器 + CLI + TUI (Task 9~11)

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