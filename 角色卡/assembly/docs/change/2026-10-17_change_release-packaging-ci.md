# 变更：Windows / macOS 发行打包与 CI 发布

- 日期：2026-10-17
- 角色：装配（assembly）
- 设计：`docs/design/2026-10-17_design_release-packaging-ci.md`（已确认）
- 任务：产出可下载的 Windows / macOS 发行包，并在推送 `v*` tag 时自动创建 GitHub Release。

## 1. 前因

桌面端此前只能从源码运行（`.venv\Scripts\python.exe desktop_main.py`）。普通用户机器上没有
Python、PySide6 与 `.venv`。同时开发机是 Windows，PyInstaller 不能交叉编译，macOS 产物
只能由 CI 的 `macos-latest` 产出。

## 2. 改动路径

| 路径 | 变更 |
| --- | --- |
| `packaging/build_common.py` | 新增。项目根定位、`__version__` 读取（`ast`，不 import 包）、版本覆盖、PyInstaller 调用、zip 压缩、产物大小格式化 |
| `packaging/ai-code-agent.spec` | 新增。两个平台共用的 PyInstaller 配方；环境变量控制 onefile / bundle；显式列出桌面端动态导入与 `openai` 子模块 |
| `packaging/build_windows.py` | 新增。`--onedir --windowed` 目录版 + `--onefile --windowed` 单文件版，分别命名并输出到 `dist/` |
| `packaging/build_macos.py` | 新增。`--onedir --windowed` → `.app`，用 `ditto -c -k --keepParent` 压缩 |
| `packaging/check_version.py` | 新增。CI 中交叉校验 tag 与 `desktop.__version__` |
| `packaging/requirements-build.txt` | 新增。构建期依赖 `pyinstaller==6.22.3`；`requirements.txt` 未改动 |
| `packaging/README.md` | 新增。产物说明、用户放置 `.env` 的位置、Windows SmartScreen 与 macOS Gatekeeper 提示 |
| `.github/workflows/release.yml` | 新增。`v*` tag 触发；`build-windows` / `build-macos` / `release` 三个 job |
| `desktop_main.py` | 修改。新增 `environment_file_path()`；打包态从 `dirname(sys.executable)` 读 `.env`，源码态保持 `load_dotenv()` 原行为；缺失提示里的路径与后续操作按源码态/打包态区分 |
| `test/assembly/check_packaging.py` | 新增。打包配置与打包态 `.env` 查找的自检（17 项） |

未改动：`requirements.txt`、`desktop/`、`myagent/`、`ai_agent_factory/`。

## 3. 设计要点

1. **一份 spec 两个平台**：`AI_CODE_AGENT_ONEFILE` 控制是否 `COLLECT`；`AI_CODE_AGENT_BUNDLE`
   控制 macOS 是否再包 `.app`。两个平台脚本不再各写一套 PyInstaller 参数。
2. **版本来源唯一**：`desktop/__init__.py` 的 `__version__`；`AI_CODE_AGENT_VERSION`
   环境变量优先（CI 传 tag 去掉 `v`）。版本读取用 `ast`，不导入桌面包。
3. **CI 权限最小化**：顶层 `contents: read`，只有 `release` job 覆盖为 `contents: write`。
4. **不使用 secret**：Release 用 `gh release create` + `GH_TOKEN: ${{ github.token }}`。
5. **不做任何签名**：macOS 未签名/未公证，Windows 无代码签名证书。

## 4. 实际验证（本机 Windows 11，`.venv` Python 3.12.0）

### 4.1 安装构建期工具

```
.venv\Scripts\python.exe -m pip install pyinstaller --no-input --disable-pip-version-check
```

结果：成功，安装 PyInstaller **6.22.3**（附带 altgraph 0.17.5、pefile 2024.8.26、
pyinstaller-hooks-contrib 2026.8、pywin32-ctypes 0.2.3、setuptools 84.0.0）。

### 4.2 Windows 构建

```
.venv\Scripts\python.exe packaging\build_windows.py
```

结果：退出码 0。产物：

| 产物 | 字节数 | 大小 |
| --- | --- | --- |
| `dist/AI-Code-Agent-1.0.0-windows-x64.zip` | 60,095,177 | 57.3 MB |
| `dist/AI-Code-Agent-1.0.0-windows-x64.exe` | 60,155,634 | 57.4 MB |
| `dist/AI-Code-Agent/AI-Code-Agent.exe`（目录版解压前） | 10,517,940 | 10.0 MB |

zip 结构检查：197 个条目；顶层文件夹为 `AI-Code-Agent/`；可执行文件在
`AI-Code-Agent/AI-Code-Agent.exe`；Qt 平台插件存在
（`AI-Code-Agent/_internal/PySide6/plugins/platforms/qwindows.dll`）。

### 4.3 启动冒烟

| 场景 | 方法 | 结果 |
| --- | --- | --- |
| 目录版，无 `.env` | 终端启动 | 打印可读缺失提示，退出码 2 |
| 目录版，无 `.env` | `Start-Process`（无控制台） | 退出码 2 |
| 目录版，有 `.env` | `Start-Process`，等待 12 秒 | 仍在运行；强制结束；无残留进程 |
| 单文件版，无 `.env` | `Start-Process` | 退出码 2；无残留进程 |
| 单文件版，有 `.env` | 启动后等待 15 秒 | 有 2 个同名进程存活（PyInstaller onefile 的父/子进程）；按进程名结束；残留 0 |

`.env` 用临时假值（`api_key=smoke-test-not-used` 等），测试后已删除；没有发起任何网络请求。
**没有调用真实模型**。

注意：PyInstaller onefile 会启动父、子两个进程；用 `Start-Process` 拿到的 PID 可能先退出，
冒烟判定必须按进程名检查，不能只看单个 PID。

### 4.4 语法与配置检查

- `python -m py_compile desktop_main.py packaging/*.py test/assembly/check_desktop_main.py`：通过。
- `packaging/ai-code-agent.spec` 用 `compile()` 检查：通过。
- `packaging/build_macos.py`：语法检查通过；**实际 macOS 构建未验证**（Windows 不能交叉编译）。
- YAML：安装 PyYAML 6.0.3 后 `yaml.safe_load` 成功；确认三个 job、顶层 `contents: read`、
  `release` job `contents: write`、`needs` 关系、`v*` tag 触发。
- 版本校验：`check_version.py v1.0.0` → 0；`v1.0.1` → 1（打印可读原因）。
- `test/assembly/check_desktop_main.py`：全部通过（无回归）。
- `test/assembly/check_packaging.py`：17 项全部通过。
- `test/assembly/check_pyside6_install.py`：通过（PySide6 6.12.0）。

## 5. 偏差与限制

1. **macOS `.env` 位置**：按任务要求，打包态固定读 `dirname(sys.executable)`。macOS `.app`
   的可执行文件位于 `AI-Code-Agent.app/Contents/MacOS/`，所以 `.env` 要放在
   `Contents/MacOS/.env`，不是设计文档里概括的「`.app` 同级」。`packaging/README.md`
   已按实际位置写明。
2. **macOS 产物未验证**：本机无 macOS。CI 首次实际运行后才能确认 `.app` 与 zip。
3. **CI 未实际运行**：未推送 tag，`release.yml` 只做了本地 YAML 解析与结构检查。
4. **仅 arm64 macOS**：`macos-latest` 当前为 Apple Silicon；Intel Mac 不可用。
5. **未签名**：Windows SmartScreen 与 macOS Gatekeeper 会提示未知发布者。
6. **`dist/` 未被 `.gitignore` 忽略**：`.gitignore` 属其他角色，本角色未修改；建议项目管理
   角色补一条 `dist/`，避免构建产物误入版本库（`temp/` 已被忽略）。
