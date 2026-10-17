"""订阅组：设置输出监听器后，三类事件按序到达。

对应契约 C1 第 1、4、5、6 条。本文件同时固化两条实现选择：

1. 订阅后**事件与 print 并存**（不抑制 ``token_deal`` / ``todo`` 的 stdout 输出），
   理由见 ``角色卡/platform-framework/api-spec.md``。
2. ``turn_completed`` 在完整回复拼装完成后、``todo`` 调用之前发出，
   因此若 ``todo`` 内部再次 ``chat()``（``myagent/`` 里确有此用法），
   事件顺序仍是「先 A 轮完成，再 B 轮的 token 与完成」，不会交叉。
"""

import pathlib
import threading

import pytest

from ai_agent_factory.agent.baseagent import AgentOutputError, AgentOutputListener
from fakes import (
    FailingLLM,
    MidStreamFailingLLM,
    RecordingAgent,
    ScriptedLLM,
)


class RecordingListener(AgentOutputListener):
    """把事件按到达顺序记录下来的监听器。"""

    def __init__(self):
        self.events = []
        self.thread_ids = []

    def on_token(self, text):
        self.events.append(("token", text))
        self.thread_ids.append(threading.get_ident())

    def on_turn_completed(self, full_text):
        self.events.append(("turn_completed", full_text))
        self.thread_ids.append(threading.get_ident())

    def on_error(self, error_info):
        self.events.append(("error", error_info))
        self.thread_ids.append(threading.get_ident())


class TokenDealBoomAgent(RecordingAgent):
    """在第 2 个 token 上失败的智能体，模拟子类回调自身出错。"""

    def token_deal(self, result):
        super().token_deal(result)
        if len(self.token_calls) == 2:
            raise ValueError("token_deal 炸了")


class TodoBoomAgent(RecordingAgent):
    """``todo`` 里失败的智能体。"""

    def todo(self, token):
        super().todo(token)
        raise ValueError("todo 炸了")


class TodoRecursingAgent(RecordingAgent):
    """``todo`` 里再次 ``chat()`` 的智能体，形状与项目/后端/前端智能体一致。"""

    def __init__(self, basellm, max_context=20):
        super().__init__(basellm, max_context)
        self.__has_recursed = False

    def todo(self, token):
        super().todo(token)
        if not self.__has_recursed:
            self.__has_recursed = True
            self.chat("续问")


def test_events_arrive_in_order_and_match_return_value():
    """三类事件的到达顺序与内容：token 逐个到达，最后是完整回复。"""
    agent = RecordingAgent(ScriptedLLM([["你", "好", "！"]]))
    listener = RecordingListener()
    agent.set_output_listener(listener)

    reply = agent.chat("打个招呼")

    assert reply == "你好！"
    assert listener.events == [
        ("token", "你"),
        ("token", "好"),
        ("token", "！"),
        ("turn_completed", "你好！"),
    ]
    assert listener.events[-1][1] == reply


def test_subscription_keeps_legacy_callbacks_and_prints(capsys):
    """订阅后仍调用 token_deal / todo，且 stdout 与不订阅时一致（并存策略）。"""
    agent = RecordingAgent(ScriptedLLM([["你", "好"]]))
    listener = RecordingListener()
    agent.set_output_listener(listener)

    agent.chat("打个招呼")

    out = capsys.readouterr().out
    assert out == "你好[todo]你好\n"
    assert agent.token_calls == ["你", "好"]
    assert agent.todo_calls == ["你好"]


def test_clear_output_listener_stops_events(capsys):
    """取消订阅后不再有事件，既有 print 行为照旧。"""
    agent = RecordingAgent(ScriptedLLM([["x"], ["y"]]))
    listener = RecordingListener()
    agent.set_output_listener(listener)

    agent.chat("第一轮")
    events_after_first_turn = list(listener.events)

    agent.clear_output_listener()
    agent.chat("第二轮")

    out = capsys.readouterr().out
    assert out == "x[todo]x\ny[todo]y\n"
    assert listener.events == events_after_first_turn
    assert [event[0] for event in listener.events] == ["token", "turn_completed"]


def test_clear_output_listener_is_idempotent():
    """重复取消订阅不报错。"""
    agent = RecordingAgent(ScriptedLLM([]))

    agent.clear_output_listener()
    agent.clear_output_listener()


def test_set_output_listener_rejects_non_listener():
    """传入不合契约的对象时立刻报可读错误，而不是运行到一半才失败。"""
    agent = RecordingAgent(ScriptedLLM([]))

    with pytest.raises(TypeError) as exc_info:
        agent.set_output_listener(object())

    assert "AgentOutputListener" in str(exc_info.value)


def test_error_event_on_llm_failure_then_exception_propagates():
    """模型调用失败：先发 error 事件，再按原样抛出。"""
    error = RuntimeError("模型服务不可用")
    agent = RecordingAgent(FailingLLM(error))
    listener = RecordingListener()
    agent.set_output_listener(listener)

    with pytest.raises(RuntimeError) as exc_info:
        agent.chat("你好")

    assert exc_info.value is error
    assert len(listener.events) == 1
    event_name, error_info = listener.events[0]
    assert event_name == "error"
    assert isinstance(error_info, AgentOutputError)
    assert error_info.exception is error
    assert "模型服务不可用" in error_info.message


def test_error_event_on_mid_stream_failure():
    """流式中途失败：已产出的 token 事件保留，不发 turn_completed。"""
    error = ConnectionError("连接中断")
    agent = RecordingAgent(MidStreamFailingLLM(["半", "截"], error))
    listener = RecordingListener()
    agent.set_output_listener(listener)

    with pytest.raises(ConnectionError):
        agent.chat("你好")

    assert [event[0] for event in listener.events] == ["token", "token", "error"]
    assert listener.events[-1][1].exception is error


def test_error_event_when_token_deal_raises(capsys):
    """``token_deal`` 自身抛错同样产生 error 事件，并继续向上抛出。"""
    agent = TokenDealBoomAgent(ScriptedLLM([["a", "b", "c"]]))
    listener = RecordingListener()
    agent.set_output_listener(listener)

    with pytest.raises(ValueError, match="token_deal 炸了"):
        agent.chat("你好")

    capsys.readouterr()
    assert [event[0] for event in listener.events] == ["token", "token", "error"]
    assert agent.todo_calls == []


def test_error_event_when_todo_raises(capsys):
    """``todo`` 抛错时，turn_completed 已发出，随后是 error 事件。"""
    agent = TodoBoomAgent(ScriptedLLM([["完成"]]))
    listener = RecordingListener()
    agent.set_output_listener(listener)

    with pytest.raises(ValueError, match="todo 炸了"):
        agent.chat("你好")

    capsys.readouterr()
    assert [event[0] for event in listener.events] == [
        "token",
        "turn_completed",
        "error",
    ]


def test_callbacks_run_on_calling_thread():
    """回调在调用线程内触发，未引入任何新线程（契约 C1 第 5 条）。"""
    agent = RecordingAgent(ScriptedLLM([["线程"]]))
    listener = RecordingListener()
    agent.set_output_listener(listener)
    caller_thread_id = threading.get_ident()

    agent.chat("验证线程")

    assert listener.thread_ids
    assert set(listener.thread_ids) == {caller_thread_id}


def test_nested_chat_emits_one_turn_completed_per_chat():
    """``todo`` 内再次 ``chat()``：每轮各自完成，顺序不交叉。"""
    agent = TodoRecursingAgent(ScriptedLLM([["第一", "轮"], ["第二", "轮"]]))
    listener = RecordingListener()
    agent.set_output_listener(listener)

    agent.chat("开始")

    assert listener.events == [
        ("token", "第一"),
        ("token", "轮"),
        ("turn_completed", "第一轮"),
        ("token", "第二"),
        ("token", "轮"),
        ("turn_completed", "第二轮"),
    ]


def test_baseagent_has_no_thread_or_gui_dependency():
    """静态把关：框架层不得引入线程、不得依赖 Qt 或任何 GUI 库。"""
    source_path = (
        pathlib.Path(__file__).resolve().parents[2]
        / "ai_agent_factory"
        / "agent"
        / "baseagent.py"
    )
    source = source_path.read_text(encoding="utf-8")

    forbidden_fragments = [
        "import threading",
        "from threading",
        "import _thread",
        "PySide6",
        "PyQt",
        "tkinter",
    ]
    for fragment in forbidden_fragments:
        assert fragment not in source, f"baseagent.py 不应出现 {fragment!r}"
