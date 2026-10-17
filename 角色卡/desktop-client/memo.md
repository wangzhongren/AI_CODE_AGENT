# 桌面客户端 memo（续接线索）

## 2026-10-17 — UI 视觉改造完成（客户要求，来源：客户原话「页面太丑」）

- **样式常量在哪**：`desktop/window.py` 顶部。颜色 / 字体常量（`WINDOW_BACKGROUND`、
  `ACCENT` 三态、`STATUS_*`、`SCROLLBAR_*`、`FONT_FAMILY`）与整份 `WINDOW_STYLESHEET` 都在那里；
  改皮肤先改这一段。样式只挂窗口（`self.setStyleSheet`），**不要**改全局 `QApplication`，
  离屏测试共用同一个应用实例。
- **测试依赖的 objectName**（不要改）：`mainWindow`（找顶层窗口）、`outputPane`、
  `requirementInput`、`sendButton`；`statusLabel` 虽无用例直接断言，但契约要求保留。
  新增控件用的名字：`titleLabel`、`header`、`statusCapsule`、`statusDot`、`hintLabel`、`centralWidget`。
- **控件结构**：central(QVBox) → header(QFrame, 标题+胶囊) / outputPane(QTextEdit) /
  inputRow(QHBox: requirementInput + sendButton) / hintLabel。三个被测试控件仍是
  `MainWindow` 后代，`findChild` 递归查找不受嵌套影响。
- **状态胶囊**：动态属性 `state` = `idle` / `busy` / `error` 驱动 QSS；统一入口
  `MainWindow.__set_status(text, state)`，会 `unpolish/polish` 让属性选择器生效。
  `display_error()` 会把胶囊切到 error 态，`finish_task()` 恢复 idle。
- **错误契约不变**：`ERROR_COLOR = "#b00020"`（小写，测试断言精确值），另起一段 + 红色加粗 + `[错误]` 前缀；
  段落另起时用 `__paragraph_format()` 加 6px 上边距。
- **离屏截图中文是方框**：`temp/desktop-client/_font_check.py` 显示该环境
  `QFontDatabase.families()` 为 **0 个字体**，是环境缺字体，不是样式 bug。
  截图基线（采样 2px）：改前 idle/streaming/error 颜色种类 25/30/26、深色像素 140/322/259；
  改后 54/54/55、392/531/545，error 红色像素 224 → 288。
- 验证口令：`41 passed`（`pytest test/desktop-client -q`）；`py_compile` 通过；
  `_check_imports.py desktop test/desktop-client` 两目录通过。
  记录：`docs/change/2026-10-17_change_ui-polish.md`。

## 2026-10-17 — S4 口令已交：`S4-DONE @2026-10-17`

- 证据命令：`.venv\Scripts\python.exe -m pytest test/desktop-client -q` → `41 passed`；
  层间依赖静态核对 `temp/desktop-client/_check_imports.py` → 两目录均「通过」。
- 注意：`su` 的派发快照会落后于仓库（连续两次按「测试为空 / 环境未就绪」派发）。
  接到 S4 类派发先核对现状，别重写已落盘的 `desktop/` 与 `test/desktop-client/`。

## 2026-10-17 — S4 完成：桌面骨架能开、能看、能关

- 环境：解释器必须用 `.venv\Scripts\python.exe`（Python 3.12.0，PySide6 6.12.0）。
  **系统 Python 3.14 没有 PySide6**，用它跑会 ImportError。
- **`.venv` 里已有 pytest 9.1.1**（装配角色装的）。主用法：
  `.venv\Scripts\python.exe -m pytest test/desktop-client -q` → `41 passed`。
  备用（纯标准库）：`.venv\Scripts\python.exe -m unittest discover -s test/desktop-client`。
  用例写成 `unittest.TestCase`，两条命令跑的是同一批用例，别为了「更 pytest」重写。
- 落地产物：`desktop/`（9 个模块）、`test/desktop-client/`（6 个用例文件 + `support.py`）、
  `api-spec.md`、`functional-description.md`、`feature-map.md`、
  `docs/feature/desktop-shell.md`、`changelog.md`、设计草案状态改为「已实施」。
- 关键实现事实（下一轮直接用，别重查）：
  - `desktop.start(orchestrator, ...)` 建窗返回句柄（不跑事件循环）；`desktop.run(...)` = start + `exec()`。
    两者都吃 `submit_method_name="chat"`，所以真实接线只要编排器有 `chat` 就能用，无需改桌面端。
  - `import desktop` 不加载 PySide6（包装函数内部才 import `desktop.app`），已有子进程用例守住。
  - C1 监听器必须继承 `AgentOutputListener`（`isinstance` 校验），`desktop/output_listener.py` 是 Qt 无关实现。
  - 事件 → 界面走 `OutputSignalBridge`（QObject + Signal），工作线程只 `emit`。
  - 关窗顺序：停转发 → cancel → join(timeout) → clear_output_listener → close/quit；重复调用安全。
  - 无控制台兜底在 `start()` 第一步，早于建窗；日志落在 `%TEMP%/codeagent-desktop/desktop-YYYYMMDD.log`。
- 测试里怎么找窗口（不碰私有字段）：`support.find_window()` 用 `QApplication.topLevelWidgets()`
  按 `objectName == "mainWindow"` 找；控件 objectName 为 `outputPane` / `requirementInput` / `sendButton`。
- 已知缺口（未解决，等契约）：
  1. **C1 实例级订阅**：子智能体的 token/error 收不到，需 C1 v2 提供「监听器下发」的公开入口。
  2. **协作式取消**：`shutdown()` 无法强杀在跑的 LLM 请求，只能停转发+拒绝新任务+daemon 线程，
     `join` 超时如实告警。真要中断需编排层提供取消入口（新契约）。
- 下一步（按 role-card 实现顺序「状态面板」）：契约 C2 已由 S3 落地（`get_snapshot()`），
  桌面端要新增状态面板渲染 + 提交/完成后刷新；`desktop/app.py` 的 `start()` 会多一个接线点。
- ShellGate 备忘：`python -c`、`cmd /c`、带空格引号参数的命令会被拒；列目录/静态核对改用
  `temp/desktop-client/_list.py`、`temp/desktop-client/_check_imports.py`。
