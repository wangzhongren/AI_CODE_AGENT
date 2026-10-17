# 功能导航：流程编排

本角色负责「下一步由谁做什么」：维护项目开发里程碑状态，按指令推进下一步，处理变更需求并分派受影响的前后端角色，报告项目状态。代码集中在 `myagent/system_manager_agent.py`。

## 功能一览

| 功能 | 状态 | 代码位置 |
| --- | --- | --- |
| 项目状态快照（`get_snapshot`，契约 C2） | 已实现、已测 | `myagent/system_manager_agent.py::get_snapshot` |
| 输出监听器下发（`set_output_listener_for_children`，契约 C1.2） | 已实现、已测 | `myagent/system_manager_agent.py::set_output_listener_for_children` |
| 子智能体订阅清除（`clear_output_listener_for_children`） | 已实现、已测 | `myagent/system_manager_agent.py::clear_output_listener_for_children` |
| 项目状态报告（`report_status`，打印到终端） | 既有，行为未变 | `myagent/system_manager_agent.py::report_status` |
| 流程推进（`execute_next_step`） | 既有，行为未变 | `myagent/system_manager_agent.py::execute_next_step` |
| 决策分发（`make_decision`，子串匹配调度词汇） | 既有，行为未变 | `myagent/system_manager_agent.py::make_decision` |
| 变更需求处理（`handle_change_request`） | 既有，行为未变 | `myagent/system_manager_agent.py::handle_change_request` |

## 项目状态快照（契约 C2）

桌面客户端要显示「项目走到哪一步」，调 `get_snapshot()` 拿一个纯数据字典，不要解析终端文字、也不要读 `project_state` 内部字段。

```python
{
    "state": {
        "prd_completed": bool,
        "guides_completed": bool,
        "backend_completed": bool,
        "frontend_completed": bool,
        "project_completed": bool,
    },
    "phase": str,   # idle | prd | guides | backend | frontend | change | done
}
```

`phase` 判定顺序（命中即返回）：

| 顺序 | 条件 | `phase` |
| --- | --- | --- |
| 1 | `project_completed` 为真 | `done` |
| 2 | 四项开发全为真、项目未标记完成 | `change` |
| 3 | `prd_completed` 为假，且流程已启动（任一标志为真或上下文已有用户消息） | `prd` |
| 4 | `prd_completed` 为假，且流程完全没启动 | `idle` |
| 5 | `guides_completed` 为假 | `guides` |
| 6 | `backend_completed` 为假 | `backend` |
| 7 | 其余 | `frontend` |

顺序与 `execute_next_step()` 的推进顺序一致；`change` 对应它「项目已完成，等待修改需求」的分支。新增 `phase` 取值属于契约变更，先改契约再改代码。

快照无副作用（不推进状态、不调智能体、不触发 LLM、不改上下文），返回副本；`report_status()` 打印行为保持不变。

详细文档：待补。`boundary.md` Section 1 里列的 `docs/feature/`、`docs/change/` 与角色根目录的 `api-spec.md` 目前被治理写边界拒绝（解析器只认 `myagent/system_manager_agent.py`、`common/orchestration`、`test/orchestration`、`feature-map.md` 四条路径），所以接口约定、判定表与偏差说明暂时写在本文件里，待边界补齐后再迁出。

## 输出监听器下发（契约 C1.2）

桌面客户端只能订阅到编排器这一个对象，而 PRD、指导文档、后端、前端是四个独立子智能体。所以由装配层在启动时调用：

| 方法 | 作用 |
| --- | --- |
| `set_output_listener_for_children(listener)` | 对 `agents` 字典里的每个子智能体调用 C1.1 的 `set_output_listener(listener)` |
| `clear_output_listener_for_children()` | 对每个子智能体调用 `clear_output_listener()`，可重复调用 |

约定：

1. **失败不静默**：某个子智能体没有订阅能力、或订阅抛错时，收集每个失败者的键名、类型名与原始错误（含异常类型），最后抛一个可读的 `RuntimeError`。这是本步选定的唯一上报通道（不写 stderr、不降级），便于装配层在启动时就发现接线不全。
2. **失败时的状态**：抛错前已成功下发的子智能体保持订阅；本方法幂等，修好后重试不会叠加订阅。
3. **幂等**：重复下发同一监听器只保留一个（C1.1 的 `set_output_listener` 是替换语义），事件不会重复到达；换一个监听器再下发则旧的收不到事件。
4. **未调用时零影响**：不下发则子智能体不订阅，三个 CLI 入口行为与从前完全一致。
5. 本方法不推进状态、不动对话上下文、不引线程、不依赖 Qt。
6. 同一个监听器对象会被 5 个实例（编排器 + 四个子智能体）同时持有，所以界面层的回调必须线程安全或只做 `signal.emit`（契约 v2「已知限制」第 1 条）。

## 错误冒泡：决策失败会到达界面层（C1.6）

`todo()` 里原先的 try/except 只打印「管理者决策解析错误」，把异常吞掉了，于是 `BaseAgent.chat()` 的 except 看不到它，监听器收到 0 个 `error` 事件——桌面窗口点了发送毫无反应，像程序死了。

2026-10-17 修复：打印之后改成裸 `raise`，让异常冒泡到 `chat()`，由那里按契约 C1 先发 `error` 事件再裸 raise。原有两行诊断打印（「管理者决策解析错误」「原始响应: …」）与顺序不变；`KeyboardInterrupt` 属 `BaseException`，不在这层被接住。

对三个 CLI 入口的影响（只读核对，入口未改）：

| 入口 | 是否用 `SystemManagerAgent` | 循环内兜底 | 结论 |
| --- | --- | --- | --- |
| `main.py` | 不用（自己串联四个智能体） | `except Exception` → 打印「❌ 发生错误」+ traceback，循环继续 | 不受影响 |
| `main3.py` | 用，`manager_agent.chat(user_input)` | `except Exception` → 打印 + traceback，`while True` 继续 | 异常被兜住，提示后退回输入，不退出程序 |
| `enhanced_main.py` | 用，`manager_agent.chat(user_input)` | 同上 | 同上 |



## 接口与依赖（`api-spec.md` 的等价内容）

公开方法：

| 方法 | 消费者 | 说明 |
| --- | --- | --- |
| `__init__(basellm, agents)` | 三个入口文件 | `agents` 为 `{'pm','pj','fe','be'}`，四个业务智能体由调用方注入 |
| `get_snapshot()` | 桌面客户端 | 契约 C2：纯数据只读快照，无副作用 |
| `set_output_listener_for_children(listener)` | 装配层（`desktop_main.py`） | 契约 C1.2：把监听器下发给四个子智能体，失败抛可读 `RuntimeError` |
| `clear_output_listener_for_children()` | 装配层 | 契约 C1.2：清除四个子智能体的订阅 |
| `report_status()` | 三个入口文件 | 打印状态，行为未变 |
| `execute_next_step()` | 入口文件 | 按状态推进下一步 |
| `handle_change_request(request)` | 入口文件 | 变更需求入口 |
| `make_decision(decision)` | `todo()` 等内部调用 | 按调度词汇分发 |

依赖方向：

- 只依赖 `ai_agent_factory/agent/baseagent.py` 的契约（C1.1 的 `set_output_listener` / `clear_output_listener`，以及 `get_context()` 读上下文长度，不写上下文）；
- 四个业务智能体只通过注入的 `agents` 字典调用，本文件不 import 任何具体智能体类；
- 不 import 三个入口文件。

装配未变：入口文件构造四个业务智能体 → 组成 `agents` 字典 → `SystemManagerAgent(llm, agents)`。

已知限制与偏差（都写进实现注释与测试）：

1. `idle` 与 `prd` 的区分借用对话上下文（是否已有用户消息），这是实现细节不是契约要求；`BaseAgent.get_context()` 语义若变化需复核。
2. 快照不加锁。桌面客户端在工作线程推进、主线程读快照时，并发安全由客户端自己保证（S4 范围）。
3. `make_decision()` 靠子串匹配、先命中先执行；回复里偶然含某关键词会走错分支，属既有风险，本次未加固（`test_first_matching_branch_wins` 把现状钉住）。

## 测试

- 目录：`test/orchestration/`
- 命令（项目根目录，必须用项目内解释器）：`.venv\Scripts\python.exe -m pytest test/orchestration -q`
- 当前结果：123 passed
- 覆盖：五个布尔 32 种组合、七个 `phase` 取值、快照无副作用、返回值是副本、`report_status()` 输出与改动前逐字一致、`make_decision()` 全部 11 个分支加兜底、依赖文件缺失与读取失败处理；监听器下发（四个子智能体事件都到达同一监听器、幂等、未下发时只收到编排器事件、清除后不再收到、缺能力/订阅抛错点名报出、下发不改状态与上下文）；决策失败冒泡（监听器收到 1 个 error 事件且是原异常、`chat()` 抛出而非正常返回、诊断打印仍在、正常路径与 `KeyboardInterrupt` 行为不变）
- 四个业务智能体与 LLM 全部用 `test/orchestration/support.py` 的替身注入，不依赖真实 LLM

## 历史

| 日期 | 类型 | 变化 |
| --- | --- | --- |
| 2026-10-17 | 新增 | 新增 `get_snapshot()` 只读快照（契约 C2，S3）；新增 `test/orchestration/` 全套用例 |
| 2026-10-17 | 新增 | 新增 `set_output_listener_for_children()` / `clear_output_listener_for_children()`（契约 v2 C1.2，S3b）；新增 11 个下发用例 |
| 2026-10-17 | 修复 | `todo()` 不再吞掉 `make_decision()` 的异常：打印诊断后裸 `raise`，`chat()` 得以按 C1.6 发 `error` 事件（S6FIX-ORCH）；新增 4 个回归用例 |
