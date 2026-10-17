# 发行包说明

本目录是 Windows / macOS 发行包的构建配方。日常源码运行方式见项目根的
`README.md`；这里只讲「怎么做出给用户下载的包」和「拿到包的用户怎么用」。

## 产物

| 平台 | 文件 | 说明 |
| --- | --- | --- |
| Windows | `AI-Code-Agent-<version>-windows-x64.zip` | 便携版：解压出一个文件夹，里面有 `AI-Code-Agent.exe` 与依赖文件 |
| Windows | `AI-Code-Agent-<version>-windows-x64.exe` | 单文件版：只有一个 exe，启动比便携版慢 |
| macOS | `AI-Code-Agent-<version>-macos.zip` | 解压得到 `AI-Code-Agent.app`（未签名、arm64） |

`<version>` 来自 `desktop/__init__.py` 的 `__version__`。CI 发布时会先核对
tag（例如 `v1.0.0`）与它一致，不一致就停止构建。本地构建可以用环境变量
`AI_CODE_AGENT_VERSION` 覆盖版本号。

## 本地构建（Windows）

在项目根执行：

```
.venv\Scripts\python.exe -m pip install --requirement packaging\requirements-build.txt
.venv\Scripts\python.exe packaging\build_windows.py
```

产物在 `dist/`。构建过程会临时使用 `temp/assembly/pyinstaller-work/`。

## macOS 构建

macOS 包**只能**在 macOS 上构建（PyInstaller 不能交叉编译）：

```
python -m pip install --requirement packaging/requirements-build.txt
python packaging/build_macos.py
```

仓库的 `.github/workflows/release.yml` 会在推送 `v*` tag 时自动在
`windows-latest` 与 `macos-latest` 上构建，并把三份文件挂到 GitHub Release。

## 用户怎么运行

发行包**不内置** `.env`。用户需要自己准备一份 `.env`，写三行：

```
api_key=你的密钥
model_name=模型名（例如 gpt-4o-mini）
base_url=接口地址（例如 https://api.openai.com/v1）
```

`.env` 放在哪里：

1. **Windows 便携版 zip**：解压后，把 `.env` 放在 `AI-Code-Agent.exe` 同一层。
2. **Windows 单文件 exe**：把 `.env` 放在 exe 同一层。
3. **macOS**：右键 `AI-Code-Agent.app` → 显示包内容 → `Contents/MacOS/`，
   把 `.env` 放在可执行文件同级（程序从这个位置读取配置）。

### Windows

- 双击 exe 即可。首次运行可能出现 SmartScreen「Windows 已保护你的电脑」，
  因为安装包没有代码签名；点「更多信息」→「仍要运行」。
- 如果 `.env` 缺失或三个变量没填全，程序不会打开窗口，会在日志里给出
  可读提示并以退出码 2 结束。

### macOS

- 包**未签名、未公证**。第一次打开会被 Gatekeeper 拦截：在访达里
  右键（或按住 Control 点按）`AI-Code-Agent.app` →「打开」→ 再点「打开」。
  之后就可以正常双击。
- 当前只构建 **arm64**（Apple Silicon）。Intel Mac 无法运行。
- 无控制台模式下，诊断信息写到系统临时目录的 `codeagent-desktop/` 下
  （文件名形如 `desktop-YYYYMMDD.log`）。

## 已知限制

- 未做代码签名。Windows SmartScreen 与 macOS Gatekeeper 都会提示未知发布者。
- macOS 仅 arm64；是否补 universal2 未定。
- PySide6 完整打包体积较大（数百 MB），单文件版启动较慢。
- 本轮 CI 只验证「能打包」，不跑测试。
