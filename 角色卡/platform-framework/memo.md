# 工作备忘录：平台框架

本文件记录本角色续接工作确实有用的少量线索。不是全局规则、任务状态表或第二份 changelog。权限仍由 `boundary.md` Section 1 决定。

## 已核实的事实

- 2026-10-17：**契约 C1 已实现并验收（S2）**。`BaseAgent` 新增 `AgentOutputListener`（`on_token` / `on_turn_completed` / `on_error`）、`AgentOutputError`（`exception` + `message`）、`set_output_listener()` / `clear_output_listener()`。完整规格见 `api-spec.md` §2。
- 2026-10-17：C1 的两个关键取舍，改动前先读这两条，别推翻：
  1. **订阅后事件与 print 并存**（不抑制 `token_deal` / `todo` 的 stdout）。原因是四个智能体的回调本体就是 `print`，抑制只能改写进程级 `sys.stdout`，而桌面端在工作线程跑管线——那是跨线程副作用。契约 C1 第 4 条允许二选一，理由写在 `api-spec.md` §2.3。
  2. **事件先发、既有回调后走**（`token` → `token_deal`；`turn_completed` → `todo`；`error` → `raise`）。`turn_completed` 放在 `todo` 之前，是为了让「`todo` 里再 `chat()`」的嵌套场景事件顺序不交叉。
- 2026-10-17：`chat()` 的 `except Exception` 在未订阅监听器时**只做 `raise`，不打印**。这是刻意的：多打一行就会破坏「未订阅时 stdout 逐字不变」。错误由三个入口自己打印。
- 2026-10-17：`chat()` 的上下文裁剪规则是 `[system] + context[-max_context:]`，仅当 `len(context) > max_context` 时触发，裁剪后长度是 `max_context + 1`。已由 `test/platform-framework/test_baseagent_context.py` 固化，**改规则前先看那组用例**。
- 2026-10-17：订阅是**实例级**的。`SystemManagerAgent` 会把活派给 `agents['pm'/'pj'/'fe'/'be']`，那些是独立对象；桌面端只订阅 manager 的话，拿不到子智能体的输出。
- 2026-10-17：`BaseAgent.__context` 与 `__output_listener` 都是名称改写私有属性（`_BaseAgent__context` / `_BaseAgent__output_listener`）。`main.py` 与 `main3.py` 现穿透 `_BaseAgent__context` 取内容——属装配角色调用方的问题，本角色应收紧封装（例如 `last_reply()`），**不是**为此放出公开字段。
- 2026-10-17：`chat()` 中 `if self.token_deal:` 与 `if self.todo:` 恒为真（抽象方法绑定后必存在）。是冗余判断，但 S2 刻意保留未动：改动面越小，越能保证「未订阅时行为逐字不变」。
- 2026-10-17：各业务智能体的 `max_context`：产品经理 30，项目经理/前端/后端 50，系统管理者 60。默认 20。
- 2026-10-17：`test/orchestration/` 是流程编排角色的套件，它驱动真实的 `SystemManagerAgent` 经过 `chat()`，可作为本角色改动的真实子类回归旁证（`python -m pytest test -q` 全绿）。

## 容易踩坑的位置

- `ai_agent_factory/llms/openai`：0 字节空文件，无扩展名。**不要**往里写内容，也不要 import。删除需客户确认。
- `file_operation_handler.py` 顶层写着 `from ai_agent_factory.llms.base_llm_openai import BaseLLM`——`base_llm_openai.py` 里没有 `BaseLLM`。该名字只用作类型标注。这是「文件产出」角色的文件；本角色若调整 `BaseLLM` 的导出位置，会直接影响这个已存在的坏引用。
- 监听器自身抛出的异常**不被捕获**，会打断当前 `chat()`。这是有意为之（不隐藏错误），别加「静默忽略」的兜底。
- `temp/platform-framework/` 是草稿区，不是交付物；被门禁拒绝的写入没有产物可存，不要往那里塞。

## 待核实的问题

- 隐式命名空间包（`agent/`、`llms/` 下无 `__init__.py`）在目标 Python 版本与打包方式下是否可靠。需客户确认是否补齐。
- `OpenAILLM.chat()` 把 `APIError` 包装成通用 `Exception`，调用方无法区分认证失败、限流与网络错误。是否引入分层异常需客户决定。
- `BaseLLM.__init__` 要求三个参数全位置必填；三个入口在环境变量缺失时会传 `None` 而不是走默认值，`None` 时 OpenAI SDK 的实际行为仍未核实。

## 下次从哪继续

1. 先读 `boundary.md` Section 1，确认授权范围未变（2026-10-17 已补入角色根目录文档面与 `temp/`）。
2. 若 S4 桌面端接入后发现事件不够用（例如需要区分「哪一轮」的 id、或需要 `turn_started`），那是**契约变更**：出 `docs/contracts/desktop-client-v2.md` 并走客户确认，不要直接改 C1 语义。
3. 若要动 `BaseAgent` / `BaseLLM` 的对外行为，先查 `角色卡/business-agents/` 与 `角色卡/assembly/` 的依赖，按共享契约变更流程走。
