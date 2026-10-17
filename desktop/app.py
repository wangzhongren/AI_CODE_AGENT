"""公开启动操作与关闭句柄（契约 C3）。

两个入口:

- ``start(orchestrator, ...)``：建好窗口并显示，**不进入事件循环**，返回关闭句柄。
  界面层的测试与「由别人托管事件循环」的场合用它。
- ``run(orchestrator, ...)``：``start`` + 进入事件循环，窗口关掉后返回同一个句柄。
  ``python -m desktop`` 用它。

两个都不接受「自己去造编排器」：编排器由外部注入（S5 装配角色负责真实接线），
本模块不持有任何业务逻辑。
"""

import sys
import threading

from desktop.errors import DesktopStartupError
from desktop.output_listener import OutputEventForwarder
from desktop.stdio_fallback import ensure_standard_streams, log_message
from desktop.worker import PipelineRunner

DEFAULT_WINDOW_TITLE = "代码生成助手（桌面端）"
DEFAULT_SUBMIT_METHOD_NAME = "chat"
DEFAULT_SHUTDOWN_TIMEOUT_SECONDS = 10.0


class DesktopHandle:
    """关闭句柄：只暴露生命周期操作。

    不暴露编排器、不暴露任何 Qt 对象（契约 C3 第 3 条）。测试或诊断需要看界面时，
    用 Qt 自己提供的 ``QApplication.topLevelWidgets()``，不要从这里挖。
    """

    def __init__(self, application, window, runner, forwarder, orchestrator):
        self.__application = application
        self.__window = window
        self.__runner = runner
        self.__forwarder = forwarder
        self.__orchestrator = orchestrator
        self.__closed = False
        self.__lock = threading.Lock()

    @property
    def is_closed(self):
        """是否已经关闭（``shutdown()`` 被调用过）。"""
        with self.__lock:
            return self.__closed

    def shutdown(self, timeout=DEFAULT_SHUTDOWN_TIMEOUT_SECONDS):
        """中断在跑的任务、回收线程、取消订阅、关闭窗口。可重复调用。"""
        with self.__lock:
            if self.__closed:
                return
            self.__closed = True

        # 1. 先停止转发：工作线程就算还在跑，也不会再往已关闭的界面写东西
        self.__forwarder.close()
        # 2. 拒绝新任务，并等待在跑的工作线程退出
        self.__runner.cancel()
        self.__runner.join(timeout)
        # 3. 取消订阅，避免编排器继续往这个句柄回调
        self.__unsubscribe()
        # 4. 关窗口并退出事件循环
        try:
            self.__window.close()
            self.__application.quit()
        except Exception as error:
            log_message("[desktop] 关闭窗口时出错：" + repr(error))

    def run_event_loop(self):
        """进入 Qt 事件循环，窗口关闭后返回。"""
        with self.__lock:
            already_closed = self.__closed
        if already_closed:
            return 0
        return self.__application.exec()

    def process_events(self):
        """处理一批待办事件（没有事件循环的场合用，例如离屏冒烟测试）。"""
        return self.__application.processEvents()

    def __unsubscribe(self):
        clear_call = getattr(self.__orchestrator, "clear_output_listener", None)
        if not callable(clear_call):
            log_message("[desktop] 编排器没有公开的 clear_output_listener，跳过取消订阅（契约 C1 建议提供）")
            return
        try:
            clear_call()
        except Exception as error:
            log_message("[desktop] 取消编排器的输出订阅失败：" + repr(error))


def start(orchestrator, *, submit_method_name=DEFAULT_SUBMIT_METHOD_NAME, window_title=None, stdio_log_directory=None):
    """建窗口并显示，返回关闭句柄。不进入事件循环。

    参数:
        orchestrator: 由外部注入的编排器对象。只需要两个公开能力：
            ``set_output_listener(listener)``（契约 C1）与一个提交方法
            （默认为 ``chat(requirement)``）。
        submit_method_name (str): 提交方法名，按编排层的公开入口配置。
        window_title (str | None): 窗口标题。
        stdio_log_directory (str | None): 无控制台模式下日志放哪。

    异常:
        DesktopStartupError: 缺 PySide6、编排器不合契约、订阅失败。抛出前会清理
            已经创建的资源（窗口、工作线程、订阅）。
    """
    # 无控制台模式先兜住 stdout/stderr，必须在建窗口之前（后面到处都在 print）
    ensure_standard_streams(stdio_log_directory)

    submit_call = _validate_orchestrator(orchestrator, submit_method_name)
    application_class, bridge_module, window_module = _import_qt_modules()
    application = _create_application(application_class)

    signal_bridge = bridge_module.OutputSignalBridge()
    main_window = window_module.MainWindow(_resolve_window_title(window_title))
    forwarder = OutputEventForwarder(signal_bridge)
    runner = PipelineRunner(submit_call, forwarder)
    handle = DesktopHandle(application, main_window, runner, forwarder, orchestrator)

    signal_bridge.token_received.connect(main_window.display_token)
    signal_bridge.turn_completed.connect(main_window.display_turn_completed)
    signal_bridge.error_received.connect(main_window.display_error)
    signal_bridge.task_finished.connect(main_window.finish_task)
    runner.set_on_task_finished(signal_bridge.task_finished.emit)
    main_window.set_submit_handler(runner.submit)
    main_window.set_close_handler(handle.shutdown)

    try:
        orchestrator.set_output_listener(forwarder)
        main_window.show()
    except Exception as error:
        handle.shutdown()
        raise DesktopStartupError(
            "启动桌面端失败（订阅输出事件或显示窗口）：" + repr(error)
        ) from error

    log_message("[desktop] 窗口已就绪：" + _resolve_window_title(window_title))
    return handle


def run(orchestrator, *, submit_method_name=DEFAULT_SUBMIT_METHOD_NAME, window_title=None, stdio_log_directory=None):
    """``start`` + 进入事件循环；窗口关闭后返回关闭句柄（已关闭状态）。"""
    handle = start(
        orchestrator,
        submit_method_name=submit_method_name,
        window_title=window_title,
        stdio_log_directory=stdio_log_directory,
    )
    try:
        handle.run_event_loop()
    finally:
        handle.shutdown()
    return handle


def _validate_orchestrator(orchestrator, submit_method_name):
    """检查注入对象是否具备需要的两个公开能力，返回提交动作。"""
    if orchestrator is None:
        raise DesktopStartupError("启动桌面端需要传入编排器对象，实际收到 None。")
    type_name = type(orchestrator).__name__
    setter = getattr(orchestrator, "set_output_listener", None)
    if not callable(setter):
        raise DesktopStartupError(
            "编排器缺少公开方法 set_output_listener（契约 C1），拿不到流式输出。"
            "实际类型：" + type_name
        )
    submit_call = getattr(orchestrator, submit_method_name, None)
    if not callable(submit_call):
        raise DesktopStartupError(
            "编排器缺少可调用的提交方法 " + submit_method_name + "（实际类型：" + type_name + "）。"
        )
    return submit_call


def _import_qt_modules():
    """导入 PySide6 相关模块；缺依赖时给出可读错误而不是堆栈。"""
    try:
        from PySide6.QtWidgets import QApplication
        from desktop import bridge as bridge_module
        from desktop import window as window_module
    except ImportError as error:
        raise DesktopStartupError(
            "启动桌面端需要 PySide6，导入失败：" + str(error)
            + "。请在项目根目录执行：.venv\\Scripts\\python.exe -m pip install --requirement requirements.txt"
        ) from error
    return QApplication, bridge_module, window_module


def _create_application(application_class):
    """复用已有的 QApplication（离屏测试会跨用例复用），没有就新建一个。"""
    application = application_class.instance()
    if application is not None:
        return application
    program_name = "desktop"
    if sys.argv and sys.argv[0]:
        program_name = sys.argv[0]
    try:
        return application_class([program_name])
    except Exception as error:
        raise DesktopStartupError(
            "创建 Qt 应用失败（常见原因：没有图形环境，或没设 QT_QPA_PLATFORM=offscreen）：" + repr(error)
        ) from error


def _resolve_window_title(window_title):
    if window_title is None:
        return DEFAULT_WINDOW_TITLE
    return window_title
