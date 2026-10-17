# 设计：Windows / macOS 发行打包与 CI 发布

- 日期：2026-10-17
- 状态：已确认（客户在方案问答中选定四项）
- 负责角色：装配（assembly）
- 客户选择：
  1. 发布远端 = 当前仓库 `wangzhongren/AI_CODE_AGENT`
  2. Windows 产物 = 便携版 zip + 单 exe
  3. macOS 产物 = 未签名 `.app` zip
  4. 触发方式 = 推送 `v*` tag 时自动构建并创建 GitHub Release

## 1. 要解决什么

桌面端目前只有源码运行方式（`.venv\Scripts\python.exe desktop_main.py`）。普通用户机器上没有 Python、没有 PySide6，也没有 `.venv`。需要产出可直接下载运行的 Windows 与 macOS 发行包，并让它们在推送版本号 tag 时自动生成、自动挂到 GitHub Release。

## 2. 为什么必须用 CI 做 macOS

本项目开发机是 Windows。PyInstaller **不能交叉编译**：在 Windows 上产不出 macOS 的 `.app`。因此：

- Windows 包：既可在本机 `.venv` 里产出（用于本地验证），也可由 CI 的 `windows-latest` 产出。
- macOS 包：**只能**由 CI 的 `macos-latest` 产出。

## 3. 归属与边界

| 路径 | 角色 | 说明 |
| --- | --- | --- |
| `.github/workflows/` | 装配 | CI 工作流 |
| `packaging/` | 装配 | PyInstaller spec、构建驱动脚本、构建期依赖清单 |
| `desktop_main.py` | 装配 | 需补「打包后从 exe 同级目录读 `.env`」 |
| `requirements.txt` | 装配 | 运行时依赖，**不加入 PyInstaller**（构建期工具） |
| `desktop/` | 桌面客户端 | 本次不改 |

治理变更：装配角色的 `boundary.yaml` 与 `boundary.md` Section 1 已新增上述两条目录。`desktop/` 与 `desktop-client` 的边界未改动，无重叠。

## 4. 打包配方

### 4.1 共同

- 入口脚本：`desktop_main.py`
- Python：3.12（与 `.venv` 一致）
- PySide6：`6.12.0`（与 `requirements.txt` 一致）
- 构建期工具：PyInstaller（装在 CI 环境，**不写进 `requirements.txt`**）
- 产物命名统一用 ASCII，避免跨平台与下载链接编码问题：
  - `AI-Code-Agent-<version>-windows-x64.zip`
  - `AI-Code-Agent-<version>-windows-x64.exe`
  - `AI-Code-Agent-<version>-macos.zip`
- 版本号来源：`desktop/__init__.py` 的 `__version__`（当前 `1.0.0`），由 tag 去掉前缀 `v` 后交叉校验；不一致则构建失败。

### 4.2 Windows

跑两次 PyInstaller：

1. `--onedir --windowed` → 目录版，整目录压成便携版 zip。
2. `--onefile --windowed` → 单文件 exe。

`--windowed` 会去掉控制台。`desktop/stdio_fallback.py` 已处理 `sys.stdout/stderr` 为 `None` 的情况，会写日志到系统临时目录 `codeagent-desktop/`，因此 `print` 不会炸。

### 4.3 macOS

- `--windowed --onedir` → `dist/AI-Code-Agent.app`
- 用 `ditto -c -k --keepParent` 压成 zip（保留权限位与 bundle 结构，`zip -r` 会丢符号链接语义）。
- 不签名、不公证。使用者首次打开会被 Gatekeeper 拦，需右键 → 打开。release 说明里要写清楚。
- 架构：`macos-latest` 当前为 Apple Silicon（arm64）。Intel (x86_64) 用户跑不了 arm64 包。**本次先只产 arm64**，是否补 universal2 需客户后续决定（universal2 要求 PySide6 提供对应 wheel，且构建时间翻倍）。

### 4.4 隐藏导入与数据文件

PyInstaller 需要显式收集：

- `PySide6` 的 Qt 插件：使用 PyInstaller 自带的 PySide6 hook；若缺失，用 `--collect-all PySide6`。
- 本项目自身包：`ai_agent_factory`、`myagent`、`desktop` 均为顶层包，在项目根执行 PyInstaller 可被发现；必要时在 spec 里加 `pathex=[项目根]` 与 `hiddenimports`。
- `desktop/__main__.py` 的动态导入（`from desktop import run`）需在 spec 中确认不会被裁掉。

## 5. 运行时行为变更（`desktop_main.py`）

**必需改动**：当前 `load_dotenv()` 无参数，按调用时工作目录向上查找 `.env`。打包后从开始菜单/访达双击启动，工作目录不确定，会找不到 `.env`。

改为：

- 打包态（`sys.frozen` 为真）：从 `os.path.dirname(sys.executable)` 读 `.env`。
- 源码态：保持现有行为（项目根 `.env`）。

其余逻辑不变：仍只做「读环境变量 → 构造对象 → 接线」，不含业务逻辑。

另：发行包不内置 `.env`。用户在 exe/`.app` 同级放 `.env`（`api_key` / `model_name` / `base_url` 三行）。release 说明与 `packaging/README.md` 要写明这一点。

## 6. CI 工作流

文件：`.github/workflows/release.yml`

触发：

```yaml
on:
  push:
    tags: ["v*"]
```

结构：

| Job | Runner | 动作 |
| --- | --- | --- |
| `build-windows` | `windows-latest` | 装 Python 3.12、`pip install -r requirements.txt` + PyInstaller、跑 `packaging/build_windows.py`、上传产物 |
| `build-macos` | `macos-latest` | 同上，跑 `packaging/build_macos.py`、上传产物 |
| `release` | `ubuntu-latest` | 需要前两个 job 成功；下载全部 artifact，创建 GitHub Release，附三个文件 |

约束：

- 权限：`permissions: contents: write`（仅 release job 需要）。
- 版本校验：tag `v1.0.0` 与 `desktop.__version__` 不一致 → job 失败并给出可读原因。
- 不在 CI 里跑 `pytest`（本轮范围只做打包）。测试门禁另行安排。
- 不提交任何凭证。`GITHUB_TOKEN` 用内置的。

## 7. 验证

| 项 | 怎么验 |
| --- | --- |
| Windows 本地产出 | 在 `.venv` 里跑 `packaging/build_windows.py`，确认 zip 与 exe 生成、exe 能开窗 |
| macOS 产出 | 只能由 CI 验证；本地无法验证 |
| CI 语法 | 本地无法完整跑；推送 `v*` tag 后看 Actions |
| `.env` 查找 | 在 exe 同级放 `.env` 启动，确认能读到三变量；缺失时给出可读提示（退出码 2） |
| 版本交叉校验 | 造一个不一致的 tag，确认 job 失败 |
| 无控制台模式 | 双击 exe（无控制台），确认不因 `print` 崩溃，日志写到临时目录 |

## 8. 已知限制（如实记录）

1. **macOS 包未签名**：Gatekeeper 会拦截，需右键打开。Windows SmartScreen 也会提示未知发布者。
2. **macOS 仅 arm64**：Intel Mac 无法运行。
3. **体积**：PySide6 完整打包约数百 MB（含 Qt 插件）。`--onefile` 单文件版启动较慢。
4. **本轮不跑测试**：CI 只验证「能打包」，不验证「功能正确」。
5. **打包后未做真实模型端到端**：与现有 S6 状态一致，客户环境缺 `.env`。
6. **本地无法验证 macOS 产物**：只能在 CI 上看结果。

## 9. 可选加固（未纳入本次实施范围，需客户单独确认）

| 编号 | 内容 | 收益 | 额外成本 |
| --- | --- | --- | --- |
| O1 | macOS universal2（arm64 + x86_64） | Intel Mac 可用 | 构建时间约翻倍；需确认 PySide6 wheel 支持 |
| O2 | Windows Inno Setup 安装包 | 开始菜单/卸载 | 多一个打包工具链 |
| O3 | macOS 签名 + 公证 | 免 Gatekeeper 拦截 | 需 Apple Developer 证书与 GitHub Secrets |
| O4 | CI 中跑 pytest | 打包前先验证功能 | 需先修好 `test/orchestration` 与 `test/desktop-client` 的 `support.py` 冲突（见 `docs/workflow.md` 已知缺陷 3） |
| O5 | 缓存 pip / PyInstaller | CI 更快 | 配置复杂度上升 |

默认未勾选，不实施。
