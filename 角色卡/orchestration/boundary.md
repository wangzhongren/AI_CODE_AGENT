# 模块边界文档：流程编排

本文件定义「流程编排」角色的改动范围。**Section 1 是唯一的改动白名单。** 本角色对该表之外的任何文件均无写权限，默认只读。

## Section 1：可修改的文件与目录

| 类型 | 可操作路径 | 用途 |
| --- | --- | --- |
| 单文件 | `myagent/system_manager_agent.py` | 编排：项目状态机、决策分发、变更请求处理、状态报告 |
| 自有目录 | `common/orchestration/` | 本角色私有辅助代码 |
| 自有目录 | `test/orchestration/` | 本角色单元测试与层内契约测试；不含生产代码 |
| 单文件 | `角色卡/orchestration/feature-map.md` | 自有系统功能导航（被接受后由本角色创建） |
| 条件目录 | `角色卡/orchestration/docs/feature/` | 稳定功能说明、流程图与历史链接 |
| 条件目录 | `角色卡/orchestration/docs/` | 本角色设计/变更/修复历史 |
| 单文件 | `角色卡/orchestration/memo.md` | 续接线索（简短、带日期与来源） |
| 单文件 | `角色卡/orchestration/changelog.md` | 变更历史 |
| 单文件 | `角色卡/orchestration/functional-description.md` | 模块说明与代码位置 |
| 单文件 | `角色卡/orchestration/api-spec.md` | 导出、依赖、契约符合性、测试证据 |
| 条件目录 | `角色卡/orchestration/docs/design/` | 设计记录 |
| 条件目录 | `角色卡/orchestration/docs/change/` | 变更记录 |
| 条件目录 | `角色卡/orchestration/docs/fix/` | 修复记录 |
| 自有目录 | `temp/orchestration/` | 未通过/返工产物暂存，供审核对照 |

**除上表所列，或已被上表目录覆盖的文件外，其余文件默认只读。** 要改动未覆盖的文件，必须先提交 Section 1 更新提案，与代码改动遵守同样的证据与接受关口。

## 本角色持有的契约

| 契约 | 位置 | 消费者 |
| --- | --- | --- |
| `project_state` 状态字典（`prd_completed` / `guides_completed` / `backend_completed` / `frontend_completed` / `project_completed`） | `system_manager_agent.py::__init__` | 三个入口文件按它判断初始开发是否完成 |
| 调度词汇（`ask_pm` / `ask_pj` / `ask_fe` / `ask_be` / `analyze_change` / `modify_fe` / `modify_be` / `modify_both` / `status` / `next` / `done`） | `system_manager_agent.py::make_decision` | 「业务智能体」角色输出对应标记；入口文件发送 `status` / `next` 命令 |
| 本角色的公开方法 `report_status()` / `execute_next_step()` / `handle_change_request()` | `system_manager_agent.py` | 三个入口文件直接调用 |
| 构造契约 `SystemManagerAgent(basellm, agents)`，`agents` 为 `{'pm','pj','fe','be'}` 字典 | `system_manager_agent.py::__init__` | 三个入口文件（`main3.py` / `enhanced_main.py`）组装 |

以上均为**跨角色契约**。本角色是 `project_state` 与调度词汇的主要负责者，改动会让消费者既有证据失效（治理不变式 #6），必须先由项目管理角色协调。

## 已知的脆弱点（本角色范围内，待治理决定是否加固）

| 项 | 现状 | 说明 |
| --- | --- | --- |
| 决策分派靠**子串匹配** LLM 自由文本 | `make_decision()` 用关键词判断分支，无 schema、无校验 | 回复中偶然含某关键词即可能误触发。加固需出方案并评审 |
| 控制标记无格式约定 | 「业务智能体」角色输出的 `modify_fe:` 等标记由本角色解析 | 双方各自维护，改一边会静默失配。**待核实**：当前是否已有约定文档 |
| 依赖上游文件存在 | `report_status()` / 状态检查读 `output/frontend_guide.md`、`output/backend_guide.json`、`output/backend_guide.md`、`output/api_spec.json` | 注意同时出现 `.md` 与 `.json` 两种后端指导文档路径。**待核实**：哪一个是权威来源 |

## 私有抽象

在本 Section 1 所列文件与 `common/orchestration/` 目录内，本角色可以增删辅助函数、工具与内部类型，无需在 Section 1 逐符号登记。上表列出的跨角色契约不适用此条。

`temp/orchestration/` 属草稿区：不是交付物、不参与验收、不进版本控制。被门禁拒绝的写入内容不得存入 temp——拒绝即零副作用，没有产物可存。

## 附注：本角色不拥有

- `myagent/` 下四个业务智能体文件 — 属「业务智能体」角色。本角色通过注入的 `agents` 字典调用，**不得** import 其类定义。
- `ai_agent_factory/` 下全部文件 — 属「平台框架」与「文件产出」角色（只读依赖）。
- 三个入口文件与 `requirements.txt` — 属「装配」角色。入口文件中的初始/变更判定逻辑属装配角色，与本角色的状态机是两个地方，改动需协调。
- 本角色**不是** `common/shared/` 的写入者，见 `角色卡/project-management/boundary.md`。
