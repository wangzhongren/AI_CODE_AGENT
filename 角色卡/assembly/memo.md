# 工作备忘录：装配

本文件记录本角色续接工作确实有用的少量线索。不是全局规则、任务状态表或第二份 changelog。权限仍由 `boundary.md` Section 1 决定。

## 已核实的事实

- 2026-10-17：三个入口的差异——`main.py`（147 行）走**不含编排器**的线性流程：产品经理多轮对话 → 项目经理出指导文档 → 后端 → 前端，然后询问是否开始新项目。`main3.py`（87 行）组装 `{'pm','pj','fe','be'}` 字典交给 `SystemManagerAgent`。`enhanced_main.py`（103 行）与 `main3.py` 高度重合，区别在初始/变更识别：按关键词 `修改` / `调整` / `更新` / `改` 判断，若变更需求来得太早会先把初始开发跑完再处理。
- 2026-10-17：三个入口都 `load_dotenv()` 后读 `api_key` / `model_name` / `base_url`，直接传给 `OpenAILLM(...)`。
- 2026-10-17：`main.py` 与 `main3.py` 都访问 `pm_agent._BaseAgent__context`（`BaseAgent` 的名称改写私有字段）取回复内容。`enhanced_main.py` 未使用该私有访问。
- 2026-10-17：用户命令词是 `status` / `next` / `quit`（三个入口都有），另有产品经理对话阶段的 `done`（仅 `main.py`）。
- 2026-10-17：`requirements.txt` 只有 `openai` 与 `python-dotenv`；无 `pyproject.toml`/`setup.py`/CI 配置。
- 2026-10-17：`.vscode/settings.json` 把 `python.analysis.extraPaths` 设为 `["./agent"]`——**这个路径在仓库里不存在**（没有顶层 `agent/` 目录），疑似历史残留。**待核实**：是否影响类型检查。

- 2026-10-17：`requirements.txt` 现有 `openai`、`python-dotenv`、`PySide6==6.12.0` 三条。项目根有 `.venv`，**用 Python 3.12.0 建**（系统默认 3.14.0 不是它）。桌面端依赖只能在该 `.venv` 里用，系统 Python 里没有 PySide6。
- 2026-10-17：本机 `pip index versions PySide6` 只列到 `6.10.1`–`6.12.0`，**没有 6.8.1**。改版本前先查。
- 2026-10-17：ShellGate 拒绝 `pip install -r requirements.txt`（`c` 硬拒规则），但同一意图的 `--requirement requirements.txt --no-input` 获准。装依赖用长参数形式。
- 2026-10-17：门禁白名单**不含** `角色卡/assembly/docs/`（boundary 列了但门禁未同步），写变更记录会被拒。暂存 `common/assembly/docs/change/`，等门禁与 boundary 对齐再迁。
- 2026-10-17：本机控制台代码页是 cp936，脚本输出中文会乱码。自检脚本 `test/assembly/check_pyside6_install.py` 因此用 ASCII 输出。
- 2026-10-17：`PySide6` 的 `__qt_version__` 属性在 6.12 不存在（抛 AttributeError），Qt 版本要读 `PySide6.QtCore.qVersion()`。
- 2026-10-17：`.venv` 内已装 **pytest 9.1.1**（S5b，`.venv\Scripts\python.exe -m pip install pytest`）。它**不在 `requirements.txt` 里**：那份清单是运行时依赖，桌面端用户不需要 pytest；开发期工具与运行时依赖分开，将来要开发依赖清单得另立文件并走边界申请。在本机跑测试一律用 `.venv\Scripts\python.exe -m pytest ...`，系统 Python 里没有 pytest。

- 2026-10-17：桌面端真实接线入口是项目根的 `desktop_main.py`（本角色写）。跑法 `.venv\Scripts\python.exe desktop_main.py`。缺环境变量时返回退出码 2，不构造 LLM。
- 2026-10-17：**监听器拿不到，靠 `ListenerFanout` 接**。`desktop.start()` 内部自建 `OutputEventForwarder` 后调 `orchestrator.set_output_listener(listener)`，`DesktopHandle` 不暴露它（C3 第 3 条）。所以交给 `desktop.run()` 的是 `ListenerFanout(orchestrator, agents)`：它在该回调里把同一个监听器铺给编排器 + 四个子智能体，其余属性 `__getattr__` 委托。不要试图从 handle 或私有字段里挖监听器。
- 2026-10-17：`set_output_listener_for_children`（S3b/C1.2）在本轮核实**仍不存在**于 `myagent/system_manager_agent.py`（workflow 里是「待派发」）。`desktop_main.py` 用 `getattr` 探测 + 回退到自行下发，S3b 落地后会自动切过去。
- 2026-10-17：`BaseAgent.set_output_listener` **校验类型**，必须是 `ai_agent_factory.agent.baseagent.AgentOutputListener` 的实例，鸭子类型会被拒（`TypeError: 输出监听器必须是 AgentOutputListener 的实例`）。写替身监听器时要继承它。
- 2026-10-17：**别在 Windows 控制台输出用 emoji**。cp936 编不出 `❌`，`print` 抛 `UnicodeEncodeError`，会让「可读报错」自己崩掉。`desktop_main.py` 已改成 `[错误]` / `[启动]` / `[退出]` 这类 ASCII 标签。（三个既有入口仍有 emoji，是它们的既有风险，不在本次范围。）
- 2026-10-17（R1）：`.venv` 内装了 **PyInstaller 6.22.3**（构建期工具，写在 `packaging/requirements-build.txt`，**不进 `requirements.txt`**）。用 `python -m PyInstaller` 调用。
- 2026-10-17（R1）：Windows 实建通过。目录版 zip 约 57.3 MB、单文件 exe 约 57.4 MB；zip 197 项，含 `AI-Code-Agent/AI-Code-Agent.exe` 与 `_internal/PySide6/plugins/platforms/qwindows.dll`。构建中间文件在 `temp/assembly/pyinstaller-work/`（已被 `.gitignore` 的 `temp/` 覆盖）。
- 2026-10-17（R1）：`--windowed` 的 exe 在**无控制台**（PowerShell `Start-Process`）下启动时，缺 `.env` 仍能打印可读提示并返回退出码 2，未出现 `sys.stdout is None` 崩溃。打包态 `.env` 从 `dirname(sys.executable)` 读。
- 2026-10-17（R1）：PyInstaller onefile 会起**父、子两个同名进程**。用 `Start-Process -PassThru` 拿到的 PID 可能先退出；冒烟/清理必须按进程名（`Get-Process -Name 'AI-Code-Agent*'`）判断与结束，否则会留下后台进程。
- 2026-10-17（R1）：macOS `.app` 的可执行文件在 `Contents/MacOS/`，按 `dirname(sys.executable)` 规则 `.env` 要放 `Contents/MacOS/.env`，不是 `.app` 同级。本地无法验证 macOS 构建。
- 2026-10-17（R1）：本机为验证 YAML 装了 **PyYAML 6.0.3**（仅开发期，不在任何 requirements 里）。`dist/` **尚未被 `.gitignore` 忽略**，且 `.gitignore` 不属本角色，需项目管理角色处理。
- 2026-10-17（FIX）：**Windows CI 控制台编码坑**。Windows runner 的默认控制台编码不是 UTF-8（英文系统约 cp1252），打包脚本 `print` 中文会抛 `UnicodeEncodeError`，进程退出码变 1，CI 会把它误报成「版本校验失败」。v1.0.0 的 `39008017545` 就是这样：`build-windows` 失败、`build-macos` 通过、`release` 跳过。本机 cp936 能编码中文所以看不出来。复现命令：`PYTHONIOENCODING=cp1252 .venv/Scripts/python.exe packaging/check_version.py v1.0.0`。已修：打包脚本入口调用 `build_common.ensure_utf8_console()`，workflow 两个 build job 再加 `PYTHONIOENCODING: "utf-8"`。新增打包脚本时记得在 `main()` 第一行调用。

## 容易踩坑的位置

- **`.env.example` 不存在**。`README.md` 让用户复制它再改名成 `.env`，但仓库里没有这个文件。用户照做会找不到。补文件或改文档需要客户确认。
- **`main.py` 不走编排器**。看到「流程不对」先确认跑的是哪个入口——`main.py` 里没有任何状态机，改变更需求的处理方式与另外两个入口完全不同。
- **初始/变更判断有两处**：入口自己一份（`enhanced_main.py` 的关键词判断），编排器 `project_state` 一份。改一处要考虑另一处。
- **不要穿透 `_BaseAgent__context`**。这是平台框架角色的私有字段。要拿回复文本应向那个角色申请公开方法。
- `.env` 被 `.gitignore` 忽略，仓库里没有，所以本地跑之前必须先自己建。
- **本地能打印中文 ≠ CI 能打印中文**。本机 cp936 能编码中文，Windows runner 不能。打包脚本新增中文输出时，先用 `PYTHONIOENCODING=cp1252` 跑一遍；入口必须调用 `ensure_utf8_console()`。

## 待核实的问题

- 三个入口是否都需要保留。`main3.py` 看起来是 `enhanced_main.py` 的前身。删除入口是破坏性操作，需客户明确确认后才动。
- 环境变量缺失时 `OpenAILLM` 的实际报错是否可读（`None` 透传给 OpenAI SDK 会怎样）。
- `.vscode/settings.json` 里 `./agent` 这个不存在的路径是否有意为之。

## 下次从哪继续

1. 先读 `boundary.md` Section 1，确认当前授权范围未变。
2. 要动环境变量名或用户命令词，先在方案里把兼容处理写清楚——这是用户可见接口。
3. 要给入口加业务判断，交回「流程编排」角色；要给入口加生成行为，交回「业务智能体」角色。
4. 启动说明（`README.md`）属「项目管理」角色，改动需求交给它。
5. 项目管理角色的 `docs/project-rules.md` 尚未建立；建立后本节应链接并核对相关条目。
6. 发行打包：先读 `packaging/README.md` 与 `docs/change/2026-10-17_change_release-packaging-ci.md`。Windows 本机可完整验证；macOS 与 GitHub Actions 只能在真实 macOS / 推送 tag 后验证。
