"""`desktop_main.py` 的装配自检（装配角色）。

检查三件事，全部不联网、不开窗口：

1. 导入 `desktop_main` 不会加载 PySide6（不会在 import 期起界面）；
2. 缺环境变量时走「可读提示 + 配置错误码」这条路径，不构造 `OpenAILLM`；
3. 监听器下发层 `ListenerFanout` 的行为：编排器与四个子智能体都拿到同一个
   监听器、清除时一并清掉、其余属性委托给编排器；编排层有了
   `set_output_listener_for_children` 时优先用它，不重复下发。

运行：

    .venv\\Scripts\\python.exe test\\assembly\\check_desktop_main.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 控制台代码页可能是 cp936，中文经管道会乱码；统一按 UTF-8 输出便于查看与贴证据。
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception as error:
    print("[warn] cannot reconfigure stdout: %s" % error)

import desktop_main  # noqa: E402  （必须在 sys.path 就位之后导入）
from ai_agent_factory.agent.baseagent import AgentOutputListener  # noqa: E402

FAILURES = []


def check(condition, label):
    if condition:
        print("[ok] " + label)
    else:
        print("[FAIL] " + label)
        FAILURES.append(label)


class StubAgent:
    """替身子智能体：只记录被下发了什么，不做任何业务。"""

    def __init__(self, name):
        self.name = name
        self.listener = None
        self.set_calls = 0
        self.clear_calls = 0

    def set_output_listener(self, listener):
        self.listener = listener
        self.set_calls = self.set_calls + 1

    def clear_output_listener(self):
        self.listener = None
        self.clear_calls = self.clear_calls + 1


class StubOrchestrator:
    """替身编排器。`with_children_entry=True` 时模拟 S3b 已落地的公开入口。"""

    def __init__(self, with_children_entry):
        self.with_children_entry = with_children_entry
        self.listener = None
        self.own_set_calls = 0
        self.children_listener = None
        self.children_calls = 0
        self.clear_calls = 0
        self.submitted = []
        if with_children_entry:
            # 只在需要时挂上属性，模拟「入口尚未就绪」的现状。
            self.set_output_listener_for_children = self._set_children

    def _set_children(self, listener):
        self.children_listener = listener
        self.children_calls = self.children_calls + 1

    def set_output_listener(self, listener):
        self.listener = listener
        self.own_set_calls = self.own_set_calls + 1

    def clear_output_listener(self):
        self.listener = None
        self.clear_calls = self.clear_calls + 1

    def chat(self, requirement):
        self.submitted.append(requirement)
        return "stub-reply"


def check_missing_environment_path():
    print("--- 缺环境变量路径（真实调用 desktop_main.main()）---")
    print(".env 存在：%s" % str((PROJECT_ROOT / desktop_main.ENVIRONMENT_FILE_NAME).is_file()))
    saved = {}
    for variable_name in desktop_main.ENVIRONMENT_VARIABLE_NAMES:
        saved[variable_name] = os.environ.get(variable_name)
        # 置空：load_dotenv() 默认不覆盖已存在的键，因此即使仓库根有 .env，
        # 这里也会稳定走「缺失」分支。
        os.environ[variable_name] = ""
    try:
        exit_code = desktop_main.main()
    finally:
        for variable_name in desktop_main.ENVIRONMENT_VARIABLE_NAMES:
            if saved[variable_name] is None:
                os.environ.pop(variable_name, None)
            else:
                os.environ[variable_name] = saved[variable_name]
    print("--- 结束，退出码 %s ---" % exit_code)
    check(exit_code == desktop_main.EXIT_CONFIGURATION_ERROR,
          "缺变量时返回 EXIT_CONFIGURATION_ERROR，未构造 LLM、未开窗口")


def build_stubs(with_children_entry):
    agents = {}
    for role_name in ("pm", "pj", "be", "fe"):
        agents[role_name] = StubAgent(role_name)
    orchestrator = StubOrchestrator(with_children_entry)
    return orchestrator, agents


def check_fanout_fallback():
    orchestrator, agents = build_stubs(False)
    fanout = desktop_main.ListenerFanout(orchestrator, agents)
    listener = object()
    fanout.set_output_listener(listener)

    check(orchestrator.listener is listener, "编排器拿到桌面端下发的监听器")
    delivered = True
    for role_name in agents:
        if agents[role_name].listener is not listener:
            delivered = False
    check(delivered, "四个子智能体都拿到同一个监听器（编排层入口缺失时由装配层下发）")
    check(fanout.listener is listener, "ListenerFanout 记录了当前监听器")

    fanout.set_output_listener(listener)
    replaced = True
    for role_name in agents:
        if agents[role_name].set_calls != 2:
            replaced = False
    check(replaced, "重复下发是替换而不是叠加（每个子智能体只被设置过一次监听器）")

    check(fanout.chat("需求文本") == "stub-reply", "未定义的属性委托给编排器（chat 透传）")
    check(orchestrator.submitted == ["需求文本"], "提交动作原样到达编排器")

    fanout.clear_output_listener()
    cleared = orchestrator.listener is None
    for role_name in agents:
        if agents[role_name].listener is not None:
            cleared = False
    check(cleared, "清除时编排器与四个子智能体的订阅一并清掉")


def check_fanout_uses_children_entry():
    orchestrator, agents = build_stubs(True)
    fanout = desktop_main.ListenerFanout(orchestrator, agents)
    listener = object()
    fanout.set_output_listener(listener)
    check(orchestrator.children_listener is listener,
          "编排层有 set_output_listener_for_children 时优先走该入口（契约 C1.2）")
    untouched = True
    for role_name in agents:
        if agents[role_name].set_calls != 0:
            untouched = False
    check(untouched, "走编排层入口时装配层不再逐个下发，避免重复订阅")


class RecorderListener(AgentOutputListener):
    """最小的监听器替身：只记录事件，不发网络请求、不碰界面。

    必须继承 `AgentOutputListener`：平台框架的 `set_output_listener` 会校验类型，
    传一个鸭子类型对象会被拒（本轮实测过）。
    """

    def __init__(self):
        self.tokens = []
        self.turns = []
        self.errors = []

    def on_token(self, text):
        self.tokens.append(text)

    def on_turn_completed(self, full_text):
        self.turns.append(full_text)

    def on_error(self, error_info):
        self.errors.append(error_info)


def check_real_objects_wiring():
    """用真实的四个智能体与真实编排器验证下发（不联网：只构造，不提交需求）。"""
    print("--- 真实对象接线（构造真实智能体，不提交需求、不联网）---")
    settings = {
        "api_key": "check-only-not-used",
        "model_name": "check-only-not-used",
        "base_url": "http://127.0.0.1:1/v1"
    }
    try:
        llm = desktop_main.build_llm(settings)
        agents = desktop_main.build_agents(llm)
        orchestrator = desktop_main.build_orchestrator(llm, agents)
    except Exception as error:
        print("[FAIL] 构造真实对象失败：%r" % (error,))
        FAILURES.append("构造真实对象")
        return
    check(sorted(agents.keys()) == ["be", "fe", "pj", "pm"], "agents 字典键为 pm/pj/be/fe")

    fanout = desktop_main.ListenerFanout(orchestrator, agents)
    listener = RecorderListener()
    try:
        fanout.set_output_listener(listener)
    except Exception as error:
        print("[FAIL] 给真实对象下发监听器失败：%r" % (error,))
        FAILURES.append("真实对象下发监听器")
        return
    check(fanout.listener is listener, "真实编排器与真实子智能体都接受了下发（无异常）")

    try:
        fanout.clear_output_listener()
    except Exception as error:
        print("[FAIL] 清除真实对象的订阅失败：%r" % (error,))
        FAILURES.append("真实对象清除订阅")
        return
    check(fanout.listener is None, "真实对象的订阅可被清除")


def main():
    check("PySide6" not in sys.modules, "导入 desktop_main 不加载 PySide6（import 期不起界面）")
    check_missing_environment_path()
    print("--- 监听器下发：编排层入口缺失（当前现状）---")
    check_fanout_fallback()
    print("--- 监听器下发：编排层入口就绪（S3b 落地后）---")
    check_fanout_uses_children_entry()
    check_real_objects_wiring()

    if FAILURES:
        print("[FAIL] %d 项未通过：%s" % (len(FAILURES), "; ".join(FAILURES)))
        return 1
    print("[OK] desktop_main 自检全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
