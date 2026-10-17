"""输出渲染（契约 C1 → 界面）：token 追加、turn_completed 另起一段、error 醒目。

覆盖的契约要求:
- C1 第 1 条：三类事件各有确定的界面表现（逐字追加 / 另起一段 / 红色加粗 ``[错误]``）。
- C1 第 6 条：错误必须让用户看见，与「点了没反应」区分开。
- role-card「线程与生命周期」：长任务在非界面线程执行（``test_long_task_runs_off_the_gui_thread``），
  界面线程只渲染；忙碌期间禁用发送，结束后恢复。
"""

import threading
import unittest

from support import (
    PROJECT_ROOT,  # noqa: F401
    FakeOrchestrator,
    find_window,
    get_application,
    wait_until,
    window_parts,
)

import desktop
from desktop.window import ERROR_COLOR


class RenderingTest(unittest.TestCase):
    def setUp(self):
        get_application()
        self.handles = []

    def tearDown(self):
        for handle in self.handles:
            handle.shutdown(timeout=2.0)
        wait_until(lambda: find_window() is None)

    def start(self, orchestrator):
        handle = desktop.start(orchestrator, window_title="渲染测试")
        self.handles.append(handle)
        wait_until(lambda: find_window() is not None)
        return handle

    def send(self, text, wait_for_idle=True):
        output_pane, requirement_input, send_button = window_parts(find_window())
        if wait_for_idle:
            # 像真实用户一样：按钮可用才点得动
            wait_until(lambda: send_button.isEnabled())
        requirement_input.setText(text)
        send_button.click()
        return output_pane, requirement_input, send_button

    def test_tokens_are_appended_and_turn_completion_starts_a_new_paragraph(self):
        orchestrator = FakeOrchestrator(replies=[["你", "好"]])
        self.start(orchestrator)

        output_pane, requirement_input, send_button = self.send("写个待办")

        self.assertTrue(
            wait_until(lambda: output_pane.toPlainText().strip() == "你好"),
            "输出区文字应为逐字追加的 token，实际：" + repr(output_pane.toPlainText()),
        )
        self.assertTrue(
            wait_until(lambda: output_pane.document().blockCount() == 2),
            "turn_completed 应另起一段，实际段数：" + str(output_pane.document().blockCount()),
        )
        self.assertEqual(orchestrator.requirements, ["写个待办"])
        self.assertEqual(requirement_input.text(), "", "发送成功后输入框应清空")
        self.assertTrue(wait_until(lambda: send_button.isEnabled()), "任务结束后发送按钮应恢复可用")

    def test_error_event_is_rendered_red_and_bold(self):
        orchestrator = FakeOrchestrator(error=RuntimeError("模型服务不可用"))
        self.start(orchestrator)

        output_pane, _input, _button = self.send("写个待办")

        self.assertTrue(wait_until(lambda: "模型服务不可用" in output_pane.toPlainText()))
        text = output_pane.toPlainText()
        self.assertIn("[错误]", text)
        self.assertIn("RuntimeError", text)

        char_format = self.last_block_format(output_pane)
        self.assertEqual(char_format.foreground().color().name(), ERROR_COLOR)
        from PySide6.QtGui import QFont

        self.assertEqual(char_format.fontWeight(), QFont.Weight.Bold)

    def test_long_task_runs_off_the_gui_thread(self):
        orchestrator = FakeOrchestrator(replies=[["好"]])
        self.start(orchestrator)

        self.send("写个待办")
        self.assertTrue(wait_until(lambda: orchestrator.requirements == ["写个待办"]))

        self.assertNotEqual(orchestrator.submit_threads[0], threading.get_ident())

    def test_empty_requirement_is_not_submitted(self):
        orchestrator = FakeOrchestrator()
        self.start(orchestrator)

        output_pane, requirement_input, send_button = self.send("   ")

        self.assertEqual(orchestrator.requirements, [])
        self.assertEqual(output_pane.toPlainText(), "")
        self.assertTrue(send_button.isEnabled())

    def test_send_button_is_disabled_while_pipeline_runs(self):
        gate = threading.Event()
        orchestrator = FakeOrchestrator(gate=gate)
        self.start(orchestrator)

        _pane, _input, send_button = self.send("写个待办")

        self.assertTrue(wait_until(lambda: not send_button.isEnabled()), "运行中应禁用发送按钮")
        gate.set()
        self.assertTrue(wait_until(lambda: send_button.isEnabled()), "任务结束后应恢复发送按钮")

    def test_two_turns_append_after_each_other(self):
        orchestrator = FakeOrchestrator(replies=[["第", "一"], ["第", "二"]])
        self.start(orchestrator)

        output_pane, _input, _button = self.send("第一轮")
        self.assertTrue(wait_until(lambda: "第一" in output_pane.toPlainText()))
        self.send("第二轮")
        self.assertTrue(wait_until(lambda: "第二" in output_pane.toPlainText()))

        self.assertEqual(orchestrator.requirements, ["第一轮", "第二轮"])

    def last_block_format(self, output_pane):
        from PySide6.QtGui import QTextCursor

        cursor = output_pane.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock, QTextCursor.MoveMode.KeepAnchor)
        return cursor.charFormat()


if __name__ == "__main__":
    unittest.main()
