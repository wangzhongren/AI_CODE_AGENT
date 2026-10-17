"""契约 C1.2：把输出监听器下发给四个子智能体。

用 `BaseAgent` 派生的替身子智能体，真实走 C1.1 的事件发送路径；
LLM 用替身，不联网、不依赖真实模型。
"""

import contextlib
import io

import pytest

from ai_agent_factory.agent.baseagent import AgentOutputListener, BaseAgent
from myagent.system_manager_agent import SystemManagerAgent

from support import StubLLM


CHILD_KEYS = ('pm', 'pj', 'fe', 'be')


class RecordingListener(AgentOutputListener):
    """记录三类事件的监听器替身。"""

    def __init__(self):
        self.tokens = []
        self.turns = []
        self.errors = []

    def on_token(self, text):
        self.tokens.append(text)

    def on_turn_completed(self, full_text):
        self.turns.append(full_text)

    def on_error(self, error_info):
        self.errors.append(error_info)


class StubChildAgent(BaseAgent):
    """`BaseAgent` 派生的子智能体替身：真实发事件，不打印、不联网。"""

    def __init__(self, basellm, label):
        super().__init__(basellm, f"你是替身子智能体：{label}", max_context=10)
        self.label = label
        self.tokens_dealt = []
        self.todo_calls = []

    def token_deal(self, result):
        # 故意不 print：避开 Windows GBK 控制台限制，同时便于断言既有通道仍被调用
        self.tokens_dealt.append(result)

    def todo(self, token):
        self.todo_calls.append(token)


class BrokenChildAgent:
    """订阅时抛错的子智能体替身。"""

    def __init__(self, error):
        self.error = error

    def set_output_listener(self, listener):
        raise self.error

    def clear_output_listener(self):
        return None


class NoClearChildAgent:
    """只有订阅能力、没有清除能力的子智能体替身。"""

    def set_output_listener(self, listener):
        return None


def build_manager_with_children():
    """装配一个编排器 + 四个带真实事件通道的子智能体替身。"""
    children = {}
    for name in CHILD_KEYS:
        child_llm = StubLLM([f"{name}-chunk-1", f"{name}-chunk-2"])
        children[name] = StubChildAgent(child_llm, name)
    manager = SystemManagerAgent(StubLLM(["orchestrator-reply"]), children)
    return manager, children


def run_capturing_output(action, *args):
    """吞掉打印输出，避免 Windows GBK 控制台编码报错。"""
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        action(*args)
    return buffer.getvalue()


def context_copy(manager):
    copied = []
    for message in manager.get_context():
        copied.append(dict(message))
    return copied


def test_dispatch_delivers_events_from_all_four_children():
    """下发后，四个子智能体各自的事件都到达同一个监听器。"""
    manager, children = build_manager_with_children()
    listener = RecordingListener()

    manager.set_output_listener_for_children(listener)

    for name in CHILD_KEYS:
        children[name].chat("开工")

    expected_tokens = []
    expected_turns = []
    for name in CHILD_KEYS:
        expected_tokens.append(f"{name}-chunk-1")
        expected_tokens.append(f"{name}-chunk-2")
        expected_turns.append(f"{name}-chunk-1{name}-chunk-2")
    assert listener.tokens == expected_tokens
    assert listener.turns == expected_turns
    # 既有通道（token_deal / todo）照常被调用，事件与 print 并存。
    assert children['pm'].tokens_dealt == ["pm-chunk-1", "pm-chunk-2"]
    assert children['pm'].todo_calls == ["pm-chunk-1pm-chunk-2"]


def test_dispatch_twice_does_not_duplicate_events():
    """幂等：同一监听器下发两次，事件不重复到达。"""
    manager, children = build_manager_with_children()
    listener = RecordingListener()

    manager.set_output_listener_for_children(listener)
    manager.set_output_listener_for_children(listener)

    children['pm'].chat("开工")

    assert listener.tokens == ["pm-chunk-1", "pm-chunk-2"]
    assert listener.turns == ["pm-chunk-1pm-chunk-2"]


def test_redispatch_replaces_previous_listener():
    """换一个监听器再下发：旧监听器不再收事件，新监听器只收一份。"""
    manager, children = build_manager_with_children()
    first_listener = RecordingListener()
    second_listener = RecordingListener()
    manager.set_output_listener_for_children(first_listener)

    manager.set_output_listener_for_children(second_listener)
    children['be'].chat("开工")

    assert first_listener.tokens == []
    assert second_listener.tokens == ["be-chunk-1", "be-chunk-2"]


def test_without_dispatch_only_orchestrator_events():
    """未下发时：子智能体不订阅，事件只来自编排器自身。"""
    manager, children = build_manager_with_children()
    listener = RecordingListener()
    manager.set_output_listener(listener)

    children['pm'].chat("开工")
    assert listener.tokens == []
    assert listener.turns == []

    run_capturing_output(manager.chat, "你好")

    assert listener.tokens == ["orchestrator-reply"]
    assert listener.turns == ["orchestrator-reply"]


def test_clear_stops_child_events():
    """清除后不再收到子智能体事件。"""
    manager, children = build_manager_with_children()
    listener = RecordingListener()
    manager.set_output_listener_for_children(listener)
    children['pm'].chat("开工")
    assert listener.turns == ["pm-chunk-1pm-chunk-2"]

    manager.clear_output_listener_for_children()
    children['pm'].chat("再开工")

    assert listener.turns == ["pm-chunk-1pm-chunk-2"]
    assert len(listener.tokens) == 2


def test_clear_is_idempotent_and_safe_when_never_dispatched():
    """清除可重复调用；从未下发时清除也不报错。"""
    manager, children = build_manager_with_children()

    manager.clear_output_listener_for_children()
    manager.clear_output_listener_for_children()

    assert children['pm'].tokens_dealt == []


def test_missing_capability_is_reported_and_others_still_subscribed():
    """某个子智能体没有订阅能力时：抛错点名是哪一个，其余照常下发。"""
    manager, children = build_manager_with_children()
    children['fe'] = object()
    listener = RecordingListener()

    with pytest.raises(RuntimeError) as error_info:
        manager.set_output_listener_for_children(listener)

    message = str(error_info.value)
    assert "fe" in message
    assert "set_output_listener" in message
    assert "object" in message
    # 其余三个已经订阅成功，不会因为一个失败而整体作废。
    children['pm'].chat("开工")
    assert listener.turns == ["pm-chunk-1pm-chunk-2"]


def test_subscription_error_is_reported_with_child_and_reason():
    """订阅抛错时：报出子智能体键名、异常类型与原始消息。"""
    manager, children = build_manager_with_children()
    manager.agents['be'] = BrokenChildAgent(ValueError("模型未就绪"))
    listener = RecordingListener()

    with pytest.raises(RuntimeError) as error_info:
        manager.set_output_listener_for_children(listener)

    message = str(error_info.value)
    assert "be" in message
    assert "ValueError" in message
    assert "模型未就绪" in message


def test_invalid_listener_error_is_not_swallowed():
    """监听器类型不对时，子类抛出的 TypeError 必须被报出来，而不是被吞掉。"""
    manager, children = build_manager_with_children()

    with pytest.raises(RuntimeError) as error_info:
        manager.set_output_listener_for_children("这不是监听器")

    message = str(error_info.value)
    assert "TypeError" in message
    for name in CHILD_KEYS:
        assert name in message


def test_clear_reports_missing_clear_capability():
    """清除时缺能力的子智能体同样要点名报出。"""
    manager, children = build_manager_with_children()
    manager.agents['pj'] = NoClearChildAgent()

    with pytest.raises(RuntimeError) as error_info:
        manager.clear_output_listener_for_children()

    message = str(error_info.value)
    assert "pj" in message
    assert "clear_output_listener" in message


def test_dispatch_does_not_change_project_state_or_context():
    """下发监听器只动订阅关系，不动项目状态与对话上下文。"""
    manager, children = build_manager_with_children()
    listener = RecordingListener()
    snapshot_before = manager.get_snapshot()
    context_before = context_copy(manager)

    manager.set_output_listener_for_children(listener)

    assert manager.get_snapshot() == snapshot_before
    assert context_copy(manager) == context_before
