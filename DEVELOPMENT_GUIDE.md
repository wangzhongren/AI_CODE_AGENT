# ai_agent_factory 开发指南

## 项目概述

`ai_agent_factory` 是一个模块化、可扩展的AI代理开发框架，提供了一种简洁的方式来创建与不同语言模型交互的AI代理。该框架采用抽象基类设计模式，使得添加新的语言模型和自定义AI代理变得简单。

## 项目结构

```
ai_agent_factory/
├── agent/
│   └── baseagent.py        # AI代理基类定义
├── llms/
│   ├── base_llm.py         # 语言模型基类定义
│   ├── base_llm_openai.py  # OpenAI模型实现
│   └── openai              # OpenAI相关实现
└── __init__.py
```

## 核心组件

### 1. BaseLLM (抽象基类)

位于 `ai_agent_factory/llms/base_llm.py`，定义所有语言模型的通用接口：

- **属性**：
  - `api_key`: API密钥
  - `base_url`: API基础URL
  - `model_name`: 模型名称

- **方法**：
  - `chat(context, **kwargs) -> Iterable[str]`: 抽象方法，实现流式对话功能

### 2. OpenAILLM (具体实现)

位于 `ai_agent_factory/llms/base_llm_openai.py`，实现了BaseLLM接口，用于与OpenAI API交互：

- 支持流式返回
- 包含错误处理机制
- 支持温度、最大token数等参数

### 3. BaseAgent (抽象基类)

位于 `ai_agent_factory/agent/baseagent.py`，定义AI代理的基本行为：

- **属性**：
  - `basellm`: 底层语言模型实例
  - `system_prompt`: 系统提示词
  - `__context`: 对话上下文（私有）
  - `max_context`: 最大上下文长度

- **方法**：
  - `todo(token)`: 抽象方法，处理完整AI回复
  - `token_deal(result)`: 抽象方法，处理流式token
  - `chat(message) -> str`: 处理用户消息的核心方法

## 开发流程

### 1. 创建新的语言模型实现

要支持新的语言模型，需要继承BaseLLM类：

```python
from ai_agent_factory.llms.base_llm import BaseLLM
from typing import Iterable, Dict, Any

class MyCustomLLM(BaseLLM):
    def __init__(self, api_key: str, base_url: str, model_name: str):
        super().__init__(api_key, base_url, model_name)
        # 初始化客户端

    def chat(self, context: list[Dict[str, str]], **kwargs) -> Iterable[str]:
        # 实现具体的聊天逻辑
        # 逐个 yield token
        pass
```

### 2. 创建自定义AI代理

创建自定义AI代理需要继承BaseAgent类并实现抽象方法：

```python
from ai_agent_factory.agent.baseagent import BaseAgent

class MyCustomAgent(BaseAgent):
    def __init__(self, basellm, system_prompt: str, max_context: int = 20):
        super().__init__(basellm, system_prompt, max_context)

    def todo(self, token: str):
        # 实现完整回复的处理逻辑
        print(f"完整回复: {token}")

    def token_deal(self, result: str):
        # 实现单个token的处理逻辑
        print(result, end='', flush=True)
```

### 3. 使用AI代理

```python
from ai_agent_factory.llms.base_llm_openai import OpenAILLM
from my_custom_agent import MyCustomAgent

# 创建语言模型实例
llm = OpenAILLM(api_key="your-api-key", model_name="gpt-4o-mini")

# 创建AI代理实例
agent = MyCustomAgent(llm, system_prompt="你是一个有用的助手")

# 与AI交互
response = agent.chat("你好")
print(response)
```

## 对话上下文管理

BaseAgent类自动管理对话上下文：

- 初始时添加系统提示词
- 每次对话自动添加用户消息和AI回复
- 限制上下文长度以避免过长的对话历史
- 保留系统提示词在上下文的开始位置

## 错误处理

- 在BaseLLM的实现中应包含适当的错误处理
- OpenAILLM包含了API级别的错误处理
- 建议在自定义实现中也包括错误处理逻辑

## 最佳实践

1. **安全性**：不要在代码中硬编码API密钥，使用环境变量或配置文件
2. **错误处理**：在实现自定义LLM时包含适当的错误处理
3. **资源管理**：确保在适当的地方关闭资源
4. **测试**：为自定义实现编写单元测试
5. **文档**：为自定义类和方法提供清晰的文档

## 扩展性

该框架设计为高度可扩展：
- 可以轻松添加新的语言模型实现
- 可以为特定用例创建自定义AI代理
- 支持不同的API参数和配置选项

## 注意事项

- 在token_deal方法中实现流式输出的处理逻辑
- 在todo方法中实现完整回复的后处理
- 注意上下文长度管理，避免超出模型限制
- 合理设置max_context参数以平衡记忆能力和性能