"""桌面客户端的错误类型。

``DesktopStartupError`` 是「界面起不来」的唯一对外错误类型：消息直接面向用户，
说明缺什么、怎么补，而不是抛一个 ``NoneType`` 堆栈（契约 C3 第 5 条）。
"""


class DesktopStartupError(RuntimeError):
    """桌面端启动失败：缺依赖、编排器不合契约、订阅失败等。"""
