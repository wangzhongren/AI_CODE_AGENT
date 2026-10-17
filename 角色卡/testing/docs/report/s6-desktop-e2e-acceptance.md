# 测试报告：S6 桌面端端到端验收（桌面客户端 v2）

- 日期：2026-10-17
- 执行角色：测试
- 契约依据：`docs/contracts/desktop-client-v2.md`（C1.1 / C1.2 / C1.3 / C2 / C3 / C4）
- 工作流依据：`docs/workflow.md`（S6）
- 受测代码范围：`desktop/`、`desktop_main.py`、`myagent/`、`ai_agent_factory/`
- 运行环境：Windows / `D:\work\vibe-code\codeagent` / `.venv\Scripts\python.exe`
  - Python 3.12.0、PySide6 6.12.0、Qt 6.12.0、openai 3.33.0、pytest 9.1.1

> 本报告只覆盖本次实际跑过的内容。**没有真实 API 调用**（原因见 §5），
> 因此「真实模型下的端到端」仍未验证。

## 1. 结论摘要

| 项 | 结果 |
| --- | --- |
| 四套单元/层内测试（分开跑） | 通过：platform-framework 18、orchestration 119、desktop-client 41；`test/assembly` 无 pytest 用例（`no tests ran`），改用其两个自检脚本，均通过 |
| 四套合并在一条 pytest 命令里跑（派发原文命令） | **失败**：`support` 模块重名冲突，6 个 desktop-client 用例收集报错，见 §2 |
| 编译检查 `compileall` | 通过（exit 0） |
| 缺环境变量路径 | 通过：可读提示 + 退出码 2，未构造 LLM、未开窗口 |
| C1.2 子智能体事件是否到达监听器（真实对象，模型替身） | **通过**：pm=4 / pj=24 / be=32 / fe=24 / sys=8，逐 token 与模型输出完全一致，0 个 error |
| 完整流程（PRD → 指导 → 后端 → 前端 → 变更需求） | 通过（离线）：5 个产出文件齐备，`phase` 在契约枚举内 |
| C1.2 第 6 条（清除子智能体订阅） | 通过：清除后子智能体 token 归零，编排器自身仍有输出 |
| GUI 离屏冒烟（`desktop.start` + 窗口） | 通过：输出区有内容、无红字错误、无残留 `desktop-pipeline` 线程、`shutdown()` 可重复调用 |
| 真实 `api_key` 端到端 | **未执行（环境无密钥）**，见 §5 |

**判定**：桌面端「能看到完整过程」的前提（C1.2）在离线口径下成立；真实模型口径未验证，
不满足「S6 端到端验收（含真实调用）」的完整要求。

## 2. 四套测试：真实输出

派发给的合并命令：

```
.venv\Scripts\python.exe -m pytest test/platform-framework test/orchestration test/desktop-client test/assembly -q
```

实际结果：**exit 2，6 个收集错误**，核心报错：

```
test\desktop-client\test_import_side_effects.py:10: in <module>
    from support import PROJECT_ROOT
E   ImportError: cannot import name 'PROJECT_ROOT' from 'support'
    (D:\work\vibe-code\codeagent\test\orchestration\support.py)
...
!!!!!!!!!! Interrupted: 6 errors during collection !!!!!!!!!!!
6 errors in 0.14s
```

原因：`test/orchestration/support.py` 与 `test/desktop-client/support.py` 是两个**同名顶层模块**，
两个测试目录都没有 `__init__.py`；合成一条命令时 `support` 先进 `sys.modules`，
另一套用例的 `from support import ...` 就拿到错的那份。
→ 这是**测试基础设施缺陷**，被测生产代码没有问题。修复属 `test/orchestration` 与
`test/desktop-client` 的所属角色（改名或把目录变成包），本角色未修改。

分开跑的真实结果（同一解释器、同一代码版本）：

```
.venv\Scripts\python.exe -m pytest test/platform-framework -q   -> 18 passed in 0.02s
.venv\Scripts\python.exe -m pytest test/orchestration -q        -> 119 passed in 0.08s
.venv\Scripts\python.exe -m pytest test/desktop-client -q       -> 41 passed in 0.79s
.venv\Scripts\python.exe -m pytest test/assembly -q             -> no tests ran in 0.01s (exit 5)
```

`test/assembly` 里是两个自检脚本而不是 pytest 用例，按脚本方式跑：

```
.venv\Scripts\python.exe test/assembly/check_pyside6_install.py -> [OK] PySide6==6.12.0 imports and matches requirements.txt
.venv\Scripts\python.exe test/assembly/check_desktop_main.py    -> [OK] desktop_main 自检全部通过（13 个 [ok]）
```

## 3. 编译与配置路径

```
.venv\Scripts\python.exe -m compileall -q myagent ai_agent_factory desktop desktop_main.py
-> exit 0，无输出
```

缺变量路径（真实执行 `desktop_main.py`，本机无 `.env`、无三个变量）：

```
.venv\Scripts\python.exe desktop_main.py
-> exit 2
[错误] 桌面端启动失败：缺少环境变量 api_key、model_name、base_url
需要这份配置：D:\work\vibe-code\codeagent\.env
  - api_key   <- 缺失
  - model_name   <- 缺失
  - base_url   <- 缺失
如果 .env 还不存在：在项目根目录新建它，写三行，例如 ...
（未构造 OpenAILLM、未开窗口）
```

注：管道捕获时中文显示为乱码，是因为控制台代码页为 cp936、消息按 cp936 写出而
管道按 UTF-8 解读；在真实 cp936 控制台里可读。这不是缺陷，但**贴证据时要注意**。

## 4. 第二步：真实对象 + 脚本化模型（离线）

脚本：`test/testing/s6_desktop_e2e_acceptance.py`
构造：真实 `ProductManagerAgent` / `ProjectManagerAgent` / `BackendDeveloperAgent` /
`FrontendDeveloperAgent` / `SystemManagerAgent` + 真实
`set_output_listener_for_children()` / `clear_output_listener_for_children()`；
模型是继承 `BaseLLM` 的脚本替身（`ScriptedLLM`），无网络。

### 4.1 C1.2 关键判定（决定性的那一条）

```
[统计] 第 1 轮（只调一次 chat）：总计 5 token（pm=4, sys=1）
[统计] 六轮累计：总计 92 token（be=32, fe=24, pj=24, pm=4, sys=8）
[统计] 监听器共收到 token 92 个；turn_completed 15 次；error 0 个
[统计] 事件回调所在线程：['MainThread']

[OK] 子智能体 pm 的 token 到达了监听器（4 个）
[OK] 子智能体 pj 的 token 到达了监听器（24 个）
[OK] 子智能体 be 的 token 到达了监听器（32 个）
[OK] 子智能体 fe 的 token 到达了监听器（24 个）
[OK] 编排器自身的 token 也到达监听器（8 个）
[OK] 全程没有 error 事件（实际 0 个）
```

每一轮都做了**逐 token 比对**：监听器收到的序列 == 替身模型为各来源产生的序列
（提取器调用不计，它不经过 `BaseAgent`）。六个轮次全部相等，因此
「子智能体 token 数为 0」这一不合格条件**没有发生**。

### 4.2 完整流程与文件产出（离线）

六轮依次为：初始需求 → 指导文档 → 后端开发 → 前端开发 → `status` → 变更需求（`modify_fe`）。

```
[产出] output/ 下共 5 个文件：
['api_spec.json', 'backend/server.js', 'backend_guide.md', 'frontend_guide.md', 'public/todo.html']
[OK] phase 取值在契约枚举内：frontend
[OK] 清除后子智能体 token 不再到达（实际 0 个）
[OK] 编排器自身的 token 仍到达（1 个）
```

`phase` 的推进：PRD 完成后 `guides` → 六轮结束后 `frontend`（变更需求把
`frontend_completed` 重置，符合 `execute_next_step` 的既有逻辑）。

### 4.3 过程中观察到的两处业务侧行为（供所属角色判断）

1. **`BackendDeveloperAgent.todo()` / `FrontendDeveloperAgent.todo()` 没有循环上限**：
   只要模型回复里仍带文件操作标签，就会 `self.chat(json.dumps(need_data))` 再问一轮。
   首次跑验收时（我的替身路由写错，让后端一直收到「指导文档」文本），两个智能体
   连续自递归，产生 11340 个 token、494 次 `turn_completed`，最后以
   `RecursionError: maximum recursion depth exceeded` 崩在 agent 内部（异常被
   agent 自己的 `try/except` 吞掉，只打印）。真实模型如果连续两三轮都返回文件操作指令，
   也会走进同一条路径。**建议由「业务智能体」角色评估是否需要轮数上限。**
2. **编排器决策分支出错时，界面完全看不到（已实测复现）**：
   `SystemManagerAgent.todo()` 把 `make_decision()` 包在自己的 `try/except` 里，只
   `print` 一行；`BaseAgent.chat()` 的 except 因此看不到这个异常，也就**不会**向监听器
   发 `error` 事件。桌面端的红字完全依赖 `error` 事件，所以这类失败在窗口里是静默的。
   复现脚本 `test/testing/check_orchestrator_decision_error.py`（真实对象 + 替身模型，
   让决策走 `ask_pj`，而产品经理从未产出 PRD）：

   ```
   [结果] chat() 正常返回，长度 22（异常没有传到调用方）
   [结果] 监听器收到 error 事件 0 个
   [结果] 监听器收到 turn_completed 1 次
   [控制台原文] ❌ 管理者决策解析错误: 'ProductManagerAgent' object has no attribute 'prd'
   [结论] 确认：决策分支失败只打到控制台，监听器/界面收不到 error 事件。
   ```

   同一处代码里 `ask_pj` 用的 `self.agents["pm"].prd` 和 `ask_be` 用的
   `getattr(self.agents['pj'], 'backend_guide')`（**没有默认值**）都可能在首次调度时
   不存在；`execute_next_step` 里同类读取都写了默认值，两处不一致。
   归「流程编排」角色判断是否需要修（本角色未改代码）。

## 5. 未执行项：真实 API 调用（阻塞原因）

派发授权可用真实 `api_key`，但**本机没有可用凭证**：

```
cwd: D:\work\vibe-code\codeagent
.env exists: False
api_key = <未设置>
model_name = <未设置>
base_url = <未设置>
```

（`temp/testing/check_env.py` 实际输出；全盘扫描也没有任何 `.env*` 文件，**本轮再次确认为同一状态**。）
因此第二步用的是脚本替身，**不能写成「真实跑通」**。要补齐这一项，需要
项目管理角色安排提供 `api_key` / `model_name` / `base_url`（写进项目根 `.env`
或注入环境变量）。

**已备好一键补齐的脚本**：`test/testing/s6_real_api_acceptance.py`
（真实 `OpenAILLM` + 四个真实业务智能体 + 编排器，只调一次 `chat()`，
需求为 `做一个能记一条待办的极简页面`，带 90 秒看门狗，用探针统计「哪个子智能体被调用过」
——因为 C1 事件不带来源标识，光看监听器无法归属）。
缺凭证时它**不构造 LLM、不联网**，实测退出码 3：

```
[env] .env exists: False
[env] 缺少环境变量：api_key、model_name、base_url（未打印任何变量值）
[停止] 未发起任何模型调用，未构造 OpenAILLM。
```

客户把 `.env` 写好后只需执行：

```
.venv\Scripts\python.exe test\testing\s6_real_api_acceptance.py
```

退出码 0 即真实口径通过；1 表示验收项未通过（会逐条列出原因）；3 仍是缺凭证。

## 6. 第三步：GUI 离屏冒烟（已做，通过）

脚本：`test/testing/s6_desktop_gui_smoke.py`

```
[info] desktop.start() 返回句柄，耗时 0.056 秒；is_closed=False
[info] 已模拟用户输入需求并点击发送：'做一个能记一条待办的极简页面'
[info] 输出区共 46 字符，前 120 字：'next\nPRD-001 待办页面：输入框、添加按钮、列表；...'
[OK] 窗口输出区出现了内容（用户能看到过程）
[OK] 输出区没有错误红字（没有 error 事件）
[OK] 任务结束后发送按钮恢复可用
[OK] 工作线程已退出（没有残留 desktop-pipeline 线程）
[OK] shutdown() 后句柄为已关闭
[OK] shutdown() 可重复调用
```

**顺带发现的可读性问题**：输出区第一行是编排器自己的原始决策词 `next`
（`SystemManagerAgent.token_deal` 把模型回复逐字打印/转发），界面上既没有
「这句话是谁说的」也没有角色前缀。C1.1/C1.2 的事件只带文本、不带来源，
所以窗口只能按到达顺序把所有 agent 的输出拼在一起。是否要加来源标识属契约变更
（C1），本角色只记录现象，不改契约。

## 7. 没测到的部分

1. 真实模型下的输出质量与稳定性（无密钥）。
2. 真实模型是否会在 `output/` 里写出可运行的前后端工程（只验证了文件生成）。
3. 窗口在**有显示器**环境下的观感（离屏只能验逻辑）。
4. LLM 调用失败（网络断、鉴权失败）在界面上的表现，只在离屏冒烟里确认了
   「无 error 事件」这一条路径，未构造失败注入。
5. `main.py` / `main3.py` / `enhanced_main.py` 三个 CLI 入口的完整流程（本次范围外，
   但 `common/` 下相关用例已随 `test/orchestration` 通过）。

## 8. 复现命令

```
.venv\Scripts\python.exe -m compileall -q myagent ai_agent_factory desktop desktop_main.py
.venv\Scripts\python.exe -m pytest test/platform-framework -q
.venv\Scripts\python.exe -m pytest test/orchestration -q
.venv\Scripts\python.exe -m pytest test/desktop-client -q
.venv\Scripts\python.exe test/assembly/check_desktop_main.py
.venv\Scripts\python.exe test/assembly/check_pyside6_install.py
.venv\Scripts\python.exe test/testing/s6_desktop_e2e_acceptance.py
.venv\Scripts\python.exe test/testing/s6_desktop_gui_smoke.py
```
