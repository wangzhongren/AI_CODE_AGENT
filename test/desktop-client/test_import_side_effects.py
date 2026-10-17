"""契约 C3 第 4 条：``import desktop`` 不得启动界面（也不得导入 Qt）。

用子进程验证，避免被本进程里其它用例已经导入的 Qt 影响。
"""

import subprocess
import sys
import unittest

from support import PROJECT_ROOT


class ImportSideEffectTest(unittest.TestCase):
    def test_import_desktop_does_not_load_qt(self):
        code = "\n".join(
            [
                "import sys",
                "import desktop",
                "loaded = 'PySide6' in sys.modules",
                "print('qt-loaded' if loaded else 'no-qt')",
                "print(hasattr(desktop, 'run'), hasattr(desktop, 'start'))",
            ]
        )
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = result.stdout.strip().splitlines()
        self.assertEqual(lines[0], "no-qt", "import desktop 不应加载 PySide6")
        self.assertEqual(lines[1], "True True", "run / start 应可直接访问")

    def test_import_desktop_does_not_create_application(self):
        code = "\n".join(
            [
                "import sys",
                "import desktop",
                "print('PySide6.QtWidgets' in sys.modules)",
            ]
        )
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "False")

    def test_module_entry_point_imports_without_starting_gui(self):
        code = "\n".join(
            [
                "import desktop.__main__ as entry",
                "print(callable(entry.main))",
            ]
        )
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            env={"QT_QPA_PLATFORM": "offscreen", "PATH": ""},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "True")


if __name__ == "__main__":
    unittest.main()
