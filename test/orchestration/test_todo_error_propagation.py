"""缺陷回归：`make_decision()` 抛错时必须冒泡到 `chat()`，C1 的 error 事件才发得出去。

修复前：`todo()` 的 try/except 只打印诊断信息、不 re-raise，`BaseAgent.chat()` 的
except 根本看不到异常，监听器收到 **0 个** error 事件，桌面窗口完全静默
（复现脚本见 `test/testing/check_orchestrator_decision_error.py`）。

复现手法：让编排器决定走 `ask_pj`，而产品经理从未产出过 PRD —— `ask_pj` 分支里
`self.agents["pm"].prd` 是唯一没有默认值的取值，必然抛 `AttributeError`。
"""

import contextlib
import io
from unittest import mock

import pytest

from myagent.system_manager_agent import SystemManagerAgent

from support import StubBusinessAgent, StubLLM
from test_output_listener_dispatch import RecordingListener


DEFECT_DECISION = "ask_pj: 请根据 PRD 生成指导文档"


def build_manager_failing_in_decision():
    """构造一个决策分支必然抛错的编排器（替身智能体 + 替身 LLM，不联网）。"""
    agents = {
        'pm': StubBusinessAgent(),
        'pj': StubBusinessAgent(),
        'fe': StubBusinessAgent(),
        'be': StubBusinessAgent(),
    }
    # ask_pj 分支会读 agents['pm'].prd，且没有默认值：删掉它就会抛 AttributeError
    del agents['pm'].prd
    manager = SystemManagerAgent(StubLLM([DEFECT_DECISION]), agents)
    return manager, agents


def test_error_event_is_emitted_and_chat_raises():
    """①监听器收到 1 个 error 事件且是原异常 ②chat() 抛出 ③诊断打印仍在。"""
    manager, agents = build_manager_failing_in_decision()
    listener = RecordingListener()
    manager.set_output_listener(listener)
    assert hasattr(agents['pm'], 'prd') is False

    buffer = io.StringIO()
    with pytest.raises(AttributeError) as raised:
        with contextlib.redirect_stdout(buffer):
            manager.chat("做一个极简待办页面")
    output = buffer.getvalue()

    # ① 恰好一个 error 事件，且携带的是原异常对象本身
    assert len(listener.errors) == 1
    assert listener.errors[0].exception is raised.value
    assert isinstance(listener.errors[0].exception, AttributeError)
    assert "AttributeError" in listener.errors[0].message

    # ③ 原有的诊断打印保留（命令行用户靠它定位）
    assert "管理者决策解析错误" in output
    assert "原始响应: " + DEFECT_DECISION in output

    # 事件顺序：本轮 turn_completed 先到，error 后到
    assert listener.turns == [DEFECT_DECISION]


def test_chat_does_not_return_normally_when_decision_fails():
    """②`chat()` 把异常抛出，而不是像修复前那样正常返回。"""
    manager, agents = build_manager_failing_in_decision()
    listener = RecordingListener()
    manager.set_output_listener(listener)

    with contextlib.redirect_stdout(io.StringIO()):
        with pytest.raises(AttributeError):
            manager.chat("做一个极简待办页面")


def test_normal_path_printing_is_unchanged():
    """正常路径（兜底分支）不改可观察行为：照常打印、不抛错、无 error 事件。"""
    manager = SystemManagerAgent(
        StubLLM(["随便聊聊"]),
        {
            'pm': StubBusinessAgent(),
            'pj': StubBusinessAgent(),
            'fe': StubBusinessAgent(),
            'be': StubBusinessAgent(),
        }
    )
    listener = RecordingListener()
    manager.set_output_listener(listener)

    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        reply = manager.chat("你好")
    output = buffer.getvalue()

    assert reply == "随便聊聊"
    assert "🤖 系统管理者: 随便聊聊" in output
    assert "⚠️  未知决策: 随便聊聊" in output
    assert "管理者决策解析错误" not in output
    assert listener.errors == []
    assert listener.turns == ["随便聊聊"]


def test_keyboard_interrupt_is_not_caught_by_todo():
    """KeyboardInterrupt 属 BaseException，todo() 不得接住它。"""
    manager = SystemManagerAgent(
        StubLLM(["任意回复"]),
        {
            'pm': StubBusinessAgent(),
            'pj': StubBusinessAgent(),
            'fe': StubBusinessAgent(),
            'be': StubBusinessAgent(),
        }
    )

    buffer = io.StringIO()
    with mock.patch.object(manager, "make_decision", side_effect=KeyboardInterrupt()):
        with pytest.raises(KeyboardInterrupt):
            with contextlib.redirect_stdout(buffer):
                manager.todo("任意回复")

    assert "管理者决策解析错误" not in buffer.getvalue()
