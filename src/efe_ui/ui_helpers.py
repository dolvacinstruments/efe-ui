from PySide6.QtWidgets import QLabel, QLineEdit, QPushButton, QSizePolicy, QWidget

from efe_ui.constants import TITLE_BAR_FONT_SIZE


def create_title_bar_label(text: str, bold: bool = True) -> QLabel:
    label = QLabel(text)
    font = label.font()
    font.setPointSize(TITLE_BAR_FONT_SIZE)
    font.setBold(bold)
    label.setFont(font)
    return label


def create_title_bar_button(text: str) -> QPushButton:
    button = QPushButton(text)
    font = button.font()
    button.setFlat(True)
    button.setStyleSheet("""
        QPushButton {
            font-weight: bold;
            padding-left: 0px;
            padding-right: 0px;
            margin: 0px;
        }
        QPushButton:hover {
                color: palette(midlight);
        }
    """)
    font.setPointSize(TITLE_BAR_FONT_SIZE)
    font.setBold(True)
    button.setFont(font)
    return button


def create_title_bar_line_edit(placeholder: str) -> QLineEdit:
    line_edit = QLineEdit()
    line_edit.setPlaceholderText(placeholder)
    line_edit.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    width = line_edit.fontMetrics().horizontalAdvance(placeholder) + 20
    line_edit.setFixedWidth(width)
    return line_edit


def set_font(widget: QWidget, font_size: int, bold: bool = False) -> None:
    font = widget.font()
    font.setPointSize(font_size)
    font.setBold(bold)
    widget.setFont(font)


def get_text_width(widget: QWidget, text: str | list[str]) -> int:
    metrics = widget.fontMetrics()
    if isinstance(text, list):
        return max(metrics.horizontalAdvance(t) for t in text)
    return metrics.horizontalAdvance(text)
