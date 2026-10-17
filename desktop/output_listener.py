"""把契约 C1 的输出事件转投给界面（本模块**不依赖 Qt**，可单独测试）。

C1 规定监听器在**调用 ``chat()`` 的线程**里被回调，也就是我们的工作线程。
所以这里只做转投，不碰任何界面控件；真正的跨线程投递由 ``desktop/bridge.py``
里的 Qt 信号完成。
"""

import threading

from ai_agent_factory.agent.baseagent import AgentOutputListener

from desktop.stdio_fallback import log_message


class OutputEventForwarder(AgentOutputListener):
    """C1 的监听器实现：把 ``token`` / ``turn_completed`` / ``error`` 交给界面接收端。

    接收端（``sink``）需实现三个方法:
        ``on_token(text)``、``on_turn_completed(full_text)``、``on_error(message)``。
    生产环境里 sink 是 Qt 信号桥；测试里可以是任意记录对象。

    关闭后（窗口已关）不再转发任何事件：宁可少画几个字，也不能在窗口销毁后
    往界面控件上写东西。
    """

    def __init__(self, sink):
        if sink is None:
            raise ValueError("OutputEventForwarder 需要一个接收端对象，实际收到 None")
        self.__sink = sink
        self.__closed = False
        self.__saw_error = False
        self.__lock = threading.Lock()

    def on_token(self, text):
        if self.__is_closed():
            return
        self.__sink.on_token(text)

    def on_turn_completed(self, full_text):
        if self.__is_closed():
            return
        self.__sink.on_turn_completed(full_text)

    def on_error(self, error_info):
        """C1 的 error 事件：记住「这一轮已经报过错」，避免工作线程重复上报。"""
        with self.__lock:
            self.__saw_error = True
        if self.__is_closed():
            return
        self.__sink.on_error(error_info.message)

    @property
    def saw_error(self):
        """本轮任务是否已经通过 C1 的 ``error`` 事件报过错。"""
        with self.__lock:
            return self.__saw_error

    def reset_turn(self):
        """开始新一轮任务前清空「已报错」标记。"""
        with self.__lock:
            self.__saw_error = False

    def report_local_error(self, exception):
        """补报一个没走 C1 ``error`` 事件的异常（例如管线在事件之外抛错）。

        界面上的失败必须让用户看见，不能只写进日志。
        """
        if self.__is_closed():
            return
        detail = str(exception).strip()
        type_name = type(exception).__name__
        if detail:
            message = "任务异常结束：" + type_name + ": " + detail
        else:
            message = "任务异常结束：" + type_name + "（异常未附带消息）"
        self.__sink.on_error(message)

    def close(self):
        """停止转发（窗口关闭时调用）。可重复调用。"""
        with self.__lock:
            if self.__closed:
                return
            self.__closed = True
        log_message("[desktop] 已停止向界面转发输出事件（窗口已关闭）")

    def __is_closed(self):
        with self.__lock:
            return self.__closed
