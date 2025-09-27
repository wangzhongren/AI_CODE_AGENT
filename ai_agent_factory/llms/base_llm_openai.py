from openai import OpenAI, APIError
from typing import Iterable, Dict, Any
from ai_agent_factory.llms.base_llm import BaseLLM

class OpenAILLM(BaseLLM):
    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1", model_name: str = "gpt-4o-mini"):
        super().__init__(api_key, base_url, model_name)
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def chat(self, context: list[Dict[str, str]], temperature: float = 0.7, max_tokens: int = None, **kwargs) -> Iterable[str]:
        """
        使用 OpenAI ChatCompletion API 进行对话，支持流式返回 token。

        Args:
            context: 对话上下文，格式为 [{"role": "user", "content": "text"}, ...]
            temperature: 控制生成文本的随机性，默认为 0.7
            max_tokens: 最大 token 数，默认为 None
            **kwargs: 其他传递给 OpenAI API 的参数

        Yields:
            流式返回的 token

        Raises:
            ValueError: 如果 context 格式不正确
            APIError: 如果 OpenAI API 调用失败
            Exception: 其他未预期的错误
        """
        # 验证上下文格式
        for msg in context:
            if not isinstance(msg, dict) or "role" not in msg or "content" not in msg:
                raise ValueError("Each message in context must be a dict with 'role' and 'content' keys")

        # 构建 API 参数
        params = {"temperature": temperature}
        if max_tokens is not None:
            params["max_tokens"] = max_tokens
        params.update(kwargs)

        try:
            with self.client.chat.completions.create(
                model=self.model_name,
                messages=context,
                stream=True,
                **params
            ) as response:
                for event in response:
                    delta = event.choices[0].delta if event.choices else None
                    if delta and delta.content:
                        yield delta.content
        except APIError as e:
            raise Exception(f"OpenAI API error: {str(e)}")
        except Exception as e:
            raise Exception(f"Unexpected error: {str(e)}")