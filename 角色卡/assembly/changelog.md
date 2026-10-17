# 变更历史：装配

按时间倒序。改动的前因后果、证据与契约偏差见 `docs/change/` 下的对应记录。

## 2026-10-17 — FIX：Windows CI 控制台编码导致版本校验误判失败

- 现象：v1.0.0 的 Actions 运行 `39008017545` 中 `build-windows` 在 `Verify tag matches desktop.__version__` 失败，`build-macos` 成功，`release` 跳过。真实原因不是版本不一致，而是 `print` 中文在非 UTF-8 控制台抛 `UnicodeEncodeError`、退出码变 1。
- 修复：`packaging/build_common.py` 新增 `ensure_utf8_console()`（`sys.stdout` / `sys.stderr` 的 `reconfigure(encoding="utf-8", errors="replace")`）；`check_version.py`、`build_windows.py`、`build_macos.py` 在 `main()` 开头、任何中文输出之前调用。
- 第二层保障：`.github/workflows/release.yml` 两个 build job 增加 `env: PYTHONIOENCODING: "utf-8"`。
- 回归测试：`test/assembly/check_packaging.py` 新增 4 项（自检从 17 项增至 21 项），用 `PYTHONIOENCODING=cp1252` 子进程固化该场景。
- 本机实测：`PYTHONIOENCODING=cp1252` 下完整跑通 `build_windows.py`（退出码 0，两份产物生成，日志无 `UnicodeEncodeError`）；`build_macos.py` 平台守卫分支中文可读、退出码 2。
- 未改动：脚本输出语言（仍为中文）、产物命名、退出码语义、`desktop/` 与依赖清单。
- 记录：`角色卡/assembly/docs/fix/2026-10-17_fix_windows-console-encoding.md`

## 2026-10-17 — R1：Windows / macOS 发行打包与 CI 发布

- 新增 `packaging/`：共用 PyInstaller spec（`ai-code-agent.spec`）、`build_common.py`、`build_windows.py`、`build_macos.py`、`check_version.py`、`requirements-build.txt`（PyInstaller 6.22.3）、`README.md`。
- 新增 `.github/workflows/release.yml`：推送 `v*` tag 时构建 Windows 便携版 zip + 单文件 exe、macOS `.app` zip，并用 `gh release create` + `github.token` 创建 Release；写权限只给 `release` job。
- 修改 `desktop_main.py`：新增 `environment_file_path()`；打包态从 `dirname(sys.executable)` 读 `.env`，源码态保持原行为；缺失提示按源码态/打包态给出正确路径与后续操作。
- 本机实测：构建退出码 0，产出 `dist/AI-Code-Agent-1.0.0-windows-x64.zip`（60,095,177 字节）与 `dist/AI-Code-Agent-1.0.0-windows-x64.exe`（60,155,634 字节）；目录版与单文件版均通过启动/缺失配置冒烟；无残留进程。
- 新增 `test/assembly/check_packaging.py`（17 项自检）。
- 未验证：macOS 实际构建（本机 Windows）、CI 实际运行（未推送 tag）。
- 记录：`docs/change/2026-10-17_change_release-packaging-ci.md`

## 2026-10-17 — S5c：新增桌面端真实接线入口 `desktop_main.py`

- 新增 `desktop_main.py`（项目根）：读 `.env` 三变量 → 构造 `OpenAILLM` + 四个业务智能体 + `SystemManagerAgent` → `desktop.run(...)`。缺变量时给可读提示并返回退出码 2，不把 `None` 传给 `OpenAILLM`。
- 新增 `ListenerFanout`：桌面端的 `set_output_listener` 一到，把同一个监听器下发给编排器与四个子智能体；清除时一并清掉；其余属性委托给编排器。编排层 `set_output_listener_for_children`（S3b）优先，缺失时用自己持有的 `agents` 字典等价下发并打印说明。
- 修复：提示语里的 emoji 在 gbk 控制台下抛 `UnicodeEncodeError`，改为 ASCII 标签。
- 新增 `test/assembly/check_desktop_main.py` 自检脚本（9 项断言，不联网不开窗）。
- 记录：`common/assembly/docs/change/2026-10-17-desktop-main-wiring.md`

## 2026-10-17 — S5b：`.venv` 内安装开发期工具 pytest

- `.venv\Scripts\python.exe -m pip install pytest` → 装到 pytest 9.1.1（附带 colorama、iniconfig、packaging、pluggy、pygments）。
- `requirements.txt` **未改动**（仍为 `openai` / `python-dotenv` / `PySide6==6.12.0` 三行）：pytest 是开发期工具，不进运行时依赖清单。
- 验证：`.venv\Scripts\python.exe -m pytest --version` → `pytest 9.1.1`。

## 2026-10-17 — S5a：PySide6 依赖入库 + 项目内虚拟环境

- `requirements.txt` 新增 `PySide6==6.12.0`（精确锁定），`openai` / `python-dotenv` 两条原样保留。
- 项目根建 `.venv`（解释器 Python 3.12.0，非系统 3.14），在其中安装全部依赖；实际装到的版本：PySide6 6.12.0、shiboken6 6.12.0、openai 3.33.0、python-dotenv 1.2.4。
- 新增 `test/assembly/check_pyside6_install.py`：只读自检脚本，断言 `import PySide6` 成功且已装版本与 `requirements.txt` 锁定值一致。
- **对契约 C4.1 的偏差**：C4 原文要求「给定主版本下限，不锁精确小版本」，实际按 ShellGate 要求精确锁定 `==`。理由与影响见变更记录。
- 记录：`common/assembly/docs/change/2026-10-17-pyside6-pin-and-venv.md`（`boundary.md` 指定的 `角色卡/assembly/docs/change/` 不在当前门禁白名单内，写入被拒，故暂存私有目录）
