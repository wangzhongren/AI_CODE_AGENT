"""契约 C2（docs/contracts/desktop-client-v1.md）的层内契约测试：项目状态快照。

覆盖：
- 五个布尔的全部 32 种组合；
- 每个 phase 取值（idle / prd / guides / backend / frontend / change / done）都可到达；
- 快照无副作用（project_state、对话上下文、业务智能体调用、LLM 调用均不变）；
- 返回值是副本、只含纯数据；
- report_status() 的打印输出与改动前逐字一致。

四个业务智能体与 LLM 一律用 support.py 里的替身注入，不依赖真实 LLM。
"""

import contextlib
import io
import itertools
import pathlib

import pytest

from myagent.system_manager_agent import SystemManagerAgent

import _baseline_capture as baseline_capture
from support import build_manager


# 契约 C2 的 phase 枚举，按契约字面量固化。
# 不引用实现里的常量，避免实现改错时测试跟着一起错。
CONTRACT_PHASES = (
    "idle",
    "prd",
    "guides",
    "backend",
    "frontend",
    "change",
    "done"
)

# 契约 C2 规定的五个状态布尔字段。
CONTRACT_STATE_KEYS = (
    'prd_completed',
    'guides_completed',
    'backend_completed',
    'frontend_completed',
    'project_completed'
)


def run_capturing_output(action):
    """执行会打印内容的动作并吞掉输出，避免 Windows GBK 控制台编码报错。"""
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        action()
    return buffer.getvalue()


def all_state_combinations():
    """五个布尔的全部 32 种组合。"""
    combinations = []
    for values in itertools.product((False, True), repeat=5):
        combinations.append(dict(zip(CONTRACT_STATE_KEYS, values)))
    return combinations


def describe(combination):
    """给每种组合一个便于定位失败用例的可读 id。"""
    parts = []
    for key in CONTRACT_STATE_KEYS:
        value = combination[key]
        parts.append(f"{key}={value}")
    return ",".join(parts)


def context_copy(manager):
    """取对话上下文的深一层副本，用于比较调用前后是否变化。"""
    copied = []
    for message in manager.get_context():
        copied.append(dict(message))
    return copied


def agent_message_counts(manager):
    """取四个业务智能体各自收到的消息条数。"""
    counts = {}
    for name in ('pm', 'pj', 'fe', 'be'):
        counts[name] = len(manager.agents[name].messages)
    return counts


def assert_phase_matches_state(phase, state):
    """phase 与 state 不得自相矛盾：每种 phase 都对应唯一的标志组合。"""
    if phase == "done":
        assert state['project_completed'] is True
    elif phase == "change":
        assert state['project_completed'] is False
        assert state['prd_completed'] is True
        assert state['guides_completed'] is True
        assert state['backend_completed'] is True
        assert state['frontend_completed'] is True
    elif phase == "prd":
        assert state['prd_completed'] is False
    elif phase == "guides":
        assert state['prd_completed'] is True
        assert state['guides_completed'] is False
    elif phase == "backend":
        assert state['prd_completed'] is True
        assert state['guides_completed'] is True
        assert state['backend_completed'] is False
    elif phase == "frontend":
        assert state['prd_completed'] is True
        assert state['guides_completed'] is True
        assert state['backend_completed'] is True
        assert state['frontend_completed'] is False
    elif phase == "idle":
        for key in CONTRACT_STATE_KEYS:
            assert state[key] is False
    else:
        raise AssertionError(f"phase 取值不在契约枚举内: {phase}")


@pytest.mark.parametrize("combination", all_state_combinations(), ids=describe)
def test_state_matches_project_state_for_every_combination(combination):
    """五个布尔的任意组合都原样反映到快照里。"""
    manager = build_manager(**combination)

    snapshot = manager.get_snapshot()

    assert list(snapshot.keys()) == ['state', 'phase']
    assert set(snapshot['state'].keys()) == set(CONTRACT_STATE_KEYS)
    for key in CONTRACT_STATE_KEYS:
        assert snapshot['state'][key] is combination[key]


@pytest.mark.parametrize("combination", all_state_combinations(), ids=describe)
def test_phase_is_within_contract_enum_and_consistent(combination):
    """任意组合下 phase 都在契约枚举内，且与 state 不矛盾。"""
    manager = build_manager(**combination)

    snapshot = manager.get_snapshot()

    assert snapshot['phase'] in CONTRACT_PHASES
    assert_phase_matches_state(snapshot['phase'], snapshot['state'])


def test_snapshot_is_a_public_method():
    """界面层要直接调用它，所以必须是公开（非下划线开头）方法。"""
    assert callable(getattr(SystemManagerAgent, "get_snapshot", None))
    assert not SystemManagerAgent.get_snapshot.__name__.startswith("_")


def test_phase_idle_before_anything_happens():
    """还没提交需求：idle。"""
    manager = build_manager()

    assert manager.get_snapshot()['phase'] == "idle"


def test_phase_prd_after_requirement_submitted():
    """需求已进入对话但 PRD 未完成：prd。"""
    manager = build_manager()

    run_capturing_output(lambda: manager.chat("做一个待办清单应用"))

    snapshot = manager.get_snapshot()
    assert snapshot['phase'] == "prd"
    # PRD 尚未完成，state 里仍是 False，两者不矛盾。
    assert snapshot['state']['prd_completed'] is False


def test_phase_guides_when_only_prd_completed():
    manager = build_manager(prd_completed=True)

    assert manager.get_snapshot()['phase'] == "guides"


def test_phase_backend_when_prd_and_guides_completed():
    manager = build_manager(prd_completed=True, guides_completed=True)

    assert manager.get_snapshot()['phase'] == "backend"


def test_phase_frontend_when_backend_completed():
    manager = build_manager(
        prd_completed=True,
        guides_completed=True,
        backend_completed=True
    )

    assert manager.get_snapshot()['phase'] == "frontend"


def test_phase_change_when_development_finished_but_not_closed():
    """四项开发都完成、项目未标记完成：等待/处理变更需求。"""
    manager = build_manager(
        prd_completed=True,
        guides_completed=True,
        backend_completed=True,
        frontend_completed=True
    )

    snapshot = manager.get_snapshot()
    assert snapshot['phase'] == "change"
    assert snapshot['state']['project_completed'] is False


def test_phase_prd_when_started_but_prd_flag_not_set():
    """状态不一致（PRD 标志为 False 但后续标志已 True）时不给 idle，避免自相矛盾。"""
    manager = build_manager(prd_completed=False, backend_completed=True)

    snapshot = manager.get_snapshot()

    assert snapshot['phase'] == "prd"
    assert snapshot['state']['backend_completed'] is True


def test_phase_done_when_project_completed():
    manager = build_manager(
        prd_completed=True,
        guides_completed=True,
        backend_completed=True,
        frontend_completed=True,
        project_completed=True
    )

    snapshot = manager.get_snapshot()
    assert snapshot['phase'] == "done"
    assert snapshot['state']['project_completed'] is True


def test_every_contract_phase_is_reachable():
    """七个取值都得能真实出现，不能有永远到不了的分支。"""
    scenarios = [
        (build_manager(), "idle"),
        (build_manager(prd_completed=True), "guides"),
        (build_manager(prd_completed=True, guides_completed=True), "backend"),
        (build_manager(
            prd_completed=True,
            guides_completed=True,
            backend_completed=True
        ), "frontend"),
        (build_manager(
            prd_completed=True,
            guides_completed=True,
            backend_completed=True,
            frontend_completed=True
        ), "change"),
        (build_manager(project_completed=True), "done"),
    ]
    observed = set()
    for manager, expected_phase in scenarios:
        observed.add(manager.get_snapshot()['phase'])
        assert manager.get_snapshot()['phase'] == expected_phase

    prd_manager = build_manager()
    run_capturing_output(lambda: prd_manager.chat("再做一个记账应用"))
    observed.add(prd_manager.get_snapshot()['phase'])

    assert observed == set(CONTRACT_PHASES)


def test_phase_follows_execute_next_step_progression():
    """快照的推进顺序与 execute_next_step() 一致：PRD → 指导 → 后端 → 前端 → 变更。"""
    manager = build_manager()
    assert manager.get_snapshot()['phase'] == "idle"

    run_capturing_output(manager.execute_next_step)
    assert manager.get_snapshot()['phase'] == "guides"

    run_capturing_output(manager.execute_next_step)
    assert manager.get_snapshot()['phase'] == "backend"

    run_capturing_output(manager.execute_next_step)
    assert manager.get_snapshot()['phase'] == "frontend"

    run_capturing_output(manager.execute_next_step)
    assert manager.get_snapshot()['phase'] == "change"


@pytest.mark.parametrize("combination", [
    {},
    {'prd_completed': True},
    {'prd_completed': True, 'guides_completed': True},
    {'prd_completed': True, 'guides_completed': True, 'backend_completed': True},
    {
        'prd_completed': True,
        'guides_completed': True,
        'backend_completed': True,
        'frontend_completed': True
    },
    {'project_completed': True},
], ids=["empty", "prd", "guides", "backend", "frontend", "done"])
def test_snapshot_has_no_side_effects(combination):
    """调用前后：project_state、上下文、业务智能体消息、LLM 调用都完全一致。"""
    manager = build_manager(**combination)
    run_capturing_output(lambda: manager.chat("初始需求"))

    state_before = dict(manager.project_state)
    context_before = context_copy(manager)
    messages_before = agent_message_counts(manager)
    llm_calls_before = len(manager.basellm.calls)

    manager.get_snapshot()

    assert manager.project_state == state_before
    assert context_copy(manager) == context_before
    assert agent_message_counts(manager) == messages_before
    assert len(manager.basellm.calls) == llm_calls_before


def test_snapshot_returns_a_copy_not_internal_references():
    """改返回值不能影响内部状态，也不能影响下一次快照。"""
    manager = build_manager(prd_completed=True)

    snapshot = manager.get_snapshot()
    original_snapshot = {
        'state': dict(snapshot['state']),
        'phase': snapshot['phase']
    }

    assert snapshot['state'] is not manager.project_state
    snapshot['state']['prd_completed'] = False
    snapshot['state']['project_completed'] = True
    snapshot['state']['injected_key'] = 'x'
    snapshot['phase'] = "done"

    assert manager.project_state['prd_completed'] is True
    assert manager.project_state['project_completed'] is False
    assert 'injected_key' not in manager.project_state
    assert manager.get_snapshot() == original_snapshot


def test_snapshot_contains_only_plain_data():
    """快照里不得出现 agent 对象、私有字段或其他可变内部引用。"""
    manager = build_manager(prd_completed=True, guides_completed=True)

    snapshot = manager.get_snapshot()

    assert isinstance(snapshot, dict)
    assert set(snapshot.keys()) == {'state', 'phase'}
    assert isinstance(snapshot['state'], dict)
    for key in CONTRACT_STATE_KEYS:
        assert isinstance(snapshot['state'][key], bool)
    assert isinstance(snapshot['phase'], str)
    # 值里没有 agent 替身，也没有列表/字典等可变内部结构。
    for key in ('pm', 'pj', 'fe', 'be'):
        assert manager.agents[key] not in snapshot['state'].values()
    for value in snapshot['state'].values():
        assert not isinstance(value, (dict, list, set, tuple))


def report_status_expected_all_false():
    return (
        "\n📊 项目状态报告:\n"
        "⏳ 产品经理: 进行中\n"
        "⏳ 项目经理: 进行中\n"
        "⏳ 后端程序员: 进行中\n"
        "⏳ 前端程序员: 进行中\n"
        "⏳ 项目整体: 进行中\n"
    )


def report_status_expected_mixed():
    return (
        "\n📊 项目状态报告:\n"
        "✅ 产品经理: PRD 已完成\n"
        "✅ 项目经理: 指导文档已完成\n"
        "⏳ 后端程序员: 进行中\n"
        "⏳ 前端程序员: 进行中\n"
        "⏳ 项目整体: 进行中\n"
    )


def report_status_expected_all_true():
    return (
        "\n📊 项目状态报告:\n"
        "✅ 产品经理: PRD 已完成\n"
        "✅ 项目经理: 指导文档已完成\n"
        "✅ 后端程序员: 接口开发已完成\n"
        "✅ 前端程序员: 页面开发已完成\n"
        "✅ 项目整体: 已完成\n"
    )


@pytest.mark.parametrize("combination,expected_output", [
    ({}, report_status_expected_all_false()),
    (
        {'prd_completed': True, 'guides_completed': True},
        report_status_expected_mixed()
    ),
    (
        {
            'prd_completed': True,
            'guides_completed': True,
            'backend_completed': True,
            'frontend_completed': True,
            'project_completed': True
        },
        report_status_expected_all_true()
    ),
], ids=["all_false", "mixed", "all_true"])
def test_report_status_output_is_unchanged(combination, expected_output):
    """三个入口依赖终端打印，输出必须与改动前逐字一致。"""
    manager = build_manager(**combination)

    output = run_capturing_output(manager.report_status)

    assert output == expected_output


def test_report_status_matches_pre_change_capture():
    """与改动前捕获的真实输出逐字比对（基线文件由 _baseline_capture.py 生成）。

    这是「report_status() 打印行为不变」的直接证据：基线文本产生于加入
    get_snapshot() 之前，不是按当前实现回填的。
    """
    golden_path = pathlib.Path(__file__).with_name("_baseline_before.txt")
    golden_text = golden_path.read_text(encoding="utf-8")

    current_text = baseline_capture.capture_text()

    assert current_text == golden_text


def test_report_status_does_not_change_state_or_snapshot():
    """打印不改状态：report_status() 前后快照一致。"""
    manager = build_manager(prd_completed=True)

    before = manager.get_snapshot()
    run_capturing_output(manager.report_status)

    assert manager.get_snapshot() == before
