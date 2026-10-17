"""``python -m desktop`` 入口（契约 C4 第 2 条的统一启动方式）。

S4 阶段没有真实编排器可注入，所以这里用 ``UnwiredOrchestrator`` 起窗口：
能开、能输入、能关。S5 装配角色会把真正的编排器接进来。
"""

from desktop.app import DEFAULT_WINDOW_TITLE
from desktop.errors import DesktopStartupError
from desktop.stdio_fallback import log_message
from desktop.unwired_orchestrator import UnwiredOrchestrator


def main(blocking=True):
    """启动桌面端。``blocking=False`` 时只建窗口不跑事件循环（测试用），返回关闭句柄。"""
    from desktop import run as run_desktop
    from desktop import start as start_desktop

    orchestrator = UnwiredOrchestrator()
    if blocking:
        return run_desktop(orchestrator, window_title=DEFAULT_WINDOW_TITLE)
    return start_desktop(orchestrator, window_title=DEFAULT_WINDOW_TITLE)


if __name__ == "__main__":
    try:
        main(blocking=True)
    except DesktopStartupError as error:
        log_message("[desktop] 启动失败：" + str(error))
        print("[desktop] 启动失败：" + str(error))
