# 功能：桌面窗口与启动关闭（desktop-shell）

- 功能编号：`desktop-shell`
- 状态：已实现（S4，2026-10-17）
- 契约：C3（启动与关闭生命周期，本角色主要负责）、C1（输出事件，本角色消费）
- 代码：`desktop/app.py`、`desktop/window.py`、`desktop/worker.py`、`desktop/output_listener.py`、`desktop/bridge.py`、`desktop/stdio_fallback.py`、`desktop/__main__.py`
- 测试：`test/desktop-client/`（41 个用例，见 `api-spec.md` 第 7 节）

## 用户视角

1. 在项目根目录执行 `.venv\Scripts\python.exe -m desktop`。
2. 出现一个窗口：上面大片是输出区，下面一行是输入框和「发送」按钮，中间一行状态文字。
3. 输入需求 → 回车或点发送。输出区里文字开始逐字出现；这期间按钮变灰、状态写「运行中…」。
4. 一轮回复结束：另起一段；出错：新的一段用红色加粗打头 `[错误]`。
5. 关窗口：程序停止接收新任务、不再往界面写内容，然后退出。再次关不会报错。

## 行为细节

| 场景 | 行为 |
| --- | --- |
| 输入为空或只有空格 | 不提交，状态提示「请先写需求，再点发送」 |
| 上一轮还在跑时点发送 | 不提交，状态提示「上一轮还在跑…」（按钮本身就是灰的） |
| 提交后管线抛异常 | 红色 `[错误] …` 一段；同一异常只显示一次（C1 报过就不再重复报） |
| 关闭时有任务在跑 | 立刻停止往界面写内容、拒绝新任务；线程是 daemon，不阻塞进程退出 |
| 缺 PySide6 | 抛 `DesktopStartupError`，消息里给出安装命令，不甩堆栈 |
| 编排器不合契约 | 同上报错；已经建的窗口、线程、订阅都会被清掉 |
| 无控制台模式（pythonw / `--noconsole`） | 启动前把 `sys.stdout` / `sys.stderr` 换成日志文件；写不成换内存缓冲，`print` 不抛异常 |

## 内部怎么做到

```
用户点发送
  → MainWindow.handle_send()                （界面线程）
  → PipelineRunner.submit()                 （界面线程，只建线程不干活）
  → 工作线程：orchestrator.chat(需求)
      → C1 在工作线程回调 OutputEventForwarder
      → sink 是 OutputSignalBridge：只 signal.emit(...)
  → Qt 把信号排队回界面线程
  → MainWindow.display_token / display_turn_completed / display_error
```

- 关闭链路：`closeEvent` → `DesktopHandle.shutdown()` → 停转发 → `PipelineRunner.cancel()` →
  `join(timeout)` → `clear_output_listener()` → 关窗口 → `quit()`。句柄用一把锁+标志位保证
  重复调用安全，并从 `closeEvent` 重入时立刻返回。
- 停止转发是关闭时最重要的一步：窗口已关，工作线程就算还活着也无法再往界面控件写东西。

## 明确不做（本步边界）

- 状态面板（契约 C2）、变更需求提交、PyInstaller 打包、界面美化。
- 真实 LLM 与环境变量读取（装配角色 S5）。
- 把监听器下发到子智能体（C1 实例级订阅缺口，需契约 v2，不在界面层绕过）。
