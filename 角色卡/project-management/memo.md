# 工作备忘录：项目管理

本文件记录本角色续接工作确实有用的少量线索。不是全局规则、任务状态表或第二份 changelog。权限仍由 `boundary.md` Section 1 决定。

## 已核实的事实

- 2026-10-17：bootstrap 由治理角色完成，产出七个角色卡与边界文档。`docs/architecture.md`、`docs/architecture/shared-components.md`、`docs/project-rules.md`、`feature-map.md`、各 `changelog.md`/`functional-description.md`/`api-spec.md` 均**尚未建立**，属本角色被接受后的工作。
- 2026-10-17：`common/shared/` 目录已存在但为空。
- 2026-10-17：项目无任何测试。`test/<角色>/` 目录已按角色建立但为空。
- 2026-10-17：项目无 `src/` 目录。五层职责映射到现有路径如下（写架构文档时用）：接口＝三个 `main*.py`；Pipeline＝`myagent/system_manager_agent.py`；Service＝`myagent/` 四个业务智能体；Provider＝`ai_agent_factory/llms/` 与 `ai_agent_factory/utils/file_operation_handler.py`；框架支持＝`ai_agent_factory/agent/baseagent.py`。
- 2026-10-17：本角色的应用代码范围只有 `common/shared/`；`README.md`、`DEVELOPMENT_GUIDE.md`、`license`、`.gitignore` 归本角色维护，属文档与项目级配置，不是应用代码。
- 2026-10-17：`.gitignore` 补入 `.venv/`（项目内虚拟环境，桌面客户端依赖）与 `temp/`（各角色草稿区）。`__pycache__/`、`*.pyc` 原本已有，未重复添加。已用 `git check-ignore` 验证三条规则命中，并确认 `README.md`、`docs/`、`common/shared/`、`test/`、`output/`、`requirements.txt` 未被误伤。

## 已识别的跨角色问题（按处理顺序排列的建议）

1. **文件操作逻辑三份重复**。`project_manager_agent.py` / `frontend_developer_agent.py` / `backend_developer_agent.py`（「业务智能体」）各自重复实现了 `FileOperationHandler`（「文件产出」）的整套方法。这是本项目最大的一处结构问题，也是最典型的跨角色集成设计任务。
2. **坏导入**。`ai_agent_factory/utils/file_operation_handler.py` 顶层 `from ai_agent_factory.llms.base_llm_openai import BaseLLM`，而该模块没有 `BaseLLM`。仅属「文件产出」角色范围内的单文件修复，不需要跨角色设计。
3. **调度词汇双向契约无文档**。「业务智能体」输出 `modify_fe:` 等标记，「流程编排」解析。双方各自维护，改一边静默失配。
4. **入口穿透 `BaseAgent` 私有字段**。`main.py`/`main3.py`（「装配」）读 `_BaseAgent__context`（「平台框架」）。需两者协调：平台框架提供公开方法，装配改用之。
5. **硬编码占位密钥**。`backend_developer_agent.py` 的 `__main__` 块含 `api_key="sk-"`。属「业务智能体」文件。

## 容易踩坑的位置

- **不要因为要写架构文档就去改被引用的文件**。白名单之外的路径一律只读。
- **不要凭 bootstrap 的观察编造项目工程规则**。`docs/project-rules.md` 的每条规则都要基于已确认的项目事实；未确认的约束如实标注。
- **协调权不等于实施批准**。本角色自己的共享代码改动同样要走方案评审与客户确认。
- 七个角色在本项目里是**维护角色**，与 `myagent/` 里那五个**业务智能体**（产品经理/项目经理/前端/后端/系统管理者）是两回事。写文档时容易混淆，措辞要明确区分。

## 待核实的问题

- 「业务智能体」的三个文件操作副本与 `FileOperationHandler` 的行为差异到底多大——是合并成一处，还是保留但统一契约。需要各所有者先给评估。
- `output/backend_guide.json` 与 `output/backend_guide.md` 哪个权威。
- 三个入口是否都需保留（属「装配」角色范围内的决定）。

## 下次从哪继续

1. 本角色被接受后，先建立 `docs/architecture.md`（含 Mermaid 角色协作图）与 `docs/project-rules.md`。
2. 再逐个安排各角色建立自己的 `feature-map.md` 与 `docs/feature/<feature-id>.md`。
3. 跨角色问题按上面「已知的跨角色问题」顺序处理，先出设计再派发。
