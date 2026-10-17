"""S6 第三步（可选）：桌面端 GUI 离屏冒烟——窗口能否把真实链路输出画出来。

做法：`QT_QPA_PLATFORM=offscreen` + 真实 `desktop.start(...)`（真实窗口、真实
工作线程、真实监听器）+ 真实四个业务智能体与真实编排器（模型仍是脚本替身，
原因见 s6_desktop_e2e_acceptance.py 顶部说明）。然后模拟用户「输入需求 + 点发送」，
观察窗口输出区是否出现内容、关闭是否干净、有无残留工作线程。

运行：

    .venv\\Scripts\\python.exe test\\testing\\s6_desktop_gui_smoke.py
"""

from __future__ import annotations

import os
import shutil
import sys
import threading
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 必须在任何 Qt 导入之前设置：没有显示器也要能建窗口。
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception as error:  # pragma: no cover
    print("[warn] cannot reconfigure stdout: %r" % (error,))

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import desktop  # noqa: E402
import desktop_main  # noqa: E402
from s6_desktop_e2e_acceptance import REQUIREMENT, build_real_objects  # noqa: E402

WORKSPACE = PROJECT_ROOT / "temp" / "testing" / "_workspace_gui"
WINDOW_OBJECT_NAME = "mainWindow"
OUTPUT_OBJECT_NAME = "outputPane"
INPUT_OBJECT_NAME = "requirementInput"
SEND_OBJECT_NAME = "sendButton"
PIPELINE_THREAD_NAME = "desktop-pipeline"
DEADLINE_SECONDS = 15.0

FAILURES = []


def check(condition, label):
    if condition:
        print("[OK] " + label)
    else:
        print("[FAIL] " + label)
        FAILURES.append(label)


def find_window():
    from PySide6.QtWidgets import QApplication
    for widget in QApplication.topLevelWidgets():
        if widget.objectName() == WINDOW_OBJECT_NAME:
            return widget
    return None


def pipeline_threads():
    return [thread for thread in threading.enumerate()
            if thread.name == PIPELINE_THREAD_NAME]


def main():
    print("=" * 70)
    print("S6 第三步：桌面端 GUI 离屏冒烟（模型为脚本替身）")
    print("=" * 70)

    saved_cwd = os.getcwd()
    handle = None
    try:
        if WORKSPACE.is_dir():
            shutil.rmtree(WORKSPACE)
        WORKSPACE.mkdir(parents=True)
        os.chdir(WORKSPACE)

        llm, agents, orchestrator = build_real_objects(["next", "next"])
        # 装配层的接线层：桌面端给它设监听器，它把同一个监听器铺到编排器
        # 与四个子智能体（契约 C1.3 的分层要求）。
        wiring = desktop_main.ListenerFanout(orchestrator, agents)

        started = time.time()
        handle = desktop.start(wiring, window_title="S6 冒烟")
        print("[info] desktop.start() 返回句柄，耗时 %.3f 秒；is_closed=%s"
              % (time.time() - started, handle.is_closed))
        check(not handle.is_closed, "句柄初始未关闭")

        from PySide6.QtWidgets import QLineEdit, QPushButton, QTextEdit
        window = find_window()
        check(window is not None, "能通过 Qt 找到主窗口（objectName=mainWindow）")
        if window is None:
            return 1

        output = window.findChild(QTextEdit, OUTPUT_OBJECT_NAME)
        input_box = window.findChild(QLineEdit, INPUT_OBJECT_NAME)
        send_button = window.findChild(QPushButton, SEND_OBJECT_NAME)
        check(output is not None and input_box is not None and send_button is not None,
              "窗口有输出区 / 输入框 / 发送按钮")
        if output is None or input_box is None or send_button is None:
            return 1

        check(output.toPlainText().strip() == "", "初始输出区为空")

        input_box.setText(REQUIREMENT)
        send_button.click()
        print("[info] 已模拟用户输入需求并点击发送：%r" % REQUIREMENT)

        deadline = time.time() + DEADLINE_SECONDS
        while time.time() < deadline:
            handle.process_events()
            if send_button.isEnabled() and output.toPlainText().strip():
                break
            time.sleep(0.02)
        handle.process_events()

        text = output.toPlainText()
        print("[info] 输出区共 %d 字符，前 120 字：%r" % (len(text), text[:120]))
        check(text.strip() != "", "窗口输出区出现了内容（用户能看到过程）")
        check("[错误]" not in text, "输出区没有错误红字（没有 error 事件）")
        check(send_button.isEnabled(), "任务结束后发送按钮恢复可用")
        check(not pipeline_threads(), "工作线程已退出（没有残留 desktop-pipeline 线程）")

        handle.shutdown()
        check(handle.is_closed, "shutdown() 后句柄为已关闭")
        handle.shutdown()  # 可重复调用（契约 C3）
        check(handle.is_closed, "shutdown() 可重复调用")
        print("[info] 关闭后再处理一批事件，确认不抛错")
        handle.process_events()

    finally:
        if handle is not None and not handle.is_closed:
            handle.shutdown()
        os.chdir(saved_cwd)

    print("")
    if FAILURES:
        print("[FAIL] %d 项未通过：%s" % (len(FAILURES), "; ".join(FAILURES)))
        return 1
    print("[OK] GUI 离屏冒烟通过（模型为脚本替身，不含真实 API 调用）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
