"""契约 C3 全条款：启动 → 关闭、重复关闭、启动失败后的清理、句柄不泄漏内部对象。

覆盖的契约要求:
- C3 第 1 条：``start()`` / ``run()`` 返回带 ``shutdown()`` 的关闭句柄。
- C3 第 2 条：``shutdown()`` 停止转发、拒绝新任务、回收线程、可重复调用不报错。
- C3 第 3 条：关闭后无残留线程；句柄不暴露编排器或 Qt 对象。
- C3 第 4 条：``import desktop`` 不启动界面（子进程用例在 ``test_import_side_effects.py``）。
- C3 第 5 条：启动失败（缺订阅方法 / 缺提交方法 / 订阅抛错）抛可读错误并清理已建资源。
"""

import threading
import time
import unittest

from support import (
    PROJECT_ROOT,  # noqa: F401
    FakeOrchestrator,
    NoSubscribeOrchestrator,
    RejectingSubscribeOrchestrator,
    find_window,
    get_application,
    live_pipeline_threads,
    wait_until,
    window_parts,
)

import desktop
from desktop.errors import DesktopStartupError


class DesktopLifecycleTest(unittest.TestCase):
    def setUp(self):
        get_application()
        self.handles = []

    def tearDown(self):
        for handle in self.handles:
            handle.shutdown(timeout=2.0)
        wait_until(lambda: find_window() is None)

    def start(self, orchestrator, **options):
        handle = desktop.start(orchestrator, **options)
        self.handles.append(handle)
        return handle

    def test_start_shows_window_and_subscribes_once(self):
        orchestrator = FakeOrchestrator()

        handle = self.start(orchestrator, window_title="测试窗口")

        window = find_window()
        self.assertIsNotNone(window, "启动后应有一个可见的主窗口")
        self.assertEqual(window.windowTitle(), "测试窗口")
        self.assertEqual(len(orchestrator.subscriptions), 1, "C1 订阅应发生在启动时")
        self.assertFalse(handle.is_closed)

    def test_shutdown_closes_window_reclaims_thread_and_unsubscribes(self):
        orchestrator = FakeOrchestrator()
        handle = self.start(orchestrator)

        handle.shutdown()

        self.assertTrue(handle.is_closed)
        self.assertIsNone(find_window(), "关闭后窗口不应还可见")
        self.assertEqual(orchestrator.clear_calls, 1, "关闭时应取消 C1 订阅")
        self.assertEqual(live_pipeline_threads(), [], "关闭后不应残留工作线程")

    def test_repeated_shutdown_is_harmless(self):
        orchestrator = FakeOrchestrator()
        handle = self.start(orchestrator)

        handle.shutdown()
        handle.shutdown()
        handle.shutdown(timeout=0.1)

        self.assertEqual(orchestrator.clear_calls, 1)

    def test_handle_exposes_no_orchestrator_and_no_qt_objects(self):
        from PySide6.QtWidgets import QApplication, QWidget

        orchestrator = FakeOrchestrator()
        handle = self.start(orchestrator)

        public_names = [name for name in dir(handle) if not name.startswith("_")]
        self.assertIn("shutdown", public_names)
        for name in public_names:
            value = getattr(handle, name)
            self.assertNotIsInstance(value, FakeOrchestrator, "句柄不得暴露编排器：" + name)
            self.assertNotIsInstance(value, QApplication, "句柄不得暴露 QApplication：" + name)
            self.assertNotIsInstance(value, QWidget, "句柄不得暴露窗口控件：" + name)

    def test_startup_failure_when_subscription_method_missing(self):
        with self.assertRaises(DesktopStartupError) as caught:
            self.start(NoSubscribeOrchestrator())

        self.assertIn("set_output_listener", str(caught.exception))
        self.assertIsNone(find_window(), "启动失败后不应留下窗口")
        self.assertEqual(live_pipeline_threads(), [], "启动失败后不应留下工作线程")

    def test_startup_failure_when_submit_method_missing(self):
        with self.assertRaises(DesktopStartupError) as caught:
            self.start(FakeOrchestrator(), submit_method_name="submit_requirement")

        self.assertIn("submit_requirement", str(caught.exception))
        self.assertIsNone(find_window(), "启动失败后不应留下窗口")
        self.assertEqual(live_pipeline_threads(), [], "启动失败后不应留下工作线程")

    def test_startup_failure_when_orchestrator_is_none(self):
        with self.assertRaises(DesktopStartupError) as caught:
            self.start(None)

        self.assertIn("None", str(caught.exception))

    def test_startup_failure_after_window_created_cleans_up(self):
        orchestrator = RejectingSubscribeOrchestrator()

        with self.assertRaises(DesktopStartupError) as caught:
            self.start(orchestrator)

        self.assertIn("订阅", str(caught.exception))
        self.assertIsNone(find_window(), "订阅失败时也要把窗口关掉")
        self.assertEqual(orchestrator.clear_calls, 1, "订阅失败时应尝试取消订阅")

    def test_run_returns_closed_handle_after_window_closes(self):
        from PySide6.QtCore import QTimer

        orchestrator = FakeOrchestrator()
        QTimer.singleShot(100, self.close_any_window)

        handle = desktop.run(orchestrator, window_title="blocking 测试")
        self.handles.append(handle)

        self.assertTrue(handle.is_closed)
        self.assertEqual(orchestrator.clear_calls, 1)
        self.assertIsNone(find_window())

    def test_shutdown_stops_forwarding_for_a_running_pipeline(self):
        gate = threading.Event()
        orchestrator = FakeOrchestrator(gate=gate)
        handle = self.start(orchestrator)
        output_pane, requirement_input, send_button = window_parts(find_window())
        requirement_input.setText("写个待办")
        send_button.click()
        self.assertTrue(wait_until(lambda: orchestrator.requirements == ["写个待办"]))

        started_at = time.monotonic()
        handle.shutdown(timeout=0.2)
        elapsed = time.monotonic() - started_at

        self.assertLess(elapsed, 3.0, "关闭不应长时间卡住界面线程")

        gate.set()
        self.assertTrue(wait_until(lambda: live_pipeline_threads() == []))
        self.assertEqual(output_pane.toPlainText().strip(), "", "关闭后不应再往窗口里写内容")

    def close_any_window(self):
        window = find_window()
        if window is not None:
            window.close()

    def test_module_entry_point_opens_window_and_reports_unwired_pipeline(self):
        """``python -m desktop`` 的入口：能开窗、能提交、能关；没接线时说人话。"""
        from desktop import __main__ as entry

        handle = entry.main(blocking=False)
        self.handles.append(handle)
        self.assertTrue(wait_until(lambda: find_window() is not None))

        output_pane, requirement_input, send_button = window_parts(find_window())
        requirement_input.setText("写个待办")
        send_button.click()

        self.assertTrue(wait_until(lambda: "还没接到编排层" in output_pane.toPlainText()))

        handle.shutdown()
        self.assertTrue(handle.is_closed)


if __name__ == "__main__":
    unittest.main()
