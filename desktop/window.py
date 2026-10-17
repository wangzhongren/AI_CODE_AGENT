"""主窗口：顶栏、输出卡片、输入行。

本模块只负责「把已经拿到的文字画出来」和「把用户动作交出去」，不含任何业务判断。

视觉规格来自 ``docs/design/2026-10-17_design_desktop-ui-polish.md``：
窗口浅灰底、输出区白色卡片、发送按钮用主色，状态用胶囊表示。
样式只挂在窗口上（``self.setStyleSheet``），不改全局 ``QApplication``，
避免影响共用同一个离屏应用实例的测试。
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QTextBlockFormat,
    QTextCharFormat,
    QTextCursor,
)
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from desktop.stdio_fallback import log_message

ERROR_COLOR = "#b00020"

# ---------- 视觉常量（改界面时先看这里） ----------

WINDOW_BACKGROUND = "#F4F6F8"
CARD_BACKGROUND = "#FFFFFF"
BORDER_COLOR = "#E3E8EF"
TEXT_PRIMARY = "#1D2430"
TEXT_SECONDARY = "#6B7684"
ACCENT = "#2F6FEB"
ACCENT_HOVER = "#2559C7"
ACCENT_PRESSED = "#1E47A8"
ACCENT_DISABLED = "#C7D6F5"
STATUS_IDLE_BACKGROUND = "#EEF1F5"
STATUS_IDLE_DOT = "#9AA4B2"
STATUS_BUSY_BACKGROUND = "#E8F0FE"
STATUS_ERROR_BACKGROUND = "#FDECEE"
SELECTION_BACKGROUND = "#D7E4FB"
SCROLLBAR_HANDLE = "#C7D0DC"
SCROLLBAR_HANDLE_HOVER = "#AAB6C6"

FONT_FAMILY = '"Microsoft YaHei UI", "PingFang SC", "Segoe UI", sans-serif'

WINDOW_STYLESHEET = f"""
QMainWindow#mainWindow {{
    background-color: {WINDOW_BACKGROUND};
}}
QWidget#centralWidget {{
    background-color: {WINDOW_BACKGROUND};
}}

/* ---------- 顶栏 ---------- */
QFrame#header {{
    border: none;
    border-bottom: 1px solid {BORDER_COLOR};
    background-color: transparent;
}}
QLabel#titleLabel {{
    color: {TEXT_PRIMARY};
    font-size: 16px;
    font-weight: 600;
}}

/* ---------- 状态胶囊 ---------- */
QFrame#statusCapsule {{
    border: none;
    border-radius: 14px;
    background-color: {STATUS_IDLE_BACKGROUND};
}}
QFrame#statusCapsule[state="busy"] {{
    background-color: {STATUS_BUSY_BACKGROUND};
}}
QFrame#statusCapsule[state="error"] {{
    background-color: {STATUS_ERROR_BACKGROUND};
}}
QLabel#statusLabel {{
    color: {TEXT_SECONDARY};
    font-size: 12px;
    background-color: transparent;
}}
QLabel#statusLabel[state="busy"] {{
    color: {ACCENT};
}}
QLabel#statusLabel[state="error"] {{
    color: {ERROR_COLOR};
    font-weight: 600;
}}
QLabel#statusDot {{
    background-color: {STATUS_IDLE_DOT};
    border: none;
    border-radius: 4px;
}}
QLabel#statusDot[state="busy"] {{
    background-color: {ACCENT};
}}
QLabel#statusDot[state="error"] {{
    background-color: {ERROR_COLOR};
}}

/* ---------- 输出卡片 ---------- */
QTextEdit#outputPane {{
    background-color: {CARD_BACKGROUND};
    border: 1px solid {BORDER_COLOR};
    border-radius: 12px;
    padding: 18px;
    color: {TEXT_PRIMARY};
    font-size: 14px;
    selection-background-color: {SELECTION_BACKGROUND};
    selection-color: {TEXT_PRIMARY};
}}

/* ---------- 输入区 ---------- */
QLineEdit#requirementInput {{
    background-color: {CARD_BACKGROUND};
    border: 1px solid {BORDER_COLOR};
    border-radius: 10px;
    padding: 0px 14px;
    color: {TEXT_PRIMARY};
    font-size: 14px;
    placeholder-text-color: {TEXT_SECONDARY};
}}
QLineEdit#requirementInput:focus {{
    border: 1px solid {ACCENT};
}}
QPushButton#sendButton {{
    background-color: {ACCENT};
    color: #FFFFFF;
    border: none;
    border-radius: 10px;
    padding: 0px 20px;
    min-width: 88px;
    font-size: 14px;
    font-weight: 600;
}}
QPushButton#sendButton:hover {{
    background-color: {ACCENT_HOVER};
}}
QPushButton#sendButton:pressed {{
    background-color: {ACCENT_PRESSED};
}}
QPushButton#sendButton:disabled {{
    background-color: {ACCENT_DISABLED};
    color: #FFFFFF;
}}
QLabel#hintLabel {{
    color: {TEXT_SECONDARY};
    font-size: 12px;
    background-color: transparent;
}}

/* ---------- 滚动条 ---------- */
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 0px;
}}
QScrollBar::handle:vertical {{
    background: {SCROLLBAR_HANDLE};
    min-height: 32px;
    border-radius: 5px;
}}
QScrollBar::handle:vertical:hover {{
    background: {SCROLLBAR_HANDLE_HOVER};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
    border: none;
    background: none;
}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
}}
QScrollBar:horizontal {{
    background: transparent;
    height: 10px;
    margin: 0px;
}}
QScrollBar::handle:horizontal {{
    background: {SCROLLBAR_HANDLE};
    min-width: 32px;
    border-radius: 5px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {SCROLLBAR_HANDLE_HOVER};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
    border: none;
    background: none;
}}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
    background: none;
}}
"""

STATUS_IDLE = "idle"
STATUS_BUSY = "busy"
STATUS_ERROR = "error"


class MainWindow(QMainWindow):
    """桌面端主窗口。

    输出区用 ``QTextEdit``（只读）：``token`` 逐字追加，``turn_completed`` 另起一段，
    ``error`` 用红色加粗显示，用户一眼能看出「哪一段是出错」。
    """

    def __init__(self, title):
        super().__init__()
        self.setObjectName("mainWindow")
        self.setWindowTitle(title)
        self.resize(880, 620)

        central = QWidget(self)
        central.setObjectName("centralWidget")
        central.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(14)

        layout.addWidget(self.__build_header(central))
        layout.addWidget(self.__build_output(central), 1)
        layout.addLayout(self.__build_input_row(central))

        self.__hint = QLabel("运行中可关闭窗口中断当前任务；按回车也可以发送。", central)
        self.__hint.setObjectName("hintLabel")
        layout.addWidget(self.__hint)

        self.setCentralWidget(central)
        self.setStyleSheet(WINDOW_STYLESHEET)
        self.__set_status("就绪", STATUS_IDLE)

        self.__submit_handler = None
        self.__close_handler = None

        self.__send.clicked.connect(self.handle_send)
        self.__input.returnPressed.connect(self.handle_send)

    # ---------- 布局 ----------

    def __build_header(self, parent):
        """顶栏：左边标题，右边状态胶囊（圆点 + 文字）。"""
        header = QFrame(parent)
        header.setObjectName("header")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 14)
        header_layout.setSpacing(12)

        title = QLabel("代码生成助手", header)
        title.setObjectName("titleLabel")
        header_layout.addWidget(title)
        header_layout.addStretch(1)

        self.__status = QLabel("就绪", header)
        self.__status.setObjectName("statusLabel")

        self.__status_dot = QLabel(header)
        self.__status_dot.setObjectName("statusDot")
        self.__status_dot.setFixedSize(8, 8)

        self.__status_capsule = QFrame(header)
        self.__status_capsule.setObjectName("statusCapsule")
        capsule_layout = QHBoxLayout(self.__status_capsule)
        capsule_layout.setContentsMargins(12, 5, 12, 5)
        capsule_layout.setSpacing(6)
        capsule_layout.addWidget(self.__status_dot)
        capsule_layout.addWidget(self.__status)
        header_layout.addWidget(self.__status_capsule)
        return header

    def __build_output(self, parent):
        """输出卡片：只读文本区，占满顶栏与输入行之间的全部空间。"""
        self.__output = QTextEdit(parent)
        self.__output.setObjectName("outputPane")
        self.__output.setReadOnly(True)
        self.__output.document().setDocumentMargin(0)
        return self.__output

    def __build_input_row(self, parent):
        """输入行：输入框占满剩余宽度，发送按钮固定在右侧。"""
        self.__input = QLineEdit(parent)
        self.__input.setObjectName("requirementInput")
        self.__input.setPlaceholderText("写下你的需求，按回车或点「发送」")
        self.__input.setFixedHeight(42)

        self.__send = QPushButton("发送", parent)
        self.__send.setObjectName("sendButton")
        self.__send.setFixedHeight(42)
        self.__send.setMinimumWidth(88)

        input_row = QHBoxLayout()
        input_row.setSpacing(12)
        input_row.addWidget(self.__input, 1)
        input_row.addWidget(self.__send)
        return input_row

    # ---------- 接线 ----------

    def set_submit_handler(self, handler):
        """注册「提交需求」动作。handler 接收需求文本，返回是否已被接受。"""
        self.__submit_handler = handler

    def set_close_handler(self, handler):
        """注册「窗口要关了」动作（由启动层接到关闭句柄上）。"""
        self.__close_handler = handler

    # ---------- 用户动作 ----------

    def handle_send(self):
        """用户点了发送（或按了回车）。"""
        handler = self.__submit_handler
        if handler is None:
            self.display_error("界面没有接到提交动作（装配缺失），无法发送需求。")
            return
        requirement = self.__input.text().strip()
        if not requirement:
            self.__set_status("请先写需求，再点发送", STATUS_IDLE)
            return
        try:
            accepted = handler(requirement)
        except Exception as error:
            log_message("[desktop] 提交需求失败：" + repr(error))
            self.display_error("提交需求失败：" + repr(error))
            self.set_busy(False)
            return
        if accepted:
            self.__input.clear()
            self.set_busy(True)
        else:
            self.__set_status("上一轮还在跑，等它结束（或关闭窗口中断）再发送", STATUS_BUSY)

    # ---------- 渲染（只在界面线程被调用） ----------

    def display_token(self, text):
        """``token`` 事件：逐字追加到输出区末尾。"""
        cursor = self.__end_cursor()
        cursor.insertText(text)
        self.__output.setTextCursor(cursor)

    def display_turn_completed(self, full_text):
        """``turn_completed`` 事件：另起一段。

        正文已经由 ``token`` 逐字画出来了，这里只负责分段，避免重复显示。
        """
        cursor = self.__end_cursor()
        cursor.insertBlock(self.__paragraph_format())
        self.__output.setTextCursor(cursor)

    def display_error(self, message):
        """``error`` 事件：另起一段，用红色加粗显示。"""
        cursor = self.__end_cursor()
        cursor.insertBlock(self.__paragraph_format())
        text_format = QTextCharFormat()
        text_format.setForeground(QColor(ERROR_COLOR))
        text_format.setFontWeight(QFont.Weight.Bold)
        cursor.insertText("[错误] " + message, text_format)
        self.__output.setTextCursor(cursor)
        self.__set_status("出错了，详见输出区", STATUS_ERROR)

    def set_busy(self, busy):
        """切换「运行中 / 就绪」外观。运行中禁用发送按钮，输入框保留。"""
        self.__send.setEnabled(not busy)
        if busy:
            self.__set_status("运行中…（关闭窗口可中断）", STATUS_BUSY)
        else:
            self.__set_status("就绪", STATUS_IDLE)

    def finish_task(self):
        """任务结束（成功、失败或异常退出）后由信号触发。"""
        self.set_busy(False)

    # ---------- Qt 事件 ----------

    def closeEvent(self, event):
        handler = self.__close_handler
        if handler is not None:
            try:
                handler()
            except Exception as error:
                log_message("[desktop] 关闭时清理失败：" + repr(error))
        super().closeEvent(event)

    # ---------- 内部工具 ----------

    def __end_cursor(self):
        cursor = self.__output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        return cursor

    @staticmethod
    def __paragraph_format():
        """段落之间留一点空隙，让多轮输出不挤在一起。"""
        block_format = QTextBlockFormat()
        block_format.setTopMargin(6)
        return block_format

    def __set_status(self, text, state):
        """更新状态文字与胶囊配色。

        配色由动态属性 ``state`` 驱动（见 ``WINDOW_STYLESHEET``），
        改完属性要重新 polish，Qt 才会重新套用样式。
        """
        self.__status.setText(text)
        widgets = (self.__status_capsule, self.__status, self.__status_dot)
        for widget in widgets:
            widget.setProperty("state", state)
            style = widget.style()
            style.unpolish(widget)
            style.polish(widget)
