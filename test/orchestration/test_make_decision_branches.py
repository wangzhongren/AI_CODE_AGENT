"""make_decision() 每个决策分支的用例，含「都不匹配」的兜底路径。

这份用例的另一个作用是把现状钉住：本步只新增了 get_snapshot() 一类只读方法，
决策分派行为必须与改动前一致。

四个业务智能体与 LLM 一律用 support.py 里的替身注入，不依赖真实 LLM。
"""

import contextlib
import io
import json
from unittest import mock

import pytest

from support import build_manager


def run_capturing_output(action, *args):
    """执行会打印内容的动作并吞掉输出，避免 Windows GBK 控制台编码报错。"""
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        action(*args)
    return buffer.getvalue()


def ready_manager(**state):
    """初始开发已完成的经理：便于观察变更分派对标志的重置。"""
    complete = {
        'prd_completed': True,
        'guides_completed': True,
        'backend_completed': True,
        'frontend_completed': True,
    }
    for key, value in state.items():
        complete[key] = value
    return build_manager(**complete)


def test_ask_pm_routes_to_product_manager():
    manager = build_manager()

    output = run_capturing_output(manager.make_decision, "ask_pm: 请确认需求细节")

    assert manager.agents['pm'].messages == ["请确认需求细节"]
    assert manager.agents['pj'].messages == []
    assert "调度产品经理" in output


def test_ask_pj_appends_prd_to_message():
    manager = build_manager()
    manager.agents['pm'].prd = "PRD-正文"

    run_capturing_output(manager.make_decision, "ask_pj: 请生成指导文档")

    assert manager.agents['pj'].messages == ["请生成指导文档产品文档：PRD-正文"]


def test_ask_fe_sends_frontend_payload():
    manager = build_manager()
    manager.agents['pj'].frontend_guide = "前端指导"
    manager.agents['be'].api_spec = {"paths": {"/login": {}}}

    run_capturing_output(manager.make_decision, "ask_fe: 做登录页")

    assert len(manager.agents['fe'].messages) == 1
    payload = json.loads(manager.agents['fe'].messages[0])
    assert payload['project_target'] == "做登录页"
    assert payload['guide'] == "前端指导"
    assert payload['api_spec'] == {"paths": {"/login": {}}}


def test_ask_be_sends_backend_payload():
    manager = build_manager()
    manager.agents['pj'].backend_guide = "后端指导"

    run_capturing_output(manager.make_decision, "ask_be: 做登录接口")

    assert len(manager.agents['be'].messages) == 1
    payload = json.loads(manager.agents['be'].messages[0])
    assert payload['project_target'] == "做登录接口"
    assert payload['guide'] == "后端指导"


def test_analyze_change_dispatches_frontend_modification():
    manager = ready_manager()
    manager.agents['pj'].analysis_result = "modify_fe: 只改按钮颜色"

    run_capturing_output(manager.make_decision, "analyze_change: 把按钮改成蓝色")

    assert len(manager.agents['pj'].messages) == 1
    assert len(manager.agents['fe'].messages) == 1
    assert manager.agents['be'].messages == []
    assert manager.project_state['frontend_completed'] is False
    assert manager.project_state['backend_completed'] is True


def test_analyze_change_dispatches_backend_modification():
    manager = ready_manager()
    manager.agents['pj'].analysis_result = "modify_be: 加一个查询接口"

    run_capturing_output(manager.make_decision, "analyze_change: 增加历史记录")

    assert len(manager.agents['be'].messages) == 1
    assert manager.agents['fe'].messages == []
    assert manager.project_state['backend_completed'] is False
    assert manager.project_state['frontend_completed'] is True


def test_analyze_change_dispatches_both_modifications():
    manager = ready_manager()
    manager.agents['pj'].analysis_result = "both_modify: 前后端都要改"

    run_capturing_output(manager.make_decision, "analyze_change: 增加用户体系")

    assert len(manager.agents['fe'].messages) == 1
    assert len(manager.agents['be'].messages) == 1
    assert manager.project_state['frontend_completed'] is False
    assert manager.project_state['backend_completed'] is False


def test_analyze_change_without_result_does_not_dispatch():
    manager = ready_manager()
    manager.agents['pj'].analysis_result = ""

    output = run_capturing_output(
        manager.make_decision,
        "analyze_change: 改一下标题"
    )

    assert len(manager.agents['pj'].messages) == 1
    assert manager.agents['fe'].messages == []
    assert manager.agents['be'].messages == []
    # 没有分派时状态不变，项目仍在 change 阶段等待结论。
    assert manager.get_snapshot()['phase'] == "change"
    assert "分析修改需求" in output


def test_modify_fe_resets_frontend_flag_only():
    manager = ready_manager()

    run_capturing_output(manager.make_decision, "modify_fe: 换配色")

    assert json.loads(manager.agents['fe'].messages[0])['project_target'] == (
        "根据以下修改需求更新前端页面:\n换配色"
    )
    assert manager.project_state['frontend_completed'] is False
    assert manager.project_state['backend_completed'] is True
    assert manager.get_snapshot()['phase'] == "frontend"


def test_modify_be_resets_backend_flag_only():
    manager = ready_manager()

    run_capturing_output(manager.make_decision, "modify_be: 加字段")

    assert json.loads(manager.agents['be'].messages[0])['project_target'] == (
        "根据以下修改需求更新后端服务:\n加字段"
    )
    assert manager.project_state['backend_completed'] is False
    assert manager.project_state['frontend_completed'] is True
    assert manager.get_snapshot()['phase'] == "backend"


def test_modify_both_resets_both_flags():
    manager = ready_manager()

    run_capturing_output(manager.make_decision, "modify_both: 加登录")

    assert len(manager.agents['be'].messages) == 1
    assert len(manager.agents['fe'].messages) == 1
    assert manager.project_state['backend_completed'] is False
    assert manager.project_state['frontend_completed'] is False
    assert manager.get_snapshot()['phase'] == "backend"


def test_status_reports_status_without_dispatch():
    manager = build_manager(prd_completed=True)

    output = run_capturing_output(manager.make_decision, "status")

    assert "项目状态报告" in output
    assert "PRD 已完成" in output
    for name in ('pm', 'pj', 'fe', 'be'):
        assert manager.agents[name].messages == []


def test_next_executes_next_step():
    manager = build_manager()

    run_capturing_output(manager.make_decision, "next")

    assert manager.project_state['prd_completed'] is True
    assert len(manager.agents['pm'].messages) == 1
    assert manager.get_snapshot()['phase'] == "guides"


def test_done_marks_project_completed():
    manager = ready_manager()

    output = run_capturing_output(manager.make_decision, "done")

    assert manager.project_state['project_completed'] is True
    assert manager.get_snapshot()['phase'] == "done"
    assert "项目开发完成" in output
    assert "最终项目成果" in output


def test_unknown_decision_falls_back_without_dispatch():
    """兜底路径：任何分支词都不匹配时不派发、不改状态。"""
    manager = build_manager()

    output = run_capturing_output(manager.make_decision, "随便聊两句天气")

    assert "未知决策" in output
    for name in ('pm', 'pj', 'fe', 'be'):
        assert manager.agents[name].messages == []
    assert manager.get_snapshot()['phase'] == "idle"


def test_first_matching_branch_wins():
    """子串匹配按 if/elif 顺序先命中先执行——已知的误匹配风险，现状如此。"""
    manager = build_manager()

    run_capturing_output(manager.make_decision, "先 status 再说，可能 next")

    assert manager.project_state['prd_completed'] is False
    assert manager.agents['pm'].messages == []


def test_todo_reports_decision_error():
    """todo() 先打印诊断，再把异常上抛（交给 chat() 发 error 事件），不吞掉。"""
    manager = build_manager()
    del manager.agents['pm'].prd

    buffer = io.StringIO()
    with pytest.raises(AttributeError):
        with contextlib.redirect_stdout(buffer):
            manager.todo("ask_pj: 请生成指导文档")

    assert "管理者决策解析错误" in buffer.getvalue()


def test_missing_guide_files_do_not_break_dispatch():
    """依赖文件缺失时：按原逻辑跳过读取，仍然完成派发。"""
    manager = build_manager()
    manager.agents['pj'].frontend_guide = ""
    manager.agents['be'].api_spec = {}

    with mock.patch("os.path.exists", return_value=False):
        run_capturing_output(manager.make_decision, "ask_fe: 做首页")

    payload = json.loads(manager.agents['fe'].messages[0])
    assert payload['guide'] == ""
    assert payload['api_spec'] == {}


def test_unreadable_guide_file_reports_error_and_continues():
    """文件存在但读不出来时：打印错误，派发继续，不抛给调用方。"""
    manager = build_manager()
    manager.agents['pj'].frontend_guide = ""

    with mock.patch("os.path.exists", return_value=True):
        with mock.patch("builtins.open", side_effect=OSError("模拟读取失败")):
            output = run_capturing_output(
                manager.make_decision,
                "ask_fe: 做首页"
            )

    assert "读取前端指导文档失败" in output
    assert "模拟读取失败" in output
    assert len(manager.agents['fe'].messages) == 1


def test_handle_change_request_goes_through_analysis():
    """变更入口先让项目经理分析，再由分析结果决定改哪一端。"""
    manager = ready_manager()
    manager.agents['pj'].analysis_result = "modify_fe: 改标题"

    run_capturing_output(manager.handle_change_request, "把标题改成项目名")

    assert len(manager.agents['pj'].messages) == 1
    assert len(manager.agents['fe'].messages) == 1
    assert manager.get_snapshot()['phase'] == "frontend"
