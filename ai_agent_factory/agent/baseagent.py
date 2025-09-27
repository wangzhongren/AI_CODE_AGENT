from abc import ABC, abstractmethod
from ai_agent_factory.llms.base_llm import BaseLLM

class BaseAgent(ABC):

    def reset_context(self):
        """重置对话上下文，保留系统提示"""
        self.__context = [{"role": "system", "content": self.system_prompt}]

    """
    抽象基类，用于定义 AI 代理的基本行为，管理对话上下文并与底层语言模型交互。

    属性:
        basellm (BaseLLM): 底层的语言模型实例，用于处理对话请求。
        system_prompt (str): 系统提示，定义 AI 代理的行为或角色。
        __context (list[dict]): 对话上下文，存储系统提示、用户消息和 AI 回复。
        max_context (int): 最大上下文长度，控制历史消息的数量以避免过长。
    """
    def get_context(self):
        return self.__context;

    def __init__(self, basellm: BaseLLM, system_prompt: str, max_context: int = 20):
        """
        初始化 BaseAgent 实例。

        参数:
            basellm (BaseLLM): 底层语言模型实例，用于处理对话请求。
            system_prompt (str): 系统提示，定义 AI 代理的初始行为或角色。
            max_context (int, optional): 最大上下文消息数，默认为 20。
        """
        self.basellm = basellm
        self.system_prompt = system_prompt
        # 初始化上下文，包含系统提示作为第一条消息
        self.__context = [{"role": "system", "content": system_prompt}]
        self.max_context = max_context

    @abstractmethod
    def todo(self, token: str):
        """
        抽象方法，子类需实现，用于处理完整的 AI 回复。

        参数:
            token (str): AI 生成的完整回复内容。

        注意:
            子类必须实现此方法以定义具体的回调逻辑。
        """
        pass

    @abstractmethod
    def token_deal(self, result: str):
        """
        抽象方法，子类需实现，用于处理流式返回的每个 token。

        参数:
            result (str): AI 生成的单个 token。

        注意:
            子类必须实现此方法以定义 token 级别的处理逻辑。
        """
        pass

    def chat(self, message: str) -> str:
        """
        处理用户输入消息，调用底层语言模型生成回复，并管理对话上下文。

        参数:
            message (str): 用户输入的消息。

        返回:
            str: AI 生成的完整回复内容。

        流程:
            1. 将用户消息添加到上下文。
            2. 调用底层语言模型生成流式回复。
            3. 拼接流式 token 并调用 token_deal 进行处理。
            4. 保存 AI 回复到上下文。
            5. 控制上下文长度，保留系统提示和最近的消息。
            6. 调用 todo 回调处理完整回复。
        """
        # 添加用户消息到上下文
        self.__context.append({"role": "user", "content": message})

        # 调用底层语言模型，获取流式回复
        result = self.basellm.chat(self.__context)

        # 拼接流式返回的 token，构成完整回复
        result_all = ""
        for token in result:
            result_all += token
            # 调用 token_deal 处理每个 token（如果子类已实现）
            if self.token_deal:
                self.token_deal(token)

        # 保存 AI 回复到上下文
        self.__context.append({"role": "assistant", "content": result_all})

        # 控制上下文长度，保留系统提示（index 0）和最近 max_context 条消息
        if len(self.__context) > self.max_context:
            self.__context = [self.__context[0]] + self.__context[-self.max_context:]

        # 调用 todo 回调处理完整回复（如果子类已实现）
        if self.todo:
            self.todo(result_all)

        return result_all