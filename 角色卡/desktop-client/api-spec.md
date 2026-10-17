# API 规格：桌面客户端（desktop/）

- 版本：v1.0（2026-10-17，S4）
- 契约依据：`docs/contracts/desktop-client-v1.md`（冻结版 sha256 `d5f1defaf0d581de…`）
- 边界依据：`角色卡/desktop-client/boundary.yaml`（sha256 `793157465739c794…`）
- 工作流依据：`docs/workflow.md`（sha256 `1216bcde30beb9a7…`）

## 1. 公开导出

### 1.1 包级（`import desktop`）

| 名称 | 类型 | 说明 |
| --- | --- | --- |
| `desktop.run(orchestrator, *, submit_method_name="chat", window_title=None, stdio_log_directory=None)` | 函数 | 启动 + 进入事件循环；窗口关掉后返回关闭句柄（已关闭状态） |
| `desktop.start(orchestrator, *, ...)` | 函数 | 同上但不进入事件循环，立刻返回关闭句柄 |
| `desktop.DesktopStartupError` | 异常类 | 启动失败的唯一对外错误类型，消息面向用户 |
| `desktop.OutputEventForwarder` | 类 | C1 监听器实现（Qt 无关），可单独使用/测试 |
| `desktop.PipelineRunner` | 类 | 工作线程执行器（Qt 无关） |

**导入期零副作用（契约 C3 第 4 条）**：`import desktop` 不导入 PySide6、不创建
`QApplication`、不建窗口。`run` / `start` 是包装函数，PySide6 在它们被调用时才由
`desktop.app` 导入。已有用例在子进程里验证（`test/desktop-client/test_import_side_effects.py`）。

### 1.2 关闭句柄 `desktop.app.DesktopHandle`

| 成员 | 说明 |
| --- | --- |
| `shutdown(timeout=10.0)` | 停转发 → 拒绝新任务 → 等线程 → 取消 C1 订阅 → 关窗口 → 退出事件循环。**可重复调用**，第二次起直接返回 |
| `run_event_loop()` | 进入 Qt 事件循环，窗口关闭后返回退出码 |
| `process_events()` | 处理一批待办事件（离屏测试用） |
| `is_closed` | 属性，是否已关闭 |

句柄**不暴露**编排器、`QApplication`、窗口或任何 Qt 对象（契约 C3 第 3 条）。已有用例
遍历句柄的全部公开属性做反向断言（`test_lifecycle.py::test_handle_exposes_no_orchestrator_and_no_qt_objects`）。

### 1.3 内部模块

| 模块 | 职责 | 依赖 Qt |
| --- | --- | --- |
| `desktop/app.py` | `run` / `start` / `DesktopHandle` / 启动校验与清理 | 是（运行期导入） |
| `desktop/window.py` | 主窗口：标题、输出区、输入框、发送按钮、渲染槽 | 是 |
| `desktop/bridge.py` | C1 事件 → Qt 信号（跨线程投递） | 是 |
| `desktop/output_listener.py` | C1 监听器实现，转投给接收端 | **否** |
| `desktop/worker.py` | 工作线程执行器（一次一个任务） | **否** |
| `desktop/stdio_fallback.py` | 无控制台模式 stdout/stderr 兜底 | **否** |
| `desktop/unwired_orchestrator.py` | S4 占位编排器（提交时说「还没接线」） | **否** |
| `desktop/errors.py` | `DesktopStartupError` | **否** |
| `desktop/__main__.py` | `python -m desktop` 入口 | 是（调用时导入） |

## 2. 注入对象的契约（编排器替身必须满足）

`run` / `start` 只要两样东西，都是编排层的**公开**入口：

1. `set_output_listener(listener)`，语义同契约 C1（`listener` 是
   `AgentOutputListener` 实例）。
2. 一个提交方法，默认名 `chat(requirement)`，可用 `submit_method_name` 改名。

可选：`clear_output_listener()`。缺失时可正常启动，`shutdown()` 会打印一条诊断
（不报错）。`SystemManagerAgent` 同时具备两者（C1 由其父类 `BaseAgent` 提供）。

## 3. 层间依赖

- 唯一向下依赖：`ai_agent_factory.agent.baseagent` 的 `AgentOutputListener` /
  `AgentOutputError`（契约 C1 定义的类型，`set_output_listener` 的 `isinstance`
  校验要求必须继承）。
- **不 import** `myagent/` 下任何模块（不含具体智能体类），**不 import**
  `ai_agent_factory.llms`（含 `OpenAILLM`），不构造 Provider 或业务 Service。
- 静态核对脚本（`temp/desktop-client/_check_imports.py`）实跑结论：`desktop`
  与 `test/desktop-client` 两个目录的 import 核对通过。
- 句柄不把编排器再导出给上层。

## 4. 契约符合性与偏差

### C1 输出事件（本角色为消费者）

| 要求 | 状态 |
| --- | --- |
| 订阅三类事件并渲染 | 符合：`token` 逐字追加；`turn_completed` 另起一段；`error` 红色加粗 |
| 公开方法订阅 | 符合：调用 `orchestrator.set_output_listener(forwarder)` |
| 回调在调用线程 | 符合：`OutputEventForwarder` 不建线程，只在工作线程里被回调 |
| 错误不被吞 | 符合：C1 已报过不重复报；没报过的异常由 `PipelineRunner` 补报，界面必定可见 |

**已知限制（本角色无法在界面层解决，需契约 C1 v2）**：C1 的订阅是**实例级**的。
编排器在 `todo` 里派发出的子智能体（PRD/后端/前端）是各自独立的实例，桌面端只能
订阅被注入的那一个对象，因此**收不到子智能体的 token / error**。本步不绕过：真实
下发方案等「把监听器下发到子智能体」的公开入口进 C1 v2 后再接。S4 用替身把「一个
可订阅对象」的形状先固定下来。

### C2 项目状态快照

本步**不实现**（派发明示留给下一步：状态面板）。`get_snapshot()` 已由 S3 落地，桌面端
尚未调用。

### C3 启动与关闭生命周期

| 要求 | 状态 |
| --- | --- |
| 公开启动操作（等价 `desktop.app.run(...)`）+ 关闭句柄 | 符合：`desktop.run` / `desktop.start` |
| `shutdown()` 中断在跑管线、回收工作线程、可重复调用 | 部分符合，见下方「限制 1」 |
| 关闭后无残留线程 | 符合（已测试：关闭后 `desktop-pipeline` 线程数归零） |
| import 不得自动启动 | 符合（子进程用例） |
| 启动失败可读 + 已完成资源清理 | 符合（缺方法 / 订阅抛错 两条用例） |

**限制 1（如实记录）**：`shutdown()` 在关闭时先停止事件转发、拒绝新任务、`join`
工作线程。但 Python 无法强杀线程：如果正在跑的 LLM 调用不返回，线程会继续活到该
调用结束。因此实际保证是「界面不再被写入、不接受新任务、线程是 daemon 不阻塞进程退出」，
而不是「立刻掐断 LLM 请求」。真正的协作式取消需要编排层提供取消入口（新契约）。
`join` 超时会打印明确警告，不会假装回收成功（有用例断言超时返回 `False`）。

**限制 2**：`python -m desktop` 目前注入 `UnwiredOrchestrator`，提交时会显示
「还没接到编排层」。真实接线属装配步骤 S5。

## 5. 打包/无控制台模式

契约 C1 的选择是「事件与 print 并存」，管线仍然大量 `print`。`start()` 在**建窗口之前**
调用 `ensure_standard_streams()`：`sys.stdout` / `sys.stderr` 为 `None` 时替换为
`%TEMP%/codeagent-desktop/desktop-YYYYMMDD.log`（行缓冲）；目录建不出或文件打不开
则退回 `io.StringIO`，保证 `print` 永不抛异常。

## 6. 装配说明（给 S5 / 根启动方式）

```python
import desktop
from myagent.system_manager_agent import SystemManagerAgent  # 由装配角色构造

orchestrator = SystemManagerAgent(...)   # 装配角色负责读环境变量、造 LLM
desktop.run(orchestrator, submit_method_name="chat")
```

- 启动方式：项目根目录 `.venv\Scripts\python.exe -m desktop`（契约 C4 第 2 条）。
- 缺 `api_key` 之类环境问题的提示归装配角色（C4 第 4 条），桌面端只负责把编排器抛
  出的错误用醒目样式显示出来。

## 7. 测试证据

命令（必须用 `.venv` 解释器；pytest 与 stdlib unittest 均可，跑的是同一批用例）：

```
.venv\Scripts\python.exe -m unittest discover -s test/desktop-client
```

实跑结果（2026-10-17）：
- `.venv\Scripts\python.exe -m pytest test/desktop-client -q` → `41 passed in 0.82s`（pytest 9.1.1）；
- `.venv\Scripts\python.exe -m unittest discover -s test/desktop-client` → `Ran 41 tests` / `OK`。

两条命令跑的是同一批用例：用例用 `unittest.TestCase` 写，pytest 与 stdlib 都能收集。

| 文件 | 覆盖 |
| --- | --- |
| `test_import_side_effects.py` | import 不加载 Qt、不建 QApplication；`desktop.__main__` 可导入 |
| `test_stdio_fallback.py` | stdout/stderr 为 None 时 print 不崩、写日志文件、写不成退 `StringIO`、已有流不被动 |
| `test_output_listener.py` | 三类事件顺序、错误消息、`saw_error` 标记、关闭后不再转发、不新建线程 |
| `test_worker.py` | 工作线程执行、忙时拒绝、事件外的异常补报、C1 报过不重复、取消、join 超时如实返回 |
| `test_lifecycle.py` | 启动→关闭、重复关闭、启动失败三类清理、句柄不泄漏内部对象、`run()` 返回已关闭句柄、关闭中断不转发 |
| `test_rendering.py` | token 追加、turn_completed 另起一段、error 红色加粗、非 GUI 线程执行、空输入不提交、运行中禁用发送、连续两轮 |

编排器一律替身注入（`support.FakeOrchestrator`），无真实 LLM、无网络、无环境变量依赖。
GUI 用例靠 `QT_QPA_PLATFORM=offscreen`（`support.py` 顶部 `setdefault`）。

## 8. 测试运行器（已解决）

装配角色已在 `.venv` 里装好 pytest 9.1.1，步骤表给的
`.venv\Scripts\python.exe -m pytest test/desktop-client -q` 可直接用。用例仍写成
`unittest.TestCase`（既能被 pytest 收集，也能 `-m unittest discover` 直接跑），
在只用标准库的环境里也不会失效。`test/desktop-client/conftest.py` 负责补导入路径与
`QT_QPA_PLATFORM=offscreen`。
