"""C1 事件转投（Qt 无关部分）：三类事件 → 界面接收端。

覆盖的契约要求:
- C1 第 1 条：``token`` / ``turn_completed`` / ``error`` 三类事件可被消费，顺序不乱。
- C1 第 5 条：回调在调用线程内触发，转投层不新建线程（``test_callbacks_keep_the_calling_thread``）。
- C1 第 6 条：错误不吞——``error`` 事件的 ``error_info.message`` 原样交到界面，且
  ``saw_error`` 让上层知道「这一轮已经报过」，避免重复或漏报。
- C3 第 2 条：关闭后（``close()``）不再转发，窗口已关时不会往界面控件写东西；``close()`` 可重复。
"""

import threading
import unittest

from support import PROJECT_ROOT, RecordingSink  # noqa: F401

from ai_agent_factory.agent.baseagent import AgentOutputError
from desktop.output_listener import OutputEventForwarder


class OutputEventForwarderTest(unittest.TestCase):
    def setUp(self):
        self.sink = RecordingSink()
        self.forwarder = OutputEventForwarder(self.sink)

    def test_tokens_and_turn_are_forwarded_in_order(self):
        self.forwarder.on_token("你")
        self.forwarder.on_token("好")
        self.forwarder.on_turn_completed("你好")

        self.assertEqual(self.sink.tokens, ["你", "好"])
        self.assertEqual(self.sink.turns, ["你好"])

    def test_error_event_reaches_sink_with_readable_message(self):
        error = RuntimeError("模型服务不可用")

        self.forwarder.on_error(AgentOutputError(error, "RuntimeError: 模型服务不可用"))

        self.assertEqual(self.sink.errors, ["RuntimeError: 模型服务不可用"])
        self.assertTrue(self.forwarder.saw_error)

    def test_reset_turn_clears_error_flag(self):
        self.forwarder.on_error(AgentOutputError(RuntimeError("炸了"), "RuntimeError: 炸了"))
        self.forwarder.reset_turn()

        self.assertFalse(self.forwarder.saw_error)

    def test_report_local_error_is_prefixed_and_names_the_type(self):
        self.forwarder.report_local_error(ValueError("配置缺 api_key"))

        self.assertEqual(len(self.sink.errors), 1)
        self.assertIn("ValueError", self.sink.errors[0])
        self.assertIn("配置缺 api_key", self.sink.errors[0])

    def test_report_local_error_without_message(self):
        self.forwarder.report_local_error(ValueError())

        self.assertIn("ValueError", self.sink.errors[0])

    def test_close_stops_forwarding_and_is_idempotent(self):
        self.forwarder.close()
        self.forwarder.close()

        self.forwarder.on_token("不该出现")
        self.forwarder.on_turn_completed("不该出现")
        self.forwarder.on_error(AgentOutputError(RuntimeError("不该出现"), "不该出现"))
        self.forwarder.report_local_error(RuntimeError("不该出现"))

        self.assertEqual(self.sink.tokens, [])
        self.assertEqual(self.sink.turns, [])
        self.assertEqual(self.sink.errors, [])

    def test_callbacks_keep_the_calling_thread(self):
        """C1 在工作线程里回调，转投层不得自己开线程。"""
        caller = threading.get_ident()

        self.forwarder.on_token("a")
        self.forwarder.on_turn_completed("a")

        self.assertEqual(self.sink.threads, [caller, caller])

    def test_requires_a_sink(self):
        with self.assertRaises(ValueError):
            OutputEventForwarder(None)


if __name__ == "__main__":
    unittest.main()
