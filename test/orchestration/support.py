"""流程编排测试的替身与工厂。

四个业务智能体与底层 LLM 全部用替身注入：单元测试不访问网络、不依赖真实 LLM。
替身只记录收到的输入，行为可预测。
"""

from myagent.system_manager_agent import SystemManagerAgent


class StubLLM:
    """底层 LLM 替身：记录每次调用，按 token 迭代返回固定文本。"""

    def __init__(self, tokens=("stub-reply",)):
        self.tokens = tuple(tokens)
        self.calls = []

    def chat(self, context):
        # BaseAgent 会逐 token 迭代返回值，因此这里返回迭代器。
        # 记录上下文副本，避免后续修改影响断言。
        copied_context = []
        for message in context:
            copied_context.append(dict(message))
        self.calls.append(copied_context)
        return iter(self.tokens)


class StubBusinessAgent:
    """业务智能体替身：记录收到的消息，并带上流程会读取的属性。"""

    def __init__(self, **attributes):
        self.messages = []
        self.prd = "PRD 内容"
        self.frontend_guide = "前端指导文档"
        self.backend_guide = "后端指导文档"
        self.api_spec = {"paths": {}}
        self.analysis_result = ""
        for name, value in attributes.items():
            setattr(self, name, value)

    def chat(self, message):
        self.messages.append(message)
        return "ok"


def build_manager(**state):
    """构造注入了四个替身的 SystemManagerAgent，可按需覆盖 project_state 标志。"""
    agents = {
        'pm': StubBusinessAgent(),
        'pj': StubBusinessAgent(),
        'fe': StubBusinessAgent(),
        'be': StubBusinessAgent(),
    }
    llm = StubLLM()
    manager = SystemManagerAgent(llm, agents)
    for key, value in state.items():
        if key not in manager.project_state:
            raise KeyError(f"project_state 没有字段 {key}")
        manager.project_state[key] = value
    return manager
