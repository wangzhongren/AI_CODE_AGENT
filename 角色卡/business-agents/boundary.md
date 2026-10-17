# 模块边界文档：业务智能体

本文件定义「业务智能体」角色的改动范围。**Section 1 是唯一的改动白名单。** 本角色对该表之外的任何文件均无写权限，默认只读。

## Section 1：可修改的文件与目录

| 类型 | 可操作路径 | 用途 |
| --- | --- | --- |
| 单文件 | `myagent/product_manager_agent.py` | 产品经理智能体：由需求生成 PRD |
| 单文件 | `myagent/project_manager_agent.py` | 项目经理智能体：生成前后端与集成指导文档、分析变更需求 |
| 单文件 | `myagent/backend_developer_agent.py` | 后端开发智能体：数据库/API 设计、生成 `api_spec.json` 与后端文件 |
| 单文件 | `myagent/frontend_developer_agent.py` | 前端开发智能体：生成页面文件（HTML/Vue/Vite） |
| 自有目录 | `common/business-agents/` | 本角色私有辅助代码 |
| 自有目录 | `test/business-agents/` | 本角色单元测试与层内契约测试；不含生产代码 |
| 单文件 | `角色卡/business-agents/feature-map.md` | 自有系统功能导航（被接受后由本角色创建） |
| 条件目录 | `角色卡/business-agents/docs/feature/` | 稳定功能说明、流程图与历史链接 |
| 条件目录 | `角色卡/business-agents/docs/` | 本角色设计/变更/修复历史 |
| 单文件 | `角色卡/business-agents/memo.md` | 续接线索（简短、带日期与来源） |
| 单文件 | `角色卡/business-agents/changelog.md` | 变更历史 |
| 单文件 | `角色卡/business-agents/functional-description.md` | 模块说明与代码位置 |
| 单文件 | `角色卡/business-agents/api-spec.md` | 导出、依赖、契约符合性、测试证据 |
| 条件目录 | `角色卡/business-agents/docs/design/` | 设计记录 |
| 条件目录 | `角色卡/business-agents/docs/change/` | 变更记录 |
| 条件目录 | `角色卡/business-agents/docs/fix/` | 修复记录 |
| 自有目录 | `temp/business-agents/` | 未通过/返工产物暂存，供审核对照 |

**除上表所列，或已被上表目录覆盖的文件外，其余文件默认只读。** 要改动未覆盖的文件，必须先提交 Section 1 更新提案，与代码改动遵守同样的证据与接受关口。

## 本角色持有的契约

| 契约 | 位置 | 消费者 |
| --- | --- | --- |
| `api_spec` 结构（接口规格 JSON） | `backend_developer_agent.py::extract_api_spec_from_response` / `ensure_api_spec_file` | `frontend_developer_agent.py`、`system_manager_agent.py`、三个入口文件 |
| 控制标记 `modify_fe:` / `modify_be:` / `both_modify:` / `need_more_info:` | `project_manager_agent.py::todo` 的输出 | `system_manager_agent.py::make_decision` 解析 |
| 生成文件清单 `self.files`（`{"filename", "content"}` 列表） | `frontend_developer_agent.py` / `backend_developer_agent.py` | 上层装配流程 |
| `handle_json_task` 的入参形状 `{"files": [...]}` | `frontend_developer_agent.py` | 上层调用方 |
| 智能体状态属性 `prd` / `frontend_guide` / `backend_guide` / `integration_doc` / `api_spec` / `analysis_result` | 各智能体 `todo()` 写入 | `system_manager_agent.py`、三个入口文件读取 |

前三项是**跨角色契约**（消费者为「流程编排」与「装配」角色）。本角色是它们的主要负责者，但改动必须由项目管理角色协调并安排消费者复测（治理不变式 #6）。

## 已知重复实现（跨角色冲突，待治理）

`project_manager_agent.py`、`frontend_developer_agent.py`、`backend_developer_agent.py` 三个文件各自**重复实现**了下列成员，覆盖了 `FileOperationHandler` 的同名方法：

```text
handle_tagged_file_operations()   handle_single_operation()
create_file()   read_file()   update_file()   delete_file()   list_files()
```

`FileOperationHandler` 属「文件产出」角色。这三份副本**在本角色**范围内，但消除重复属跨角色改动：须由项目管理角色出设计，明确合并后的唯一实现与适配方式后再实施。**在治理决定之前，不得再新增第四份副本，也不得单方面改动「文件产出」角色的实现来迁就副本。**

## 私有抽象

在本 Section 1 所列文件与 `common/business-agents/` 目录内，本角色可以增删辅助函数、工具与内部类型，无需在 Section 1 逐符号登记。上面列出的跨角色契约不适用此条，其变更须走协调流程。

## 遗留与已知缺陷

| 项 | 现状 | 处置 |
| --- | --- | --- |
| `backend_developer_agent.py` 的 `__main__` 块 | 含硬编码占位密钥 `api_key="sk-"`、DashScope `base_url`、模型名 `qwen3-max` | 已知问题。**不得**扩展为真实凭证来源。清理需客户决定，属本角色文件 |
| 三个智能体覆盖 `FileOperationHandler` 同名方法 | 见上节 | 跨角色重构，需项目管理角色设计 |
| 提示词驱动的控制标记 | 纯字符串匹配，无 schema | 现状可用但脆弱。加固需与「流程编排」角色协调 |

`temp/business-agents/` 属草稿区：不是交付物、不参与验收、不进版本控制。被门禁拒绝的写入内容不得存入 temp——拒绝即零副作用，没有产物可存。

## 附注：本角色不拥有

- `ai_agent_factory/` 下全部文件 — 属「平台框架」与「文件产出」角色（只读依赖）。
- `myagent/system_manager_agent.py` — 属「流程编排」角色。
- 三个入口文件与 `requirements.txt` — 属「装配」角色。
- 本角色**不是** `common/shared/` 的写入者，见 `角色卡/project-management/boundary.md`。
