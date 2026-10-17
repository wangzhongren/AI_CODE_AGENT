"""桌面端依赖自检脚本（装配角色）。

用途：在项目内虚拟环境 `.venv` 里确认 `PySide6` 真正可导入，且已装版本
与 `requirements.txt` 里锁定的版本一致。

运行方式（从项目根目录执行）：

    .venv\\Scripts\\python.exe test\\assembly\\check_pyside6_install.py

退出码 0 表示依赖就绪；1 表示导入失败或版本与锁不一致。
本脚本只做只读检查，不改任何文件、不启动界面。

输出刻意使用 ASCII：Windows 控制台默认代码页（cp936）下中文会显示成乱码。
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

# 本文件位于 <项目根>/test/assembly/，向上两级是项目根。
PROJECT_ROOT = Path(__file__).resolve().parents[2]
REQUIREMENTS_PATH = PROJECT_ROOT / "requirements.txt"
PACKAGE_NAME = "PySide6"


def read_pinned_version(requirements_path, package_name):
    """从 requirements.txt 里取出 `package_name==x.y.z` 的版本号。

    找不到固定项返回 None（调用方据此给出可读提示）。
    """
    if not requirements_path.is_file():
        print("[FAIL] requirements file not found: %s" % requirements_path)
        return None

    prefix = package_name + "=="
    with open(requirements_path, encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if line.startswith(prefix):
                return line[len(prefix):]
    print("[FAIL] no pinned '%s' entry in %s" % (package_name, requirements_path))
    return None


def main():
    print("interpreter: %s" % sys.executable)
    print("python: %s" % sys.version.split()[0])

    pinned = read_pinned_version(REQUIREMENTS_PATH, PACKAGE_NAME)
    if pinned is None:
        return 1
    print("requirements.txt pins: %s==%s" % (PACKAGE_NAME, pinned))

    try:
        module = importlib.import_module(PACKAGE_NAME)
    except Exception as error:
        # 不吞异常：打印可读原因后以失败退出。
        print("[FAIL] import %s failed: %s" % (PACKAGE_NAME, error))
        return 1

    installed = module.__version__
    print("installed: %s==%s" % (PACKAGE_NAME, installed))

    try:
        from PySide6 import QtCore
    except Exception as error:
        print("[FAIL] import PySide6.QtCore failed: %s" % error)
        return 1
    print("Qt: %s" % QtCore.qVersion())

    if installed != pinned:
        print("[FAIL] version mismatch: pinned %s, installed %s" % (pinned, installed))
        return 1

    print("[OK] %s==%s imports and matches requirements.txt" % (PACKAGE_NAME, installed))
    return 0


if __name__ == "__main__":
    sys.exit(main())
