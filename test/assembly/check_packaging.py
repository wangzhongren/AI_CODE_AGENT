"""发行打包配置与打包态 ``.env`` 查找的自检（装配角色）。

不构建产物、不联网、不开窗口。检查：

1. 版本号读取与产物命名；
2. `desktop_main.environment_file_path()` 在源码态 / 打包态分别指向哪里；
3. 打包态 `read_environment()` 真的从 exe 同级目录读到三个变量；
4. 两个构建脚本与 `check_version.py` 语法可编译；
5. `.github/workflows/release.yml` 能被 YAML 解析，且 job 与权限结构符合设计。

运行：

    .venv\\Scripts\\python.exe test\\assembly\\check_packaging.py
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PACKAGING_DIRECTORY = PROJECT_ROOT / "packaging"
for path in (PROJECT_ROOT, PACKAGING_DIRECTORY):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

# 控制台代码页可能是 cp936，中文经管道会乱码；统一按 UTF-8 输出便于查看与贴证据。
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception as error:
    print("[warn] cannot reconfigure stdout: %s" % error)

import build_common  # noqa: E402  （必须在 sys.path 就位之后导入）
import desktop_main  # noqa: E402

FAILURES = []


def check(condition, label):
    if condition:
        print("[ok] " + label)
    else:
        print("[FAIL] " + label)
        FAILURES.append(label)


def check_version_and_names():
    version = build_common.read_desktop_version()
    check(version == "1.0.0", "从 desktop/__init__.py 读到 __version__ = 1.0.0（实际 %s）" % version)

    saved = os.environ.get(build_common.VERSION_ENVIRONMENT_VARIABLE)
    os.environ[build_common.VERSION_ENVIRONMENT_VARIABLE] = "v9.9.9"
    try:
        check(build_common.resolve_version() == "9.9.9",
              "AI_CODE_AGENT_VERSION 覆盖版本号并去掉开头的 v")
    finally:
        if saved is None:
            os.environ.pop(build_common.VERSION_ENVIRONMENT_VARIABLE, None)
        else:
            os.environ[build_common.VERSION_ENVIRONMENT_VARIABLE] = saved

    check(build_common.ARTIFACT_BASE_NAME == "AI-Code-Agent", "产物基础名是 ASCII 的 AI-Code-Agent")


def check_environment_paths():
    saved_frozen = getattr(sys, "frozen", None)
    saved_executable = sys.executable
    try:
        if hasattr(sys, "frozen"):
            del sys.frozen
        source_path = desktop_main.environment_file_path()
        check(source_path == os.path.join(os.getcwd(), ".env"),
              "源码态：.env 提示路径是当前工作目录（保持原行为）")

        fake_directory = os.path.join(tempfile.gettempdir(), "ai-code-agent-check")
        sys.frozen = True
        sys.executable = os.path.join(fake_directory, "AI-Code-Agent.exe")
        frozen_path = desktop_main.environment_file_path()
        check(frozen_path == os.path.join(fake_directory, ".env"),
              "打包态：.env 路径是可执行文件同级目录")
    finally:
        sys.executable = saved_executable
        if saved_frozen is None:
            if hasattr(sys, "frozen"):
                del sys.frozen
        else:
            sys.frozen = saved_frozen


def check_frozen_read_environment():
    saved_frozen = getattr(sys, "frozen", None)
    saved_executable = sys.executable
    saved_values = {}
    directory = tempfile.mkdtemp(prefix="ai-code-agent-env-")
    environment_path = Path(directory) / ".env"
    environment_path.write_text(
        "api_key=frozen-key\nmodel_name=frozen-model\nbase_url=http://127.0.0.1:1/v1\n",
        encoding="utf-8",
    )
    try:
        for variable_name in desktop_main.ENVIRONMENT_VARIABLE_NAMES:
            saved_values[variable_name] = os.environ.pop(variable_name, None)
        sys.frozen = True
        sys.executable = str(Path(directory) / "AI-Code-Agent.exe")
        settings, missing_names = desktop_main.read_environment()
        check(missing_names == [], "打包态：exe 同级的 .env 被读到，无缺失变量")
        check(settings.get("api_key") == "frozen-key", "打包态：api_key 值正确")
    finally:
        for variable_name, old_value in saved_values.items():
            if old_value is None:
                os.environ.pop(variable_name, None)
            else:
                os.environ[variable_name] = old_value
        sys.executable = saved_executable
        if saved_frozen is None:
            if hasattr(sys, "frozen"):
                del sys.frozen
        else:
            sys.frozen = saved_frozen
        try:
            environment_path.unlink()
            os.rmdir(directory)
        except OSError as error:
            print("[warn] cleanup failed: %r" % (error,))


def check_scripts_compile():
    script_names = ["build_common.py", "build_windows.py", "build_macos.py", "check_version.py"]
    for script_name in script_names:
        path = PACKAGING_DIRECTORY / script_name
        try:
            compile(path.read_text(encoding="utf-8"), str(path), "exec")
            check(True, "语法可编译：" + script_name)
        except SyntaxError as error:
            check(False, "语法可编译：" + script_name + "（%r）" % (error,))


def check_workflow():
    workflow_path = PROJECT_ROOT / ".github" / "workflows" / "release.yml"
    try:
        import yaml
    except ImportError:
        print("[skip] 未安装 PyYAML，跳过 workflow 解析检查")
        return
    data = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    check(isinstance(data, dict), "release.yml 可被 YAML 解析")
    jobs = data.get("jobs", {})
    check(sorted(jobs.keys()) == ["build-macos", "build-windows", "release"],
          "workflow 含 build-windows / build-macos / release 三个 job")
    check(data.get("permissions", {}).get("contents") == "read",
          "顶层权限是 contents: read")
    check(jobs.get("release", {}).get("permissions", {}).get("contents") == "write",
          "只有 release job 拿到 contents: write")
    needs = jobs.get("release", {}).get("needs", [])
    check(sorted(needs) == ["build-macos", "build-windows"],
          "release job 依赖两个构建 job")
    trigger = data.get(True, data.get("on", {}))
    check(trigger.get("push", {}).get("tags") == ["v*"], "触发条件是推送 v* tag")


def main():
    check_version_and_names()
    check_environment_paths()
    check_frozen_read_environment()
    check_scripts_compile()
    check_workflow()

    if FAILURES:
        print("[FAIL] %d 项未通过：%s" % (len(FAILURES), "; ".join(FAILURES)))
        return 1
    print("[OK] 打包配置自检全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
