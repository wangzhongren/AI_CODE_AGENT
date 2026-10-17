"""pytest 引导：让本目录的 ``support.py`` 与项目根都可导入，并固定离屏平台。

用例本身用 ``unittest.TestCase`` 写（既能被 pytest 收集，也能
``python -m unittest discover`` 直接跑）。本文件只补导入路径与离屏环境，
不含任何用例、不改变被测试的行为。
"""

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parents[1]

for path in (HERE, PROJECT_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

# 没有显示器也能跑 GUI 用例。必须在任何 Qt 导入之前设置。
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
