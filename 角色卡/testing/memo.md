# 工作备忘录：测试

本文件记录本角色续接工作确实有用的少量线索。不是全局规则、任务状态表或第二份 changelog。权限仍由 `boundary.md` Section 1 决定。

## 已核实的事实

- 2026-10-17：**派发指定的必读资料有两处不存在**：仓库根没有 `references/`（`references/testing.md`、
  `references/entrypoint.md`、`references/documentation.md`、`references/architecture.md` 均 ENOENT），
  也**没有 `docs/project-rules.md`**（项目管理角色尚未建立）。规则状态据此报告为「未确认」，
  本角色没有自行建立或修改任何全局约束。
- 2026-10-17：`ai_agent_factory/utils/file_operation_handler.py` 顶部
  `from ai_agent_factory.llms.base_llm_openai import BaseLLM` **不会报错**——`base_llm_openai.py`
  自己 `from ...base_llm import BaseLLM`，所以那个名字确实存在于该模块命名空间。旧备忘里的
  「坏导入」待核实项可以销掉。
- 2026-10-17：四套测试**分开跑**全部通过（platform-framework 18、orchestration 119、
  desktop-client 41）；`test/assembly` 里是自检脚本不是 pytest 用例，跑 pytest 会 `exit 5`。
- 2026-10-17：**合并成一条 pytest 命令会失败**——`test/orchestration/support.py` 与
  `test/desktop-client/support.py` 同名顶层模块冲突，6 个用例收集报错。属测试基础设施问题，
  修复归这两个目录的所属角色。
- 2026-10-17：`.venv` 版本：Python 3.12.0 / PySide6 6.12.0 / Qt 6.12.0 / openai 3.33.0 / pytest 9.1.1。
- 2026-10-17：**本机没有可用 `api_key`**：三个环境变量都未设置，全盘也没有 `.env*` 文件。
  任何「真实 API 调用」类验收在本机都无法执行，必须先由项目管理角色安排提供凭证。
- 2026-10-17：S6 离线验收的结论见 `docs/report/s6-desktop-e2e-acceptance.md`：
  C1.2（子智能体事件到达监听器）在真实对象 + 模型替身口径下成立；
  真实模型口径未验证。
- 2026-10-17：**实测确认**：编排器 `make_decision()` 分支里抛错时（例如 `ask_pj` 读取
  尚未生成的 `self.agents["pm"].prd`），异常被 `todo()` 自己的 try/except 吞成一行 print，
  `chat()` 看不到异常，**监听器收到 0 个 error 事件**——桌面端窗口完全静默。
  复现：`test/testing/check_orchestrator_decision_error.py`。
- 2026-10-17：`SystemManagerAgent.token_deal` 会把模型原始回复（含 `next` / `ask_pm:` 这类
  决策词）逐字转发给监听器，界面输出区因此会先出现一行 `next`；C1 事件不带来源标识，
  窗口无法区分「谁说的」。是否加来源属契约变更，本角色只记录。

## 容易踩坑的位置

- **七个维护角色 vs 五个业务智能体**。`角色卡/` 下是本项目七个**维护角色**；`myagent/` 里是系统
  自己用的**业务智能体**。两者名称重叠，写报告时要明确区分。
- **业务智能体的系统提示词互相包含对方称呼**：编排器提示里有「后端程序员 / 前端程序员」，
  后端/前端提示里有「项目经理」，项目经理提示里有「产品经理」。写替身模型（或任何按提示词
  路由的夹具）必须按「提取器 → 系统架构师 → 后端 → 前端 → 项目经理 → 产品经理」的顺序判定，
  否则会认错智能体、让某个 agent 收到不该收的任务并自递归。
- **`BackendDeveloperAgent` / `FrontendDeveloperAgent` 的 `todo()` 没有轮数上限**：回复里仍有
  文件操作标签就会再 `chat()` 一轮。替身必须能在第二轮给出「无文件操作」的收尾回复，
  否则无限递归到 `RecursionError`（异常被 agent 自己吞掉，只打印）。真实模型也有可能触发。
- **子智能体回灌的判定条件**：`todo()` 回灌的是 `json.dumps(list)`（以 `[` 开头）；
  编排器下发的是 `json.dumps(dict)`（以 `{` 开头）。只把 `[` 当回灌，否则后端/前端
  一行代码都不会产出。
- **`output/` 与 `config` 会互相污染**：验收脚本要 `chdir` 到 `temp/testing/_workspace*` 隔离。
- **控制台是 cp936**：智能体会 print emoji，脚本要先
  `sys.stdout.reconfigure(encoding="utf-8", errors="replace")`；反过来，中文消息经管道捕获
  会显示成乱码（`desktop_main.py` 的缺变量提示就是这样），贴证据时要说明。
- **不要为了让结果变绿改断言或跳过**。发现其他角色的测试/代码有问题，报告而不是代改。

## 已完成的一次性动作

- 2026-10-17：建立 `test/testing/s6_desktop_e2e_acceptance.py`（真实对象 + 模型替身，
  六轮，逐 token 比对）与 `test/testing/s6_desktop_gui_smoke.py`（`QT_QPA_PLATFORM=offscreen`
  + 真实 `desktop.start`）。两者都不联网，可随时复跑。
- 2026-10-17：`temp/testing/` 下留了 4 个一次性小脚本（`check_env.py`、`print_versions.py`、
  `list_tree.py`、`find_env.py`），草稿区，不属交付物。

## 下次从哪继续

1. 先读 `boundary.md` Section 1，确认授权范围未变。
2. 若拿到 `api_key`：把 `s6_desktop_e2e_acceptance.py` 的 `ScriptedLLM` 换成真实
   `OpenAILLM`，轮次收到 1～2 轮，重跑并把统计写进报告 §5。
3. `ask_be` / `ask_pj` 分支的属性缺失问题已经用替身实测确认（见「已核实的事实」），
   若「流程编排」角色修了，用 `check_orchestrator_decision_error.py` 复测即可。
4. 合并跑四套测试的 `support` 冲突若被所属角色修好，应复跑那条派发原文命令并更新报告 §2。
