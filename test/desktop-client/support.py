"""test/desktop-client 的公用工具与替身（不含生产代码）。

编排器一律用替身注入，不依赖真实 LLM、网络或环境变量。
``QT_QPA_PLATFORM=offscreen`` 必须在导入 Qt 之前设好，所以放在本模块顶部。
"""

import os
import sys
import threading
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from ai_agent_factory.agent.baseagent import AgentOutputError  # noqa: E402


class RecordingSink:
    """记录 OutputEventForwarder 交来的三类事件。"""

    def __init__(self):
        self.tokens = []
        self.turns = []
        self.errors = []
        self.threads = []

    def on_token(self, text):
        self.tokens.append(text)
        self.threads.append(threading.get_ident())

    def on_turn_completed(self, full_text):
        self.turns.append(full_text)
        self.threads.append(threading.get_ident())

    def on_error(self, message):
        self.errors.append(message)
        self.threads.append(threading.get_ident())


class FakeOrchestrator:
    """替身编排器：只实现契约要求的两个公开能力。

    - ``set_output_listener`` / ``clear_output_listener``（契约 C1）
    - ``chat(message)``：按剧本吐出 token，可选先挂住（模拟长任务）或抛错。
    """

    def __init__(self, replies=None, error=None, gate=None):
        if replies is None:
            replies = [["你", "好"]]
        self.replies = replies
        self.error = error
        self.gate = gate
        self.listener = None
        self.subscriptions = []
        self.requirements = []
        self.submit_threads = []
        self.clear_calls = 0

    def set_output_listener(self, listener):
        self.listener = listener
        self.subscriptions.append(listener)

    def clear_output_listener(self):
        self.clear_calls += 1
        self.listener = None

    def chat(self, message):
        self.requirements.append(message)
        self.submit_threads.append(threading.get_ident())
        if self.gate is not None:
            self.gate.wait(5.0)
        if self.error is not None:
            message_text = type(self.error).__name__ + ": " + str(self.error)
            self.listener.on_error(AgentOutputError(self.error, message_text))
            raise self.error
        full_text = ""
        for token_line in self.replies:
            full_text = ""
            for token in token_line:
                full_text += token
                # 契约 C1 的选择是「事件与 print 并存」，这里照抄真实行为
                print(token, end="")
                self.listener.on_token(token)
            self.listener.on_turn_completed(full_text)
        return full_text


class NoSubscribeOrchestrator:
    """不合契约的编排器：没有 set_output_listener。"""

    def chat(self, message):
        return ""


class RejectingSubscribeOrchestrator:
    """订阅时抛错的编排器：用来验证「启动失败后清理」。"""

    def __init__(self):
        self.clear_calls = 0

    def set_output_listener(self, listener):
        raise RuntimeError("订阅失败（替身故意抛错）")

    def clear_output_listener(self):
        self.clear_calls += 1

    def chat(self, message):
        return ""


# ---------- Qt 相关工具（只有用到 Qt 的用例才调用） ----------


def get_application():
    """返回（必要时创建）唯一的 QApplication。离屏模式下不需要显示器。"""
    from PySide6.QtWidgets import QApplication

    application = QApplication.instance()
    if application is None:
        application = QApplication(["desktop-tests"])
    return application


def find_window():
    """按 objectName 找当前可见的主窗口；没有则返回 None。"""
    application = get_application()
    for widget in application.topLevelWidgets():
        if widget.objectName() == "mainWindow" and widget.isVisible():
            return widget
    return None


def window_parts(window):
    """取输出区、输入框、发送按钮（都靠 objectName 找，不碰私有字段）。"""
    from PySide6.QtWidgets import QLineEdit, QPushButton, QTextEdit

    output_pane = window.findChild(QTextEdit, "outputPane")
    requirement_input = window.findChild(QLineEdit, "requirementInput")
    send_button = window.findChild(QPushButton, "sendButton")
    return output_pane, requirement_input, send_button


def wait_until(condition, timeout=5.0):
    """一边处理 Qt 事件一边等条件成立。"""
    application = get_application()
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        application.processEvents()
        if condition():
            return True
        time.sleep(0.005)
    application.processEvents()
    return bool(condition())


def live_pipeline_threads():
    """还活着的管线工作线程。"""
    return [thread for thread in threading.enumerate() if thread.name == "desktop-pipeline"]
