"""手动刷新 report_status() 基线输出。平时不需要跑。

用法（项目根目录）：`python -m pytest test/orchestration/_baseline_run.py`
产物：`test/orchestration/_baseline_after.txt`

只有在确认「report_status() 的打印行为应当改变」时才刷新；
默认情况下 `test_project_state_snapshot.py` 用它和 `_baseline_before.txt` 比对的规则是：
改动前后输出必须逐字一致。
"""

import _baseline_capture


def test_refresh_baseline():
    _baseline_capture.capture_to_file("test/orchestration/_baseline_after.txt")
