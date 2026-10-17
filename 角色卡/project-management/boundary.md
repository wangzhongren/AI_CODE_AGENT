# 模块边界文档：项目管理

本文件定义「项目管理」角色的改动范围。**Section 1 是唯一的改动白名单。** 本角色对该表之外的任何文件均无写权限，默认只读。

## Section 1：可修改的文件与目录

| 类型 | 可操作路径 | 用途 |
| --- | --- | --- |
| 自有目录 | `common/shared/` | 跨角色共享组件；本角色是唯一写入者 |
| 自有目录 | `test/project-management/shared/` | `common/shared/` 的专属测试；不含生产代码 |
| 单文件 | `角色卡/project-management/docs/architecture.md` | 总体架构：系统用途、角色职责、主要模块、公开契约、Mermaid 协作图 |
| 单文件 | `角色卡/project-management/docs/architecture/shared-components.md` | 共享组件清单（共享组件的唯一描述处） |
| 单文件 | `角色卡/project-management/docs/project-rules.md` | 项目全局工程规则 |
| 条件目录 | `角色卡/project-management/docs/meetings/` | 被要求主持会议时的共享纪要 |
| 条件目录 | `角色卡/project-management/docs/scheduling/` | 每个协作任务一份 Git 可读排期记录 `<task-id>.md` |
| 单文件 | `角色卡/project-management/feature-map.md` | 功能导航（无直接负责的业务功能，列共享组件） |
| 条件目录 | `角色卡/project-management/docs/feature/` | 共享组件的稳定功能说明 |
| 条件目录 | `角色卡/project-management/docs/` | 本角色设计/变更/修复历史 |
| 单文件 | `README.md` | 项目总览：架构说明、环境配置、运行方式 |
| 单文件 | `DEVELOPMENT_GUIDE.md` | `ai_agent_factory` 框架开发指南 |
| 单文件 | `license` | 项目许可证正文（MIT） |
| 单文件 | `.gitignore` | 版本控制忽略规则 |
| 单文件 | `角色卡/project-management/memo.md` | 续接线索（简短、带日期与来源） |
| 单文件 | `角色卡/project-management/changelog.md` | 变更历史 |
| 单文件 | `角色卡/project-management/functional-description.md` | 模块说明与代码位置 |
| 单文件 | `角色卡/project-management/api-spec.md` | 导出、依赖、契约符合性、测试证据 |
| 条件目录 | `角色卡/project-management/docs/design/` | 设计记录 |
| 条件目录 | `角色卡/project-management/docs/change/` | 变更记录 |
| 条件目录 | `角色卡/project-management/docs/fix/` | 修复记录 |
| 自有目录 | `temp/project-management/` | 未通过/返工产物暂存，供审核对照 |

**除上表所列，或已被上表目录覆盖的文件外，其余文件默认只读。** 要改动未覆盖的文件，必须先提交 Section 1 更新提案，与代码改动遵守同样的证据与接受关口。

## 本角色的应用代码范围只有 `common/shared/`

本角色是 `common/shared/` 的**唯一写入者**，同时维护其专属测试与共享组件文档。这是本角色唯一的应用代码权限。

**不得**修改：
- 其他角色的业务代码（`ai_agent_factory/agent/`、`ai_agent_factory/llms/`、`ai_agent_factory/utils/`、`myagent/`）
- 其他角色的私有 `common/<role-id>/` 子树
- 三个入口文件与 `requirements.txt`
- 调用方测试（`test/<其他角色>/`）
- 层契约源码、Model 定义、构建配置、权限配置、角色卡与边界文档

## 共享组件文档格式

`docs/architecture/shared-components.md` 是共享组件的当前复用清单，与带日期的变更历史分开。每个组件一个条目：

| 字段 | 说明 |
| --- | --- |
| 名称与用途 | 解决什么问题，共享带来的好处 |
| 代码与公开入口 | 实际路径与受支持的入口 |
| 所有者与使用者 | 本角色为维护者；当前消费者角色与调用位置；计划中的使用者要标明 |
| 契约与示例 | 输入、输出、错误，以及一段简短的用法示例 |
| 测试与变更影响 | 对应测试、受影响消费者与兼容性注意事项 |

跨角色复用的顺序：角色报告需求 → 本角色写设计并确定消费者 → 客户确认文档并授权实施 → 本角色实现并测试 `common/shared/` → 安排各消费者接入 → 运行受影响的测试 → 更新清单、相关功能流程/历史与项目架构。同版本同范围的既有同意可以复用。**批准提取后不得留下两份各自维护的副本**；各原所有者更新自己的调用方并移除过时实现。

## 当前状态：`common/shared/` 为空

截至 bootstrap，`common/shared/` 目录已建立但**尚无组件**。`docs/architecture/shared-components.md` 与 `docs/architecture.md` 由本角色在被接受后建立。

**候选共享组件（仅记录，未批准实施）**：三个业务智能体各自重复实现的一套文件操作方法（`create_file` / `read_file` / `update_file` / `delete_file` / `list_files` / `handle_tagged_file_operations` / `handle_single_operation`）与 `FileOperationHandler` 的同名方法重叠。消除这份重复涉及「业务智能体」与「文件产出」两个角色，属于典型的跨角色集成设计任务。**是否做、怎么做，须先出设计并经客户确认，不得直接开工。**

## 已知的遗留问题（本角色文档范围内）

| 项 | 现状 | 说明 |
| --- | --- | --- |
| `README.md` 引用不存在的 `.env.example` | README 让用户复制该文件，仓库中无此文件 | 文档与实物不符。补文件（属「装配」角色）或改文档（属本角色），需客户决定走哪条 |
| `DEVELOPMENT_GUIDE.md` 列出的目录树 | 含 `ai_agent_factory/llms/openai`（0 字节残留），未提缺失的 `__init__.py` | 描述与现状有出入，属本角色文件，可随架构文档一并校正 |
| 项目无全局工程规则 | `docs/project-rules.md` 尚未建立 | bootstrap 不虚构项目规则；本角色被接受后建立 |

## 私有抽象

在 `common/shared/` 内，本角色可以增删辅助函数与内部类型，无需在 Section 1 逐符号登记。共享组件的公开契约不适用此条——变更是跨角色事项，须走设计评审与消费者复测。

`temp/project-management/` 属草稿区：不是交付物、不参与验收、不进版本控制。被门禁拒绝的写入内容不得存入 temp——拒绝即零副作用，没有产物可存。

## 附注：本角色不拥有

- `ai_agent_factory/` 下全部文件 — 属「平台框架」与「文件产出」角色。
- `myagent/` 下全部文件 — 属「业务智能体」与「流程编排」角色。
- 三个入口文件与 `requirements.txt` — 属「装配」角色。
- `test/<其他角色>/` — 属各自角色。
- 角色卡与边界文档 — 属治理角色。
