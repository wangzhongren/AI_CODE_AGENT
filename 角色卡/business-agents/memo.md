# 工作备忘录：业务智能体

本文件记录本角色续接工作确实有用的少量线索。不是全局规则、任务状态表或第二份 changelog。权限仍由 `boundary.md` Section 1 决定。

## 已核实的事实

- 2026-10-17：三个开发类智能体的 `todo()` 都有一条「处理完文件操作再调 `self.chat()`」的自递归路径，原本**无轮数上限**（实测 494 轮后 `RecursionError`，异常被 `try/except` 吞掉）。已修：类常量 `MAX_FOLLOWUP_ROUNDS = 8` + `reserve_followup_round()`，达上限向 stderr 打印含轮数警告并停止递归，递归链自然结束时 `followup_round` 归零。见 `docs/fix/2026-10-17-todo-followup-round-limit.md`。
- 2026-10-17：`test/business-agents/test_followup_round_limit.py` 是**该目录第一个测试文件**，10 个用例全过；替身 LLM 用 `ScriptedLLM`，通过「提取提示词里含 `文件操作指令提取器`」区分「提取操作」与「智能体自身对话」两类 `chat()` 调用，并把提取结果设为 `[]` 让三个智能体都走到递归路径且不写盘。

- 2026-10-17：`product_manager_agent.py` 只有 14 行。`system_prompt` 是硬编码中文串，`todo()` 把整段回复存进 `self.prd` 并打印，`max_context=30`。无文件 I/O——PRD 只留在内存里，靠调用方取出。
- 2026-10-17：四个智能体的 `max_context` 与职责：产品经理 30 / 项目经理 50 / 前端 50 / 后端 50（编排器 60）。
- 2026-10-17：三个开发类智能体（项目经理、前端、后端）都在 `__init__` 里把 `FileOperationHandler.get_file_operation_prompt()` 拼进自己的 `system_prompt`，并各自 `self.output_dir = "output"`。
- 2026-10-17：`project_manager_agent.py::todo()` 会从回复里识别控制标记 `modify_fe:` / `modify_be:` / `both_modify:` / `need_more_info:`，并把结果放进 `self.analysis_result`；随后写入 `output/` 下的 `frontend_guide.md`、`backend_guide.md`、`integration_doc.md`。
- 2026-10-17：`backend_developer_agent.py` 的 `__main__` 块用硬编码 `api_key="sk-"`、DashScope `base_url`、模型 `qwen3-max` 直连真实 API——**这是占位符，不是可用凭证**。不要照着它扩展。
- 2026-10-17：`frontend_developer_agent.py` 有 `handle_json_task()`，吃 `{"files":[{filename, content}]}` 形状的输入；`backend_developer_agent.py` 有 `extract_api_spec_from_response()` 与 `ensure_api_spec_file()` 两个 `api_spec` 专门方法。

## 容易踩坑的位置

- 2026-10-17：`myagent/frontend_developer_agent.py` 本次改动后整文件换行符变成 LF（原仓库是 CRLF）；`git diff` 因此会显示整文件变化。`core.autocrlf` 已开启（git 提示「LF will be replaced by CRLF」），`git add` 时会归一化回 CRLF，实际内容与提示词未变。若下次要动这个文件，注意别再让 diff 变噪声。

- **三个文件各自定义了一套文件操作方法**（`create_file` / `read_file` / `update_file` / `delete_file` / `list_files` / `handle_tagged_file_operations` / `handle_single_operation`），名字与 `FileOperationHandler` 完全相同，会盖住实例上的方法。看到「调用了 handler 的方法」时，实际跑的往往是本文件里那一份。改之前先确认走哪条路径。
- **控制标记是跨角色契约**。`project_manager_agent.py` 输出的 `modify_fe:` 等标记由 `system_manager_agent.py` 解析。改动标记拼写、加空格、换行位置都会让调度静默失配——不会报错，只是不生效。改前必须与「流程编排」角色协调。
- **提示词即接口**。`system_prompt` 改了，模型输出格式就可能变，连带影响标记解析与 `api_spec` 抽取。改提示词要同时检查依赖它输出格式的解析逻辑。
- `handle_json_task` 的入参是 `{"files": [...]}`；`self.files` 是累积列表，注意是否需要在多次任务之间清空——**待核实**。

## 待核实的问题

- `self.files` 在多次 `chat()` 之间是否累积，调用方（入口/编排）是否依赖它只含本轮文件。这是潜在的重复写入来源。
- 三个副本与 `FileOperationHandler` 实际行为差异有多大（越界校验是否一致、错误处理是否一致）。属跨角色调查，需项目管理角色安排。
- 「待核实」：`project_manager_agent.py` 从文件重新加载指导文档（`load_guides_from_files`）与 `todo()` 内直接写属性，两条路径是否会互相覆盖。

## 下次从哪继续

1. 先读 `boundary.md` Section 1，确认当前授权范围未变。
2. 要改控制标记或 `api_spec` 结构，先查 `角色卡/orchestration/` 与 `角色卡/assembly/` 的依赖说明。
3. 消除文件操作重复实现是跨角色任务，先提交项目管理角色。
4. 项目管理角色的 `docs/project-rules.md` 尚未建立；建立后本节应链接并核对相关条目。
