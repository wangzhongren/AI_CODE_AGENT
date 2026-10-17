# API 与装配说明：装配（assembly）

- 日期：2026-10-17
- 本次范围：发行打包与 CI 发布（R1）；Windows CI 控制台编码修复（FIX）
- 设计：`docs/design/2026-10-17_design_release-packaging-ci.md`
- 变更记录：`docs/change/2026-10-17_change_release-packaging-ci.md`
- 修复记录：`docs/fix/2026-10-17_fix_windows-console-encoding.md`

本文件记录本角色对外可调用的入口、依赖方向、契约符合性与验证证据。

## 1. 桌面端入口 `desktop_main.py`

### 1.1 公开函数

| 函数 | 返回 | 说明 |
| --- | --- | --- |
| `environment_file_path()` | `str` | `.env` 应所在的位置。打包态（`sys.frozen` 为真）为 `os.path.dirname(sys.executable)` 下的 `.env`；源码态为当前工作目录下的 `.env`（仅用于提示，实际读取仍用 `load_dotenv()` 的向上查找） |
| `read_environment()` | `(dict, list)` | 读取 `api_key` / `model_name` / `base_url`；空字符串按缺失处理。打包态用 `load_dotenv(environment_file_path())`，源码态保持 `load_dotenv()` |
| `explain_missing_environment(missing_names)` | `None` | 打印缺失项、`.env` 路径与填写示例。打包态提示「程序所在目录」与「重新打开本程序」，源码态提示项目根与 `.venv\Scripts\python.exe desktop_main.py` |
| `build_llm(settings)` | `OpenAILLM` | 由配置构造 Provider 入口 |
| `build_agents(llm)` | `dict` | `pm` / `pj` / `be` / `fe` 四个业务智能体 |
| `build_orchestrator(llm, agents)` | `SystemManagerAgent` | 编排器 |
| `main()` | `int` | 退出码：0 正常，1 运行错误，2 配置缺失 |

### 1.2 环境变量契约（未改）

`api_key`、`model_name`、`base_url` 三个变量名与必填性保持不变。发行包不内置 `.env`。

### 1.3 层级依赖

入口只 import：`desktop`（公开启动操作）、`SystemManagerAgent`、四个业务智能体、
`OpenAILLM`。未新增对下层私有字段的访问。

## 2. 构建脚本 `packaging/`

### 2.1 `build_common.py`

| 名称 | 说明 |
| --- | --- |
| `ARTIFACT_BASE_NAME` | `"AI-Code-Agent"` |
| `VERSION_ENVIRONMENT_VARIABLE` | `"AI_CODE_AGENT_VERSION"` |
| `PROJECT_ROOT` / `DIST_DIRECTORY` / `WORK_DIRECTORY` | 项目根、`dist/`、`temp/assembly/pyinstaller-work/` |
| `ensure_utf8_console()` | 把 `sys.stdout` / `sys.stderr` 切到 UTF-8（`errors="replace"`），保证中文在非 UTF-8 控制台可打印；三个脚本入口第一行调用 |
| `read_desktop_version()` | 用 `ast` 从 `desktop/__init__.py` 读 `__version__` |
| `resolve_version()` | 环境变量优先（去掉开头 `v`），否则读 `desktop.__version__` |
| `ensure_pyinstaller()` | 缺 PyInstaller 时给可读提示并退出 |
| `clean_outputs(version)` | 清理本次版本对应的旧产物与目录版输出 |
| `run_pyinstaller(onefile, bundle, app_name, version)` | 设置 `AI_CODE_AGENT_*` 环境变量后调用 `python -m PyInstaller` |
| `zip_directory(source, archive, root_name)` | 压缩目录，zip 内保留顶层文件夹 |
| `describe_file(path)` / `format_size(size)` | 构建日志用的大小描述 |

### 2.2 命令行

| 脚本 | 平台 | 产出 |
| --- | --- | --- |
| `python packaging/build_windows.py` | Windows | `dist/AI-Code-Agent-<version>-windows-x64.zip`、`dist/AI-Code-Agent-<version>-windows-x64.exe` |
| `python packaging/build_macos.py` | macOS | `dist/AI-Code-Agent.app`、`dist/AI-Code-Agent-<version>-macos.zip` |
| `python packaging/check_version.py <tag>` | 任意 | 一致返回 0，不一致返回 1，参数错误返回 2 |

两个构建脚本从自身位置定位项目根，不写死绝对路径；非目标平台返回 2 并说明原因。

### 2.3 PyInstaller spec 环境变量

| 变量 | 取值 | 作用 |
| --- | --- | --- |
| `AI_CODE_AGENT_PROJECT_ROOT` | 绝对路径 | `pathex`，供 PyInstaller 找到顶层包 |
| `AI_CODE_AGENT_APP_NAME` | `AI-Code-Agent` | 可执行文件名 / `.app` 名 |
| `AI_CODE_AGENT_ONEFILE` | `1` / `0` | `1` 产出单文件，`0` 产出目录版 |
| `AI_CODE_AGENT_BUNDLE` | `1` / `0` | `1` 时在目录版外再包 macOS `.app` |
| `AI_CODE_AGENT_VERSION` | 版本号 | macOS bundle 版本 |

显式隐藏导入：桌面端 8 个模块、`myagent` 5 个智能体模块、`ai_agent_factory` 3 个模块，
以及 `collect_submodules("openai")`。`desktop.run` 在函数内部导入 `desktop.app`，必须显式列出。

### 2.4 构建期依赖

`packaging/requirements-build.txt`：`pyinstaller==6.22.3`。运行时 `requirements.txt` 未改动
（仍为 `openai` / `python-dotenv` / `PySide6==6.12.0`）。

## 3. CI：`.github/workflows/release.yml`

| 项 | 值 |
| --- | --- |
| 触发 | `push` tag `v*` |
| 顶层权限 | `contents: read` |
| `build-windows` | `windows-latest`，`env: PYTHONIOENCODING=utf-8`，Python 3.12，装运行时与构建期依赖，版本校验，构建，上传 artifact |
| `build-macos` | `macos-latest`，`env: PYTHONIOENCODING=utf-8`，同上 |
| `release` | `ubuntu-latest`，`needs` 前两个 job，`permissions: contents: write`，下载全部 artifact，检查数量为 3，`gh release create --verify-tag --generate-notes` |
| 凭证 | `GH_TOKEN: ${{ github.token }}`，不引用任何 `secrets.*` |
| 版本校验 | 两个构建 job 都执行 `python packaging/check_version.py "${{ github.ref_name }}"` |

## 4. 契约符合性

| 设计条目 | 状态 |
| --- | --- |
| 版本来自 `desktop.__version__`，tag 交叉校验 | 符合 |
| Windows 便携 zip + 单文件 exe | 符合（本机实测） |
| macOS `.app` + `ditto` zip | 脚本符合；**实际构建未验证** |
| `--windowed`，日志兜底 | 符合；打包态缺失配置也能返回 2，无崩溃 |
| 打包态 `.env` 从 exe 同级读取 | 符合 |
| CI 写权限只给 release job | 符合（YAML 结构检查） |
| 不引用 secret、不签名 | 符合 |
| CI 不跑 pytest | 符合 |

## 5. 偏差与限制

1. macOS `.app` 的 `sys.executable` 在 `Contents/MacOS/`，因此 `.env` 实际位置是
   `AI-Code-Agent.app/Contents/MacOS/.env`，不是 `.app` 同级。`packaging/README.md` 已按实际写法说明。
2. macOS 构建与 CI 均未在本机实际运行；只做了语法/YAML 检查。
3. macOS 仅 arm64、未签名。
4. `dist/` 未被 `.gitignore` 忽略；`.gitignore` 属其他角色，需项目管理角色处理。

## 6. 测试证据

| 检查 | 命令 | 结果 |
| --- | --- | --- |
| 版本校验一致 | `python packaging/check_version.py v1.0.0` | 退出码 0 |
| 版本校验不一致 | `python packaging/check_version.py v1.0.1` | 退出码 1，打印可读原因 |
| 非 UTF-8 控制台（一致） | `PYTHONIOENCODING=cp1252 python packaging/check_version.py v1.0.0` | 退出码 0，中文可读（FIX 前退出码 1） |
| 非 UTF-8 控制台（不一致） | `PYTHONIOENCODING=cp1252 python packaging/check_version.py v1.0.1` | 退出码 1，打印可读的不一致说明 |
| Windows 构建 | `.venv\Scripts\python.exe packaging\build_windows.py` | 退出码 0，两份产物生成 |
| Windows 构建（cp1252） | `PYTHONIOENCODING=cp1252 ... packaging\build_windows.py` | 退出码 0，中文可读，日志无 `UnicodeEncodeError` |
| macOS 脚本（cp1252） | `PYTHONIOENCODING=cp1252 ... packaging\build_macos.py` | 退出码 2（平台守卫），中文可读 |
| 目录版冒烟（有/无 `.env`） | 终端与 `Start-Process` | 有 `.env` 存活 12 秒；无 `.env` 退出码 2；无残留 |
| 单文件版冒烟（有/无 `.env`） | `Start-Process` + 按进程名清理 | 有 `.env` 15 秒后父/子两进程存活；无 `.env` 退出码 2；残留 0 |
| Python 语法 | `python -m py_compile ...` | 通过 |
| spec 语法 | `compile()` | 通过 |
| workflow YAML | PyYAML 6.0.3 `safe_load` | 通过，结构与权限符合设计 |
| 打包自检 | `python test/assembly/check_packaging.py` | 21 项全部通过（新增 4 项编码回归） |
| 桌面入口自检 | `python test/assembly/check_desktop_main.py` | 全部通过（无回归） |
| PySide6 自检 | `python test/assembly/check_pyside6_install.py` | 通过 |
