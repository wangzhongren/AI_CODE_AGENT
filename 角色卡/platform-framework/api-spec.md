# API 规格：平台框架（`ai_agent_factory` 运行时与 LLM 抽象）

本文件记录本角色实际导出的 API、依赖方向、装配方式，以及它实现的契约与偏差。

| 修订 | 日期 | 内容 |
| --- | --- | --- |
| rev 1 | 2026-10-17 | 实现契约 C1（`BaseAgent` 输出事件订阅），见 `docs/contracts/desktop-client-v1.md` |
| rev 1.1 | 2026-10-17 | 本文件迁到规范位置 `角色卡/platform-framework/api-spec.md`，正文不变；`common/platform-framework/api-spec.md` 改为指针 |

---

## 1. 实际导出

### 1.1 `ai_agent_factory/agent/baseagent.py`

| 符号 | 类型 | 说明 |
| --- | --- | --- |
| `BaseAgent` | 抽象类 | 智能体运行时：对话上下文管理、`chat()` 主流程、输出事件分发 |
| `BaseAgent.chat(message: str) -> str` | 方法 | 一轮对话，返回完整回复 |
| `BaseAgent.get_context()` | 方法 | 返回对话上下文（既有 API，未改动） |
| `BaseAgent.reset_context()` | 方法 | 重置上下文，保留系统提示（既有 API，未改动） |
| `BaseAgent.todo(token: str)` | 抽象方法 | 子类实现：处理一轮完整回复（既有契约，未改动） |
| `BaseAgent.token_deal(result: str)` | 抽象方法 | 子类实现：处理单个流式 token（既有契约，未改动） |
| `BaseAgent.set_output_listener(listener)` | 方法 | **rev 1 新增**：订阅运行期输出事件 |
| `BaseAgent.clear_output_listener()` | 方法 | **rev 1 新增**：取消订阅 |
| `AgentOutputListener` | 抽象类 | **rev 1 新增**：监听器契约，`on_token` / `on_turn_completed` / `on_error` |
| `AgentOutputError` | 冻结数据类 | **rev 1 新增**：`error` 事件载荷，字段 `exception`、`message` |

### 1.2 `ai_agent_factory/llms/base_llm.py`

| 符号 | 说明 |
| --- | --- |
| `BaseLLM(api_key, base_url, model_name)` | 模型供应商抽象契约，rev 1 未改动 |
| `BaseLLM.chat(context, **kwargs) -> Iterable[str]` | 流式 token 迭代器，rev 1 未改动 |

### 1.3 `ai_agent_factory/llms/base_llm_openai.py`

| 符号 | 说明 |
| --- | --- |
| `OpenAILLM` | OpenAI 兼容流式实现，rev 1 未改动 |

---

## 2. 契约 C1 的实现方式

契约来源：`docs/contracts/desktop-client-v1.md`（v1，冻结于 2026-10-17），C1 章节。

### 2.1 三类事件

| 事件 | 回调 | 载荷 | 触发时机 |
| --- | --- | --- | --- |
| `token` | `on_token(text)` | 单个流式增量字符串 | 每收到一个 token，**在**交给 `token_deal` **之前** |
| `turn_completed` | `on_turn_completed(full_text)` | 本轮完整回复，与 `chat()` 返回值相同 | 完整回复拼装、写入上下文、上下文裁剪都完成之后；`todo` 调用之前 |
| `error` | `on_error(error_info)` | `AgentOutputError(exception, message)` | `chat()` 内任一步抛错时；随后原异常继续向上抛出 |

`AgentOutputError.message` 形如 `RuntimeError: 模型服务不可用`；异常没有附带文本时形如 `TimeoutError(异常未附带消息)`。

### 2.2 顺序约定：事件先发，既有回调后走

三条事件都遵循同一顺序规则：**先把事件发出去，再走既有通道**。

- `token` 事件 → 再调用 `token_deal(token)`
- `turn_completed` 事件 → 再调用 `todo(full_text)`
- `error` 事件 → 再 `raise` 原异常

这样定有两条实际收益：

1. 子类回调（`token_deal` / `todo`）里出错时，界面层已经收到了出错前的全部输出，事件流始终是模型输出的完整镜像。
2. `myagent/` 的项目经理、后端、前端智能体确实会在 `todo()` 内部再次调用 `self.chat()`。把 `turn_completed` 放在 `todo` 之前，事件顺序是「A 轮 token → A 轮完成 → B 轮 token → B 轮完成」，不会出现「B 轮先进界面、A 轮后到」的交叉。

### 2.3 订阅后：事件与 print **并存**（不抑制）

契约 C1 第 4 条把选择权交给本角色。**选择：并存。** 即订阅后 `token_deal` / `todo` 照常被调用、照常写 stdout，事件是额外的一条通道。

理由：

1. **抑制无法安全实现。** 四个业务智能体的 `token_deal` 实现就是 `print(result, end='', flush=True)`，`todo` 实现里也有大量 `print`（进度、文件操作日志）。要「调用它们但不让它们写 stdout」，只能临时改写进程级的 `sys.stdout`（`contextlib.redirect_stdout`）。桌面端会在自己开的工作线程里跑管线，而 `sys.stdout` 是进程级全局对象——改写会同时压掉主线程和界面层的输出，属于跨线程副作用，比多几行控制台日志危险得多。
2. **不牺牲子类副作用。** `todo` 不只打印：它解析文件操作指令、缓存 `frontend_guide` / `api_spec`、调度子智能体。并存策略下这些行为一个字都不用动，也不需要我去区分「这行 print 该不该留」。
3. **对桌面端没有实际代价。** 界面从事件取数，与 stdout 无关；需要安静时，桌面端可以把控制台藏起来，这是它的展示选择，不是框架的语义。

### 2.4 线程与 GUI 依赖

- 三个回调都在**调用 `chat()` 的那个线程**里同步触发。框架不创建线程、不使用 `asyncio`、不 import `threading`。
- 框架不依赖 Qt 或任何 GUI 库；事件转投界面线程由桌面端自行负责（契约 C1 第 5 条）。
- 静态把关：`test/platform-framework/test_baseagent_output_events.py::test_baseagent_has_no_thread_or_gui_dependency` 扫描 `baseagent.py` 源码，禁止出现 `import threading`、`import _thread`、`PySide6`、`PyQt`、`tkinter`。

### 2.5 错误处理

- `chat()` 用 `except Exception` 捕获运行期错误（**不捕 `BaseException`**，`KeyboardInterrupt` 仍按原方式冒泡，三个入口的中断处理不受影响）。
- 捕获后先发 `error` 事件，再 `raise` —— 裸 `raise` 保留原异常类型与 traceback，不包装、不改写。
- 子类回调抛错同样走这条路径：`token_deal` / `todo` 的异常也先发 `error` 再抛。
- 未订阅监听器时，`except` 块只做 `raise`：异常照旧抛给调用方（三个入口用 `except Exception` 打印「❌ 发生错误」），**不额外打印**，否则会破坏「未订阅时 stdout 逐字不变」。
- 监听器自身的异常**不被捕获**：会原样向上传播并打断本轮 `chat()`。框架不吞掉任何异常，也不为监听器的 bug 编造降级路径。

### 2.6 订阅粒度

订阅是**按 agent 实例**的，不是全局的。桌面端若要看管线内部子智能体的输出，需要对相应实例各自订阅：`SystemManagerAgent` 会把工作派给 `agents['pm' / 'pj' / 'fe' / 'be']`，这些是独立对象。

### 2.7 未订阅时行为（契约 C1 第 3 条）

未订阅时 `__emit_token` / `__emit_turn_completed` / `__emit_error` 都是空操作，`chat()` 的可观察行为与 rev 0 完全一致：`token_deal` 逐 token 调用、`todo` 每轮一次、stdout 内容与顺序不变、返回值不变、上下文与裁剪规则不变。这一点由两组用例共同证明：同一批「不订阅」用例在改动前后各跑一次，断言未改、结果一致（见第 5 节）。

---

## 3. 支持的入口（消费者）

### 3.1 三个 CLI 入口 —— 只读核对结论：不受影响

| 入口 | 用法 | 结论 |
| --- | --- | --- |
| `main.py` | 4 个业务智能体 + 依次 `chat()`；读 `_BaseAgent__context`、`pm.prd`、`pj.frontend_guide/backend_guide`、`be.api_spec` | 不订阅监听器；`chat()` 签名、返回值、上下文写入、print 行为均未变 → 输出与行为不变 |
| `main3.py` | `SystemManagerAgent(llm, agents)` + `.chat()` / `.handle_change_request()` / `.execute_next_step()` / `.report_status()`；读 `project_state` | 同上，本次未改 `report_status` / 上下文 / 决策流程 → 不变 |
| `enhanced_main.py` | 同 `main3.py`，另加 `initial_development_done` 流程控制 | 同上 → 不变 |

三个入口共同依赖的既有行为，rev 1 全部保留：`token_deal` 逐 token 调用、`todo` 每轮调用一次、两者都写 stdout、`chat()` 返回完整回复、`get_context()` 返回上下文、`max_context` 裁剪规则、`KeyboardInterrupt` 不被吞。

### 3.2 四个业务智能体 —— 只读核对结论：形状兼容

| 智能体 | `token_deal` | `todo` | 结论 |
| --- | --- | --- | --- |
| `ProductManagerAgent` | `print(result, end='', flush=True)` | 存 `self.prd` + print | 兼容：调用次数与时机未变 |
| `ProjectManagerAgent` | 同上 | 解析文件操作、加载指导文档，`is_need_loop` 时再 `chat()` | 兼容：递归 `chat()` 下每轮各自 `turn_completed`，未订阅时无任何变化 |
| `BackendDeveloperAgent` | 同上 | 文件操作 + 递归 `chat()` + `ensure_api_spec_file()` | 兼容 |
| `FrontendDeveloperAgent` | 同上 | 文件操作 + 递归 `chat()` | 兼容 |
| `SystemManagerAgent` | 同上 | `make_decision()` 调度子智能体 `chat()` | 兼容；子智能体是独立实例，需各自订阅 |

四个智能体的 `__init__` 都调用了 `super().__init__()`（其中项目经理、系统管理者先设自身属性再调 super），因此 `__output_listener` 一定会被初始化；没有任何一个把 `token_deal` / `todo` 置为 `None`，既有的 `if self.token_deal:` / `if self.todo:` 判断逻辑保持原样。

`ai_agent_factory/utils/file_operation_handler.py`（属「文件产出」角色）不使用 `BaseAgent`，只通过注入的 `BaseLLM` 实例调用 `llm.chat(context=...)` —— 本次改动不触及该路径。

### 3.3 桌面客户端（S4，待接入）

消费方式：

```python
from ai_agent_factory.agent.baseagent import AgentOutputListener, AgentOutputError

class WindowListener(AgentOutputListener):
    def on_token(self, text):
        ...      # 把增量投到界面线程
    def on_turn_completed(self, full_text):
        ...
    def on_error(self, error_info):
        ...

manager_agent.set_output_listener(WindowListener())
manager_agent.chat("做一个待办清单应用")   # 在工作线程里调用
manager_agent.clear_output_listener()      # 关闭窗口前取消
```

---

## 4. 依赖与装配

- `baseagent.py` 只依赖 `ai_agent_factory.llms.base_llm.BaseLLM`（契约）与标准库 `abc`、`dataclasses`；**不依赖** `base_llm_openai.py`，也不依赖 `myagent/` 或任何入口文件。
- rev 1 新增的标准库依赖仅 `dataclasses`（Python 3.7+）。
- 没有新增第三方依赖，因此 `requirements.txt` 不需要变化。
- 装配约束：一个 agent 实例同一时刻只有一个监听器；重复 `set_output_listener` 会替换旧的。多消费者需要自行在监听器里分发。

---

## 5. 符合性与偏差

| C1 条目 | 实现情况 | 状态 |
| --- | --- | --- |
| 1. 三类事件可订阅 | `set_output_listener` + `AgentOutputListener` 三个回调；`error_info` 含 `exception` 与 `message` | 符合 |
| 2. 订阅是公开方法 | `set_output_listener(listener)` / `clear_output_listener()` | 符合（命名即契约建议名） |
| 3. 未订阅时行为逐字不变 | 事件发射为空操作；两组用例在改动前后各跑一次 | 符合 |
| 4. 订阅后抑制或并存并写明 | 选择**并存**，理由见 2.3；`token_deal` / `todo` 仍被调用 | 符合 |
| 5. 回调在调用线程内、不引入线程与 Qt | 同步直接调用；静态扫描把关 | 符合 |
| 6. 错误不被吞 | 先发 `error` 再裸 `raise`，保留类型与 traceback | 符合 |

**偏差：无。**

契约本身的条款没有发现与代码现状矛盾之处：`token_deal` / `todo` 的实际调用路径（逐 token / 每轮一次，均在 `chat()` 内）与 C1 描述一致。

---

## 6. 测试证据

测试目录：`test/platform-framework/`（本角色自有）。全部使用测试替身，不联网、不调用真实模型。

| 文件 | 覆盖 |
| --- | --- |
| `conftest.py` | 把项目根加入 `sys.path` |
| `fakes.py` | `ScriptedLLM` / `FailingLLM` / `MidStreamFailingLLM` / `RecordingAgent` |
| `test_baseagent_legacy_output.py` | **不订阅组**：stdout 逐字断言、`token_deal` / `todo` 调用顺序、多轮累加 |
| `test_baseagent_output_events.py` | **订阅组**：三类事件顺序与内容、并存策略、取消订阅、类型校验、三类错误的 `error` 事件、调用线程一致、嵌套 `chat()` 完成顺序、无线程/GUI 依赖静态扫描 |
| `test_baseagent_context.py` | 上下文裁剪边界（`len == max_context` 不裁剪、超出后保留系统提示 + 最近 N 条）、`reset_context` |

实际命令与结果：

```
python -m pytest test/platform-framework -q
```

| 时点 | 结果 | 说明 |
| --- | --- | --- |
| 改动前（`baseagent.py` rev 0） | `6 passed` | 只有不订阅组 + 上下文组，用作「改动前 stdout 基线」 |
| 改动后（rev 1，尚未加订阅用例时） | `test_baseagent_output_events.py` 收集失败：`ImportError: cannot import name 'AgentOutputError'` | 证明订阅用例确实依赖新 API，不是空跑 |
| 改动后（rev 1 最终） | `18 passed` | 6 个既有用例断言未改、结果一致 + 12 个订阅用例通过 |
| 文档迁移复核（2026-10-17） | `18 passed` | 只搬文档、未动代码与测试，复跑仍全绿 |

跨角色旁证（只读，不改对方文件）：

```
python -m pytest test -q
→ 125 passed
```

`test/orchestration/`（流程编排角色所有）在这台机器上与我的改动同批存在。它直接构造 `SystemManagerAgent`
（`BaseAgent` 的真实子类）并驱动 `chat()` / `make_decision()` / `report_status()` 路径。该套件全部通过，
说明 rev 1 没有破坏真实业务智能体经由 `chat()` 的既有行为——比只读审阅更强的证据。

---

## 7. 已知限制

1. **嵌套 `chat()`**：`todo()` 内再次 `chat()` 时，每轮各发一次 `turn_completed`。监听器若要把输出追加到同一个气泡，需要自己按轮次切分。
2. **监听器异常会打断管线**：监听器抛出的异常不被吞掉，会终止当前 `chat()`。这是刻意的（不隐藏错误），代价是界面层的 bug 会打断业务流程。
3. **未订阅时不打印错误**：`chat()` 的 `except` 分支在未订阅时只 `raise`，不写 stdout —— 这是为满足「未订阅时 stdout 逐字不变」而刻意保留的；错误由调用方（三个入口）打印。
4. **订阅是实例级**，不是全局；管线内部子智能体需各自订阅。

---

## 8. 变更历史

| 日期 | 版本 | 变更 | 影响面 | 文档 |
| --- | --- | --- | --- | --- |
| 2026-10-17 | rev 1 | `BaseAgent` 增加输出事件订阅（契约 C1）：新增 `AgentOutputListener`、`AgentOutputError`、`set_output_listener()`、`clear_output_listener()`；`chat()` 增加事件发射与 `try/except` 上报 | 三个 CLI 入口与四个业务智能体行为不变（只读核对 + 回归用例）；桌面客户端可订阅 | `docs/contracts/desktop-client-v1.md` C1；本文件 |
| 2026-10-17 | rev 1.1 | 本文档从临时位置 `common/platform-framework/api-spec.md` 迁到规范位置；旧位置改为指针 | 无代码影响 | 本文件 |

变更要点（rev 0 → rev 1）：

1. 新增两个公开类型 `AgentOutputListener`（抽象类）、`AgentOutputError`（冻结数据类）。
2. `BaseAgent.__init__` 初始化 `__output_listener = None`。
3. 新增 `set_output_listener()` / `clear_output_listener()` 与三个私有发射方法。
4. `chat()` 内顺序调整为「事件先发、既有回调后走」，整体包进 `try/except`：先发 `error` 再裸 `raise`。
5. `chat()` 的 docstring 更新为 8 步流程，并写明顺序约定。
6. 既有 `if self.token_deal:` / `if self.todo:` 判断、上下文裁剪规则、返回值保持原样（不视为需要清理的死代码，改动面越小越好）。
