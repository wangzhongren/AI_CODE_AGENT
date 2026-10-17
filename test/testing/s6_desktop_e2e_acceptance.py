"""S6 验收：桌面端链路的真实对象端到端检查（离线，模型为脚本化替身）。

本脚本验证契约 `docs/contracts/desktop-client-v2.md` 里最关键的 C1.2：
**监听器下发给四个子智能体后，子智能体的事件确实到达了同一个监听器。**

为什么模型用替身而不是真实 OpenAI：
本机（D:/work/vibe-code/codeagent）没有 `api_key` / `model_name` / `base_url`
三个环境变量，项目根也没有 `.env`（见 temp/testing/check_env.py 的实际输出），
所以无法发起真实 API 调用。除模型本身之外，本脚本构造的都是**真实生产对象**：

    ScriptedLLM（继承 BaseLLM 的替身）
        + 真实的 ProductManagerAgent / ProjectManagerAgent /
          BackendDeveloperAgent / FrontendDeveloperAgent
        + 真实的 SystemManagerAgent
        + 真实的 set_output_listener_for_children() / clear_output_listener_for_children()

所以本脚本证明的是「编排层 + 业务智能体 + 监听器」这段**真实链路的接线**，
**不证明真实模型下也能跑通**（模型输出的随机性、真实文件操作指令的格式，
只有真实调用才能覆盖）。报告必须按这个口径写。

运行：

    .venv\\Scripts\\python.exe test\\testing\\s6_desktop_e2e_acceptance.py
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import re
import shutil
import sys
import threading
import time
from collections import Counter, deque
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 控制台代码页可能是 cp936，业务智能体会 print emoji；统一按 UTF-8 输出并用
# replace 兜底，避免 print 自己抛 UnicodeEncodeError 打断流程。
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception as error:  # pragma: no cover
    print("[warn] cannot reconfigure stdout: %r" % (error,))

from ai_agent_factory.agent.baseagent import AgentOutputListener  # noqa: E402
from ai_agent_factory.llms.base_llm import BaseLLM  # noqa: E402
from myagent.backend_developer_agent import BackendDeveloperAgent  # noqa: E402
from myagent.frontend_developer_agent import FrontendDeveloperAgent  # noqa: E402
from myagent.product_manager_agent import ProductManagerAgent  # noqa: E402
from myagent.project_manager_agent import ProjectManagerAgent  # noqa: E402
from myagent.system_manager_agent import SystemManagerAgent  # noqa: E402

WORKSPACE = PROJECT_ROOT / "temp" / "testing" / "_workspace"
LOG_DIR = PROJECT_ROOT / "temp" / "testing" / "_logs"
REQUIREMENT = "做一个能记一条待办的极简页面"

# 假回复里不能带 emoji：真实控制台是 gbk。回复也刻意写短，控制 token 规模。
PM_REPLY = "PRD-001 待办页面：输入框、添加按钮、列表；数据只有一条待办，不涉及登录。"
PJ_GUIDE_REPLY = (
    "指导文档如下。\n"
    "<create_file path=\"frontend_guide.md\">\n"
    "# 前端指导\n"
    "页面：public/todo.html\n"
    "接口：GET /api/v1/todos\n"
    "</create_file>\n"
    "<create_file path=\"backend_guide.md\">\n"
    "# 后端指导\n"
    "接口：GET /api/v1/todos\n"
    "建表：CREATE TABLE todo(id INTEGER PRIMARY KEY, text TEXT);\n"
    "</create_file>\n"
    "两份指导文档已生成。"
)
PJ_CHANGE_REPLY = "modify_fe: 把添加按钮改成蓝色"
BE_REPLY = (
    "后端实现如下。\n"
    "<create_file path=\"api_spec.json\">"
    "{\"openapi\": \"3.0.0\", \"paths\": {\"/api/v1/todos\": {\"get\": {}}}}"
    "</create_file>\n"
    "<create_file path=\"backend/server.js\">"
    "const express = require('express');\n"
    "const app = express();\n"
    "app.get('/api/v1/todos', (req, res) => res.json([{ text: 'a' }]));\n"
    "app.use(express.static('public'));\n"
    "app.listen(3000);\n"
    "</create_file>"
)
FE_REPLY = (
    "前端页面如下。\n"
    "<create_file path=\"public/todo.html\">"
    "<!doctype html><html><body><h1>待办</h1><ul></ul></body></html>"
    "</create_file>"
)
ACK_REPLY = "已收到文件操作结果，本轮没有更多文件操作。"

CREATE_FILE_PATTERN = re.compile(
    r'<create_file\s+path="([^"]+)"\s*>(.*?)</create_file>', re.DOTALL
)

# 替身模型的调用上限：防止被测代码里的重试/递归把整轮跑飞。
MAX_LLM_CALLS = 120


def chunk_text(text, size=12):
    """把一段回复切成小块，模拟流式 token。"""
    return [text[index:index + size] for index in range(0, len(text), size)]


def extract_operations_as_json(user_text):
    """替身模型的「文件操作提取」能力：把 <create_file> 标签转成 JSON 数组。

    真实链路里这一步由 `file_operation_handler.llm_extract_file_operations`
    调模型完成；替身必须返回同样的 JSON 结构，否则文件产出这条路走不通。
    """
    operations = []
    for path, content in CREATE_FILE_PATTERN.findall(user_text):
        operations.append({
            "operation": "CREATE_FILE",
            "path": path.strip(),
            "content": content.strip()
        })
    return json.dumps(operations, ensure_ascii=False)


class ScriptedLLM(BaseLLM):
    """脚本化模型替身：按「提问的是哪个智能体」返回固定回复。

    日志 `log` 按产生顺序记录 `(来源, 小块文本)`，来源取值：
    `sys`（编排器）/ `pm` / `pj` / `be` / `fe` / `extractor`（文件操作提取）。
    验收脚本用这份日志与监听器收到的 token 逐条比对，从而确认
    「每一个来源产生的每一个 token 都到达了监听器」。
    """

    def __init__(self, decisions):
        super().__init__("scripted-key", "http://127.0.0.1:0/v1", "scripted-model")
        self.decisions = deque(decisions)
        self.log = []
        self.calls = []
        self.call_count = 0

    def _next_reply(self, system_prompt, user_text):
        # 判定顺序很关键：各智能体的系统提示词互相包含对方的称呼
        # （编排器提示里有「后端程序员」，后端提示里有「项目经理」），
        # 必须先判最特殊的，否则会认错智能体。
        if "文件操作指令提取器" in system_prompt:
            return "extractor", extract_operations_as_json(user_text)
        if "系统架构师" in system_prompt:
            if self.decisions:
                return "sys", self.decisions.popleft()
            return "sys", "status"
        if "后端程序员" in system_prompt:
            return "be", self._followup_or(BE_REPLY, user_text)
        if "前端程序员" in system_prompt:
            return "fe", self._followup_or(FE_REPLY, user_text)
        if "项目经理" in system_prompt:
            if "修改需求" in user_text:
                return "pj", PJ_CHANGE_REPLY
            return "pj", PJ_GUIDE_REPLY
        if "产品经理" in system_prompt:
            return "pm", PM_REPLY
        return "unknown", "未识别的智能体提示词"

    @staticmethod
    def _followup_or(first_reply, user_text):
        """子智能体在 todo() 里回灌文件操作结果时会再调一次 chat，这里收尾。

        只认「以 [ 开头」的列表：`todo()` 回灌的是
        `json.dumps(need_data)`，need_data 是 list。编排器下发的任务本身是
        `json.dumps({...})`（以 `{` 开头），不能当成回灌，否则子智能体永远
        只回一句收尾语、一行代码都不产出。
        """
        if user_text.lstrip().startswith("["):
            return ACK_REPLY
        return first_reply

    def chat(self, context, **kwargs):
        system_prompt = context[0]["content"] if context else ""
        user_text = context[-1]["content"] if context else ""
        self.call_count += 1
        if self.call_count > MAX_LLM_CALLS:
            raise RuntimeError(
                "替身模型调用次数超过上限 %d：被测代码可能陷入重试/递归" % MAX_LLM_CALLS
            )
        source, reply = self._next_reply(system_prompt, user_text)
        self.calls.append((source, user_text[:50].replace("\n", " ")))
        for chunk in chunk_text(reply):
            self.log.append((source, chunk))
            yield chunk


class RecordingListener(AgentOutputListener):
    """记录型监听器：只记事件，不做任何渲染、不发网络请求。"""

    def __init__(self):
        self.tokens = []
        self.turns = []
        self.errors = []
        self.emit_threads = set()

    def on_token(self, text):
        self.emit_threads.add(threading.current_thread().name)
        self.tokens.append(text)

    def on_turn_completed(self, full_text):
        self.turns.append(full_text)

    def on_error(self, error_info):
        self.errors.append(error_info)


FAILURES = []


def check(condition, label):
    if condition:
        print("[OK] " + label)
    else:
        print("[FAIL] " + label)
        FAILURES.append(label)


def prepare_directories():
    for directory in (WORKSPACE, LOG_DIR):
        if directory.is_dir():
            shutil.rmtree(directory)
        directory.mkdir(parents=True)
    os.chdir(WORKSPACE)
    print("[info] 工作目录已切到测试隔离区：%s" % WORKSPACE)


def build_real_objects(decisions):
    """真实生产对象：真实四个业务智能体 + 真实编排器，只有模型是替身。"""
    llm = ScriptedLLM(decisions)
    agents = {
        "pm": ProductManagerAgent(llm),
        "pj": ProjectManagerAgent(llm),
        "be": BackendDeveloperAgent(llm),
        "fe": FrontendDeveloperAgent(llm)
    }
    orchestrator = SystemManagerAgent(llm, agents)
    return llm, agents, orchestrator


def produced_agent_tokens(llm, since_index):
    """替身模型在窗口内为「智能体」产生的 token（排除文件操作提取的调用）。"""
    return [(source, token) for (source, token) in llm.log[since_index:]
            if source != "extractor"]


def attribute(received_tokens, produced_tokens):
    """按产生顺序把收到的 token 归属到来源。"""
    counter = Counter()
    for index, (source, _token) in enumerate(produced_tokens):
        if index < len(received_tokens):
            counter[source] += 1
    return counter


def describe_counter(counter, label):
    total = sum(counter.values())
    parts = ", ".join("%s=%d" % (name, counter[name]) for name in sorted(counter))
    print("[统计] %s：总计 %d token（%s）" % (label, total, parts if parts else "无"))
    return total


def run_round(orchestrator, llm, listener, message, round_name, captured_chunks):
    """跑一轮编排器 chat()，返回本轮统计。

    智能体自己会大量 print（token_deal 逐字打印），这里把它们的标准输出
    收进内存，避免几百行噪声盖住验收结论；完整原文另存日志文件。
    """
    log_start = len(llm.log)
    token_start = len(listener.tokens)
    turn_start = len(listener.turns)
    error_start = len(listener.errors)

    buffer = io.StringIO()
    started = time.time()
    with contextlib.redirect_stdout(buffer):
        reply = orchestrator.chat(message)
    elapsed = time.time() - started
    captured_chunks.append("=== %s | chat(%r) ===\n%s" % (round_name, message, buffer.getvalue()))

    produced = produced_agent_tokens(llm, log_start)
    received = listener.tokens[token_start:]
    counter = attribute(received, produced)

    print("")
    print("=== %s ===" % round_name)
    print("[调用] orchestrator.chat(%r)" % message)
    print("[结果] 编排器返回 %d 字符；耗时 %.3f 秒；替身模型累计调用 %d 次"
          % (len(reply), elapsed, len(llm.calls)))
    describe_counter(counter, round_name)
    print("[事件] turn_completed %d 次；本轮新增 error %d 个"
          % (len(listener.turns) - turn_start, len(listener.errors) - error_start))

    match = received == [token for (_source, token) in produced]
    check(match, "%s：各来源产生的每个 token 都到达了监听器（%d/%d）"
          % (round_name, len(received), len(produced)))
    if not match:
        for index in range(min(len(received), len(produced))):
            if received[index] != produced[index][1]:
                print("[差异] 第 %d 个 token：监听器收到 %r，模型产生 %r"
                      % (index, received[index], produced[index][1]))
                break
        print("[差异] 收到 %d 个，产生 %d 个" % (len(received), len(produced)))

    return {
        "name": round_name,
        "elapsed": elapsed,
        "counter": counter,
        "produced": len(produced),
        "received": len(received),
        "errors": listener.errors[error_start:]
    }


def list_output_files():
    output_dir = Path("output")
    if not output_dir.is_dir():
        return []
    return sorted(str(path.relative_to(output_dir)).replace("\\", "/")
                  for path in output_dir.rglob("*") if path.is_file())


def main():
    print("=" * 70)
    print("S6 验收：桌面端链路真实对象端到端检查（离线 / 模型为脚本替身）")
    print("=" * 70)

    saved_cwd = os.getcwd()
    captured = []
    try:
        prepare_directories()

        decisions = [
            "next",                                  # 1: 生成 PRD
            "next",                                  # 2: 生成开发指导
            "next",                                  # 3: 后端开发
            "next",                                  # 4: 前端开发
            "status",                                # 5: status 命令
            "analyze_change: 把添加按钮改成蓝色"       # 6: 变更需求 -> modify_fe
        ]
        llm, agents, orchestrator = build_real_objects(decisions)
        listener = RecordingListener()

        print("")
        print("--- 接线：编排器订阅 + 下发给四个子智能体（C1.2）---")
        orchestrator.set_output_listener(listener)
        check(sorted(agents.keys()) == ["be", "fe", "pj", "pm"], "agents 字典为 pm/pj/be/fe")
        orchestrator.set_output_listener_for_children(listener)
        # 幂等（C1.2 第 4 条）：重复下发不得叠加订阅。
        orchestrator.set_output_listener_for_children(listener)
        print("[OK] set_output_listener_for_children 调用两次均未抛错（幂等）")

        rounds = []
        rounds.append(run_round(orchestrator, llm, listener, REQUIREMENT,
                                "第 1 轮 单次 chat（对应真实 API 只调一次的形状）", captured))
        snapshot_first = orchestrator.get_snapshot()
        print("[快照] %r" % (snapshot_first,))
        for name, message in (
            ("第 2 轮 指导文档", "next"),
            ("第 3 轮 后端开发", "next"),
            ("第 4 轮 前端开发", "next"),
            ("第 5 轮 status 命令", "status"),
            ("第 6 轮 变更需求 -> modify_fe", "把添加按钮改成蓝色")
        ):
            rounds.append(run_round(orchestrator, llm, listener, message, name, captured))

        snapshot_after_dev = orchestrator.get_snapshot()
        print("[快照] 开发完成后 %r" % (snapshot_after_dev,))

        total_counter = Counter()
        for item in rounds:
            total_counter.update(item["counter"])

        print("")
        print("=== 汇总 ===")
        print("第 1 轮（只调一次 chat）来源分布：")
        describe_counter(rounds[0]["counter"], "第 1 轮")
        print("六轮累计来源分布：")
        describe_counter(total_counter, "六轮累计")
        print("[统计] 监听器共收到 token %d 个；turn_completed %d 次；error %d 个"
              % (len(listener.tokens), len(listener.turns), len(listener.errors)))
        print("[统计] 六轮总耗时 %.3f 秒" % sum(item["elapsed"] for item in rounds))
        print("[统计] 事件回调所在线程：%s" % sorted(listener.emit_threads))

        print("")
        print("--- 关键判定（C1.2：子智能体事件是否真的到达监听器）---")
        for source in ("pm", "pj", "be", "fe"):
            check(total_counter[source] > 0,
                  "子智能体 %s 的 token 到达了监听器（%d 个）"
                  % (source, total_counter[source]))
        check(total_counter["sys"] > 0,
              "编排器自身的 token 也到达监听器（%d 个）" % total_counter["sys"])
        check(not listener.errors, "全程没有 error 事件（实际 %d 个）" % len(listener.errors))
        for error_info in listener.errors:
            print("[error] %s" % error_info.message)

        print("")
        print("--- 文件产出（跨角色：业务智能体 -> 文件产出层）---")
        files = list_output_files()
        print("[产出] output/ 下共 %d 个文件：%s" % (len(files), files))
        for expected in ("frontend_guide.md", "backend_guide.md", "api_spec.json",
                         "backend/server.js", "public/todo.html"):
            check(expected in files, "产出文件存在：%s" % expected)

        print("")
        print("--- C2 状态快照 ---")
        check(snapshot_after_dev["phase"] in SystemManagerAgent.PHASE_VALUES,
              "phase 取值在契约枚举内：%s" % snapshot_after_dev["phase"])

        print("")
        print("--- C1.2 第 6 条：清除子智能体订阅后不再收到子智能体事件 ---")
        orchestrator.clear_output_listener_for_children()
        log_start = len(llm.log)
        token_start = len(listener.tokens)
        with contextlib.redirect_stdout(io.StringIO()):
            orchestrator.chat("status")
        produced = produced_agent_tokens(llm, log_start)
        received = listener.tokens[token_start:]
        after_clear = attribute(received, produced)
        describe_counter(after_clear, "清除后一轮")
        child_total = sum(after_clear[name] for name in ("pm", "pj", "be", "fe"))
        check(child_total == 0, "清除后子智能体 token 不再到达（实际 %d 个）" % child_total)
        check(after_clear["sys"] > 0,
              "编排器自身的 token 仍到达（%d 个）" % after_clear["sys"])

    finally:
        os.chdir(saved_cwd)
        log_path = LOG_DIR / "agent-stdout.log"
        log_path.write_text("\n".join(captured), encoding="utf-8", errors="replace")
        print("[info] 智能体原始输出已存：%s" % log_path)

    print("")
    if FAILURES:
        print("[FAIL] %d 项未通过：%s" % (len(FAILURES), "; ".join(FAILURES)))
        return 1
    print("[OK] S6 离线验收项全部通过（模型为脚本替身，不含真实 API 调用）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
