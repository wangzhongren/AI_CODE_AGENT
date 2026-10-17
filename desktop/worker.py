"""工作线程：把长任务挪出界面线程（本模块**不依赖 Qt**）。

管线一次提交要跑多次 LLM 往返，放在界面线程里窗口就会白屏假死。
这里用 ``threading.Thread`` 跑一次提交，事件仍由 C1 在工作线程里回调，
经 ``OutputEventForwarder`` → Qt 信号回到界面线程。
"""

import threading

from desktop.stdio_fallback import log_message

THREAD_NAME = "desktop-pipeline"


class PipelineRunner:
    """一次只跑一个任务的执行器。

    - ``submit(requirement)``：把需求丢到工作线程；已有任务在跑时**拒绝**并返回 ``False``。
    - ``cancel() + join(timeout)``：关闭时先拒绝新任务，再等工作线程退出。

    已知限制：Python 线程无法被强杀，所以取消只能在任务边界生效——正在跑的
    LLM 调用必须自己结束。关闭后仍存活的线程是 daemon 线程，不会阻止进程退出；
    ``join`` 超时会打印警告，不会假装回收成功。
    """

    def __init__(self, submit_call, forwarder):
        if not callable(submit_call):
            raise TypeError("PipelineRunner 需要可调用的提交动作，实际收到: " + repr(type(submit_call)))
        self.__submit_call = submit_call
        self.__forwarder = forwarder
        self.__lock = threading.Lock()
        self.__thread = None
        self.__cancelled = False
        self.__on_task_finished = None

    def set_on_task_finished(self, callback):
        """设置「任务结束」回调（界面用它恢复按钮状态）。回调在工作线程里被调用。"""
        self.__on_task_finished = callback

    @property
    def is_busy(self):
        """是否还有任务在跑。"""
        with self.__lock:
            thread = self.__thread
        if thread is None:
            return False
        return thread.is_alive()

    @property
    def is_cancelled(self):
        with self.__lock:
            return self.__cancelled

    def submit(self, requirement):
        """启动一次提交。接受返回 ``True``，拒绝（忙 / 已关闭）返回 ``False``。"""
        with self.__lock:
            if self.__cancelled:
                return False
            running = self.__thread
            if running is not None and running.is_alive():
                return False
            worker = threading.Thread(
                target=self.__run_once,
                args=(requirement,),
                name=THREAD_NAME,
                daemon=True,
            )
            self.__thread = worker
        worker.start()
        return True

    def cancel(self):
        """拒绝后续任务。可重复调用。"""
        with self.__lock:
            self.__cancelled = True

    def join(self, timeout):
        """等工作线程退出。返回 ``True`` 表示已回收，``False`` 表示超时仍在跑。"""
        with self.__lock:
            thread = self.__thread
        if thread is None:
            return True
        thread.join(timeout)
        if thread.is_alive():
            log_message(
                "[desktop] 警告：工作线程在 " + str(timeout) + " 秒内没有退出，"
                "管线没有响应取消；该线程是 daemon，不会阻止进程退出。"
            )
            return False
        return True

    def __run_once(self, requirement):
        """工作线程主体：跑一次提交，任何异常都要让用户看见。"""
        self.__forwarder.reset_turn()
        try:
            self.__submit_call(requirement)
        except Exception as exception:
            if self.__forwarder.saw_error:
                # C1 已经发过 error 事件（界面已显示），这里只留一条诊断
                log_message("[desktop] 管线抛出异常，已通过 C1 error 事件上报：" + repr(exception))
            else:
                self.__forwarder.report_local_error(exception)
        finally:
            callback = self.__on_task_finished
            if callback is not None:
                callback()
