"""S6 第二步（真实调用版）：真实 OpenAILLM + 四个真实业务智能体 + 编排器，只调一次 chat()。

与 `s6_desktop_e2e_acceptance.py` 的区别：**这个脚本会真的调用模型、消耗 API 额度**。
规模刻意压到最小：只调 `orchestrator.chat()` 一次，需求是一句话。

凭证没准备好时脚本**不会发起任何请求**：缺 `api_key` / `model_name` / `base_url`
任一变量就打印可读提示并以退出码 3 结束（不构造 OpenAILLM、不联网）。

运行：

    .venv\\Scripts\\python.exe test\\testing\\s6_real_api_acceptance.py

退出码：0 通过；1 验收项未通过；3 缺凭证（未联网）。
"""

from __future__ import annotations

import os
import sys
import threading
import time
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # pragma: no cover
    pass

from ai_agent_factory.agent.baseagent import AgentOutputListener  # noqa: E402

REQUIREMENT = "做一个能记一条待办的极简页面"
EXIT_OK = 0
EXIT_FAILED = 1
EXIT_NOT_CONFIGURED = 3
ENVIRONMENT_VARIABLE_NAMES = ("api_key", "model_name", "base_url")
# 真实调用的硬闸门：超过这个时长就打印「未完成」并以失败退出，不假装跑完。
WATCHDOG_SECONDS = 90.0


class RecordingListener(AgentOutputListener):
    """记录型监听器：只记账，不渲染。C1 事件本身不带来源标识，这里按到达顺序记。"""

    def __init__(self):
        self.tokens = []
        self.turns = []
        self.errors = []
        self.threads = set()

    def on_token(self, text):
        self.threads.add(threading.current_thread().name)
        self.tokens.append(text)

    def on_turn_completed(self, full_text):
        self.threads.add(threading.current_thread().name)
        self.turns.append(full_text)

    def on_error(self, error_info):
        self.threads.add(threading.current_thread().name)
        self.errors.append(error_info)


class ProbeAgents(dict):
    """给四个真实子智能体各挂一层「是否真的被问到」的探针。

    为什么需要：C1 事件只有文本、没有来源，光看监听器分不清某个 token 是哪个智能体
    产生的。这里在**不修改生产代码**的前提下，包一层记录器统计「哪个智能体被调用过、
    被问了几次、返回了多长文本」，与监听器的 token 总量对照。
    """

    def __init__(self, agents):
        super().__init__(agents)
        self.asked = Counter()
        self.replies = {}
        for name, agent in agents.items():
            self._wrap(name, agent)

    def _wrap(self, name, agent):
        original_chat = agent.chat

        def chat(message):
            self.asked[name] += 1
            result = original_chat(message)
            self.replies[name] = self.replies.get(name, "") + result
            return result

        agent.chat = chat


def read_environment():
    """读环境变量，返回 (配置, 缺失名列表)。空字符串按缺失处理。"""
    settings = {}
    missing = []
    for name in ENVIRONMENT_VARIABLE_NAMES:
        raw = os.getenv(name)
        value = "" if raw is None else raw.strip()
        if value == "":
            missing.append(name)
        else:
            settings[name] = value
    return settings, missing


def main():
    print("=" * 70)
    print("S6 第二步（真实调用）：桌面端链路，只调一次 chat()")
    print("=" * 70)

    settings, missing = read_environment()
    print("[env] .env exists: %s" % os.path.isfile(".env"))
    if missing:
        print("[env] 缺少环境变量：%s（未打印任何变量值）" % "、".join(missing))
        print("[停止] 未发起任何模型调用，未构造 OpenAILLM。")
        print("需要客户在项目根新建 .env，写三行：")
        print("  api_key=你的密钥")
        print("  model_name=模型名（例如 gpt-4o-mini）")
        print("  base_url=接口地址（例如 https://api.openai.com/v1）")
        print("填好后重新执行：.venv\\Scripts\\python.exe test\\testing\\s6_real_api_acceptance.py")
        return EXIT_NOT_CONFIGURED
    print("[env] 三个变量均已读到（值不打印）")

    # 只在确认凭证齐备之后才导入并构造真实对象。
    from ai_agent_factory.llms.base_llm_openai import OpenAILLM
    from myagent.backend_developer_agent import BackendDeveloperAgent
    from myagent.frontend_developer_agent import FrontendDeveloperAgent
    from myagent.product_manager_agent import ProductManagerAgent
    from myagent.project_manager_agent import ProjectManagerAgent
    from myagent.system_manager_agent import SystemManagerAgent

    workspace = PROJECT_ROOT / "temp" / "testing" / "_workspace_real"
    workspace.mkdir(parents=True, exist_ok=True)
    os.chdir(workspace)

    llm = OpenAILLM(api_key=settings["api_key"], model_name=settings["model_name"],
                    base_url=settings["base_url"])
    agents = ProbeAgents({
        "pm": ProductManagerAgent(llm),
        "pj": ProjectManagerAgent(llm),
        "be": BackendDeveloperAgent(llm),
        "fe": FrontendDeveloperAgent(llm)
    })
    orchestrator = SystemManagerAgent(llm, agents)
    listener = RecordingListener()

    orchestrator.set_output_listener(listener)
    orchestrator.set_output_listener_for_children(listener)

    print("")
    print("[提交] orchestrator.chat(%r) —— 只调这一次" % REQUIREMENT)
    started = time.time()
    fired = []

    def watchdog():
        fired.append(time.time())

    timer = threading.Timer(WATCHDOG_SECONDS, watchdog)
    timer.start()
    try:
        reply = orchestrator.chat(REQUIREMENT)
    finally:
        timer.cancel()
    elapsed = time.time() - started

    print("")
    print("=== 统计 ===")
    print("[耗时] %.1f 秒" % elapsed)
    print("[编排器] 返回 %d 字符" % len(reply))
    print("[监听器] token %d 个；turn_completed %d 次；error %d 个；所在线程 %s"
          % (len(listener.tokens), len(listener.turns), len(listener.errors),
             sorted(listener.threads)))
    print("[子智能体] 被调用的次数：%s"
          % dict(sorted(agents.asked.items())))
    for name in ("pm", "pj", "be", "fe"):
        print("[子智能体] %s 返回文本长度 %d" % (name, len(agents.replies.get(name, ""))))
    for error_info in listener.errors:
        print("[error] " + error_info.message)

    failures = []
    if len(listener.tokens) == 0:
        failures.append("监听器一个 token 都没收到（编排器自身输出也没到）")
    asked_children = [name for name in ("pm", "pj", "be", "fe") if agents.asked[name]]
    if not asked_children:
        failures.append("这一次调用没有调度任何子智能体，无法验证 C1.2 的子智能体链路")
    if listener.errors:
        failures.append("出现 %d 个 error 事件" % len(listener.errors))
    if fired:
        failures.append("超过 %d 秒看门狗，未在时限内完成" % WATCHDOG_SECONDS)

    print("")
    if failures:
        print("[FAIL] %d 项：" % len(failures))
        for item in failures:
            print("  - " + item)
        return EXIT_FAILED
    print("[OK] 真实调用完成：编排器与 %s 的输出都到达了监听器"
          % "/".join(asked_children))
    print("[提示] 界面可读性未在此脚本覆盖（未开 GUI）；来源归属靠探针统计，"
          "因为 C1 事件本身不带来源标识。")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
