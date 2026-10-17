# 接口说明：业务智能体

## 实际导出（供上层装配使用）

| 类 | 位置 | 构造 | 主要入口 |
| --- | --- | --- | --- |
| `ProductManagerAgent` | `myagent/product_manager_agent.py` | `(basellm)` | `chat(需求)`；结果在 `prd` |
| `ProjectManagerAgent` | `myagent/project_manager_agent.py` | `(basellm)` | `chat(prd 或变更需求)`；结果在 `frontend_guide` / `backend_guide` / `integration_doc` / `analysis_result` |
| `BackendDeveloperAgent` | `myagent/backend_developer_agent.py` | `(basellm)` | `chat(后端指导文档)`；结果在 `api_spec` / `files` / `output/` |
| `FrontendDeveloperAgent` | `myagent/frontend_developer_agent.py` | `(basellm)` | `chat(前端指导文档)`、`handle_json_task(token)`；结果在 `files` / `output/` |

三者都继承 `BaseAgent`，因此同时具备 `reset_context()`、`get_context()`、`set_output_listener()` / `clear_output_listener()`（契约 C1 事件通道）。

## 对外新增/变更的成员（FIX-2026-10-17-01）

| 成员 | 类型 | 语义 |
| --- | --- | --- |
| `MAX_FOLLOWUP_ROUNDS` | 类常量，三个开发类智能体各一份，值 `8` | `todo()` 里「再调一次 `self.chat()`」的最大轮数 |
| `reserve_followup_round() -> bool` | 实例方法 | `True` = 允许再发起一轮（计数 +1）；`False` = 已达上限，已向 stderr 打印含轮数的警告、计数清零，调用方必须停止递归 |
| `followup_round` | 实例属性 | 当前这串任务已用掉的后轮数；递归链自然结束（本轮无文件操作标签）时归零 |

## 依赖

- 向下：`ai_agent_factory.agent.baseagent.BaseAgent`、`ai_agent_factory.llms.base_llm.BaseLLM`、`ai_agent_factory.utils.file_operation_handler.FileOperationHandler`。
- **不依赖**：三个入口文件、`myagent/system_manager_agent.py`（流程编排属上层）。
- 本角色不写 `common/shared/`，不 import 其他角色的私有 `common/` 代码。

## 设计契约与符合性

| 契约 | 位置 | 本次（FIX-2026-10-17-01）是否改动 |
| --- | --- | --- |
| `api_spec` 结构 | `backend_developer_agent.py::extract_api_spec_from_response` / `ensure_api_spec_file` | 未改动 |
| 控制标记 `modify_fe:` / `modify_be:` / `both_modify:` / `need_more_info:` | `project_manager_agent.py::todo` 输出 → 流程编排解析 | 未改动（`system_prompt` 与匹配逻辑都未动） |
| 生成文件清单 `self.files` | 前端/后端智能体 → 上层装配 | 未改动 |
| `handle_json_task` 入参形状 `{"files": [...]}` | `frontend_developer_agent.py` | 未改动 |
| 智能体状态属性 `prd` / `*_guide` / `integration_doc` / `api_spec` / `analysis_result` | 各 `todo()` 写入 → 流程编排与入口读取 | 未改动 |
| 事件通道 C1（`AgentOutputListener`） | `BaseAgent` | 未改动；达上限走 stderr，不额外发 `on_error` 事件（避免被上层当成硬失败中断装配） |

偏差说明：达上限时**不抛异常**，改为 stderr 警告 + 停止递归。理由见[修复记录第 2.2 节](docs/fix/2026-10-17-todo-followup-round-limit.md)。

## 测试证据

- 测试目录：`test/business-agents/`（本角色自有，`boundary.md` Section 1 覆盖）。
- 文件：`test/business-agents/test_followup_round_limit.py` — 10 个用例，全部用替身 LLM（`ScriptedLLM`），不触网、不写仓库文件。
- 覆盖点：控制标记不受影响（未改动，靠既有行为保证）；`api_spec` 抽取与 `handle_json_task` 的输入形状校验仍由既有实现承担**（待补：本角色尚未为这两项建用例，属后续加固）**；本次新增覆盖递归上限、可见警告、正常路径不变、上限值边界。
- 最近一次真实运行：

```
D:/work/vibe-code/codeagent/.venv/Scripts/python.exe -m pytest test/business-agents -q
..........                                                               [100%]
10 passed in 0.54s
```

## 装配说明

上层按 `basellm` 逐个构造，各自订阅需要的输出监听器（子智能体是独立实例，需各自订阅），然后 `chat()` 驱动。文件产物落在进程工作目录的 `output/`（可用实例属性 `output_dir` 改写，`self.fo.output_dir` 需同步）。
