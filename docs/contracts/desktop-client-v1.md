# 契约：桌面客户端 v1

- **状态**：冻结（2026-10-17，客户确认）。
- **不可变**：本文件冻结后不改。任何内容变化（含勘误）出新文件 `desktop-client-v2.md`，旧版保留可读。
- **适用范围**：`desktop-client` 角色与它在 S2/S3/S5 的三个上游交接。
- **工作流**：`docs/workflow.md`。

---

## C1 输出事件（主负责者：平台框架）

**位置**：`ai_agent_factory/agent/baseagent.py`
**消费者**：桌面客户端；三个 CLI 入口是既有消费者，必须继续工作。

### 要求

1. 运行期产生的三类事件可被订阅：
   - `token(text)` — 流式增量文本；
   - `turn_completed(full_text)` — 一次 `chat()` 的完整回复；
   - `error(error_info)` — 运行期错误，`error_info` 至少含异常对象与可读消息。
2. 订阅必须是**公开方法**（具体命名由平台框架定，语义等价于 `set_output_listener(listener)` / `clear_output_listener()`）。
3. **未设置监听器时，现有行为必须逐字不变**：`token_deal` / `todo` 仍照常执行，即仍 `print` 到 stdout。三个入口的回归测试须证明这一点。
4. **设置监听器后**，由平台框架决定是「抑制 `token_deal`/`todo` 的 print」还是「事件与 print 并存」，但**必须**在其 `api-spec.md` 写明选择。若选择抑制，须保证 `token_deal`/`todo` 仍被调用（供子类做副作用），只是不再写 stdout；不得让四个业务智能体的既有实现失效。
5. 回调在**调用线程**内触发（通常是界面层开的工作线程）。平台框架**不得**引入线程、不得依赖 Qt 或任何 GUI 库。
6. 错误不得被吞掉：先发 `error` 事件，再按原有方式抛出或记录。

### 验收证据

- `test/platform-framework/` 中有订阅与不订阅两组用例。
- 不订阅组：断言仍走 `token_deal`/`todo`，stdout 行为与改动前一致。
- 订阅组：断言三类事件按序到达、内容与 `chat()` 返回值一致。
- 三个入口的复测结论（按治理不变式 #6，由项目管理角色协调）。

---

## C2 项目状态快照（主负责者：流程编排）

**位置**：`myagent/system_manager_agent.py`
**消费者**：桌面客户端。

### 要求

1. 公开方法返回**纯数据**字典（语义等价于 `get_snapshot()`）：

```python
{
    "state": {
        "prd_completed": bool,
        "guides_completed": bool,
        "backend_completed": bool,
        "frontend_completed": bool,
        "project_completed": bool,
    },
    "phase": str,
}
```

2. `phase` 的稳定取值（新增取值属契约变更）：

| 取值 | 含义 |
| --- | --- |
| `"idle"` | 尚未开始 |
| `"prd"` | 正在/已完成 PRD 阶段 |
| `"guides"` | 开发指导文档阶段 |
| `"backend"` | 后端开发阶段 |
| `"frontend"` | 前端开发阶段 |
| `"change"` | 变更需求处理中 |
| `"done"` | 项目完成 |

3. 快照必须**无副作用**：不推进 `project_state`、不触发 LLM 请求、不改上下文。
4. 返回的字典**不得**包含 agent 对象、私有字段或其他可变内部引用；调用方修改返回值不得影响内部状态。
5. `report_status()` 的打印行为保持不变（三个入口依赖它输出到终端）。

### 验收证据

- `test/orchestration/` 中覆盖：五个布尔的各种组合、每个 `phase` 取值、调用前后 `project_state` 与上下文均未变化、`report_status()` 输出与改动前一致。

---

## C3 启动与关闭生命周期（主负责者：桌面客户端）

**位置**：`desktop/`（公开启动操作）
**消费者**：装配、根启动方式。

### 要求

1. 暴露一个公开启动操作（语义等价于 `desktop.app.run(...)`），返回**关闭句柄**，句柄带 `shutdown()`。
2. `shutdown()` 必须：中断在跑的管线、回收工作线程、可重复调用不报错。
3. 关闭后进程不得残留线程；返回的句柄不得暴露管线内部对象（不得返回 `SystemManagerAgent` 或其字段）。
4. **import `desktop` 包不得自动启动界面**（不得有 import 期副作用）。
5. 启动失败（如缺依赖、缺环境变量）必须给出可读错误，并完成已创建资源的清理。

### 验收证据

- `test/desktop-client/` 覆盖：启动→关闭、重复关闭、启动失败后的清理、import 无副作用。
- 编排层用替身注入，不得依赖真实 LLM 或网络。

---

## C4 依赖与启动方式（主负责者：装配）

### 要求

1. `requirements.txt` 增加 `PySide6`（给定主版本下限，不锁精确小版本）。
2. 启动方式统一记录为 `python -m desktop`（从项目根目录执行）。
3. 环境变量契约（`api_key` / `model_name` / `base_url`）**不变**；桌面端与 CLI 共用同一份 `.env`。
4. 缺环境变量时，桌面端应给出可读提示，不得把 `None` 直接传给 `OpenAILLM`。

### 验收证据

- 干净环境按 `README.md` 步骤能启动。
- 缺 `api_key` 时的报错是可读的，不是 `NoneType` 堆栈。

---

## 失效规则

| 变更 | 后果 |
| --- | --- |
| C1 变化 | S2 重做；S4 起既有回交作废、重派 |
| C2 变化 | S3 重做；S4 起既有回交作废、重派 |
| C3 变化 | S4 重做；S6 重跑 |
| C4 变化 | S5 重做；S6 重跑 |

契约变更一律出新版本文件并同步更新 `docs/workflow.md`，经客户确认后生效。未受影响的步骤不回滚、不重跑。
