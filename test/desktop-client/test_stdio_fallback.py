"""无控制台模式下的 stdout / stderr 兜底。

覆盖的契约要求:
- C1 第 3、4 条：订阅后 ``token_deal`` / ``todo`` 仍照常 ``print``（事件与终端输出并存），
  所以 ``pythonw`` / ``--noconsole`` 下 ``sys.stdout is None`` 必须先兜住，
  否则管线第一个 ``print`` 就会抛异常。
- C3 第 5 条：启动失败要可读、可清理；兜底必须在建窗口之前完成，写不成日志要退内存缓冲
  （``print`` 永远不炸）。
"""

import io
import os
import sys
import tempfile
import unittest

from support import PROJECT_ROOT  # noqa: F401  （把项目根放进 sys.path）

from desktop.stdio_fallback import ensure_standard_streams, log_message, remembered_messages


class EnsureStandardStreamsTest(unittest.TestCase):
    def setUp(self):
        self.saved_stdout = sys.stdout
        self.saved_stderr = sys.stderr
        self.directory = tempfile.mkdtemp(prefix="desktop-stdio-")

    def tearDown(self):
        for stream in (sys.stdout, sys.stderr):
            if stream is None:
                continue
            if stream is self.saved_stdout or stream is self.saved_stderr:
                continue
            try:
                stream.close()
            except (OSError, ValueError) as error:
                print("[test] 关闭兜底流失败：" + repr(error), file=self.saved_stderr)
        sys.stdout = self.saved_stdout
        sys.stderr = self.saved_stderr

    def test_none_streams_are_replaced_and_print_works(self):
        sys.stdout = None
        sys.stderr = None

        replaced = ensure_standard_streams(self.directory)

        self.assertEqual(len(replaced), 2)
        self.assertIsNotNone(sys.stdout)
        self.assertIsNotNone(sys.stderr)
        print("这一行如果抛异常，说明兜底没生效")
        log_message("[desktop] 诊断行")
        sys.stdout.flush()
        sys.stderr.flush()

        log_files = [name for name in os.listdir(self.directory) if name.endswith(".log")]
        self.assertEqual(len(log_files), 1)
        with open(os.path.join(self.directory, log_files[0]), encoding="utf-8") as handle:
            content = handle.read()
        self.assertIn("这一行如果抛异常，说明兜底没生效", content)
        self.assertIn("诊断行", content)

    def test_unwritable_directory_falls_back_to_memory_buffer(self):
        blocker = os.path.join(self.directory, "not-a-directory")
        with open(blocker, "w", encoding="utf-8") as handle:
            handle.write("我是文件，不是目录")
        sys.stdout = None
        sys.stderr = None

        replaced = ensure_standard_streams(blocker)

        self.assertEqual(len(replaced), 2)
        self.assertIsInstance(sys.stdout, io.StringIO)
        print("内存兜底也要能 print")
        self.assertIn("内存兜底也要能 print", sys.stdout.getvalue())

    def test_existing_streams_are_left_alone(self):
        replaced = ensure_standard_streams(self.directory)

        self.assertEqual(replaced, [])
        self.assertIs(sys.stdout, self.saved_stdout)

    def test_only_missing_stream_is_replaced(self):
        sys.stdout = None

        replaced = ensure_standard_streams(self.directory)

        self.assertEqual(len(replaced), 1)
        self.assertIsNotNone(sys.stdout)
        self.assertIs(sys.stderr, self.saved_stderr)

    def test_remembered_messages_capture_when_stderr_missing(self):
        from desktop import stdio_fallback

        sys.stderr = None
        before = len(stdio_fallback.remembered_messages())

        log_message("没有 stderr 时也不能丢")

        messages = stdio_fallback.remembered_messages()
        self.assertEqual(len(messages), before + 1)
        self.assertEqual(messages[-1], "没有 stderr 时也不能丢")


if __name__ == "__main__":
    unittest.main()
