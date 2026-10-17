"""C1 事件 → Qt 信号（跨线程投递）。

工作线程里只做 ``signal.emit(...)``；Qt 会把信号排队送到它所属的界面线程，
界面控件只在界面线程里被碰。这是「界面线程只渲染」的关键一环。
"""

from PySide6.QtCore import QObject, Signal


class OutputSignalBridge(QObject):
    """把 C1 的三类事件与「任务结束」变成 Qt 信号。

    方法名与 ``OutputEventForwarder`` 需要的接收端一致，可以直接当 sink 用。
    """

    token_received = Signal(str)
    turn_completed = Signal(str)
    error_received = Signal(str)
    task_finished = Signal()

    def on_token(self, text):
        self.token_received.emit(text)

    def on_turn_completed(self, full_text):
        self.turn_completed.emit(full_text)

    def on_error(self, message):
        self.error_received.emit(message)
