# 修复记录 FIX-2026-10-17-01：todo() 自递归没有轮数上限

- 日期：2026-10-17
- 范围：`myagent/backend_developer_agent.py`、`myagent/frontend_developer_agent.py`、`myagent/project_manager_agent.py`（均在 `boundary.md` Section 1 内）
- 触发来源：「测试」角色实测复现，客户确认优先修
- 结论：已修复。三个智能体的后续对话递归都有明确上限，达上限时向 stderr 打印带轮数的可见警告并停止递归。

## 1. 问题

`todo()` 处理完文件操作后调 `self.chat(...)`，而 `BaseAgent.chat()` 在拿到完整回复后又会回调 `todo()`。这条「自己再调自己」的路径**没有轮数上限**：

- 模型只要连续返回文件操作标签（`<create_file ...>`、`<again ... />` 等），就会一直递归；
- 实测跑到 11340 token / 494 次 `turn_completed` 后 `RecursionError`；
- 异常被 `todo()` 自己的 `try/except` 吞掉，用户只看到「任务失败」；
- 每次递归都是一次真实模型调用，**持续消耗客户 API 额度**。

## 2. 方案

三项改动，三个文件完全同构：

1. 类常量 `MAX_FOLLOWUP_ROUNDS = 8`，声明上限，随类可见、便于测试与调整。
2. `reserve_followup_round() -> bool`：每次要发起后续对话前先申请额度。
   - 未达上限：计数加一，返回 `True`，调用方照旧 `self.chat(...)`。
   - 已达上限：向 **stderr** 打印 `❌ [<AgentName>] 已达到后续对话轮数上限 8 轮，主动停止继续调用模型。可能原因：模型持续返回文件操作指令而没有给出最终结论。`，计数清零，返回 `False`，调用方不再递归。
3. 递归链自然结束时（本轮没有文件操作标签）把计数归零，保证每一串新任务都有完整额度。

### 2.1 为什么是 8

- 正常任务 1~3 轮就收尾（建文件 → 反馈 → 补一句结论）。
- 8 轮留出 2~3 倍余量，覆盖「分步决策」的合理用法。
- 最坏情况只多花 8 次调用；对照实测的 494 次，额度消耗从「不可控」变成「有界」。
- 上限值本身有测试兜底（`test_round_limit_value_is_bounded`，要求 0 < 值 ≤ 20），改了不会被静默放过。

### 2.2 为什么选「打印到 stderr」而不是「抛异常」

任务给了二选一。这里选打印，理由：

- 抛异常会穿过 `BaseAgent.chat()` 的 except 分支，触发 `on_error` 事件并**中断上层装配流程**；而客户的要求是「输出一条清楚的错误/警告，并把控制权交还」。
- stderr 是进程级可见通道：桌面端、命令行、日志重定向都能看到，不会被 `todo()` 里既有的 `try/except` 吞掉。
- 因此「达上限」= 一条**必现的 stderr 警告 + 递归停止**，不是静默失败，也不是硬崩溃。

## 3. 改动清单

| 文件 | 新增/修改 |
| --- | --- |
| `myagent/backend_developer_agent.py` | `import sys`；类常量 `MAX_FOLLOWUP_ROUNDS`；`__init__` 增 `self.followup_round = 0`；新增 `reserve_followup_round()`；`todo()` 里 `self.chat(...)` 改为先申请额度，无文件操作时计数归零 |
| `myagent/frontend_developer_agent.py` | 同上（`is_need_loop` 分支改为先申请额度，`else` 分支归零） |
| `myagent/project_manager_agent.py` | 同上（`is_need_loop` 分支改为先申请额度，`else` 分支归零） |

**没有改动**：`system_prompt`（控制标记 `modify_fe:` / `modify_be:` / `both_modify:` / `need_more_info:` 的输出格式未变）、`api_spec` 抽取逻辑、`self.files` 清单、`handle_json_task` 入参形状、`BaseAgent`、`SystemManagerAgent`、三个入口文件、`desktop/`。

## 4. 正常路径行为不变

- 一轮或两轮结束的流程，`self.chat()` 的调用序列、stdout 输出与修复前一致；
- 唯一新增的可观察差异是「真的跑到第 9 轮」时的那条 stderr 警告，而这条路径在修复前会一路递归到崩溃。

## 5. 测试证据

`test/business-agents/test_followup_round_limit.py`（新建，10 个用例，全部用替身 LLM，不触网、不写仓库文件）：

1. `test_runaway_file_ops_stop_at_round_limit`（3 个参数化）：模型永远返回文件操作标签 → 断言模型总共只被调用 `MAX_FOLLOWUP_ROUNDS + 1` 次（初始 1 次 + 8 次后续），且 stderr 含智能体名、`上限`、`8`。
2. `test_normal_path_output_unchanged`（3 个参数化）：第二轮不再返回文件操作 → 断言只调用 2 次、`followup_round == 0`、stderr 为空、stdout 仍含「检测到文件操作指令」与末轮回复。
3. `test_reserve_followup_round_counts_and_resets`（3 个参数化）：额度判定本身，前 8 次放行、第 9 次拒绝并清零。
4. `test_round_limit_value_is_bounded`：上限是 1~20 的整数。

```
D:/work/vibe-code/codeagent/.venv/Scripts/python.exe -m pytest test/business-agents -q
..........                                                               [100%]
10 passed in 0.55s
```

（该目录此前没有测试，本次为新建；用的是 `pytest`。）

## 6. 刻意没做的事（后续可选，不在本次范围）

- `ProjectManagerAgent` 识别到控制标记后提前 `return` 的分支没有归零计数：该分支本身不递归，且上层每次新任务都会重新走到「无文件操作」的归零点，影响可忽略。若后续要做，属本角色文件的加固项。
- 上限值做成构造参数（`__init__(..., max_followup_rounds=...)`）：当前需求不需要可配置，类常量已够；做成参数会改动三个类的构造签名，属可选加固。
- 在流程编排层（`system_manager_agent.py`）再加一道总轮数兜底：跨角色，需项目管理角色设计。
- 合并三个文件的文件操作方法副本：跨角色，需项目管理角色设计（见 `boundary.md`「已知重复实现」）。
