"""无控制台模式下的 stdout / stderr 兜底（Windows ``pythonw`` / ``--noconsole``）。

背景：契约 C1 选择「事件与 print 并存、不抑制终端输出」，整条管线仍然靠 ``print``
往外吐文字。打包成 ``--noconsole`` 或用 ``pythonw.exe`` 启动时，``sys.stdout`` 可能是
``None``，此时任何一个 ``print`` 都会抛 ``AttributeError``，管线当场炸掉。

本模块在**创建窗口之前**把这些为 ``None`` 的标准流换成可写对象：优先写日志文件，
写不成退到内存里的 ``io.StringIO``（保证 ``print`` 永远不炸）。
"""

import datetime
import io
import os
import sys
import tempfile

LOG_DIRECTORY_NAME = "codeagent-desktop"

_notes = []


def ensure_standard_streams(log_directory=None):
    """把为 ``None`` 的 ``sys.stdout`` / ``sys.stderr`` 换成可写流。

    参数:
        log_directory (str | None): 日志目录。为 ``None`` 时用系统临时目录下的
            ``codeagent-desktop/``。目录建不出来或文件打不开时退回内存缓冲。

    返回:
        list: 被替换上去的对象，顺序为 ``[stderr, stdout]`` 中实际被替换的那些。
            测试可据此还原，正常运行不需要关心。
    """
    replaced = []
    for stream_name in ("stderr", "stdout"):
        current = getattr(sys, stream_name, None)
        if current is not None:
            continue
        stream = _open_log_stream(stream_name, log_directory)
        setattr(sys, stream_name, stream)
        replaced.append(stream)

    if replaced:
        log_message("[desktop] 无控制台模式：stdout/stderr 已重定向（共 " + str(len(replaced)) + " 个）")
    return replaced


def log_message(text):
    """写一行诊断信息到 stderr；stderr 也为 ``None`` 时先记在内存里。"""
    stream = getattr(sys, "stderr", None)
    if stream is None:
        _notes.append(text)
        return
    try:
        stream.write(text + "\n")
        stream.flush()
    except (OSError, ValueError) as error:
        _notes.append(text)
        _notes.append("[desktop] 写 stderr 失败：" + repr(error))


def remembered_messages():
    """返回没写出去的诊断信息副本（stderr 不可用时才有内容）。"""
    return list(_notes)


def _open_log_stream(stream_name, log_directory):
    """打开（或退回）一个可写流。全部失败时返回内存缓冲，保证不抛异常。"""
    directory = _prepare_directory(log_directory)
    if directory is None:
        return io.StringIO()

    file_name = "desktop-" + _today() + ".log"
    path = os.path.join(directory, file_name)
    try:
        return open(path, "a", encoding="utf-8", buffering=1)
    except OSError as error:
        _remember("[desktop] 打不开日志文件 " + path + "：" + repr(error))
        return io.StringIO()


def _prepare_directory(log_directory):
    """返回可用的日志目录；建不出来返回 ``None``。"""
    if log_directory is None:
        directory = os.path.join(tempfile.gettempdir(), LOG_DIRECTORY_NAME)
    else:
        directory = log_directory
    try:
        os.makedirs(directory, exist_ok=True)
    except OSError as error:
        _remember("[desktop] 建不了日志目录 " + directory + "：" + repr(error))
        return None
    return directory


def _today():
    return datetime.date.today().strftime("%Y%m%d")


def _remember(text):
    """记录一条在流还没就绪时无法写出的信息。"""
    _notes.append(text)
