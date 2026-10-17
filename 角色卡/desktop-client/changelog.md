# 变更历史：桌面客户端

## 2026-10-17 — UI 视觉改造：顶栏 / 输出卡片 / 输入行三段式（客户要求）

- 仅改 `desktop/window.py`：新增视觉常量与窗口级 `WINDOW_STYLESHEET`，
  布局改为「顶栏 + 状态胶囊 → 白色输出卡片 → 输入行 + 辅助提示」。
- 发送按钮改主色 `#2F6FEB` 三态（悬停 / 按下 / 禁用），输入框高 42px、聚焦主色边框；
  状态胶囊就绪 / 运行中 / 错误三种配色，前置 8px 圆点（动态属性 `state` 驱动）。
- 保持不变：全部 `objectName`、控件类型、`ERROR_COLOR = "#b00020"`、错误渲染逻辑、
  公开方法签名、契约 C3（`desktop/__init__.py` 未动）、无新依赖。
- 验证：`pytest test/desktop-client -q` → **41 passed**；`py_compile` 通过；
  三张离屏截图重生成，采样颜色种类 25/30/26 → 54/54/55，深色像素同步上升。
  离屏环境字体库为空（0 个），截图中文字为方框，属环境限制，不是样式问题。
- 详见 `docs/change/2026-10-17_change_ui-polish.md`。

## 2026-10-17 — S4b：测试套件在 `.venv` 里跑通（pytest 可用）

- 装配角色已把 pytest 9.1.1 装进 `.venv`；步骤表里的
  `.venv\Scripts\python.exe -m pytest test/desktop-client -q` 现在可用：
  **41 passed in 0.82s**。
- 测试文件：`support.py`（替身与 Qt 工具）+ `conftest.py`（导入路径与离屏平台）+
  6 个用例文件（`test_import_side_effects` / `test_stdio_fallback` / `test_output_listener`
  / `test_worker` / `test_lifecycle` / `test_rendering`）。
- 本轮改动仅限测试与文档：每个用例文件头部补齐「覆盖哪几条契约要求」；
  `test_startup_failure_when_submit_method_missing` 增加「不残留窗口 / 工作线程」断言。
- **`desktop/` 实现零改动**：测试没有暴露实现缺陷，未做任何「为了变绿」的放宽。
- `api-spec.md` 第 7、8 节更新为 pytest 主用法 + unittest 备用（同一批用例）。

## 2026-10-17 — S4：桌面客户端骨架（PySide6）能开、能看、能关

- 新增 `desktop/` 包（M1–M6，按 `docs/design/2026-10-18_S4-桌面骨架设计草案.md` 实施）：
  - `app.py`：`run()` / `start()` / `DesktopHandle`（契约 C3）。
  - `window.py`：主窗口（标题、只读输出区、输入框、发送按钮）。
  - `worker.py`：工作线程执行器（Qt 无关），忙时拒绝、异常可见、取消与 join。
  - `output_listener.py`：C1 监听器实现（Qt 无关）；`bridge.py`：事件 → Qt 信号。
  - `stdio_fallback.py`：无控制台模式 stdout/stderr 兜底。
  - `unwired_orchestrator.py`、`__main__.py`：`python -m desktop` 能开窗（真实接线留给 S5）。
  - `errors.py`：`DesktopStartupError`。
- 新增 `test/desktop-client/`：41 个用例，编排器全部替身注入，GUI 走 `QT_QPA_PLATFORM=offscreen`。
- 文档：`api-spec.md`、`functional-description.md`、`feature-map.md`、
  `docs/feature/desktop-shell.md`；设计草案状态更新为「已实施」。
- 与设计草案的偏差：
  1. 草案里「M3 工作线程 + M4 事件转投」按 Qt 依赖切成三层（Qt 无关核心 / 信号桥 / 窗口），
     目的是让「事件 → 界面」这部分在没有显示器的环境里也能测。
  2. 句柄增加了 `run_event_loop()` / `process_events()` 两个方法，用于 `run()` 与离屏测试；
     它们仍不暴露任何 Qt 对象。
  3. 测试框架用 `unittest` 而非 `pytest`：`.venv` 里没有 pytest（见 api-spec 第 8 节）。
- 未实施（O1–O3，未经客户确认）：输出区行数上限、窗口内取消按钮、状态栏显示日志路径。

## 2026-10-17 — S4 第一次派发：环境阻塞，未落代码

- `pip install PySide6` 被 ShellGate（pm 规则集）拒绝；本机无任何 Qt 绑定，窗口无法验证，
  报 blocked 并交回。产物只有 `memo.md` 与设计草案。
- 复派后由装配角色固定 `PySide6==6.12.0` 到 `requirements.txt` 并建 `.venv`，阻塞解除。
