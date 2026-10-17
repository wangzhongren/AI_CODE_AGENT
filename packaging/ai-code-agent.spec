# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 配方：Windows 与 macOS 共用。

由 ``packaging/build_windows.py`` / ``packaging/build_macos.py`` 通过环境变量驱动：

- ``AI_CODE_AGENT_PROJECT_ROOT``：项目根，供 PyInstaller 找到顶层包；
- ``AI_CODE_AGENT_APP_NAME``：产物名（``AI-Code-Agent``）；
- ``AI_CODE_AGENT_ONEFILE``：``1`` 时产出单文件，``0`` 时产出目录版；
- ``AI_CODE_AGENT_BUNDLE``：``1`` 时在目录版外面再包一层 macOS ``.app``。

``--windowed`` 对应 ``console=False``：不弹控制台。桌面端把它往临时目录写的日志见
``desktop/stdio_fallback.py``。
"""

import os

from PyInstaller.utils.hooks import collect_submodules

PROJECT_ROOT = os.environ["AI_CODE_AGENT_PROJECT_ROOT"]
APP_NAME = os.environ.get("AI_CODE_AGENT_APP_NAME", "AI-Code-Agent")
ONE_FILE = os.environ.get("AI_CODE_AGENT_ONEFILE", "0") == "1"
BUILD_BUNDLE = os.environ.get("AI_CODE_AGENT_BUNDLE", "0") == "1"

# desktop.run 在函数内部才 import desktop.app；静态分析看不到这条边，
# 所以桌面端模块全部显式列出，避免被裁掉。
HIDDEN_IMPORTS = [
    "desktop.app",
    "desktop.bridge",
    "desktop.errors",
    "desktop.output_listener",
    "desktop.stdio_fallback",
    "desktop.unwired_orchestrator",
    "desktop.window",
    "desktop.worker",
    "myagent.backend_developer_agent",
    "myagent.frontend_developer_agent",
    "myagent.product_manager_agent",
    "myagent.project_manager_agent",
    "myagent.system_manager_agent",
    "ai_agent_factory.agent.baseagent",
    "ai_agent_factory.llms.base_llm_openai",
    "ai_agent_factory.utils.file_operation_handler",
]

# openai 内部有按名字动态加载的模块，逐个收集更稳。
HIDDEN_IMPORTS += collect_submodules("openai")

analysis = Analysis(
    [os.path.join(PROJECT_ROOT, "desktop_main.py")],
    pathex=[PROJECT_ROOT],
    binaries=[],
    datas=[],
    hiddenimports=HIDDEN_IMPORTS,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "pytest"],
    noarchive=False,
)

pyz = PYZ(analysis.pure)

EXE_OPTIONS = dict(
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
)

if ONE_FILE:
    exe = EXE(
        pyz,
        analysis.scripts,
        analysis.binaries,
        analysis.datas,
        [],
        exclude_binaries=False,
        **EXE_OPTIONS
    )
else:
    exe = EXE(
        pyz,
        analysis.scripts,
        [],
        exclude_binaries=True,
        **EXE_OPTIONS
    )
    collected = COLLECT(
        exe,
        analysis.binaries,
        analysis.datas,
        strip=False,
        upx=False,
        name=APP_NAME,
    )
    if BUILD_BUNDLE:
        app = BUNDLE(
            collected,
            name=APP_NAME + ".app",
            icon=None,
            bundle_identifier="com.wangzhongren.aicodeagent",
            version=os.environ.get("AI_CODE_AGENT_VERSION", "1.0.0"),
            info_plist={
                "NSHighResolutionCapable": True,
                "LSMinimumSystemVersion": "12.0",
            },
        )
