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