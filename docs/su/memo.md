# su 工作备忘录

## 2026-10-17

### 会话历史（同一项目，多轮）

1. 只读勘察：`README.md`、三个入口、`myagent/*`、`ai_agent_factory/agent/baseagent.py`、
   `ai_agent_factory/llms/base_llm_openai.py`、7 张角色卡与 7 份 `boundary.md`。
2. 口径更正：首轮误称「无治理种子」，实际已 bootstrap（`角色卡/` 下 7 角色齐备）。
   成因：拿几个候选路径读失败就反推。教训：读不到就说「未确认」。
3. 边界未生效期：多次写入被 `F6 边界未被接受` 拒绝（零副作用）；客户 `confirmed:true` 后仍未放行
   → 结论：接受动作不在 su 的确认通道内。**后经客户在应用侧确认，`.ans/project.json` 写入
   `acceptance.accepted=true`（8 份边界 sha256 已 pin），写权恢复。**

### 桌面客户端（PySide6）— 进行中

**客户需求**：添加桌面客户端。客户在 3 个技术路线中选定 **A：PySide6 单进程桌面应用**。

**关键发现（决定方案）**：现有管线的输出全部是 `print`——
`SystemManagerAgent.token_deal()` 是 `print(result, end='', flush=True)`，`todo()` 同样 print；
三个 CLI 入口也是 print + input()。**管线没有「输出」这个概念，只有「打印」**，界面层无法干净取数。
三条路（捕获 stdout / 给 BaseAgent 加钩子 / 子进程跑 CLI）中选定**加钩子**。

**已落盘**：

| 文件 | 内容 |
| --- | --- |
| `角色卡/desktop-client/role-card.md` | 新角色卡（9499 B），含退回/返工流程与 temp 草稿区规则 |
| `角色卡/desktop-client/boundary.md` | Section 1 白名单（3922 B） |
| `角色卡/desktop-client/boundary.yaml` | 机器可读边界（1358 B） |
| `docs/workflow.md` | S1–S7 步骤表、完成口令、变更与重验（3975 B） |
| `docs/contracts/desktop-client-v1.md` | C1 输出事件 / C2 状态快照 / C3 生命周期 / C4 依赖（5465 B，已冻结） |
| `.ans/project.json` | roles 表新增 desktop-client；acceptance 与 8 条 pin 未动（已回读核对） |

**边界变更**：仅新建角色。S2 改的 `baseagent.py`、S3 改的 `system_manager_agent.py`、
S5 改的 `requirements.txt` 均在各角色**现有** Section 1 内，**未扩张任何既有角色的写权**。

**派发与看护记录（2026-10-17）**：

- S2 → `platform-framework`（C1 输出事件订阅）；S3 → `orchestration`（C2 状态快照）。两者并行。
- 派发后系统报「会话因边界更新重建」，随后收束提示称「全部角色空闲、队列为空」。
  **核查（03:45:53）证明收束判定与实际不符**：两角色均 `busy=true`、`进行中 dispatch`、
  `contextSource=fresh`，正在读契约与源码。**派发未丢失**。据此不收尾，继续等待回交。

**观察到的环境障碍（如实记录，不阻断）**：

1. `run_shell` 在本环境不可用于列举：`ls -R` → `spawn ls ENOENT`；
   `python -c "..."` → 审核拒绝（命中 c 硬拒规则）。`python --version` 可执行。
   → 角色无法列目录，只能按已知路径逐个 `read_file`。它们各自浪费了 2–3 轮尝试。
2. `platform-framework` 去读 `角色卡/platform-framework/references/architecture.md`（路径猜错，
   references 实际在 skillRoot 下）与 `角色卡/project-management/docs/project-rules.md`（不存在）。
   根因：各角色卡的「必读资料」引用了**尚不存在**的文档——`docs/project-rules.md`、
   `docs/architecture.md`、`feature-map.md` 都由项目管理角色在被接受后才建立，至今未建。
3. 后果评估：不阻断本步（C1/C2 的实现只依赖源码与契约），但会让每个角色多烧几轮。
   是否补建这些文档由 S7 承担；**不在本步扩边界**。

**看护记录（03:48，轮次逼近超时告警）**：`orchestration` 报 90% 预警线。
核查 `role_status` + `session_tail`：`busy=true`、`进行中 dispatch`、无挂起确认卡；
轨迹为「抓基线 → 两次 `edit_file` 改 `system_manager_agent.py` 成功 → `pytest` → `git diff --stat`
→ 写 `test/orchestration/support.py`、`conftest.py`」，每步均有产出，属**正常长轮次**。
结论：不中断。中断会丢失已落盘的实现。仅告知，不提议恢复动作。

**看护记录（03:48，platform-framework 超时）**：`role_status` 显示 `timed_out @ 03:48:02.627Z`，
会话有 `本轮已中止` 行。**已自动恢复**：03:48:10.999 收到重投的同一条 S2 派发，新一轮进行中
（`busy=true`、`contextSource=recovered`）。

中止时盘上产物（未丢）：
- `test/platform-framework/conftest.py`、`fakes.py`、`test_baseagent_legacy_output.py`、
  `test_baseagent_context.py`
- 改动前基线已跑出：**6 个用例全通过**（针对未改动的 `baseagent.py`）
- **`baseagent.py` 尚未修改**——正要写订阅事件组时被掐断。

处置：不提议恢复动作（已自愈，再中断反而有害）。后续核对 S2 回交时**必须验证**：
① 那 6 个基线用例是否真在未改动代码上跑的（可复现性）；② 生产改动后基线组是否仍全通过。

**回交汇总（03:48，两份均 failed）**：

- `platform-framework`（S2）：产物 4 个测试文件（`test/platform-framework/` 下 `conftest.py`、
  `fakes.py`、`test_baseagent_legacy_output.py`、`test_baseagent_context.py`），替身质量好
  （含 `FailingLLM`/`MidStreamFailingLLM` 为 error 事件预留）。**但 `baseagent.py` 我逐行读过，
  与任务前完全一致，没有任何订阅方法 → C1 未实现。** 「6 个基线用例通过」仅是角色自述，
  我无法运行 pytest 复验（`su 只读档` 拒绝执行）。结论：**未完成**。
- `orchestration`（S3）：`system_manager_agent.py` 已落地 `get_snapshot()`、`_derive_phase()`、
  `_requirement_submitted()`、`PHASE_*`/`STATE_KEYS` 常量（我读过全文确认）；`report_status()`
  未被改动；测试 `test_project_state_snapshot.py` 扎实（32 种布尔组合、phase 可达性、
  无副作用、副本语义、打印逐字比对）。**但无正式报告、无 `S3-DONE` 口令、无测试运行输出。**
  结论：**实现就绪，未验收**。

**系统性问题：120 秒硬超时对这个项目不够。** 两角色各连续超时一次；派发后各自自动重开新一轮，
当前均 `busy=true`、`进行中 dispatch`。若再超时，须把 S2/S3 拆成更小的子步骤（单轮可完成）。

**杂项**：`test/orchestration/` 下留有抓基线用的临时脚本 `_baseline_capture.py`、
`_baseline_run.py`、`_baseline_before.txt`，属该角色边界内，要求其回交时清理或说明。

**治理缺陷发现（03:49，重要）**：`platform-framework` 在 03:49:22 完成代码后，写
`角色卡/platform-framework/api-spec.md` 被门禁拒绝：`目标路径未匹配任何边界条目`。
核查其 `boundary.md` Section 1：只有 `feature-map.md`、`角色卡/<role>/docs/feature/`、
`角色卡/<role>/docs/`，**没有 memo.md / changelog.md / functional-description.md / api-spec.md**。

后果：**7 个既有角色的角色卡都要求交这些文档，但边界一律没授予**——角色写不了自己的交付物。
`platform-framework` 已自行降级把 api-spec 写进 `common/platform-framework/api-spec.md`（其私有目录，
合法但不是规范位置）。这是 bootstrap 遗留缺陷，与我建 `desktop-client` 时按规范授予完整文档面形成对比。

修复方式：给 7 份 boundary.md 的 Section 1 统一补上文档面（memo/changelog/functional-description/
api-spec 四个单文件 + docs/design|change|fix 三个条件目录 + `temp/<role>/`）。
**风险**：改 boundary.md 会使 `.ans/project.json` 里对应 7 条 pin 的 sha256 失效，
极可能让所有角色再次被 F6 拒写，**须客户在应用侧重新接受**。
因此**不在两角色跑轮次期间动手**——先报客户，等轮次结束后再递确认卡。

**S2 回交验收（03:50，结论 blocked）**：我逐行读了 `ai_agent_factory/agent/baseagent.py` 与
`test/platform-framework/test_baseagent_output_events.py`，核对结果：
- 实现属实：`AgentOutputError`（frozen dataclass，含 exception + message）、`AgentOutputListener`
  （三抽象方法）、`set_output_listener()`（类型校验）/`clear_output_listener()`（幂等）、三个私有发射方法；
  `chat()` 包 try/except：token 先发事件再走 `token_deal`、`turn_completed` 在 `todo` 之前、出错先发
  error 再 **裸 raise**（保留类型与 traceback）。`except Exception` 不捕 `BaseException` → KeyboardInterrupt 仍冒泡。
- 订阅组测试 **12 个用例**，与自报一致，覆盖：顺序与内容、并存策略、取消订阅及幂等、类型校验、
  四类 error 路径、调用线程一致、嵌套 chat 顺序、静态扫描禁止 threading/Qt。
- **测试运行结果（18 passed / 全仓 125 passed）为角色自述，我无法复验**（`su 只读档` 拒绝 pytest）。
- 卡点：文档面未授予（见上条治理缺陷），角色按规矩拒绝自行扩权、不给 `S2-DONE`。**处置正确**。

**新风险（记给 S4）**：C1 采用「事件与 print 并存、不抑制」。Windows 无控制台模式（`--noconsole`/pythonw）
下 `sys.stdout` 可能为 None，`print` 会抛异常。桌面端须自行处理（重定向到日志或 devnull），
此项不在平台框架边界内，属 desktop-client。派发 S4 时必须写进任务文本。

**S3 回交验收（03:51，结论 failed，但这次带了真实 pytest 输出）**：
`python -m pytest test/orchestration/test_project_state_snapshot.py -q` →
`..................................F.F.F.F.F.F.F..........` **7 failed**，全部集中在
`test_phase_is_within_contract_enum_and_consistent`。

**我的诊断（读代码 + 数组合得出，非猜测）**：失败的组合形如
`prd=False, guides=False, backend=False, frontend=True, project_completed=False`。
实现 `_derive_phase()` 在 `prd_completed=False` 时直接落到 `idle`（除非上下文已有用户消息）；
而测试的 `assert_phase_matches_state()` 断言 `idle ⇒ 五个标志全 False`。
数量恰好对上：`prd=False & project_completed=False` 且 `guides/backend/frontend` 至少一个为 True
→ `2^3 - 1 = 7` 种，与 7 个 F 一致。
判断：这些是**正常流程下不可能出现的矛盾状态**（前端完成而 PRD 未完成）。实现没错，
是测试对不可达状态断言过强。**但不能因此判过**——按规矩不得为变绿而放宽断言，
必须由该角色给出有理由的取舍并写进 api-spec。

**新坑：orchestration 队列里仍挂着原始 S3 派发**（入队 03:45:45，`队列 1`）。
角色虽 `busy=false`，但该条目会自动再跑一轮，预计同样吃满 120 秒（已 `timed_out` 计 2）。

**因此本轮决定：不改边界、不重派。** 理由：它下一轮要写盘，此刻改 boundary.md 会让 pin
失配、把它打入 F6，白烧一轮。等这次重跑结果出来再动。

**S3 验收（03:51 后，结论 completed，我判过）**：
- 7 个失败是**在实现里修好的，不是改松断言**。`_derive_phase()` 新增 `_project_started(state)`：
  五标志任一为真或上下文已有用户消息 ⇒ 不算 idle ⇒ 矛盾组合落到 `prd`。我先前读过的
  `assert_phase_matches_state` 断言未被删改。
- `report_status()` / `make_decision()` / `execute_next_step()` 逐段比对，与改动前一致。
- 角色自报 `python -m pytest test/orchestration -q → 108 passed`；**我无法独立复验**
  （`su 只读档`拒绝 pytest），采信其回执并如实标注。其上一轮主动交出 7 failed 的真实输出，
  增加了可信度。
- 超范围但可接受：新增 `test_make_decision_branches.py`（20 例），符合其 role-card
  「每个决策分支都要有对应用例」的质量约束。
- 遗留：`test/orchestration/` 下 `_baseline_capture.py`、`_baseline_run.py`、
  `_baseline_before.txt`、`_baseline_after.txt` 为抓基线临时件，需其清理或说明保留理由。
- 同样受文档面缺陷阻塞：api-spec 内容暂寄存在 `feature-map.md`。

**S3-DONE 已由角色给出**（2026-10-17）。

**边界文档面修复已落盘（03:5x，客户确认后）**：7 份 `boundary.md` 各补 8 行（memo / changelog /
functional-description / api-spec 四个单文件 + docs/design|change|fix 三个条件目录 + `temp/<role>/`），
并在「私有抽象」后补 temp 草稿区说明；`docs/workflow.md` 新增「当前进度」与「任务粒度」两节
（S1/S3 已 DONE，S2 待文档补位，S4 前置追加 S2-DONE）。

**已知后果**：`.ans/project.json` 里这 7 条 pin 的 sha256 已失效，需客户在应用侧重接受。
已告知客户；并已按 J-1 派发小任务给 `platform-framework`（迁移 api-spec + 补 S2-DONE），
若仍被 F6 拒则它会如实报 blocked，据此判断 pin 是否真的拦写。

**S2 收尾验收（判过，S2-DONE 接受）**：读了 `角色卡/platform-framework/api-spec.md`（正文完整：
C1 三类事件触发时机、顺序约定及两条收益、并存策略三条理由、线程与 GUI 约束、错误处理、
订阅粒度、三个入口与四个智能体只读核对表、符合性表「偏差：无」、测试证据表、已知限制 4 条、
变更历史 rev1/rev1.1）、`common/platform-framework/api-spec.md`（确为 612 字节指针，无第二份正文）、
`feature-map.md`（已改为文档索引表，无「临时位置」表述）。代码零改动，与上一轮我复核的版本一致。

**重要事实：pin 失配没有拦写。** 角色四次写入全部「已获准并落盘」，无 F6。说明门禁校验的是
boundary 内容而非 pin 哈希；pin 仅作接受时的证据快照。→ 客户不必为了「能用」去重接受，
但 pin 里的 sha256 现已与实际文件不符（记录失真），建议顺手刷新一次。

**S4 已派发（desktop-client）**，按新「任务粒度」限定为最小骨架：能开/能看/能关。
四条硬约束已写入任务文本：① C1 订阅是实例级（子智能体需各自订阅，本步用替身）；
② 长任务在工作线程、信号回界面线程；③ 关闭要能中断并回收线程、重复关闭不报错；
④ Windows 无控制台模式 `sys.stdout` 为 None 时 print 会炸，必须兜住并测试。
明确不做：状态面板(C2)、打包、美化、真实接线（归 S5）。

**S4 回交（blocked，环境阻塞）**：本机无任何 Qt 绑定（角色用 `pip show` 核实 PySide6/PyQt6 均无），
`python -m pip install PySide6` 被 ShellGate（pm 规则集）拒绝，理由：未固定版本、未指定 requirements、
会装入共享 Python 环境。角色**未写任何 GUI 代码**（不交未运行过的代码）、未改 requirements、未绕过门禁，
只落两份材料：`角色卡/desktop-client/memo.md`、`角色卡/desktop-client/docs/design/2026-10-18_S4-桌面骨架设计草案.md`。

**其设计中值得注意的三点（我已读全文）**：
1. Qt 无关核心（`output_listener.py`）与 Qt 桥（`bridge.py`）切开，使输出转投逻辑在没装 Qt 时也能测；
2. Qt 懒加载：`import desktop` 不触发 Qt 导入、不建 `QApplication`，满足 C3「import 无副作用」；
3. stdout 兜底放在**创建窗口之前**，写 `%TEMP%/codeagent-desktop/`，失败退回 `io.StringIO`。

**它报出的契约缺口（真实且重要）**：C1 订阅是**实例级**，而 `SystemManagerAgent` 派发的
pm/pj/fe/be 是独立实例 → 桌面端只订阅注入的那一个对象，**收不到子智能体的流式输出**。
它按规矩没有在界面层绕过，交回调度。→ 需要契约 C1 出 **v2**：编排层提供「把监听器下发到子智能体」
的公开入口。影响面：S2 的回交需作废重验追加该方法；S4 的渲染部分依赖它才能看到完整输出。
**当前不阻塞 S4 骨架**（骨架用替身），但真实接线（S5/S6）前必须解决。

**阻塞解除需客户决策**（我无法授权环境变更）：见下条待确认项。

**S5a 验收（判过）**：`requirements.txt` = `openai` / `python-dotenv` / `PySide6==6.12.0`（既有两行未动，
已核）。`.venv` 用 Python 3.12.0 建成并装好 PySide6 6.12.0 / shiboken6 6.12.0；自检脚本
`test/assembly/check_pyside6_install.py` 在 `.venv` 里 exit 0，输出 `installed: PySide6==6.12.0` /
`Qt: 6.12.0`（角色回执，我无法运行复验）。选版偏差：派发建议 6.8.1 但本机索引只有 6.10.1–6.12.0，
就近取 6.12.0，理由正当。

**新发现（重要，门禁解析器行为）**：`assembly` 报 `角色卡/assembly/docs/change/`「不在门禁白名单」。
我读了它最新的 `boundary.md`——**该行确实存在**（我这一轮刚加的 `条件目录` 行）。
结合三条证据：
- `desktop-client` 有 `boundary.yaml`（`kind: directory`），写 `角色卡/desktop-client/docs/design/` **成功**；
- `platform-framework` 只有 `boundary.md`，写 `角色卡/platform-framework/api-spec.md`（`单文件` 行）**成功**；
- `assembly` 只有 `boundary.md`，写 `角色卡/assembly/docs/change/`（`条件目录` 行）**失败**。
→ **门禁对 .md 表格只认 `单文件` / `自有目录` 两类，`条件目录` 行不被解析。** YAML 的 `kind: directory` 正常。
修复方向：给 7 个既有角色各补一份 `boundary.yaml`（镜像其 Section 1 全部条目），与 `desktop-client` 对齐。
这正是我最初向客户提过的假设②，现已有直接证据。

**另记**：pip 短参数 `-r` 被规则误拒、`--requirement` 长参数可过；属规则误伤，已告知后续角色改用长参数。

**S4 已重派**（环境就绪）。

**S4 第一次回交（failed／超时，S4 未完成）**：`desktop/` 落了 10 个实现文件
（`errors.py`、`stdio_fallback.py`、`output_listener.py`、`worker.py`、`bridge.py`、`window.py`、
`app.py`、`__init__.py`、`unwired_orchestrator.py`、`__main__.py`），外加 `temp/desktop-client/_smoke.py`；
**`test/desktop-client/` 一个测试都没有**，且 `.venv` 无 pytest（`No module named pytest`）→ 零验证。

我读了 `desktop/app.py` 与 `desktop/worker.py`，质量判断（静态）：
- C3 生命周期做到位：`start()` 不跑事件循环、`run()` 跑；句柄只暴露 `shutdown/is_closed`，
  不返回编排器或 Qt 对象；`shutdown()` 顺序合理（停转发 → 拒新任务+join → 退订 → 关窗 quit），
  可重复调用；启动失败捕获后先 `handle.shutdown()` 清理再抛 `DesktopStartupError`。
- 线程：daemon 线程、忙时拒绝新任务、`join(timeout)` 超时会打印警告而**不假装回收成功**，
  并诚实标注「Python 线程无法强杀，取消只在任务边界生效」。这点很难得。
- 复用 `QApplication.instance()` 以支持离屏测试复用；`_import_qt_modules()` 把 PySide6 延迟到
  真正启动时才导入（`import desktop` 无副作用的前提）。

**队列堆积记录（04:03）**：`desktop-client` 队列有 **2 条**待投递——原始的「S4 重派」（入队 03:58:21）
与后来的「S4c：只跑测试」（入队 04:03:20）；角色已 `timed_out` 2 次。
→ **超时的派发会被系统自动重投，而我没有删除队列条目的原语**（`propose_recovery` 只有
abort-turn / rebuild-session / redeliver 三值，都不能撤销一条待投递项）。
后果：大任务 S4 会再自动跑一遍，可能重复写文件并再次超时；S4c 排在它后面。
处置：**不再追加派发**（只会让队列更长）；观察回执。若大 S4 反复超时，向客户提议恢复动作
（须客户一键确认，我不自行执行）。这与 `orchestration` 早前「队列里挂着原始 S3」属同一机制问题。

**S4 判过（S4-DONE）**：`41 passed in 0.80s`（pytest 9.1.1），同一批用例 `unittest discover` 也 `OK`；
`desktop/` 实现零改动；未删用例、未放宽断言。角色如实更正了我的一处信息滞后（我派任务时说
`test/desktop-client/` 是空的，实际上一轮已写好 6 个文件 41 个用例，只是当时缺 pytest 跑不了）。
本轮它做的补强：4 个用例文件补契约头、新增 `conftest.py`（导入路径 + offscreen）、
加强「缺提交方法」用例同时断言无残留窗口/线程、把 api-spec/memo/changelog 里「没有 pytest」
的陈述更正为「pytest 主用 + unittest 备用」。
**我的复验边界**：测试文件质量我读过两份确认是真测；`41 passed` 与 `unittest OK` 属角色回执，
我（su 只读档）无法独立运行复验。

**下一阶段需要客户决策的三件事**（已整理为一张确认卡）：
1. **契约 C1 出 v2**：监听器下发到子智能体的公开入口（否则窗口只显示编排器自己的话）；
2. **assembly 增加真实接线入口** `desktop_main.py`（现在 `python -m desktop` 用的是
   `unwired_orchestrator` 占位，会输出「还没接到编排层」）；
3. **7 个角色补 `boundary.yaml`**（门禁不解析 .md 的 `条件目录` 行，已有三条证据）。

**契约 v2 与边界对齐已落盘（客户确认后）**：`docs/contracts/desktop-client-v2.md`（C1.2 监听器下发、
C4 依赖精确锁定，v1 不动）；7 份 `boundary.yaml`（内容与各 `.md` 的 Section 1 逐行等价）；
`角色卡/assembly/boundary.md` Section 1 增 `desktop_main.py`；`docs/workflow.md` 当前进度更新
（S4-DONE、新增 S3b/S5c、契约版本说明）。

**已派发**：S3b → `orchestration`（C1.2 监听器下发到四个子智能体）；S5c → `assembly`
（`desktop_main.py` 真实接线 + 缺环境变量可读提示）。

**S3b 判过（S3b-DONE）**：读 `myagent/system_manager_agent.py` 全文确认新增
`set_output_listener_for_children(listener)`、`clear_output_listener_for_children()`、
`_raise_child_listener_failures()`：遍历 `self.agents.items()` 逐个下发，缺能力或抛错都收集
「键名（类型名）+ 异常类型 + 原文」后统一抛 `RuntimeError`，**不静默跳过、不降级**；
幂等依赖 C1.1 的替换语义。`make_decision`/`execute_next_step`/`report_status`/`get_snapshot` 未变。
角色回执 `.venv` 内 `pytest test/orchestration -q` → 119 passed（108 既有 + 11 新增），我无法复验。

**S5c 判过（S5c-DONE）**：读 `desktop_main.py` 全文确认——只做「读 .env → 构造 OpenAILLM+四智能体+
SystemManagerAgent → desktop.run」；缺变量 exit 2 并逐条列出缺失项、`.env` 路径与三行示例；
`ListenerFanout` 解决「装配层拿不到桌面端内部监听器」的问题：桌面端调 `set_output_listener` 的瞬间，
把同一监听器铺给编排器+四个子智能体，清除时一并清掉，其余属性 `__getattr__` 委托，**不穿透私有属性、
`desktop/` 零改动**。优先用编排层的 `set_output_listener_for_children`，缺失时才退回用自己持有的
agents 字典（两种分支都有用例）。`desktop.DesktopStartupError` 确在 `desktop/__init__.py` 中导出，
异常捕获不会落空。自查发现并修掉两个真实缺陷：① emoji 在 gbk 控制台抛 `UnicodeEncodeError`；
② `set_output_listener` 的类型校验会拒鸭子类型。

**我的调度失误（记档）**：S3b（编排层下发入口）与 S5c（装配接线）我并行派发，但后者依赖前者的 API。
结果 assembly 读到的是 orchestration 写入前的旧文件，回交里写「S3b 仍未落地」。**实际我 04:0x 已核过
`set_output_listener_for_children` 存在**。它不是造假，是竞态。教训：有依赖的两步不能并行。
所幸它用 `getattr` 探测 + 等价下发，入口就绪后自动切换，无需返工。

**未解疑点**：`角色卡/assembly/docs/change/` **仍然被门禁拒**（角色把变更记录写进
`common/assembly/docs/change/`），而我这一轮已给 assembly 写了含该目录的 `boundary.yaml`。
说明 YAML 未被加载器采用，或需重建会话才生效。待查——影响 7 个角色的 docs 子目录写入。

**已派发**：S7 → `project-management`（README 启动说明 + 架构文档；并修「README 引用不存在的
.env.example」这个老问题）；S6 → `testing`（端到端验收，**客户已授权真实 API 调用**，要求控制规模、
分三步走、子智能体 token 数为 0 即判不合格）。

**S6 回执（failed/超时，但含实质结论；角色拒绝发 S6-DONE，处置正确）**：
- **C1.2 关键证据成立**：真实四智能体 + 真实 `SystemManagerAgent` + 真实
  `set_output_listener_for_children`，模型换替身；六轮累计 92 token，
  `be=32 / fe=24 / pj=24 / pm=4 / sys=8`，**每轮监听器收到序列与模型产出逐条相等**，error 0；
  清除订阅后子智能体 token 归零、编排器仍有输出。
- 离线完整流程产出 5 个文件（`api_spec.json`、`backend/server.js`、`backend_guide.md`、
  `frontend_guide.md`、`public/todo.html`），`phase` 落在契约枚举内。
- **真实 API 仍未验证**：全盘无 `.env`，三变量均未设置 → 需客户建 `.env`。
- **真缺陷 1（严重）**：`make_decision` 分支抛错时 `chat()` 正常返回、**监听器收到 0 个 error**，
  只在控制台打印「管理者决策解析错误」→ 桌面窗口对这类失败**完全静默**。根因：`SystemManagerAgent.todo()`
  内部 `try/except` 吞掉异常，C1 的 error 事件无从发出。
- **真缺陷 2（成本风险）**：`BackendDeveloperAgent` / `FrontendDeveloperAgent` 的 `todo()` **无轮数上限**，
  模型连续返回文件操作标签时自递归，实测 11340 token / 494 次 turn_completed 后 `RecursionError`。
- **缺陷 3（测试基建）**：四套测试合并跑 exit 2，`test/orchestration/support.py` 与
  `test/desktop-client/support.py` 同名顶层模块且无 `__init__.py` → `ImportError: cannot import name 'PROJECT_ROOT'`。
- **观察**：C1 事件不带来源标识，窗口无法区分「谁说的」；输出区首行是原始决策词 `next`。

**S6FIX 两项均判过**：
- 缺陷一（静默失败，`orchestration`）：`todo()` 诊断打印后改裸 `raise`，异常冒泡到 `chat()` 使 C1
  的 `error` 事件得以发出。我读了 `test_todo_error_propagation.py`，断言硬（`errors[0].exception is
  raised.value`、`chat()` 抛而非返回、正常路径打印逐字不变、`KeyboardInterrupt` 不被接住）。
  `test/orchestration` 123 passed（回执）。
- 缺陷二（无限递归，`business-agents`）：三文件加 `MAX_FOLLOWUP_ROUNDS = 8` + `followup_round` +
  `reserve_followup_round()`，达上限向 stderr 打印含轮数警告并停止，链结束归零。
  `test/business-agents` 10 passed（回执）。
**我发现的一处落差（未修，告知客户）**：上限警告打到 **stderr**，而桌面端 `stdio_fallback` 把
stderr 重定向到日志文件（`%TEMP%/codeagent-desktop/`）→ **窗口里看不到这条警告**。agent 层修复正确，
但桌面用户实际感受是"静默停下"。可选后续：让上限事件走 C1 的 error 通道（需评估是否会被
`BaseAgent.chat()` 的 except 打断上层流程——正是该角色选择打印而非抛异常的理由）。
**另一个已知瑕疵**：`frontend_developer_agent.py` 行尾被改成 LF（原 CRLF），git diff 显示整文件变化，
内容与提示词未变。

**待办**：

1. 等 S2、S3 回交并核对完成口令与测试证据。
2. S2+S3 都通过后才派 S4（desktop-client：窗口骨架与接线）。
3. S4 完成后派 S5（assembly：requirements 增 PySide6 + 启动方式），再 S6（testing 端到端）、
   S7（project-management 架构与 README 更新，可与 S6 并行）。

### 待确认项

- 无。新增角色是否需应用侧重新接受边界：已在确认卡中提示客户，未收到反馈。
- 若客户希望减少角色空转，可考虑补建 `docs/project-rules.md` 等必读文档——需另立治理变更。
