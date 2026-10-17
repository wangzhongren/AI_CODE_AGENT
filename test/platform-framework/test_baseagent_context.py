"""``BaseAgent`` 层内契约测试：上下文裁剪边界。

裁剪规则（改动前后一致）：当 ``len(context) > max_context`` 时，
保留 ``[系统提示] + 最近 max_context 条``。恰好等于 ``max_context`` 时不裁剪。
本文件把这条既有规则固化成测试，避免以后改契约时无声破坏。
"""

from fakes import RecordingAgent, ScriptedLLM


def test_context_equal_to_max_context_is_not_clipped():
    """len(context) == max_context 时不裁剪，系统提示仍在 index 0。"""
    llm = ScriptedLLM([["回复"]])
    agent = RecordingAgent(llm, max_context=3)

    agent.chat("需求")

    context = agent.get_context()
    assert len(context) == 3
    assert context[0] == {"role": "system", "content": "你是一个测试用智能体。"}
    assert context[1] == {"role": "user", "content": "需求"}
    assert context[2] == {"role": "assistant", "content": "回复"}


def test_context_over_max_context_keeps_system_prompt_and_recent_messages():
    """超出后裁剪为 [系统提示] + 最近 max_context 条，长度变为 max_context + 1。"""
    llm = ScriptedLLM([["第一轮回复"], ["第二轮回复"]])
    agent = RecordingAgent(llm, max_context=3)

    agent.chat("第一问")
    agent.chat("第二问")

    context = agent.get_context()
    assert len(context) == 4
    assert [message["role"] for message in context] == [
        "system",
        "assistant",
        "user",
        "assistant",
    ]
    assert context[0]["content"] == "你是一个测试用智能体。"
    assert context[1]["content"] == "第一轮回复"
    assert context[2]["content"] == "第二问"
    assert context[3]["content"] == "第二轮回复"


def test_reset_context_restores_system_prompt_only():
    """``reset_context`` 后只剩系统提示，后续对话继续正常工作。"""
    llm = ScriptedLLM([["旧回复"], ["新回复"]])
    agent = RecordingAgent(llm, max_context=10)

    agent.chat("旧问题")
    agent.reset_context()
    reply = agent.chat("新问题")

    context = agent.get_context()
    assert reply == "新回复"
    assert len(context) == 3
    assert context[0]["role"] == "system"
    assert context[1] == {"role": "user", "content": "新问题"}
    assert context[2] == {"role": "assistant", "content": "新回复"}
