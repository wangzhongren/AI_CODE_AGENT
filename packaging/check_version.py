"""校验发布 tag 与 ``desktop.__version__`` 是否一致。

CI 用法：

    python packaging/check_version.py v1.0.0

一致返回 0；不一致返回 1，并打印可读原因；参数不对返回 2。
本地也可以直接运行来核对版本。
"""

from __future__ import annotations

import sys

from build_common import ensure_utf8_console, read_desktop_version


def normalize_tag(tag):
    """去掉 tag 开头的 ``v``，其余原样保留。"""
    if tag.startswith("v"):
        return tag[1:]
    return tag


def main(arguments):
    ensure_utf8_console()
    if len(arguments) != 1:
        print("用法：python packaging/check_version.py <tag，例如 v1.0.0>")
        return 2

    tag = arguments[0].strip()
    if tag == "":
        print("[版本校验] tag 为空，无法校验。")
        return 2

    tag_version = normalize_tag(tag)
    desktop_version = read_desktop_version()
    print("[版本校验] tag=" + tag + "（按 " + tag_version + " 比较），desktop.__version__=" + desktop_version)

    if tag_version != desktop_version:
        print("[版本校验] 失败：tag 版本 " + tag_version
              + " 与 desktop/__init__.py 的 __version__ " + desktop_version + " 不一致。")
        print("[版本校验] 请把 desktop/__init__.py 的 __version__ 改成 " + tag_version
              + "，或改推与代码版本一致的 tag。")
        return 1

    print("[版本校验] 通过。")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
