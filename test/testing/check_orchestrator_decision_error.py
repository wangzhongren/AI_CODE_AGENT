"""验证：编排器 make_decision 分支内部抛错时，监听器还能不能收到 error 事件。

背景（读代码得到，此处实测）：`SystemManagerAgent.todo()` 把 `make_decision()`
包在自己的 try/except 里，只打印一行；`BaseAgent.chat()` 的 except 因此看不到
这个异常，也就不会向监听器发 `error` 事件。桌面端的红字是靠 `error` 事件画的。

用归零规模复现：让编排器决定走 `ask_pj`，而产品经理从未产出过 PRD，
`self.agents["pm"].prd` 不存在 —— 这是 `ask_pj` 分支里唯一没有默认值的取值。
"""

from __future__ import annotations

import contextlib
import io
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from s6_desktop_e2e_acceptance import RecordingListener, build_real_objects  # noqa: E402


def main():
    print("=" * 70)
    print("验证：编排器决策分支抛错时监听器是否收到 error 事件")
    print("=" * 70)

    # 决策直接走 ask_pj：此时 pm 从未产出 PRD，self.agents["pm"].prd 不存在。
    llm, agents, orchestrator = build_real_objects(["ask_pj: 请根据 PRD 生成指导文档"])
    listener = RecordingListener()
    orchestrator.set_output_listener(listener)

    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        reply = orchestrator.chat("做一个能记一条待办的极简页面")
    captured = buffer.getvalue()

    print("[结果] chat() 正常返回，长度 %d（异常没有传到调用方）" % len(reply))
    print("[结果] 监听器收到 error 事件 %d 个" % len(listener.errors))
    print("[结果] 监听器收到 turn_completed %d 次" % len(listener.turns))
    printed_error = "管理者决策解析错误" in captured
    print("[结果] 控制台里出现了「管理者决策解析错误」：%s" % printed_error)
    if printed_error:
        for line in captured.splitlines():
            if "管理者决策解析错误" in line:
                print("[控制台原文] " + line.strip())
                break

    # pm 缺失该属性是抛错前提，这里顺带确认一下前提成立。
    print("[结果] agents['pm'] 有 prd 属性：%s" % hasattr(agents["pm"], "prd"))

    if len(listener.errors) == 0 and printed_error:
        print("")
        print("[结论] 确认：决策分支失败只打到控制台，监听器/界面收不到 error 事件。")
        return 0
    print("")
    print("[结论] 与预期不符，需要重新核对代码路径。")
    return 1


if __name__ == "__main__":
    sys.exit(main())
