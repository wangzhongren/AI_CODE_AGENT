# 模块说明：业务智能体

本角色提供四个业务智能体（`myagent/` 下），属五层结构里的 Service 层：它们把「需求文本」变成 PRD、开发指导文档、后端接口规格与前端页面文件。依赖方向只向下——`ai_agent_factory` 的 `BaseAgent` 与 `FileOperationHandler`；不 import 三个入口文件，也不 import 流程编排的 `system_manager_agent.py`。

## 代码位置

| 文件 | 职责 | 对外状态属性 |
| --- | --- | --- |
| `myagent/product_manager_agent.py` | 由需求生成 PRD | `prd` |
| `myagent/project_manager_agent.py` | 生成 `frontend_guide.md` / `backend_guide.md` / `integration_doc.md`；分析变更需求 | `frontend_guide`、`backend_guide`、`integration_doc`、`analysis_result` |
| `myagent/backend_developer_agent.py` | 数据库/API 设计、生成 `output/api_spec.json` 与后端文件 | `api_spec`、`files` |
| `myagent/frontend_developer_agent.py` | 生成前端页面文件（文件操作标签 + `{"files": [...]}` JSON 任务） | `files` |

## 业务变换

四个智能体的形态相同：`chat(用户/上游消息)` → 流式 token 逐个回调 `token_deal()` 打印 → 一轮结束回调 `todo()` 解析完整回复。

`todo()` 里一个重要的机制是**文件操作标签**：回复中出现 `<create_file path="...">`、`<update_file ...>`、`<again reason="..." />` 等标签时，交给 `FileOperationHandler.handle_tagged_file_operations()` 执行，然后把操作结果再喂回模型，让它决定下一步。这个「再喂回」就是后续对话轮次。

**后续对话轮数上限（FIX-2026-10-17-01）**：三个开发类智能体都有 `MAX_FOLLOWUP_ROUNDS = 8` 类的自递归上限，通过 `reserve_followup_round()` 申请额度；达上限时向 stderr 打印带轮数的警告并停止递归，递归链自然结束时计数归零。详见[功能文档](docs/feature/followup-round-limit.md)与[修复记录](docs/fix/2026-10-17-todo-followup-round-limit.md)。

## 已知债务

- 三个文件各自复制了一套文件操作方法（`create_file` / `read_file` / `update_file` / `delete_file` / `list_files` / `handle_tagged_file_operations` / `handle_single_operation`），盖住了 `FileOperationHandler` 的同名方法。合并属跨角色改动，需项目管理角色出设计。
- `backend_developer_agent.py` 的 `__main__` 块含硬编码占位密钥 `api_key="sk-"` 与 DashScope 地址，**不得**扩展为真实凭证来源。
- 控制标记 `modify_fe:` / `modify_be:` / `both_modify:` / `need_more_info:` 是纯字符串匹配的跨角色契约，消费者是流程编排；改动必须与「流程编排」角色协调。
