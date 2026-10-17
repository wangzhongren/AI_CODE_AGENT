# 模块边界文档：平台框架

本文件定义「平台框架」角色的改动范围。**Section 1 是唯一的改动白名单。** 本角色对该表之外的任何文件均无写权限，默认只读。

## Section 1：可修改的文件与目录

| 类型 | 可操作路径 | 用途 |
| --- | --- | --- |
| 单文件 | `ai_agent_factory/agent/baseagent.py` | 智能体运行时抽象基类：对话上下文、流式回调分发、`chat()` 主流程 |
| 单文件 | `ai_agent_factory/llms/base_llm.py` | LLM 供应商抽象契约（`BaseLLM`） |
| 单文件 | `ai_agent_factory/llms/base_llm_openai.py` | OpenAI 兼容流式实现（`OpenAILLM`） |
| 单文件 | `ai_agent_factory/llms/openai` | 0 字节无扩展名残留文件（见下方「遗留文件」） |
| 单文件 | `ai_agent_factory/__init__.py` | 包标记（当前为空） |
| 自有目录 | `common/platform-framework/` | 本角色私有辅助代码与框架支持代码 |
| 自有目录 | `test/platform-framework/` | 本角色单元测试与层内契约测试；不含生产代码 |
| 单文件 | `角色卡/platform-framework/feature-map.md` | 自有系统功能导航（被接受后由本角色创建） |
| 条件目录 | `角色卡/platform-framework/docs/feature/` | 稳定功能说明、流程图与历史链接 |
| 条件目录 | `角色卡/platform-framework/docs/` | 本角色设计/变更/修复历史 |
| 单文件 | `角色卡/platform-framework/memo.md` | 续接线索（简短、带日期与来源） |
| 单文件 | `角色卡/platform-framework/changelog.md` | 变更历史 |
| 单文件 | `角色卡/platform-framework/functional-description.md` | 模块说明与代码位置 |
| 单文件 | `角色卡/platform-framework/api-spec.md` | 导出、依赖、契约符合性、测试证据 |
| 条件目录 | `角色卡/platform-framework/docs/design/` | 设计记录 |
| 条件目录 | `角色卡/platform-framework/docs/change/` | 变更记录 |
| 条件目录 | `角色卡/platform-framework/docs/fix/` | 修复记录 |
| 自有目录 | `temp/platform-framework/` | 未通过/返工产物暂存，供审核对照 |

**除上表所列，或已被上表目录覆盖的文件外，其余文件默认只读。** 要改动未覆盖的文件，必须先提交 Section 1 更新提案，与代码改动遵守同样的证据与接受关口。

## 本角色持有的共享抽象（唯一主要负责者）

以下抽象被多个角色依赖，**本角色是它们唯一的主要负责者**。其他角色只能作为只读依赖引用，不得定义第二份：

| 抽象 | 位置 | 消费者 |
| --- | --- | --- |
| `BaseAgent`（智能体运行时契约与对话循环） | `ai_agent_factory/agent/baseagent.py` | `myagent/` 全部五个智能体 |
| `BaseLLM`（模型供应商契约） | `ai_agent_factory/llms/base_llm.py` | `baseagent.py`、`file_operation_handler.py` |
| `OpenAILLM`（模型供应商实现） | `ai_agent_factory/llms/base_llm_openai.py` | 三个入口文件、`backend_developer_agent.py` |
| 对话消息契约 `{"role": str, "content": str}` | `baseagent.py` 中的上下文结构 | `file_operation_handler.py`、`OpenAILLM.chat()`、全部业务智能体 |
| 智能体回调契约 `todo(token)` / `token_deal(result)` | `baseagent.py` 的抽象方法 | `myagent/` 全部五个智能体 |

**主负责者变更会使其所有引用方的既有测试证据失效**（治理不变式 #6）。改动上述任一项前必须由项目管理角色协调，并安排引用方复测。

## 私有抽象

在本 Section 1 所列文件与 `common/platform-framework/` 目录内，本角色可以增删辅助函数、工具与内部类型，无需在 Section 1 逐符号登记。从当前任务就近开始；出现真实的跨角色复用需求时交项目管理角色。契约类型仍属于本层或 Model 层，不得因多个角色使用就搬进 `common/`。

## 遗留文件与已知缺陷

| 项 | 现状 | 处置 |
| --- | --- | --- |
| `ai_agent_factory/llms/openai` | 0 字节、无扩展名、不可导入 | 判为误建残留。删除需客户确认；确认前保留且不引用，禁止写入内容 |
| `agent/`、`llms/`、`utils/`、`myagent/` 下缺少 `__init__.py` | 依赖隐式命名空间包 | 现状可运行。是否补齐需客户决定，不得单方面改动包结构 |
| `OpenAILLM.chat()` 异常处理 | 把 `APIError` 与通用 `Exception` 都包成同一个 `Exception`，丢失原始类型 | 已知缺陷。修复需先出方案并经项目管理角色评审 |

`temp/platform-framework/` 属草稿区：不是交付物、不参与验收、不进版本控制。被门禁拒绝的写入内容不得存入 temp——拒绝即零副作用，没有产物可存。

## 附注：本角色不拥有

- `ai_agent_factory/utils/file_operation_handler.py` — 属「文件产出」角色。本角色仅按 Section 1 契约被其引用。
- `myagent/` 下全部文件 — 属「业务智能体」与「流程编排」角色。
- 三个入口文件与 `requirements.txt` — 属「装配」角色。
- 本角色**不是** `common/shared/` 的写入者，见 `角色卡/project-management/boundary.md`。
