# 工作备忘录：流程编排

本文件记录本角色续接工作确实有用的少量线索。不是全局规则、任务状态表或第二份 changelog。权限仍由 `boundary.md` Section 1 决定。

## 已核实的事实

- 2026-10-17：`SystemManagerAgent.__init__(basellm, agents)` 接收注入的 `agents` 字典，键为 `pm` / `pj` / `fe` / `be`。本文件**不** import 四个具体智能体类——这个解耦要在后续修改中保持。
- 2026-10-17：`project_state` 有 5 个布尔标志：`prd_completed`、`guides_completed`、`backend_completed`、`frontend_completed`、`project_completed`。三个入口文件只读前四个来判断「初始开发是否完成」。
- 2026-10-17：`todo()` 把 LLM 回复交给 `make_decision()`。可识别的分支词包括 `ask_pm` / `ask_pj` / `ask_fe` / `ask_be` / `analyze_change` / `modify_fe` / `modify_be` / `modify_both` / `status` / `next` / `done`。
- 2026-10-17：`max_context=60`，是四个智能体中最高的——因为要承载整条流程的对话历史。
- 2026-10-17：`report_status()` 读 `output/` 下的 `frontend_guide.md`、`backend_guide.json`、`backend_guide.md`、`api_spec.json`。**同时存在 `.json` 与 `.md` 两种后端指导文档路径**，需确认真实来源。
- 2026-10-17：入口文件（`main3.py` / `enhanced_main.py`）自己也做了一次「初始还是变更」的判断，与本角色状态机是**两处独立逻辑**。改一边要考虑另一边。

## 容易踩坑的位置

- **子串匹配会误触发**。`make_decision()` 判断的是关键词是否出现在文本里，不是结构化字段。LLM 回复里提到「status」这类词就可能走错分支。加分支时留意判定顺序——先匹配到的先赢。
- **控制标记是双向契约**。`modify_fe:` / `modify_be:` / `both_modify:` 由「业务智能体」角色的 `project_manager_agent.py` 产生，本角色解析。改任何一边都要协调另一边，且不会报错，只会静默不生效。
- **入口也有一份状态判断**。`enhanced_main.py` 会自己检查 `project_state` 四个标志来判断要不要跑完整流程。状态推进逻辑改动会让入口行为跟着变。
- 本角色**不持有业务逻辑**。遇到「PRD 生成得不对」这类问题，归「业务智能体」角色；本角色只该改顺序、分支、状态。

## 待核实的问题

- `output/backend_guide.json` 与 `output/backend_guide.md` 谁权威，另一个是否遗留。影响 `report_status()` 的读取路径。
- 现有分支的判定顺序，以及「都不匹配」时的兜底行为。
- `handle_change_request()` 如何决定分派给前端、后端还是两边——是解析项目经理智能体的标记，还是另有一套判断。

## 下次从哪继续

1. 先读 `boundary.md` Section 1，确认当前授权范围未变。
2. 要改调度词汇或 `project_state` 字段，先查 `角色卡/business-agents/` 与 `角色卡/assembly/` 的依赖说明。
3. 「决策分派靠子串匹配」的加固属于本角色范围内的改进，但需先出方案经项目管理角色评审。
4. 项目管理角色的 `docs/project-rules.md` 尚未建立；建立后本节应链接并核对相关条目。
