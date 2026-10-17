"""发行构建的共用逻辑（装配角色）。

两个平台脚本（``build_windows.py`` / ``build_macos.py``）只保留各自独有的步骤，
其余都放在这里：定位项目根、读取版本号、调用 PyInstaller、压缩产物。

设计见 ``docs/design/2026-10-17_design_release-packaging-ci.md``。
"""

from __future__ import annotations

import ast
import importlib.util
import os
import subprocess
import sys
import zipfile
from pathlib import Path

ARTIFACT_BASE_NAME = "AI-Code-Agent"
VERSION_ENVIRONMENT_VARIABLE = "AI_CODE_AGENT_VERSION"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DESKTOP_INIT_FILE = PROJECT_ROOT / "desktop" / "__init__.py"
SPEC_FILE = Path(__file__).resolve().with_name("ai-code-agent.spec")
DIST_DIRECTORY = PROJECT_ROOT / "dist"
WORK_DIRECTORY = PROJECT_ROOT / "temp" / "assembly" / "pyinstaller-work"


def ensure_utf8_console():
    """把标准输出 / 错误切到 UTF-8，保证中文在任何控制台编码下都能打印。

    Windows 控制台的默认编码取决于系统区域（例如英文系统为 cp1252），
    打印中文会抛 ``UnicodeEncodeError`` 并让脚本以退出码 1 结束。
    这里显式改成 UTF-8；``errors="replace"`` 保证即使终端字体显示不了，
    也只是出现替代字符，不会让进程崩溃。

    必须在任何中文输出之前调用。用 ``getattr`` 探测 ``reconfigure``：
    流被替换成不支持它的对象（例如测试捕获器）时跳过即可。
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        reconfigure(encoding="utf-8", errors="replace")


def read_desktop_version():
    """从 ``desktop/__init__.py`` 读出字符串常量 ``__version__``。

    用 ``ast`` 解析而不是 import：构建脚本不需要加载桌面包，也不会因为
    导入失败或副作用把版本读取弄成另一条故障路径。
    """
    if not DESKTOP_INIT_FILE.is_file():
        raise RuntimeError("找不到版本文件：" + str(DESKTOP_INIT_FILE))
    source = DESKTOP_INIT_FILE.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(DESKTOP_INIT_FILE))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "__version__":
                value = node.value
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    return value.value
    raise RuntimeError("desktop/__init__.py 里没有字符串常量 __version__")


def resolve_version():
    """返回本次构建使用的版本号。

    环境变量 ``AI_CODE_AGENT_VERSION`` 优先（CI 传入 tag 去掉 ``v`` 后的值），
    否则读 ``desktop.__version__``。开头的 ``v`` 会被去掉，避免产物名出现两次 ``v``。
    """
    environment_value = os.environ.get(VERSION_ENVIRONMENT_VARIABLE, "").strip()
    if environment_value != "":
        if environment_value.startswith("v"):
            environment_value = environment_value[1:]
        return environment_value
    return read_desktop_version()


def ensure_pyinstaller():
    """确认当前解释器里装了 PyInstaller，缺了给出可读提示。"""
    if importlib.util.find_spec("PyInstaller") is None:
        raise SystemExit(
            "构建需要 PyInstaller，但当前 Python 里没有。请先执行：\n"
            "  " + sys.executable + " -m pip install --requirement packaging/requirements-build.txt"
        )


def clean_outputs(version):
    """删掉本脚本负责的旧产物，保证 zip 里不会混进上一次构建的文件。"""
    import shutil

    directory_build = DIST_DIRECTORY / ARTIFACT_BASE_NAME
    if directory_build.is_dir():
        shutil.rmtree(directory_build)
    app_bundle = DIST_DIRECTORY / (ARTIFACT_BASE_NAME + ".app")
    if app_bundle.is_dir():
        shutil.rmtree(app_bundle)
    raw_executable = DIST_DIRECTORY / (ARTIFACT_BASE_NAME + ".exe")
    if raw_executable.is_file():
        raw_executable.unlink()
    archive_patterns = [
        ARTIFACT_BASE_NAME + "-" + version + "-windows-x64.zip",
        ARTIFACT_BASE_NAME + "-" + version + "-windows-x64.exe",
        ARTIFACT_BASE_NAME + "-" + version + "-macos.zip",
    ]
    for file_name in archive_patterns:
        path = DIST_DIRECTORY / file_name
        if path.is_file():
            path.unlink()


def run_pyinstaller(*, onefile, bundle, app_name, version):
    """按统一 spec 调用 PyInstaller。

    ``onefile`` 决定 spec 里是否用 COLLECT；``bundle`` 决定 macOS 是否再包一层
    ``.app``。所有 PyInstaller 参数都收在 ``ai-code-agent.spec`` 与这里，两个平台
    脚本不再各写一套。
    """
    environment = os.environ.copy()
    environment["AI_CODE_AGENT_PROJECT_ROOT"] = str(PROJECT_ROOT)
    environment["AI_CODE_AGENT_APP_NAME"] = app_name
    environment["AI_CODE_AGENT_ONEFILE"] = "1" if onefile else "0"
    environment["AI_CODE_AGENT_BUNDLE"] = "1" if bundle else "0"
    environment["AI_CODE_AGENT_VERSION"] = version

    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--distpath",
        str(DIST_DIRECTORY),
        "--workpath",
        str(WORK_DIRECTORY),
        str(SPEC_FILE),
    ]
    print("[packaging] 运行：" + " ".join(command))
    subprocess.run(command, cwd=str(PROJECT_ROOT), env=environment, check=True)
    print("[packaging] PyInstaller 完成（onefile=" + str(onefile) + ", bundle=" + str(bundle) + "）")


def zip_directory(source_directory, archive_path, archive_root_name):
    """把目录压成 zip，压缩包内保留一个顶层文件夹。"""
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for file_path in sorted(source_directory.rglob("*")):
            if not file_path.is_file():
                continue
            relative_path = file_path.relative_to(source_directory).as_posix()
            archive_name = archive_root_name + "/" + relative_path
            archive.write(file_path, archive_name)


def describe_file(path):
    """返回「路径（大小）」给构建日志用。"""
    size = path.stat().st_size
    return str(path) + " (" + format_size(size) + ")"


def format_size(size):
    """把字节数换成人能读的 MB / GB。"""
    megabytes = size / (1024.0 * 1024.0)
    if megabytes < 1024.0:
        return "%.1f MB" % megabytes
    return "%.2f GB" % (megabytes / 1024.0)
