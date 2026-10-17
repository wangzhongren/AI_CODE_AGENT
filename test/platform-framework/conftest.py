"""平台框架测试的公用引导。

用途：把项目根目录放进 ``sys.path``，这样无论从哪个工作目录启动 pytest，
测试都能 ``import ai_agent_factory``。不引入任何第三方依赖。
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
