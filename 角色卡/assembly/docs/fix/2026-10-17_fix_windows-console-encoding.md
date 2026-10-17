# 修复记录 FIX-2026-10-17-01：Windows CI 控制台编码导致版本校验误判失败

- 日期：2026-10-17
- 范围：`packaging/build_common.py`、`packaging/check_version.py`、`packaging/build_windows.py`、
  `packaging/build_macos.py`、`.github/workflows/release.yml`、`test/assembly/check_packaging.py`
  （均在 `boundary.md` Section 1 内）
- 触发来源：v1.0.0 的 GitHub Actions 运行 `39008017545`：`build-macos` 成功、`build-windows`
  在 `Verify tag matches desktop.__version__` 步骤失败、`release` 被跳过；客户确认优先修
- 结论：已修复。打包脚本在任何控制台编码下都能打印中文，不再因编码抛异常。

## 1. 问题

`build-windows` 失败不是因为版本不一致，而是因为脚本打印中文时崩溃：

```text
UnicodeEncodeError: 'charmap' codec can't encode characters in position 1-4: character maps to <undefined>
```

Python 在非 UTF-8 控制台下按本地代码页编码 `stdout`。Windows runner 的默认控制台编码不是
UTF-8（英文系统通常是 cp1252），`[版本校验]` 中的中文无法编码，`print` 抛
`UnicodeEncodeError`，解释器以退出码 1 结束。CI 只看到「版本校验步骤失败」，于是把故障
指向了版本号，掩盖了真实原因。

macOS runner 默认 UTF-8，同一脚本通过；本机代码页是 cp936，能编码中文（只是显示乱码，
不抛异常），所以本地一直没暴露。

## 2. 复现

```bash
PYTHONIOENCODING=cp1252 .venv/Scripts/python.exe packaging/check_version.py v1.0.0
```

修复前：`UnicodeEncodeError`，退出码 1。
（`PYTHONIOENCODING` 让 Python 用 cp1252 编码标准流，等效于英文 Windows runner。）

## 3. 方案

两层保障，代码层为主、CI 环境变量为辅：

1. **代码层（主）**：`packaging/build_common.py` 新增 `ensure_utf8_console()`，对
   `sys.stdout` / `sys.stderr` 调用 `reconfigure(encoding="utf-8", errors="replace")`。
   - 用 `getattr` 探测 `reconfigure`：流被换成不支持它的对象（例如测试捕获器）时跳过，
     不会因此新增一条故障路径。
   - `errors="replace"` 保证即使终端字体显示不了中文，也只出现替代字符，不会崩。
   - `check_version.py`、`build_windows.py`、`build_macos.py` 在 `main()` 第一行调用，
     早于任何中文输出（包括「用法」「平台不支持」等早退分支）。
2. **CI 层（辅）**：`.github/workflows/release.yml` 的 `build-windows` 与 `build-macos`
   job 增加 `env: PYTHONIOENCODING: "utf-8"`。代码层若被绕过（例如将来新增的打包脚本
   忘记调用），环境变量仍能让 Python 以 UTF-8 启动标准流。

**没有**把脚本改成纯英文输出：中文可读性是有意保留的，问题在编码不在语言。

## 4. 改动清单

| 文件 | 变更 |
| --- | --- |
| `packaging/build_common.py` | 新增 `ensure_utf8_console()` |
| `packaging/check_version.py` | import 并在 `main()` 开头调用 `ensure_utf8_console()` |
| `packaging/build_windows.py` | `main()` 开头调用 `build_common.ensure_utf8_console()` |
| `packaging/build_macos.py` | 同上 |
| `.github/workflows/release.yml` | 两个 build job 增加 `env: PYTHONIOENCODING: "utf-8"` |
| `test/assembly/check_packaging.py` | 新增 4 项回归检查：函数存在；`PYTHONIOENCODING=cp1252` 子进程退出码 0；输出按 UTF-8 可读；stderr 无编码异常 |

未改动：`desktop/`、`myagent/`、`ai_agent_factory/`、`requirements.txt`、`requirements-build.txt`、
PyInstaller spec、产物命名、退出码语义。

## 5. 验证

| 检查 | 命令 | 结果 |
| --- | --- | --- |
| 复现场景（一致） | `PYTHONIOENCODING=cp1252 .venv/Scripts/python.exe packaging/check_version.py v1.0.0` | 退出码 0，中文可读 |
| 复现场景（不一致） | `PYTHONIOENCODING=cp1252 .venv/Scripts/python.exe packaging/check_version.py v1.0.1` | 退出码 1，打印可读的不一致说明 |
| 正常编码（一致） | `.venv/Scripts/python.exe packaging/check_version.py v1.0.0` | 退出码 0 |
| 打包自检 | `.venv/Scripts/python.exe test/assembly/check_packaging.py` | 21 项全部通过 |
| 语法 | `python -m py_compile` 四个打包脚本 | 通过 |
| macOS 脚本中文输出 | `PYTHONIOENCODING=cp1252 ... build_macos.py` | 退出码 2（平台守卫），中文可读，无 traceback |
| Windows 构建中文输出 | `PYTHONIOENCODING=cp1252 .venv/Scripts/python.exe packaging/build_windows.py` | 见第 7 节（实际执行结果） |

## 6. 为什么不是在 CI 里把代码页改成 UTF-8

`chcp 65001` 只在当前 shell 生效，对 Python 解释器如何编码标准流不一定生效，而且还要处理
重定向；脚本自身保证编码，在任何 runner、任何本地终端都成立，不依赖工作流写法。CI 的
`PYTHONIOENCODING` 只是第二层，不作为唯一依赖。

## 7. Windows 构建实际执行结果

用复现用的同一环境完整跑了一次 Windows 构建（不是只测输出路径）：

```bash
PYTHONIOENCODING=cp1252 .venv/Scripts/python.exe packaging/build_windows.py
```

结果：退出码 0，全程中文可读，日志中 `UnicodeEncodeError` 出现 0 次。产物正常生成：

| 产物 | 字节数 |
| --- | --- |
| `dist/AI-Code-Agent-1.0.0-windows-x64.zip` | 60,099,012 |
| `dist/AI-Code-Agent-1.0.0-windows-x64.exe` | 60,162,641 |

同时 `PYTHONIOENCODING=cp1252 ... build_macos.py` 在 Windows 上走平台守卫分支，
退出码 2、中文可读、无 traceback，证明早退分支也受保护。

修复后的 `test/assembly/check_packaging.py` 为 21 项全部通过（原 17 项 + 4 项编码回归）；
`check_desktop_main.py` 与 `check_pyside6_install.py` 通过（无回归）。

## 8. 未验证与后续

- **CI 仍未重新运行**：按任务边界，本次不提交、不推送、不动 tag。需要主会话决定如何重新
  触发 v1.0.0 的发布流程（重跑失败的 job 或重新推 tag）。
- macOS runner 上的实际输出未直接观测；`build_macos` 的代码路径与 Windows 共用同一
  `ensure_utf8_console()`，且本机用 cp1252 验证了其早退分支。
