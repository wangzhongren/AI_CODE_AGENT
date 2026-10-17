"""Windows 发行包构建（装配角色）。

产出两份，都放在 ``dist/``：

1. ``AI-Code-Agent-<version>-windows-x64.zip`` —— `--onedir --windowed` 的便携版，
   解压后是带 ``AI-Code-Agent.exe`` 的文件夹；
2. ``AI-Code-Agent-<version>-windows-x64.exe`` —— `--onefile --windowed` 的单文件。

在项目根执行：

    .venv\\Scripts\\python.exe packaging\\build_windows.py

版本号默认读 ``desktop/__init__.py``；设置环境变量 ``AI_CODE_AGENT_VERSION``
可覆盖（CI 传入 tag 去掉 ``v`` 后的值）。
"""

from __future__ import annotations

import sys

import build_common


def main():
    if sys.platform != "win32":
        print("[打包] build_windows.py 只能在 Windows 上运行；当前平台：" + sys.platform)
        return 2

    version = build_common.resolve_version()
    app_name = build_common.ARTIFACT_BASE_NAME
    archive_name = app_name + "-" + version + "-windows-x64.zip"
    executable_name = app_name + "-" + version + "-windows-x64.exe"

    print("[打包] 项目根：" + str(build_common.PROJECT_ROOT))
    print("[打包] 版本：" + version)
    build_common.ensure_pyinstaller()
    build_common.clean_outputs(version)

    print("[打包] 第一步：目录版（--onedir --windowed）")
    build_common.run_pyinstaller(onefile=False, bundle=False, app_name=app_name, version=version)

    directory_build = build_common.DIST_DIRECTORY / app_name
    if not directory_build.is_dir():
        print("[打包] 失败：没有生成目录版 " + str(directory_build))
        return 1

    archive_path = build_common.DIST_DIRECTORY / archive_name
    print("[打包] 压缩目录版：" + str(archive_path))
    build_common.zip_directory(directory_build, archive_path, app_name)

    print("[打包] 第二步：单文件版（--onefile --windowed）")
    build_common.run_pyinstaller(onefile=True, bundle=False, app_name=app_name, version=version)

    raw_executable = build_common.DIST_DIRECTORY / (app_name + ".exe")
    if not raw_executable.is_file():
        print("[打包] 失败：没有生成单文件 " + str(raw_executable))
        return 1
    executable_path = build_common.DIST_DIRECTORY / executable_name
    if executable_path.exists():
        executable_path.unlink()
    raw_executable.replace(executable_path)

    print("[打包] 完成。产物：")
    print("  " + build_common.describe_file(archive_path))
    print("  " + build_common.describe_file(executable_path))
    print("[打包] 把 .env（api_key / model_name / base_url 三行）放在 exe 同级目录后再启动。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
