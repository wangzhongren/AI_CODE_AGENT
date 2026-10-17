# 变更：桌面端界面视觉改造（ui-polish）

- 日期：2026-10-17
- 角色：桌面客户端（desktop-client）
- 来源：客户反馈「这个页面太丑了，你修改一下」
- 设计依据：`docs/design/2026-10-17_design_desktop-ui-polish.md`（已确认）
- 改动路径：`desktop/window.py`（唯一生产代码改动）
- 未改动：`desktop/app.py`、`desktop_main.py`、`packaging/`、`.github/`、`myagent/`、`ai_agent_factory/`、`requirements.txt`

## 改了什么

1. `desktop/window.py` 顶部新增视觉常量（窗口背景、卡片、边框、文字、主色三态、状态胶囊配色、
   滚动条配色、字体回退链）与模块级 `WINDOW_STYLESHEET`。
2. 布局改为三段：顶栏（标题 + 状态胶囊，底部分隔线）→ 输出卡片（占满剩余空间）→
   输入行（输入框 + 发送按钮）+ 辅助提示标签。
3. 输出区：白底、12px 圆角、1px 边框、18px 内边距、主色浅调选中色；段落之间加 6px 上边距。
4. 输入框：固定高 42px、10px 圆角、左右 14px 内边距，聚焦时边框变主色。
5. 发送按钮：固定高 42px、10px 圆角、主色底白字、最小宽 88px，含悬停 / 按下 / 禁用三态。
6. 状态胶囊：浅灰底（就绪）/ 浅蓝底 + 主色文字（运行中）/ 浅红底 + 错误色文字（错误），
   前置 8px 圆点。由动态属性 `state`（`idle` / `busy` / `error`）驱动样式，
   `__set_status()` 负责更新文字与重新 polish。
7. 滚动条：宽 10px、圆角滑块、悬停加深。
8. 样式用 `self.setStyleSheet(WINDOW_STYLESHEET)` 挂在窗口上，不改全局 `QApplication`。

## 兼容性（逐条核对）

- `objectName` 全部保留：`mainWindow`、`outputPane`、`statusLabel`、`requirementInput`、`sendButton`。
- 控件类型不变：`QTextEdit` / `QLineEdit` / `QPushButton` / `QLabel`。
- `ERROR_COLOR = "#b00020"` 精确值不变；错误渲染仍是「另起一段 + 红色加粗 + `[错误]` 前缀」。
- 公开方法签名不变：`display_token`、`display_turn_completed`、`display_error`、`set_busy`、
  `finish_task`、`handle_send`、`set_submit_handler`、`set_close_handler`。
- 契约 C3 不变：`desktop/__init__.py` 未改，导入时仍不加载 Qt；本次只改本就依赖 Qt 的 `window.py`。
- 未新增生产依赖；未使用 emoji。

## 行为上的小变化

- `display_error()` 额外把状态胶囊切到「出错了，详见输出区」（红色样式）；
  任务结束时 `finish_task()` → `set_busy(False)` 会恢复「就绪」。
  这不改变错误文本本身，也不改变事件流。
- 空需求提示、忙时拒发提示改走同一个 `__set_status()`，文字内容与原来一致。

## 验证证据（实际执行）

| 项 | 命令 | 结果 |
| --- | --- | --- |
| 单元测试 | `.venv\Scripts\python.exe -m pytest test/desktop-client -q` | **41 passed in 0.84s** |
| 语法 | `.venv\Scripts\python.exe -m py_compile desktop/window.py` | 通过 |
| 层间依赖 | `.venv\Scripts\python.exe temp/desktop-client/_check_imports.py desktop test/desktop-client` | 两目录均「核对通过」 |
| 截图 | `.venv\Scripts\python.exe temp/desktop-client/_screenshots.py` | 生成 idle / streaming / error 三张 PNG（880x620） |
| 像素核对 | `.venv\Scripts\python.exe temp/desktop-client/_verify_shots.py` | 见下表 |

像素核对（采样步长 2px）：

| 截图 | 改前颜色种类 / 深色像素 / 红色像素 | 改后颜色种类 / 深色像素 / 红色像素 |
| --- | --- | --- |
| 01-idle | 25 / 140 / 0 | **54 / 392 / 0** |
| 02-streaming | 30 / 322 / 0 | **54 / 531 / 0** |
| 03-error | 26 / 259 / 224 | **55 / 545 / 288** |

## 已知限制

1. 离屏截图里中文显示为方框。已用 `temp/desktop-client/_font_check.py` 核实：
   该离屏环境的 `QFontDatabase.families()` 返回 **0 个字体**，属于截图环境缺字体，
   不是界面样式问题；真实 Windows 桌面运行不受影响（设计文档 §6.1 已记录）。
2. 本轮不做 Markdown / 代码高亮渲染。
3. 本轮不做暗色主题。
4. 状态胶囊的「错误」态会在任务结束信号到达后恢复为「就绪」，这是既有 `finish_task` 行为，
   本轮未改事件时序。
