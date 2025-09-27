
from abc import ABC, abstractmethod
from typing import Iterable, Dict, Any

class BaseLLM(ABC):
    def __init__(self, api_key: str, base_url: str, model_name: str):
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name

    @abstractmethod
    def chat(self, context: list[Dict[str, str]], **kwargs) -> Iterable[str]:
        """
        抽象方法：给定上下文，返回一个 token 的迭代器。
        
        参数:
            context: 对话历史，例如
                [
                    {"role": "system", "content": "你是一个助手"},
                    {"role": "user", "content": "你好"},
                ]
            kwargs: 额外参数，例如 temperature, max_tokens
        
        返回:
            一个可迭代对象，逐个产出字符串 token。
        """
        pass

        
    