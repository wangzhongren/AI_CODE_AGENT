# 功能导航：业务智能体

本角色负责的系统功能，以及代码与文档的对应关系。新增或删除功能时同步更新本表。

| 功能 | 说明 | 代码位置 | 稳定文档 |
| --- | --- | --- | --- |
| 生成产品需求文档 | 由用户需求生成 PRD，结果放在 `self.prd` | `myagent/product_manager_agent.py::todo` | 待补 |
| 生成前后端开发指导文档 | 由 PRD 生成 `frontend_guide.md` / `backend_guide.md` / `integration_doc.md` | `myagent/project_manager_agent.py::todo` | 待补 |
| 分析变更需求 | 识别 `modify_fe:` / `modify_be:` / `both_modify:` / `need_more_info:`，写入 `self.analysis_result`（消费者：流程编排） | `myagent/project_manager_agent.py::todo` | 待补 |
| 生成后端接口规格 | 抽取并落盘 `output/api_spec.json`（`self.api_spec`），消费者：前端智能体、流程编排、入口文件 | `myagent/backend_developer_agent.py::extract_api_spec_from_response` / `ensure_api_spec_file` | 待补 |
| 生成前端页面文件 | 处理文件操作标签与 `{"files": [...]}` JSON 任务，落地页面文件（`self.files`） | `myagent/frontend_developer_agent.py::todo` / `handle_json_task` | 待补 |
| 后续对话轮数上限 | `todo()` 自递归的硬上限与可见警告，防崩溃、防烧 API 额度 | 三个开发类智能体的 `MAX_FOLLOWUP_ROUNDS` / `reserve_followup_round()` | [followup-round-limit.md](docs/feature/followup-round-limit.md) |
