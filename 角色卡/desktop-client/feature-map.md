# 功能导航：桌面客户端

本角色负责的系统功能，以及每个功能的位置、状态与文档。状态：`已实现` / `未开工`。

| 功能 | 用户看到什么 | 代码 | 文档 | 状态 |
| --- | --- | --- | --- | --- |
| 桌面窗口与主界面 | 一个带标题的窗口：输出区、状态行、输入框、发送按钮 | `desktop/window.py` | `docs/feature/desktop-shell.md` | 已实现（S4，2026-10-17） |
| 启动与关闭生命周期 | 双击/命令启动出窗口；关窗口就退出，不残留线程 | `desktop/app.py` | `docs/feature/desktop-shell.md` | 已实现（S4） |
| 流式输出渲染 | 文字逐字出现；一轮结束另起一段；错误红色加粗 | `desktop/output_listener.py`、`desktop/bridge.py`、`desktop/window.py` | `docs/feature/desktop-shell.md` | 已实现（S4，仅「被注入对象」的事件） |
| 无控制台模式 print 兜底 | 打包后不带黑窗口也不崩 | `desktop/stdio_fallback.py` | `api-spec.md` 第 5 节 | 已实现（S4） |
| 需求输入与提交 | 写一句话，回车或点发送，长任务不卡界面 | `desktop/window.py`、`desktop/worker.py` | `docs/feature/desktop-shell.md` | 已实现（S4；真实编排器待 S5 接线） |
| 项目状态面板（契约 C2） | 五个阶段完成没完成、现在到哪一步 | 未写 | — | 未开工（下一步） |
| 变更需求提交 | 项目跑完后提出变更 | 未写 | — | 未开工 |
| 打包（PyInstaller） | 一个 exe，双击即用 | 未写 | — | 未开工 |

## 交接关系

- 上游给本角色的东西：`SystemManagerAgent` 的公开方法（C1 订阅、C2 快照、提交入口）。
- 本角色给出去的东西：`desktop.run(orchestrator, ...)` 启动操作与关闭句柄（契约 C3），
  供装配角色（S5）接线、测试角色（S6）联调。
- 卡住本角色的已知缺口：C1 实例级订阅（子智能体事件收不到），需 C1 v2。
