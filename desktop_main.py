"""桌面端真实接线入口（装配角色）。

契约 `docs/contracts/desktop-client-v2.md`：

- **C4 第 5 条**：`api_key` / `model_name` / `base_url` 缺任何一个都要给出可读提示，
  不得把 `None` 传给 `OpenAILLM`。
- **C4 第 6 条**：这是「真实接线」入口，启动方式是
  `.venv\\Scripts\\python.exe desktop_main.py`。
- **C1.3**：监听器由装配层在启动时下发到四个子智能体（`desktop/` 不越层遍历）。

本文件只做三件事：读环境变量、构造对象、把它们接起来。**不含业务逻辑**——
PRD 怎么写、下一步调度谁，都属「流程编排」角色。

分层：本入口只 import 编排器（`SystemManagerAgent`）、四个业务智能体、Provider 构造
入口（`OpenAILLM`）与桌面端的公开启动操作（`desktop.run`）。

**消息里刻意不用 emoji**：Windows 控制台常用代码页是 gbk/cp936，编不出 emoji 时
`print` 会抛 `UnicodeEncodeError` —— 那会让「可读报错」自己先崩掉。
（2026-10-17 实测：`❌` 在 `.venv\\Scripts\\python.exe desktop_main.py` 下抛过这个错。）
"""

import os
import sys
import traceback

from dotenv import load_dotenv

import desktop
from ai_agent_factory.llms.base_llm_openai import OpenAILLM
from myagent.backend_developer_agent import BackendDeveloperAgent
from myagent.frontend_developer_agent import FrontendDeveloperAgent
from myagent.product_manager_agent import ProductManagerAgent
from myagent.project_manager_agent import ProjectManagerAgent
from myagent.system_manager_agent import SystemManagerAgent

# 环境变量契约（C4 第 5 条）：名字不改，CLI 与桌面端共用同一份 .env。
ENVIRONMENT_VARIABLE_NAMES = ("api_key", "model_name", "base_url")
ENVIRONMENT_FILE_NAME = ".env"
WINDOW_TITLE = "代码生成助手（桌面端）"

EXIT_OK = 0
EXIT_RUNTIME_ERROR = 1
EXIT_CONFIGURATION_ERROR = 2


def environment_file_path():
    """返回 `.env` 应该所在的位置。

    打包态（PyInstaller 冻结后）工作目录不确定，双击启动时不能靠「从当前目录向上找」。
    此时配置固定读可执行文件同级目录：便携版是解压后 exe 所在的文件夹，单文件版是
    exe 旁边，macOS 是 `.app/Contents/MacOS/`（`sys.executable` 所在目录）。

    源码态保持原有行为：由 `load_dotenv()` 从当前工作目录向上查找，这里只返回
    用于提示的路径。
    """
    if getattr(sys, "frozen", False):
        return os.path.join(os.path.dirname(sys.executable), ENVIRONMENT_FILE_NAME)
    return os.path.join(os.getcwd(), ENVIRONMENT_FILE_NAME)


def read_environment():
    """读取环境变量，返回 (配置字典, 缺失的变量名列表)。

    空字符串按缺失处理：`api_key=` 这种空值传给 `OpenAILLM` 与 `None` 一样会让
    用户在窗口里看到一个看不懂的 SDK 报错。
    """
    if getattr(sys, "frozen", False):
        load_dotenv(environment_file_path())
    else:
        load_dotenv()
    settings = {}
    missing_names = []
    for variable_name in ENVIRONMENT_VARIABLE_NAMES:
        raw_value = os.getenv(variable_name)
        value = ""
        if raw_value is not None:
            value = raw_value.strip()
        if value == "":
            missing_names.append(variable_name)
        else:
            settings[variable_name] = value
    return settings, missing_names


def explain_missing_environment(missing_names):
    """把「缺哪个变量、.env 该放哪」讲清楚（C4 第 5 条）。"""
    environment_path = environment_file_path()
    print("[错误] 桌面端启动失败：缺少环境变量 " + "、".join(missing_names))
    print("需要这份配置：" + environment_path)
    for variable_name in ENVIRONMENT_VARIABLE_NAMES:
        if variable_name in missing_names:
            print("  - " + variable_name + "   <- 缺失")
        else:
            print("  - " + variable_name + "   （已读到）")
    if getattr(sys, "frozen", False):
        print("如果 " + ENVIRONMENT_FILE_NAME + " 还不存在：在程序所在目录新建它，写三行，例如")
    else:
        print("如果 " + ENVIRONMENT_FILE_NAME + " 还不存在：在项目根目录新建它，写三行，例如")
    print("  api_key=你的密钥")
    print("  model_name=模型名（例如 gpt-4o-mini）")
    print("  base_url=接口地址（例如 https://api.openai.com/v1）")
    if getattr(sys, "frozen", False):
        print("填好后重新打开本程序。")
    else:
        print("填好后重新执行：.venv\\Scripts\\python.exe desktop_main.py")


def build_llm(settings):
    """按配置构造 Provider 入口对象。"""
    return OpenAILLM(
        api_key=settings["api_key"],
        model_name=settings["model_name"],
        base_url=settings["base_url"]
    )


def build_agents(llm):
    """构造四个业务智能体，返回编排器需要的 agents 字典。"""
    agents = {
        "pm": ProductManagerAgent(llm),
        "pj": ProjectManagerAgent(llm),
        "be": BackendDeveloperAgent(llm),
        "fe": FrontendDeveloperAgent(llm)
    }
    return agents


def build_orchestrator(llm, agents):
    """构造编排器。"""
    return SystemManagerAgent(llm, agents)


class ListenerFanout:
    """把桌面端下发的监听器转发给编排器和四个子智能体（C1.2 / C1.3）。

    为什么需要这一层：`desktop.start()` 在内部自己创建监听器，然后调用
    `orchestrator.set_output_listener(listener)`（C1.3 的左半句）。装配层手里
    没有那个对象，只有把它交出去的时机。把本类交给桌面端，这一刻就能把**同一个**
    监听器分发给编排器和四个子智能体，不必穿透任何私有状态。

    分发顺序：编排器自己有的「下发给子智能体」公开入口（C1.2 的
    `set_output_listener_for_children`）优先；该入口还没就绪时，退回用装配层自己
    持有的 `agents` 字典逐个下发（同样是公开方法 `set_output_listener`）。

    其余属性（`chat`、`get_snapshot` 等）原样委托给真正的编排器，本类不复制任何
    业务逻辑。
    """

    def __init__(self, orchestrator, agents):
        self._orchestrator = orchestrator
        self._agents = agents
        self._listener = None

    @property
    def listener(self):
        """当前已下发的监听器，未下发时为 None。"""
        return self._listener

    def set_output_listener(self, listener):
        """桌面端调用这里；本方法负责把监听器铺到每一个会产生输出的对象上。"""
        self._listener = listener
        self._orchestrator.set_output_listener(listener)
        self._deliver_to_children(listener)

    def clear_output_listener(self):
        """关闭窗口时取消全部订阅（C1 的清除入口，含子智能体）。"""
        self._listener = None
        self._orchestrator.clear_output_listener()
        self._clear_children()

    def _deliver_to_children(self, listener):
        children_entry = getattr(self._orchestrator, "set_output_listener_for_children", None)
        if callable(children_entry):
            try:
                children_entry(listener)
            except Exception as error:
                print("[错误] 编排器把监听器下发给子智能体失败：" + repr(error))
                raise
            return
        # 该入口尚未就绪（S3b 属「流程编排」角色）：打印清楚，然后用自己手里的
        # agents 字典完成等价接线，不崩、不静默。
        print("[接线] 编排器暂无 set_output_listener_for_children（契约 C1.2 待编排层落地），"
              "改由 desktop_main 用自己持有的 agents 字典逐个下发。")
        for role_name in self._agents:
            agent = self._agents[role_name]
            setter = getattr(agent, "set_output_listener", None)
            if not callable(setter):
                print("[接线] 警告：子智能体 " + role_name + " 没有 set_output_listener，"
                      "它自己的输出进不了窗口（契约 C1.2 要求如实报告，不静默降级）")
                continue
            try:
                setter(listener)
            except Exception as error:
                print("[接线] 给子智能体 " + role_name + " 下发监听器失败：" + repr(error))
                raise

    def _clear_children(self):
        children_clear = getattr(self._orchestrator, "clear_output_listener_for_children", None)
        if callable(children_clear):
            try:
                children_clear()
            except Exception as error:
                print("[接线] 编排器清除子智能体订阅失败：" + repr(error))
            return
        for role_name in self._agents:
            agent = self._agents[role_name]
            clearer = getattr(agent, "clear_output_listener", None)
            if not callable(clearer):
                print("[接线] 警告：子智能体 " + role_name + " 没有 clear_output_listener，跳过取消订阅")
                continue
            try:
                clearer()
            except Exception as error:
                # 关窗路径要尽量走完，不因为一个取消订阅失败就中断清理。
                print("[接线] 取消子智能体 " + role_name + " 的订阅失败：" + repr(error))

    def __getattr__(self, attribute_name):
        orchestrator = self.__dict__.get("_orchestrator")
        if orchestrator is None:
            raise AttributeError(attribute_name)
        return getattr(orchestrator, attribute_name)


def main():
    """读配置 → 构造 → 接线 → 启动界面。返回进程退出码。"""
    settings, missing_names = read_environment()
    if missing_names:
        explain_missing_environment(missing_names)
        return EXIT_CONFIGURATION_ERROR

    try:
        llm = build_llm(settings)
        agents = build_agents(llm)
        orchestrator = build_orchestrator(llm, agents)
    except Exception as error:
        print("[错误] 构造智能体失败：" + repr(error))
        traceback.print_exc()
        return EXIT_RUNTIME_ERROR

    wiring = ListenerFanout(orchestrator, agents)
    print("[启动] 桌面端启动中。在窗口里提交需求，编排器与四个角色的输出都会显示出来。")
    try:
        desktop.run(wiring, window_title=WINDOW_TITLE)
    except desktop.DesktopStartupError as error:
        print("[错误] 桌面端启动失败：" + str(error))
        return EXIT_RUNTIME_ERROR
    except Exception as error:
        print("[错误] 桌面端运行中出错：" + repr(error))
        traceback.print_exc()
        return EXIT_RUNTIME_ERROR

    print("[退出] 桌面端已关闭。")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
