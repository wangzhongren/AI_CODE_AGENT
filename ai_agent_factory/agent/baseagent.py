
from abc import ABC, abstractmethod
from dataclasses import dataclass
from ai_agent_factory.llms.base_llm import BaseLLM


@dataclass(frozen=True)
class AgentOutputError:
    """运行期错误的纯数据描述，随 ``error`` 事件交给监听器。

    属性:
        exception (BaseException): 原始异常对象，监听器可据此判断类型。
        message (str): 可读的错误说明，形如 ``RuntimeError: 模型服务不可用``。
    """

    exception: BaseException
    message: str


class AgentOutputListener(ABC):
    """``BaseAgent`` 运行期输出事件的监听器契约。

    用途：让界面层（例如桌面客户端）不用去读 stdout，就能拿到流式增量、
    一轮完整回复和运行期错误。

    约定:
        - 三个回调都在**调用 ``chat()`` 的那个线程**里被触发；本框架不建线程。
        - 回调里不要抛异常。抛出的异常会原样向上传播（不会被吞掉），
          并会打断正在进行的 ``chat()``。
        - 取消订阅用 ``BaseAgent.clear_output_listener()``。
    """

    @abstractmethod
    def on_token(self, text: str):
        """收到一个流式增量文本。"""
        pass

    @abstractmethod
    def on_turn_completed(self, full_text: str):
        """一轮 ``chat()`` 的完整回复，内容与 ``chat()`` 的返回值一致。"""
        pass

    @abstractmethod
    def on_error(self, error_info: AgentOutputError):
        """运行期发生错误。本回调返回后，原始异常仍会继续向上抛出。"""
        pass


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
        __output_listener (AgentOutputListener | None): 输出事件监听器，未订阅时为 None。
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
        # 未订阅输出事件时的默认状态：只有 token_deal / todo 这一条既有通道
        self.__output_listener = None

    def set_output_listener(self, listener: AgentOutputListener):
        """
        订阅运行期输出事件（契约 C1）。

        参数:
            listener (AgentOutputListener): 事件监听器，须实现
                ``on_token`` / ``on_turn_completed`` / ``on_error``。

        说明:
            订阅只影响这个 agent 实例。``token_deal`` / ``todo`` 仍然照常被调用、
            仍然 print 到 stdout（事件与既有通道并存，不抑制终端输出）。
            ``myagent/`` 的项目经理、后端、前端智能体会在 ``todo`` 里调度子智能体，
            子智能体是各自独立的实例，需要各自订阅才能取到它们的事件。
        """
        if not isinstance(listener, AgentOutputListener):
            raise TypeError(
                "输出监听器必须是 AgentOutputListener 的实例，实际收到: "
                + repr(type(listener))
            )
        self.__output_listener = listener

    def clear_output_listener(self):
        """取消订阅输出事件，回到「只有 token_deal / todo」的既有行为。可重复调用。"""
        self.__output_listener = None

    def __emit_token(self, text: str):
        """把流式增量交给监听器；未订阅时什么也不做。"""
        listener = self.__output_listener
        if listener is None:
            return
        listener.on_token(text)

    def __emit_turn_completed(self, full_text: str):
        """把一轮完整回复交给监听器；未订阅时什么也不做。"""
        listener = self.__output_listener
        if listener is None:
            return
        listener.on_turn_completed(full_text)

    def __emit_error(self, exception: Exception):
        """把运行期错误交给监听器；未订阅时什么也不做。

        监听器自身抛出的异常不在此处捕获，会原样向上传播。
        """
        listener = self.__output_listener
        if listener is None:
            return
        detail = str(exception).strip()
        if detail:
            message = f"{type(exception).__name__}: {detail}"
        else:
            message = f"{type(exception).__name__}(异常未附带消息)"
        listener.on_error(AgentOutputError(exception=exception, message=message))

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
            3. 拼接流式 token：每个 token 先发 token 事件，再交给 token_deal。
            4. 保存 AI 回复到上下文。
            5. 控制上下文长度，保留系统提示和最近的消息。
            6. 向监听器发 turn_completed 事件。
            7. 调用 todo 回调处理完整回复。
            8. 任一步抛错时，先向监听器发 error 事件，再把原异常原样抛出。

        顺序约定:
            事件先发、既有回调后走。未订阅监听器时事件发不出去，
            因此第 3、6 步对既有行为没有任何可观察影响。
        """
        # 添加用户消息到上下文
        self.__context.append({"role": "user", "content": message})

        try:
            # 调用底层语言模型，获取流式回复
            result = self.basellm.chat(self.__context)

            # 拼接流式返回的 token，构成完整回复
            result_all = ""
            for token in result:
                result_all += token
                # 先发 token 事件：即使子类回调随后失败，事件流仍是模型输出的完整镜像
                self.__emit_token(token)
                # 再调用 token_deal 处理每个 token（如果子类已实现）
                if self.token_deal:
                    self.token_deal(token)

            # 保存 AI 回复到上下文
            self.__context.append({"role": "assistant", "content": result_all})

            # 控制上下文长度，保留系统提示（index 0）和最近 max_context 条消息
            if len(self.__context) > self.max_context:
                self.__context = [self.__context[0]] + self.__context[-self.max_context:]

            # 完整回复已就绪：先发 turn_completed，再走 todo
            # 这样若 todo 内部再次 chat()，事件顺序是「先本轮完成，再下一轮」
            self.__emit_turn_completed(result_all)

            # 调用 todo 回调处理完整回复（如果子类已实现）
            if self.todo:
                self.todo(result_all)
        except Exception as exception:
            # 先发 error 事件，再原样抛出：不吞异常、不改异常类型
            self.__emit_error(exception)
            raise

        return result_all
