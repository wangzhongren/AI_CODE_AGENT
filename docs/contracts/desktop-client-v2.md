# 契约：桌面客户端 v2

- **状态**：冻结（2026-10-17，客户确认）。
- **不可变**：本文件冻结后不改。任何内容变化出新文件 `desktop-client-v3.md`。
- **与 v1 的关系**：`desktop-client-v1.md` 一字未改、保留可读。v2 **继承 v1 全部条款**，只修改 C1（追加监听器下发）与 C4（依赖精确锁定）。C2、C3 与 v1 完全一致。
- **工作流**：`docs/workflow.md`。

---

## C1（改）：输出事件 + 监听器下发

### C1.1 继承 v1 的三类事件与订阅方式

不变：`token` / `turn_completed` / `error` 三类事件；公开的 `set_output_listener(listener)` / `clear_output_listener()`；未订阅时行为逐字不变；事件与 print 并存（不抑制）；回调在调用线程内、框架不引入线程与 Qt；错误先发事件再裸 `raise`。

### C1.2 新增：把监听器下发到子智能体

**问题**：v1 的订阅是按实例的。`SystemManagerAgent` 把工作派给 `agents['pm' / 'pj' / 'be' / 'fe']`，它们是独立对象。桌面端只能订阅注入给它的那一个对象，因此**看不到 PRD、后端、前端的流式输出**——用户提交需求后，只看到编排器自己的几句话。

**要求（主负责者：流程编排，文件 `myagent/system_manager_agent.py`）**：

1. 提供**公开入口**把监听器下发给四个子智能体。命名可自定，语义等价于 `set_output_listener_for_children(listener)`。
2. 行为：对 `agents` 字典中的**每一个**实例调用 v1 的 `set_output_listener(listener)`。
3. **不得静默跳过**：若某个子智能体没有该能力或订阅抛错，必须报告是哪一个、什么错；不得整体静默降级。
4. **幂等**：重复下发不得叠加订阅（同一监听器重复设置应被替换，最终每个子智能体只持有一个监听器）。
5. **未调用时零影响**：不调用该入口时，子智能体不订阅，行为与当前现状完全一致。
6. 不引入线程、不依赖 Qt；`clear_output_listener` 亦应能把子智能体的订阅一并清除（或提供对应的清除入口）。

**验收证据**（`test/orchestration/`）：

- 下发后，四个子智能体各自产生的事件能被同一个监听器收到（用替身智能体与替身 LLM，不联网）；
- 重复下发两次，事件不重复到达；
- 未下发时，事件只来自编排器自身；
- 清除后不再收到任何子智能体事件。

### C1.3 桌面端如何使用（消费者：desktop-client）

```python
handle = desktop.start(orchestrator)          # desktop 内部调用 orchestrator.set_output_listener(listener)
orchestrator.set_output_listener_for_children(listener)   # 由装配层负责下发，桌面端不越层
```

**分层要求**：下发动作由**装配层**（`desktop_main.py`）在启动时完成，`desktop` 包**不得**自己去遍历编排器内部结构——那是穿透私有状态。

---

## C2（不变）

与 v1 完全一致：`get_snapshot()` 返回 `{'state': 五布尔, 'phase': 七枚举}`，无副作用、返回副本、纯数据；`report_status()` 打印行为不变。

---

## C3（不变）

与 v1 完全一致：公开启动操作 + 关闭句柄；`shutdown()` 中断任务、回收线程、可重复调用；`import desktop` 无副作用；启动失败清理已创建资源；句柄不暴露编排器与 Qt 对象。

---

## C4（改）：依赖精确锁定

### 变更理由

v1 要求「给定主版本下限、不锁精确小版本」。实际执行中：ShellGate 要求固定版本；不锁版本会让 Qt 渲染行为随版本漂移；可复现安装在排障时是刚需。

### v2 要求（主负责者：装配）

1. `requirements.txt` 必须**精确锁定** `PySide6==6.12.0`（升级需出契约 v3）。
2. `requirements.txt` 只放**运行时**依赖：`openai`、`python-dotenv`、`PySide6==6.12.0`。
3. **开发期工具不进 `requirements.txt`**：`pytest` 装在项目内 `.venv`，版本记录在装配角色的 `memo.md`。
4. 所有命令统一用 `.venv\Scripts\python.exe`（Windows）；系统 Python 未装依赖，不得用于跑测试。
5. 环境变量契约（`api_key` / `model_name` / `base_url`）不变，桌面端与 CLI 共用同一份 `.env`；缺变量时必须给出可读提示，不得把 `None` 传给 `OpenAILLM`。
6. 启动方式：`python -m desktop`（界面 + 占位编排器）与 `.venv\Scripts\python.exe desktop_main.py`（真实接线）两种；后者由装配角色提供。

---

## 失效规则（v2）

| 变更 | 后果 |
| --- | --- |
| C1.1 变化 | S2 重做；S4 渲染部分作废重验 |
| C1.2 变化 | S3b（新增的下发步骤）重做；S4 不需重做（桌面端只消费事件） |
| C2 / C3 变化 | 对应步骤重做；S6 重跑 |
| C4 变化 | S5 重做；S6 重跑 |

契约变更一律出新版本文件并同步更新 `docs/workflow.md`，经客户确认后生效。未受影响的步骤不回滚、不重跑。

---

## 已知限制（v2 明确记录）

1. 监听器是**按实例**持有的：桌面端给编排器设一个监听器，装配层再把同一个监听器下发给子智能体——同一个监听器对象会被 5 个实例同时持有，其回调必须线程安全或只做 `signal.emit`。
2. 桌面端**不得**自行遍历编排器的 `agents` 字典下发监听器（穿透私有状态）；下发属装配层职责。
3. 子智能体在 `todo()` 内递归调用 `chat()` 时，每轮各发一次 `turn_completed`，监听器需自行按轮次切分。
