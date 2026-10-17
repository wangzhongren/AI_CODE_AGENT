"""macOS 发行包构建（装配角色）。

产出，都放在 ``dist/``：

1. ``AI-Code-Agent.app`` —— `--onedir --windowed` 的应用包（未签名）；
2. ``AI-Code-Agent-<version>-macos.zip`` —— 用 ``ditto -c -k --keepParent`` 压缩，
   保留 bundle 结构与权限位。

在项目根执行：

    python packaging/build_macos.py

只能在 macOS 上运行：PyInstaller 不能交叉编译，Windows 本机产不出 ``.app``。
版本号默认读 ``desktop/__init__.py``，``AI_CODE_AGENT_VERSION`` 可覆盖。
"""

from __future__ import annotations

import subprocess
import sys

import build_common


def main():
    build_common.ensure_utf8_console()
    if sys.platform != "darwin":
        print("[打包] build_macos.py 只能在 macOS 上运行；当前平台：" + sys.platform)
        print("[打包] PyInstaller 不支持交叉编译：macOS 产物必须由 macOS 机器或 CI 产出。")
        return 2

    version = build_common.resolve_version()
    app_name = build_common.ARTIFACT_BASE_NAME
    archive_name = app_name + "-" + version + "-macos.zip"

    print("[打包] 项目根：" + str(build_common.PROJECT_ROOT))
    print("[打包] 版本：" + version)
    build_common.ensure_pyinstaller()
    build_common.clean_outputs(version)

    print("[打包] 构建 .app（--onedir --windowed）")
    build_common.run_pyinstaller(onefile=False, bundle=True, app_name=app_name, version=version)

    app_path = build_common.DIST_DIRECTORY / (app_name + ".app")
    if not app_path.is_dir():
        print("[打包] 失败：没有生成 " + str(app_path))
        return 1

    archive_path = build_common.DIST_DIRECTORY / archive_name
    print("[打包] 压缩 .app：" + str(archive_path))
    command = [
        "ditto",
        "-c",
        "-k",
        "--keepParent",
        str(app_path),
        str(archive_path),
    ]
    print("[打包] 运行：" + " ".join(command))
    subprocess.run(command, check=True)

    print("[打包] 完成。产物：")
    print("  " + build_common.describe_file(app_path))
    print("  " + build_common.describe_file(archive_path))
    print("[打包] .app 未签名也未公证：使用者首次打开需要右键 -> 打开。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
