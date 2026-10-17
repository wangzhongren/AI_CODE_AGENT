# 项目工作流：桌面客户端 v1（PySide6）

本文件是「添加桌面客户端」这一轮协作的步骤表。契约全文见 `docs/contracts/desktop-client-v1.md`（冻结于 2026-10-17）。
每个角色动手前按序读：本工作流 → 本步骤契约 → 本角色 role-card 的必读资料。读到与派发描述不符（版本/接口对不上）⇒ **停止并交 blocked 报告**，不得猜、不得改契约。

## 步骤表

| # | 步骤 | 角色 | 前置依赖 | 契约 | 交接物 | 完成口令 | 验收 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S1 | 冻结契约 | su | — | — | `docs/contracts/desktop-client-v1.md` | `S1-DONE` | 客户确认（已完成 2026-10-17） |
| S2 | `BaseAgent` 输出事件钩子 | platform-framework | S1 | C1 | `ai_agent_factory/agent/baseagent.py` 的公开订阅方法 + `test/platform-framework/` 用例 | `S2-DONE` | 未订阅时三个入口行为逐字不变；订阅后事件可被消费；平台框架不引入线程、不依赖 Qt |
| S3 | 项目状态快照方法 | orchestration | S1 | C2 | `myagent/system_manager_agent.py` 的公开快照方法 + `test/orchestration/` 用例 | `S3-DONE` | 五个布尔齐全、`phase` 取值在契约枚举内、调用无副作用、`report_status()` 打印行为不变 |
| S4 | 桌面端骨架与接线 | desktop-client | S2, S3 | C1, C2, C3 | `desktop/` 可启动窗口、工作线程、输出渲染、状态面板 | `S4-DONE` | 能提交需求、能看到流式输出、能读到状态面板、能干净关闭并回收线程 |
| S5 | 依赖与启动装配 | assembly | S4 | C4 | `requirements.txt` 增 `PySide6`、启动方式说明 | `S5-DONE` | 干净环境按说明能启动；启动失败有可读报错 |
| S6 | 端到端集成验收 | testing | S4, S5 | C1–C4 | `test/testing/` 用例与测试报告 | `S6-DONE` | 从输入需求到产出文件全链路；关闭后无残留进程；不得用替身冒充联调通过 |
| S7 | 架构与使用文档更新 | project-management | S2–S5 | — | `角色卡/project-management/docs/architecture.md`、`README.md` | `S7-DONE` | 协作图含桌面客户端；启动说明与实际一致 |

## 当前进度（2026-10-17 更新）

| 步骤 | 状态 | 说明 |
| --- | --- | --- |
| S1 | `S1-DONE` | 契约冻结，已从 v1 升级到 v2 |
| S2 | `S2-DONE` | `BaseAgent` 输出事件；`test/platform-framework` 18 passed |
| S3 | `S3-DONE` | `get_snapshot()` 状态快照；`test/orchestration` 119 passed |
| S3b | `S3b-DONE` | 监听器下发到四个子智能体（契约 C1.2），11 个新用例 |
| S4 | `S4-DONE` | `desktop/` 骨架；`test/desktop-client` 41 passed |
| S5a | `S5a-DONE` | `PySide6==6.12.0` 精确锁定 + 项目内 `.venv`（Python 3.12） |
| S5b | `S5b-DONE` | `.venv` 内 pytest 9.1.1（开发期依赖，不进 `requirements.txt`） |
| S5c | `S5c-DONE` | `desktop_main.py` 真实接线；缺变量 exit 2 且提示可读 |
| S6 | **部分完成** | 离线 `S6b-DONE`：92 token（be=32 / fe=24 / pj=24 / pm=4 / sys=8），逐 token 比对 6/6 全等，error 0；**真实模型验证待客户提供 `.env`** |
| S6FIX | 进行中 | ① 编排器 `todo()` 吞异常致 `error` 事件发不出；② 业务智能体 `todo()` 自递归无轮数上限 |
| S7 | `S7-DONE` | README 重写 + 架构文档（含 Mermaid 数据流图）；已纠正"侧边面板"等与实物不符的描述 |
| S8 | 待定 | 桌面端状态面板（`get_snapshot()` 已就绪，界面未接） |

**契约版本**：以 `docs/contracts/desktop-client-v2.md` 为准（2026-10-17 客户确认）。v1 保留可读、不再引用。C1.2 与 C4 以 v2 为准。

## 已知缺陷与未测项（2026-10-17）

1. **静默失败**：`make_decision()` 某分支抛错时，`SystemManagerAgent.todo()` 吞掉异常，导致 C1 的 `error` 事件发不出——桌面窗口对这类失败完全静默（S6FIX 修复中）。复现：`test/testing/check_orchestrator_decision_error.py`。
2. **自递归无轮数上限**：后端 / 前端智能体的 `todo()` 在模型连续返回文件操作标签时会自递归，实测 11340 token / 494 轮后 `RecursionError` 并被自身 try/except 吞掉（S6FIX 修复中）。
3. **测试基建冲突**：`test/orchestration/support.py` 与 `test/desktop-client/support.py` 同名顶层模块且无 `__init__.py`，四套合跑会 exit 2（`ImportError: cannot import name 'PROJECT_ROOT'`）。**分开跑均全绿**：18 / 119 / 41。
4. **C1 事件不带来源标识**：监听器收到的是纯文本，窗口无法区分某段输出来自哪个智能体。
5. **真实模型端到端未测**：客户环境缺 `.env`，真实 API 链路一次都没跑过。

## 真实验收的一键命令

客户在项目根新建 `.env`（`api_key` / `model_name` / `base_url` 三行）后执行：

```
.venv\Scripts\python.exe test/testing/s6_real_api_acceptance.py
```

退出码：`0` = 真实口径通过；`1` = 验收项未通过（逐条列原因）；`3` = 仍缺凭证（不构造 LLM、不联网）。

## 任务粒度（2026-10-17 新增）

单轮硬超时为 120 秒。S2、S3 各自触发过 2 次以上超时，均发生在把「实现 + 测试 + 文档」塞进同一轮时。据此约定：

1. 一次派发只推进**一个可验证的小步**，交付物能在单轮内写完并跑完验证。
2. 跨越「实现 → 测试 → 文档」的大步必须拆开：先实现并通过测试拿到口令，再单独补文档。
3. 派发时写清「本步不做什么」，避免顺手扩范围导致超时。
4. 角色超时中止前已落盘的产物不算完成；重新派发时须写明「已有产物在 X，先核对，不要重写」。

## 完成口令

格式：`<步骤号>-DONE @<YYYY-MM-DD> 证据:<项目内路径>`

例：`S2-DONE @2026-10-20 证据:ai_agent_factory/agent/baseagent.py, test/platform-framework/test_output_events.py`

口令必须由回交的角色自己给出，并附实际运行的测试命令与结果。**跳过、无法运行、未解决的检查不算通过。**

## 并行与串行

- S2 与 S3 无依赖关系，**可以并行**。
- S4 必须等 S2、S3 都给出完成口令后才开工。
- S5 依赖 S4 存在可启动的入口；S6 依赖 S4、S5。
- S7 可与 S6 并行。

## 变更与重验

1. **契约变更**（C1–C4 任一项内容变化）：出**新版本文件** `docs/contracts/desktop-client-v2.md`，同步更新本文件步骤表与本变更记录，走客户确认流程；受影响的步骤**既有回交作废**，不得再采信，向受影响角色重派并引用新地址。
2. **受影响范围**：改 C1 ⇒ S2 重做，S4 起作废重交；改 C2 ⇒ S3 重做，S4 起作废重交；改 C3 ⇒ S4 重做，S6 重跑；改 C4 ⇒ S5 重做，S6 重跑。
3. **未受影响的步骤不回滚、不重跑。** 例如只改界面内部实现，只重跑 S4 与 S6。
4. **共享基础契约变更**（`BaseAgent` 对外行为）：按治理不变式 #6，须由「项目管理」角色协调并安排全部调用方（三个入口 + 四个业务智能体）复测，复测结果作为 S2 验收证据的一部分。

## 边界现状

- 本次新建角色 `desktop-client`，边界见 `角色卡/desktop-client/boundary.md`。
- S2 改的 `baseagent.py` 在「平台框架」现有 Section 1 内；S3 改的 `system_manager_agent.py` 在「流程编排」现有 Section 1 内；S5 改的 `requirements.txt` 在「装配」现有 Section 1 内。**三者均不需要扩张边界。**
