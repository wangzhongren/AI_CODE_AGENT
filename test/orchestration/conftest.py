"""让测试在任意工作目录下都能 import 生产模块。

pytest 只把测试文件所在目录加入 sys.path，项目根目录需要显式补入。
这只影响测试进程，不改变生产代码的导入方式。
"""

import pathlib
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
