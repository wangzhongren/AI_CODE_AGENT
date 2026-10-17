"""桌面客户端包（PySide6）。

契约 C3 第 4 条：**导入本包不得启动界面，也不得导入 Qt**。
所以这里只导出与 Qt 无关的部分；``run`` / ``start`` 在被真正调用时才去导入
``desktop.app``（进而导入 PySide6）。
"""

from desktop.errors import DesktopStartupError
from desktop.output_listener import OutputEventForwarder
from desktop.worker import PipelineRunner

__version__ = "1.0.0"

__all__ = [
    "DesktopStartupError",
    "OutputEventForwarder",
    "PipelineRunner",
    "run",
    "start",
]


def run(orchestrator, *, submit_method_name="chat", window_title=None, stdio_log_directory=None):
    """启动桌面端并进入事件循环（详见 ``desktop.app.run``）。"""
    from desktop.app import run as run_application

    return run_application(
        orchestrator,
        submit_method_name=submit_method_name,
        window_title=window_title,
        stdio_log_directory=stdio_log_directory,
    )


def start(orchestrator, *, submit_method_name="chat", window_title=None, stdio_log_directory=None):
    """建窗口并显示，返回关闭句柄，不进入事件循环（详见 ``desktop.app.start``）。"""
    from desktop.app import start as start_application

    return start_application(
        orchestrator,
        submit_method_name=submit_method_name,
        window_title=window_title,
        stdio_log_directory=stdio_log_directory,
    )
