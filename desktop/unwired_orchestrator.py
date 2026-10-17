"""S4 阶段的占位编排器：让 ``python -m desktop`` 能开窗、能看、能关。

真正的编排器（``SystemManagerAgent``）由装配角色在 S5 接线：读环境变量、
构造 LLM 与业务智能体、再把实例注入 ``desktop.run(...)``。本类**不含任何业务逻辑**，
只把「还没接线」这件事讲清楚——提交时抛一个可读异常，界面会用醒目的错误样式显示。
"""


class UnwiredOrchestrator:
    """只满足启动层契约（C1 订阅 + 一个提交方法）的空壳编排器。"""

    def __init__(self):
        self.__listener = None

    @property
    def has_listener(self):
        """是否已有监听器订阅（诊断用）。"""
        return self.__listener is not None

    def set_output_listener(self, listener):
        self.__listener = listener

    def clear_output_listener(self):
        self.__listener = None

    def chat(self, message):
        """占位提交：明确告诉用户还没接到编排层，而不是假装在工作。"""
        raise RuntimeError(
            "桌面端还没接到编排层（S4 只做界面骨架）。等装配步骤把真实编排器接进来后，"
            "这里才会真的生成项目。"
        )
