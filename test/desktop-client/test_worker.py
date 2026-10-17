"""工作线程：长任务离开界面线程、忙时拒绝、异常可见、取消与回收。

覆盖的契约要求:
- C3 第 2 条：``shutdown()`` 依赖的能力——取消后拒绝新任务、回收线程，
  回收不了要如实报告（``join`` 超时返回 ``False``，不假装成功）。
- C1 第 6 条：异常不得静默吞掉。C1 已发过 ``error`` 事件的不重复报，
  没发过的由工作线程补报给界面。
- role-card「线程与生命周期」：长任务一律在工作线程，界面线程只渲染。
"""

import threading
import time
import unittest

from support import PROJECT_ROOT, RecordingSink  # noqa: F401

from ai_agent_factory.agent.baseagent import AgentOutputError
from desktop.worker import THREAD_NAME, PipelineRunner


class PipelineRunnerTest(unittest.TestCase):
    def setUp(self):
        self.sink = RecordingSink()
        from desktop.output_listener import OutputEventForwarder

        self.forwarder = OutputEventForwarder(self.sink)
        self.finished = threading.Event()

    def build(self, submit_call):
        runner = PipelineRunner(submit_call, self.forwarder)
        runner.set_on_task_finished(self.finished.set)
        return runner

    def test_submit_runs_on_a_worker_thread(self):
        seen = {}

        def submit_call(requirement):
            seen["thread"] = threading.get_ident()
            seen["requirement"] = requirement

        runner = self.build(submit_call)
        accepted = runner.submit("写个待办")
        runner.join(5.0)

        self.assertTrue(accepted)
        self.assertNotEqual(seen["thread"], threading.get_ident())
        self.assertEqual(seen["requirement"], "写个待办")
        self.assertTrue(self.finished.is_set())
        self.assertFalse(runner.is_busy)

    def test_busy_runner_rejects_second_submission(self):
        gate = threading.Event()

        def submit_call(requirement):
            gate.wait(5.0)

        runner = self.build(submit_call)
        self.assertTrue(runner.submit("第一轮"))
        rejected = runner.submit("第二轮")
        gate.set()
        runner.join(5.0)

        self.assertFalse(rejected)

    def test_exception_without_c1_error_event_is_reported_to_ui(self):
        def submit_call(requirement):
            raise RuntimeError("管线在事件之外炸了")

        runner = self.build(submit_call)
        runner.submit("写个待办")
        runner.join(5.0)

        self.assertEqual(len(self.sink.errors), 1)
        self.assertIn("RuntimeError", self.sink.errors[0])
        self.assertIn("管线在事件之外炸了", self.sink.errors[0])

    def test_exception_already_reported_by_c1_is_not_duplicated(self):
        def submit_call(requirement):
            self.forwarder.reset_turn()
            self.forwarder.on_error(AgentOutputError(RuntimeError("模型挂了"), "RuntimeError: 模型挂了"))
            raise RuntimeError("模型挂了")

        runner = self.build(submit_call)
        runner.submit("写个待办")
        runner.join(5.0)

        self.assertEqual(self.sink.errors, ["RuntimeError: 模型挂了"])

    def test_cancel_prevents_new_submissions(self):
        runner = self.build(lambda requirement: None)
        runner.cancel()
        runner.cancel()

        self.assertFalse(runner.submit("写个待办"))
        self.assertTrue(runner.is_cancelled)

    def test_join_reports_timeout_instead_of_pretending_success(self):
        gate = threading.Event()

        def submit_call(requirement):
            gate.wait(5.0)

        runner = self.build(submit_call)
        runner.submit("长任务")
        runner.cancel()
        collected = runner.join(0.1)
        gate.set()
        reclaimed = runner.join(5.0)

        self.assertFalse(collected, "任务没结束时应如实返回 False，不能假装回收成功")
        self.assertTrue(reclaimed, "任务结束后应能回收线程")

    def test_thread_uses_the_documented_name(self):
        seen = {}

        def submit_call(requirement):
            seen["name"] = threading.current_thread().name

        runner = self.build(submit_call)
        runner.submit("写个待办")
        runner.join(5.0)

        self.assertEqual(seen["name"], THREAD_NAME)

    def test_requires_callable_submit(self):
        with self.assertRaises(TypeError):
            PipelineRunner(None, self.forwarder)


if __name__ == "__main__":
    unittest.main()
