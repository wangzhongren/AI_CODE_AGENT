# 变更历史：业务智能体

## 2026-10-17 — FIX-2026-10-17-01：`todo()` 自递归加上限，堵住崩溃与额度消耗

- **改了什么**：`BackendDeveloperAgent` / `FrontendDeveloperAgent` / `ProjectManagerAgent` 在 `todo()` 里「处理完文件操作后再调一次 `self.chat()`」的递归，现在有明确上限 `MAX_FOLLOWUP_ROUNDS = 8`。达上限时向 stderr 打印带轮数的警告并停止递归，不再静默、也不再继续递归；递归链自然结束时计数归零。
- **为什么**：模型连续返回文件操作标签时该循环无上限，实测 494 轮后 `RecursionError`，且被 `todo()` 自身 `try/except` 吞掉；真实环境里持续消耗 API 额度。
- **行为变化**：只有「真的跑满 8 轮」这条原本会崩溃的路径新增一条 stderr 警告；一到两轮结束的正常流程输出与调用序列不变。
- **契约影响**：`system_prompt`、控制标记 `modify_fe:` 等、`api_spec` 抽取、`self.files`、`handle_json_task` 入参形状均未改动。
- **文档**：[修复记录](docs/fix/2026-10-17-todo-followup-round-limit.md)、[功能说明](docs/feature/followup-round-limit.md)
- **测试**：`test/business-agents/test_followup_round_limit.py`（新建，10 个用例，替身 LLM），`pytest test/business-agents -q` → 10 passed。
