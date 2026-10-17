"""平台框架测试共用的测试替身（不含生产代码）。

这些替身只实现 ``BaseAgent`` / ``BaseLLM`` 的公开契约，用来在不联网、
不依赖真实模型的前提下观察 ``BaseAgent.chat()`` 的既有输出行为。
"""

from ai_agent_factory.agent.baseagent import BaseAgent
from ai_agent_factory.llms.base_llm import BaseLLM


class ScriptedLLM(BaseLLM):
    """按脚本逐轮返回 token 的模型替身。

    ``tokens_per_turn`` 是二维列表：第 n 个元素是第 n 次 ``chat()`` 要产出的 token 序列。
    """

    def __init__(self, tokens_per_turn):
        super().__init__(
            api_key="test-key",
            base_url="http://localhost/v1",
            model_name="test-model",
        )
        self.__turns = [list(tokens) for tokens in tokens_per_turn]
        self.contexts_seen = []

    def chat(self, context, **kwargs):
        # 记录调用当刻的上下文快照，供上下文裁剪测试断言
        self.contexts_seen.append([dict(message) for message in context])
        if not self.__turns:
            raise AssertionError("测试脚本里已经没有更多轮次的 token 了")
        return iter(self.__turns.pop(0))


class FailingLLM(BaseLLM):
    """调用即失败的模型替身，用于验证 error 事件。"""

    def __init__(self, error):
        super().__init__(
            api_key="test-key",
            base_url="http://localhost/v1",
            model_name="test-model",
        )
        self.error = error

    def chat(self, context, **kwargs):
        raise self.error


class MidStreamFailingLLM(BaseLLM):
    """先吐出若干 token 再失败的模型替身，模拟流式中途断开。"""

    def __init__(self, prefix_tokens, error):
        super().__init__(
            api_key="test-key",
            base_url="http://localhost/v1",
            model_name="test-model",
        )
        self.prefix_tokens = list(prefix_tokens)
        self.error = error

    def chat(self, context, **kwargs):
        return self.__generate()

    def __generate(self):
        for token in self.prefix_tokens:
            yield token
        raise self.error


class RecordingAgent(BaseAgent):
    """记录 ``token_deal`` / ``todo`` 调用的智能体替身。

    两个回调的实现形状与 ``myagent/`` 下四个业务智能体一致：
    ``token_deal`` 原样 ``print`` 每个 token，``todo`` ``print`` 一整行完整回复。
    stdout 因此可以被逐字断言。
    """

    def __init__(self, basellm, max_context=20):
        super().__init__(basellm, "你是一个测试用智能体。", max_context)
        self.token_calls = []
        self.todo_calls = []

    def token_deal(self, result):
        self.token_calls.append(result)
        print(result, end="", flush=True)

    def todo(self, token):
        self.todo_calls.append(token)
        print(f"[todo]{token}")
