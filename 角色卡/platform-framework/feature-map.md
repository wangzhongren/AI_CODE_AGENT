# 功能导航：平台框架

本角色提供的底层能力。每一项给出名称、一句话用途、状态与文档链接。

| 功能 | 一句话用途 | 状态 | 文档 |
| --- | --- | --- | --- |
| 智能体对话上下文管理 | 维护 `[系统提示] + 历史消息`，保证系统提示始终在首位，并在超出 `max_context` 时只保留最近若干条 | 已实现 | `api-spec.md` §1.1、`test/platform-framework/test_baseagent_context.py` |
| 流式 token 回调分发（既有通道） | `chat()` 把每个 token 交给子类的 `token_deal()`、把完整回复交给 `todo()` | 已实现 | `api-spec.md` §2.7、`test/platform-framework/test_baseagent_legacy_output.py` |
| 流式输出事件订阅（契约 C1） | 让界面层订阅 `token` / `turn_completed` / `error` 三类事件，不用读 stdout 就能渲染输出 | 已实现（rev 1，2026-10-17） | `api-spec.md` §2、`test/platform-framework/test_baseagent_output_events.py` |
| LLM 供应商契约 `BaseLLM` | 定义模型侧唯一契约：`chat(context) -> Iterable[str]` | 已实现 | `api-spec.md` §1.2 |
| OpenAI 兼容流式实现 `OpenAILLM` | 按 `BaseLLM` 契约调用 OpenAI 兼容接口并逐 token 产出 | 已实现（含已知缺陷：异常被统一包装成 `Exception`，见 `boundary.md`） | `api-spec.md` §1.3 |

## 文档索引

| 文档 | 内容 |
| --- | --- |
| `api-spec.md` | 导出、依赖、契约 C1 实现方式与取舍、符合性、测试证据 |
| `memo.md` | 带日期的续接线索 |
| `boundary.md` | Section 1 改动白名单（唯一授权来源） |

## 上游契约

- `docs/contracts/desktop-client-v1.md` — C1 输出事件（主负责者：平台框架）
- `docs/workflow.md` — S2 步骤与验收口径
