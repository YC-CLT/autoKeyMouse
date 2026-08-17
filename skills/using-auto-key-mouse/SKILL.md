---
name: using-auto-key-mouse
description: Use when on Windows and needing to replay recorded keyboard/mouse macros, automate desktop clicks and keystrokes, or run background automation without stealing window focus
---

# autoKeyMouse

回放已录制的键鼠脚本。CLI 命令 `autokeymouse`，支持前台/后台。

## When to Use

- 执行已录制的宏/脚本、桌面点击、按键
- 后台自动化（不抢焦点、不占光标）
- 查看可用脚本列表

**NOT for:** 录制新脚本（需人工）

## 命令

```bash
autokeymouse list              # 列出脚本
autokeymouse list --json       # JSON 格式
autokeymouse inspect <dir>     # 查看脚本详情
autokeymouse play <dir> [opts] # 回放
```

## play 参数

| 参数 | 默认 | 说明 |
|------|------|------|
| `--backend` / `-b` | `foreground` | `foreground`（win32api，需焦点）\| `background`（cua-driver，不抢焦点） |
| `--backend-fallback` | `false` | 后台失败自动切前台 |
| `--times` / `-n` | `1` | 循环次数 |
| `--speed` / `-s` | `1.0` | 速度倍率 |

## 前台 vs 后台

**前台：** win32api 精确模拟 down/up，支持拖拽、组合键。需焦点，抢占光标。

**后台：** cua-driver 桌面驱动，不抢焦点/光标。但 down/up 合并为原子操作（拖拽→点击，组合键→单键），浏览器/Electron 可能失败。

**规则：默认 `--backend background`。失败后加 `--backend-fallback`。**

## 输出解析

格式 `[TAG] key=value`。关注 `[PLAY] Done ... status=completed|stopped`。

## 热键

| 热键 | 作用 |
|------|------|
| `F9` | 停止回放 |
| `F8` | 暂停/恢复 |

## 脚本格式

`script.json`，坐标相对值 `[0~1]`，分辨率无关。事件类型：`mouse`（move/left_down/left_up/right_down/right_up/wheel）、`key`（down/up）、`text`。

## 常见错误

| 错误 | 修复 |
|------|------|
| 后台模式浏览器/Electron 无效 | 加 `--backend-fallback` |
| 高 DPI 缩放异常 | 已自动处理，无需干预 |