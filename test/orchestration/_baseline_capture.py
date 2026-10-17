"""report_status() 输出的基线捕获工具。

用途：改动 report_status() 之前和之后各捕获一次输出，逐字比较，确认打印行为没变。
三个入口（main.py / main3.py / enhanced_main.py）依赖这段打印，所以它是跨角色契约。

- 捕获：`python -m pytest test/orchestration/_baseline_run.py`
  （本文件名不匹配 pytest 的 test_*.py / *_test.py，不会被自动收集，只在显式指定时运行）
- 基线文件：`_baseline_before.txt` 是 2026-10-17 加入 get_snapshot() 之前的真实输出，
  `test_project_state_snapshot.py` 会拿它和当前输出逐字比对。

只捕获当前逻辑的输出，不做判断；判断留给测试。
"""

import contextlib
import io

from support import build_manager


# 三种代表状态：全未完成、部分完成、全部完成。
SCENARIOS = {
    "all_false": {
        'prd_completed': False,
        'guides_completed': False,
        'backend_completed': False,
        'frontend_completed': False,
        'project_completed': False,
    },
    "mixed": {
        'prd_completed': True,
        'guides_completed': True,
        'backend_completed': False,
        'frontend_completed': False,
        'project_completed': False,
    },
    "all_true": {
        'prd_completed': True,
        'guides_completed': True,
        'backend_completed': True,
        'frontend_completed': True,
        'project_completed': True,
    },
}


def capture_text():
    """返回三种状态下的 report_status() 打印文本。

    打印内容含 emoji，Windows 控制台默认 GBK 编码会报错，因此统一重定向到内存缓冲。
    """
    chunks = []
    for name, state in SCENARIOS.items():
        manager = build_manager(**state)
        chunks.append(f"===== {name} =====")
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            manager.report_status()
        chunks.append(buffer.getvalue())
        chunks.append("===== end =====")
    return "\n".join(chunks)


def capture_to_file(path):
    """把捕获文本写入文件（UTF-8），用于刷新基线。"""
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(capture_text())
