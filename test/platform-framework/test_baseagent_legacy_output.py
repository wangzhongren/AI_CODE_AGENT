"""不订阅组：未设置输出监听器时，既有行为必须逐字不变。

对应契约 C1 第 3 条：``token_deal`` / ``todo`` 仍照常执行、仍 print 到 stdout。
这些用例先在改动前的 ``baseagent.py`` 上跑通，作为「改动前」基线；
改动后再跑一次，两次结果一致才算回归通过。
"""

from fakes import RecordingAgent, ScriptedLLM


def test_unsubscribed_prints_and_callbacks_unchanged(capsys):
    """不订阅时的 stdout 与回调调用顺序逐字不变。"""
    agent = RecordingAgent(ScriptedLLM([["你", "好", "！"]]))

    reply = agent.chat("打个招呼")

    out = capsys.readouterr().out
    assert out == "你好！[todo]你好！\n"
    assert agent.token_calls == ["你", "好", "！"]
    assert agent.todo_calls == ["你好！"]
    assert reply == "你好！"


def test_unsubscribed_token_deal_order_follows_stream(capsys):
    """token_deal 必须按模型产出的顺序、逐个被调用。"""
    tokens = ["a", "b", "c", "d"]
    agent = RecordingAgent(ScriptedLLM([tokens]))

    reply = agent.chat("随便说点什么")

    capsys.readouterr()
    assert agent.token_calls == tokens
    assert agent.todo_calls == ["abcd"]
    assert reply == "abcd"


def test_unsubscribed_multi_turn_keeps_printing(capsys):
    """连续两轮对话，每轮都走 token_deal + todo，stdout 按轮累加。"""
    agent = RecordingAgent(ScriptedLLM([["x"], ["y"]]))

    first = agent.chat("第一轮")
    second = agent.chat("第二轮")

    out = capsys.readouterr().out
    assert out == "x[todo]x\ny[todo]y\n"
    assert first == "x"
    assert second == "y"
    assert agent.token_calls == ["x", "y"]
    assert agent.todo_calls == ["x", "y"]
