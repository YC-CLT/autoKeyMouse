# KeymouseGo 调研文档

## 背景

[KeymouseGo](https://github.com/taojy123/KeymouseGo) 是一个开源键鼠录制回放工具，定位为"精简绿色版按键精灵"，由 `taojy123` 创建并维护。当前本地仓库版本为 **v5.2**，是项目最新稳定版本。

## 核心发现

### 1. 项目概览

| 属性 | 值 |
|------|-----|
| 仓库 | `github.com/taojy123/KeymouseGo` |
| 语言 | Python 3.7+ |
| 许可证 | GPL-2.0 |
| 平台 | Windows / Linux / macOS |
| 当前版本 | v5.2 |
| UI 框架 | PySide6 (Qt6) |
| 打包 | PyInstaller (-F -w) |

### 2. 架构设计

项目采用**平台抽象层 + 策略模式**，核心架构分层清晰：

```
KeymouseGo.py          # 入口：GUI 模式 / CLI 模式分发
├── UIFunc.py           # 主窗口逻辑（继承 QMainWindow + UI_UIView）
├── UIFileDialogFunc.py # 文件管理对话框
│
├── Event/              # 事件模型层（平台抽象）
│   ├── __init__.py     # 平台检测 → 导出 WindowsEvent 或 UniversalEvent
│   ├── Event.py        # 抽象基类 Event（delay, event_type, action_type, action）
│   ├── WindowsEvents.py     # Windows 实现：win32api.keybd_event + mouse_event
│   └── UniversalEvents.py   # 跨平台实现：pyautogui
│
├── Recorder/           # 录制层（平台抽象）
│   ├── __init__.py     # 平台检测 → 导出对应 Recorder
│   ├── globals.py      # 共享状态：RecordSignal, 时间戳, 鼠标间隔
│   ├── WindowsRecorder.py   # Windows：pyWinhook (HookManager) + cpyHook
│   └── UniversalRecorder.py # 跨平台：pynput (mouse.Listener + keyboard.Listener)
│
├── Util/               # 工具层
│   ├── Parser.py       # 脚本解析器（LegacyParser + ScriptParser）→ JsonObject 链表
│   ├── RunScriptClass.py    # 回放线程（QThread + QWaitCondition 精确时序控制）
│   ├── Global.py       # State 枚举（IDLE/RUNNING/RECORDING/PAUSE_*）
│   └── ClickedLabel.py # 热键设置点击标签
│
├── Plugin/             # 插件系统
│   ├── Interface.py    # 抽象接口 PluginInterface
│   └── Manager.py      # 插件发现/注册/调用（importlib + json5 manifest）
│
├── assets/             # 资源：i18n 翻译(.ts/.qm)、音效(.wav/.mp3)
└── archived/           # 旧版代码存档（Frame1.py, config.py, note.md）
```

### 3. 平台适配策略

Event 和 Recorder 模块均在 `__init__.py` 中通过 `platform.system()` 做运行时平台检测：

- **Windows**：`WindowsEvent` + `WindowsRecorder`，依赖 `pywin32`、`pyWinhook`、`cpyHook`
- **Linux/macOS**：`UniversalEvent` + `UniversalRecorder`，依赖 `pynput`、`pyautogui`

两套依赖独立声明在 `requirements-windows.txt` 和 `requirements-universal.txt`。

### 4. 脚本系统（v5.2 重大变更）

**v5.2 将脚本格式从自定义文本改为 `json5`**，支持更丰富的控制流：

| 脚本节点类型 | 说明 |
|-------------|------|
| `event` | 基础事件（鼠标/键盘/输入） |
| `sequence` | 顺序执行子事件序列 |
| `if` | 条件分支（do / else），由插件函数提供判断 |
| `goto` | 跳转到指定 label |
| `subroutine` | 子程序调用 |
| `custom` | 自定义插件函数调用 |

脚本解析器 [Parser.py](file:///D:/CodeFile/autoKeyMouse/KeymouseGo/Util/Parser.py) 将 JSON 对象转换为**单向链表**（JsonObject 含 `next_object` 和 `next_object_if_false`），支持 `label` 和 `goto` 的延迟绑定机制。

### 5. 回放执行引擎

[RunScriptClass.py](file:///D:/CodeFile/autoKeyMouse/KeymouseGo/Util/RunScriptClass.py) 使用 `QThread + QWaitCondition` 实现精确时序控制：

- `sleep(ms)` 通过 `QWaitCondition.wait(mutex, deadline)` 实现，可被外部 `resume()` 中断
- 支持暂停/恢复：`eventPause` 标志 + `wait_if_pause()` 检查
- 遍历 JsonObject 链表，根据节点类型分发执行
- 插件函数通过 `PluginManager.call()` 调用

### 6. 录制机制

录制通过全局钩子捕获键鼠事件：

- **Windows**：`pyWinhook.HookManager` 钩键盘，`cpyHook.cSetHook(WH_MOUSE_LL)` 钩鼠标（支持侧键）
- **跨平台**：`pynput` 的 `mouse.Listener` + `keyboard.Listener`

事件通过 `Qt Signal`（`RecordSignal.event_signal`）发射到 UI 层，记录到 `self.record` 列表中，录制结束时写入 `scripts/` 目录的 `.json5` 文件。

关键细节：
- 录制不记录鼠标移动轨迹（默认精度 200ms 间隔，设为 0 则不录制移动）
- 鼠标坐标保存为**屏幕比例**（相对值 `x/SW, y/SH`），支持跨分辨率回放
- Windows 多屏模式下保存绝对坐标（物理像素）

### 7. 插件系统

v5.2 新增的插件系统，不兼容旧版：

- 插件放在 `plugins/` 目录下，每个插件一个子目录
- 通过 `manifest.json5` 声明元信息（name, version, entry, plugin_class）
- 使用 `importlib.machinery.SourceFileLoader` 动态加载
- 插件通过 `register_functions()` 注册可调用函数，存入 `PluginManager.functions` 字典
- 脚本中 `custom` 类型节点通过 `PluginManager.call()` 调用插件函数

### 8. 热键系统

- 默认热键：`F6` 启动、`F9` 停止、`F7` 录制
- 支持自定义热键（组合键如 `Ctrl+Shift+X`），通过 `keys_pool` 缓冲池实现
- 热键设置模式（`State.SETTING_HOT_KEYS`）下点击按钮后捕获下一个按键
- 热键冲突检测：同一热键不能绑定多个功能

### 9. 国际化

- 使用 Qt Linguist 工具链：`.ts` 翻译源文件 → `.qm` 编译文件
- 支持语言：简体中文、English、繁體中文
- 通过 `QTranslator` 运行时加载

### 10. 版本历史关键节点

| 版本 | 关键变更 |
|------|---------|
| v3.0 | 因 macOS 兼容困难，回退到 Windows-only (win32api) |
| v4.0 | PySide2 重写 UI，Monomux 贡献 |
| v4.1 | 新增命令行模式 |
| v5.0 | 插件系统初步实现，英文文档，高DPI适配 |
| v5.1 | 恢复 Linux/macOS 支持，多屏支持 |
| v5.2 | 脚本格式改为 json5，新插件系统（不兼容旧版），自定义热键 |

## 结论

KeymouseGo 是一个**成熟的键鼠自动化工具**，经历了从 Windows-only → 跨平台 → 回退 → 再跨平台的演进。v5.2 版本架构清晰，平台抽象设计合理，json5 脚本系统支持条件分支和插件扩展，功能已超越简单的录制回放。

**与 autoKeyMouse 项目的关系**：autoKeyMouse 项目（当前工作目录的父项目）似乎是基于类似理念的独立实现，使用了不同的技术栈（PIL + FFT NCC 模板匹配 + 卡尔曼滤波），偏向于视觉定位的自动化。KeymouseGo 更偏向传统的键鼠事件录制回放，两者可以互补参考。

## 参考来源

- 本地仓库：`D:\CodeFile\autoKeyMouse\KeymouseGo\`
- GitHub：`https://github.com/taojy123/KeymouseGo`
- 关键文件：
  - [KeymouseGo.py](file:///D:/CodeFile/autoKeyMouse/KeymouseGo/KeymouseGo.py) - 入口文件
  - [Event/__init__.py](file:///D:/CodeFile/autoKeyMouse/KeymouseGo/Event/__init__.py) - 平台抽象
  - [Event/WindowsEvents.py](file:///D:/CodeFile/autoKeyMouse/KeymouseGo/Event/WindowsEvents.py) - Windows 事件执行
  - [Event/UniversalEvents.py](file:///D:/CodeFile/autoKeyMouse/KeymouseGo/Event/UniversalEvents.py) - 跨平台事件执行
  - [Recorder/WindowsRecorder.py](file:///D:/CodeFile/autoKeyMouse/KeymouseGo/Recorder/WindowsRecorder.py) - Windows 录制钩子
  - [Recorder/UniversalRecorder.py](file:///D:/CodeFile/autoKeyMouse/KeymouseGo/Recorder/UniversalRecorder.py) - 跨平台录制钩子
  - [Util/Parser.py](file:///D:/CodeFile/autoKeyMouse/KeymouseGo/Util/Parser.py) - 脚本解析器
  - [Util/RunScriptClass.py](file:///D:/CodeFile/autoKeyMouse/KeymouseGo/Util/RunScriptClass.py) - 回放执行引擎
  - [Plugin/Manager.py](file:///D:/CodeFile/autoKeyMouse/KeymouseGo/Plugin/Manager.py) - 插件管理器
  - [Changelog.md](file:///D:/CodeFile/autoKeyMouse/KeymouseGo/Changelog.md) - 版本历史