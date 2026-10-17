"""业务智能体 todo() 自递归的轮数上限测试。

背景（缺陷）：`BackendDeveloperAgent` / `FrontendDeveloperAgent` /
`ProjectManagerAgent` 的 `todo()` 在检测到文件操作标签后会再调一次
`self.chat(...)`，而 `chat()` 又会回调 `todo()`。模型若持续返回文件操作
指令，这个循环没有任何上限，实测跑到 494 轮后 RecursionError，异常还被
自身的 `try/except` 吞掉，同时在真实环境里持续消耗 API 额度。

本文件的用例用替身 LLM 构造「永远返回文件操作标签」的情形，验证：
1. 递归一定在上限处停下；
2. 停下时向 stderr 输出含轮数的可见警告；
3. 正常路径（一两轮就结束）行为不变。

所有 LLM 调用都是替身，不触网、不写仓库文件。
"""

import contextlib
import io

import pytest

from ai_agent_factory.llms.base_llm import BaseLLM
from myagent.backend_developer_agent import BackendDeveloperAgent
from myagent.frontend_developer_agent import FrontendDeveloperAgent
from myagent.project_manager_agent import ProjectManagerAgent


# 智能体一轮回复里只要带一条文件操作标签，todo() 就会再调一次模型
AGENT_FILE_OP_REPLY = "<list_files />"
AGENT_FINAL_REPLY = "全部文件已生成，任务完成。"

# FileOperationHandler 会把标签交给 LLM 再提取成结构化操作。
# 替身这里返回空数组：标签仍在文本里（has_file_operations 为真），
# 但没有可执行的操作，于是三个智能体都会走到「再调一次 chat()」这条路径上，
# 也正是不写盘、最适合用来测递归上限的形态。
EXTRACTION_REPLY = "[]"
EXTRACTION_PROMPT_MARK = "文件操作指令提取器"


class ScriptedLLM(BaseLLM):
    """替身 LLM：按脚本返回固定回复，并记录被调用次数。

    参数:
        agent_replies: 智能体自身对话使用的回复序列。用完后重复最后一条，
            这样 `["<list_files />"]` 就表示「永远返回文件操作标签」。
    """

    def __init__(self, agent_replies):
        # BaseLLM 要求三个参数，这里全部是占位值，不会真的用来发请求
        super().__init__(api_key="fake-key", base_url="http://fake.local", model_name="fake-model")
        self.agent_replies = list(agent_replies)
        self.agent_chat_calls = 0
        self.extraction_chat_calls = 0

    def chat(self, context, **kwargs):
        system_prompt = context[0]["content"]
        if EXTRACTION_PROMPT_MARK in system_prompt:
            self.extraction_chat_calls += 1
            return iter([EXTRACTION_REPLY])
        index = self.agent_chat_calls
        if index >= len(self.agent_replies):
            index = len(self.agent_replies) - 1
        self.agent_chat_calls += 1
        return iter([self.agent_replies[index]])


AGENT_FACTORIES = [
    (BackendDeveloperAgent, "BackendDeveloperAgent"),
    (FrontendDeveloperAgent, "FrontendDeveloperAgent"),
    (ProjectManagerAgent, "ProjectManagerAgent"),
]


def make_agent(agent_class, replies, tmp_path):
    """构造智能体，并把文件操作落地目录改到临时目录。"""
    agent = agent_class(ScriptedLLM(replies))
    agent.output_dir = str(tmp_path)
    agent.fo.output_dir = str(tmp_path)
    return agent


@pytest.mark.parametrize("agent_class,agent_name", AGENT_FACTORIES)
def test_runaway_file_ops_stop_at_round_limit(agent_class, agent_name, tmp_path):
    """模型永远返回文件操作标签时，递归必须在上限处停下并给出可见警告。"""
    agent = make_agent(agent_class, [AGENT_FILE_OP_REPLY], tmp_path)
    captured_stderr = io.StringIO()

    with contextlib.redirect_stderr(captured_stderr):
        agent.chat("开始生成")

    warning = captured_stderr.getvalue()
    # 1. 递归停下：一次初始调用 + MAX_FOLLOWUP_ROUNDS 次后续调用
    assert agent.basellm.agent_chat_calls == agent.MAX_FOLLOWUP_ROUNDS + 1
    # 2. 停下时用户看得见，且消息里带轮数
    assert agent_name in warning
    assert "上限" in warning
    assert str(agent.MAX_FOLLOWUP_ROUNDS) in warning
    # 3. 计数已清零，下一次外部请求仍有完整额度
    assert agent.followup_round == 0


@pytest.mark.parametrize("agent_class,agent_name", AGENT_FACTORIES)
def test_normal_path_output_unchanged(agent_class, agent_name, tmp_path):
    """第二轮不再返回文件操作时，按原有一轮收尾，不出现任何上限警告。"""
    agent = make_agent(agent_class, [AGENT_FILE_OP_REPLY, AGENT_FINAL_REPLY], tmp_path)
    captured_stdout = io.StringIO()
    captured_stderr = io.StringIO()

    with contextlib.redirect_stdout(captured_stdout):
        with contextlib.redirect_stderr(captured_stderr):
            agent.chat("开始生成")

    stdout = captured_stdout.getvalue()
    # 一次初始调用 + 一次后续调用，然后自然结束
    assert agent.basellm.agent_chat_calls == 2
    assert agent.followup_round == 0
    assert captured_stderr.getvalue() == ""
    # 既有输出保持不变：首轮报「检测到文件操作指令」，末轮把模型回复原样回显
    assert "检测到文件操作指令" in stdout
    assert AGENT_FINAL_REPLY in stdout


@pytest.mark.parametrize("agent_class,agent_name", AGENT_FACTORIES)
def test_reserve_followup_round_counts_and_resets(agent_class, agent_name, tmp_path):
    """额度判定本身：前 N 次放行，第 N+1 次拒绝并清零。"""
    agent = make_agent(agent_class, [AGENT_FINAL_REPLY], tmp_path)
    captured_stderr = io.StringIO()

    with contextlib.redirect_stderr(captured_stderr):
        granted = [agent.reserve_followup_round() for _ in range(agent.MAX_FOLLOWUP_ROUNDS)]
        refused = agent.reserve_followup_round()

    assert all(granted) is True
    assert refused is False
    assert str(agent.MAX_FOLLOWUP_ROUNDS) in captured_stderr.getvalue()
    assert agent.followup_round == 0


def test_round_limit_value_is_bounded():
    """上限必须是明确的正整数，不能退化成 0 或无限。"""
    for agent_class, agent_name in AGENT_FACTORIES:
        limit = agent_class.MAX_FOLLOWUP_ROUNDS
        assert isinstance(limit, int)
        assert 0 < limit <= 20
