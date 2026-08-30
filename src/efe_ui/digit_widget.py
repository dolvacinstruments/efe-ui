from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtGui import QEnterEvent, QFontMetrics, QWheelEvent
from PySide6.QtWidgets import QApplication, QLayout, QPushButton, QVBoxLayout, QWidget

from efe_ui.constants import ARROW_FONT_SIZE, DIGIT_FONT_SIZE

_WIDTH = None
_ARROW_HEIGHT = None
_DIGIT_HEIGHT = None


class DigitWidget(QWidget):
    clicked = Signal()
    incremented = Signal()
    decremented = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._value: str = "-"

        self._is_editable = False
        self._is_selected = False
        self._is_error = False
        self._is_hovered_over = False

        self._setup_ui()
        self._connect_signals()

    def set_value(self, value: str) -> None:
        self._value = value
        self._digit_button.setText(self._get_text())

    def set_editable(self, editable: bool) -> None:
        self._is_editable = editable
        self._update_style()

    def set_selected(self, selected: bool) -> None:
        self._is_selected = selected
        self._update_style()

    def set_error(self, error: bool) -> None:
        self._is_error = error
        self._update_style()

    def is_hovered_over(self) -> bool:
        return self._is_hovered_over

    def enterEvent(self, event: QEnterEvent) -> None:
        super().enterEvent(event)
        self._is_hovered_over = True
        self._update_style()

    def leaveEvent(self, event: QEvent) -> None:
        super().leaveEvent(event)
        self._is_hovered_over = False
        self._update_style()

    def wheelEvent(self, event: QWheelEvent) -> None:
        if self._is_editable:
            delta = event.angleDelta().y()
            if delta > 0:
                self.incremented.emit()
            elif delta < 0:
                self.decremented.emit()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        self.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

        self._up_button = QPushButton("︿")
        layout.addWidget(self._up_button, alignment=Qt.AlignmentFlag.AlignCenter)

        self._digit_button = QPushButton(self._get_text())
        layout.addWidget(self._digit_button, alignment=Qt.AlignmentFlag.AlignCenter)

        self._down_button = QPushButton("﹀")
        layout.addWidget(self._down_button, alignment=Qt.AlignmentFlag.AlignCenter)

        self._initial_style()

        policy = self.sizePolicy()
        policy.setRetainSizeWhenHidden(True)
        self.setSizePolicy(policy)

    def _connect_signals(self) -> None:
        self._up_button.clicked.connect(self.incremented)
        self._digit_button.clicked.connect(self.clicked)
        self._down_button.clicked.connect(self.decremented)

    def _update_style(self) -> None:
        if self._is_error and self._is_editable:
            self._style_editable_error()
        elif self._is_error and not self._is_editable:
            self._style_non_editable_error()
        elif not self._is_error and self._is_editable:
            self._style_editable_ok()
        elif not self._is_error and not self._is_editable:
            self._style_non_editable_ok()

        if self._is_selected and self._is_editable and not self._is_error:
            self._style_selected()
        else:
            self._style_unselected()

        if self._is_hovered_over and self._is_editable and not self._is_error:
            self._style_hovered()
        else:
            self._style_unhovered()

    def _style_editable_ok(self) -> None:
        for button in [self._up_button, self._digit_button, self._down_button]:
            button.setEnabled(True)
            button.setStyleSheet("""
                QPushButton {
                    color: palette(window-text);
                    background-color: transparent;
                    border: none;
                    padding: 0px;
                }
                QPushButton:hover {
                    color: palette(mid);
                }
                QPushButton:pressed {
                    color: palette(window-text);
                    background-color: transparent;
                    border: none;
                    padding: 0px;
                }
                QPushButton[selected="true"] {
                    background-color: palette(highlight);
                    border: 1px solid palette(highlight);
                }
            """)

    def _style_non_editable_ok(self) -> None:
        for button in [self._up_button, self._digit_button, self._down_button]:
            button.setEnabled(False)
            button.setStyleSheet("""
                QPushButton {
                    color: palette(window-text);
                    background-color: transparent;
                    border: none;
                    padding: 0px;
                }
            """)

    def _style_editable_error(self) -> None:
        for button in [self._up_button, self._digit_button, self._down_button]:
            button.setEnabled(True)
            button.setStyleSheet("""
                QPushButton {
                    color: red;
                    background-color: transparent;
                    border: none;
                    padding: 0px;
                }
                QPushButton:hover {
                    color: red;
                }
                QPushButton:pressed {
                    color: palette(window-text);
                    background-color: transparent;
                    border: none;
                    padding: 0px;
                }
                QPushButton[selected="true"] {
                    background-color: palette(highlight);
                    border: 1px solid palette(highlight);
                }
            """)

    def _style_non_editable_error(self) -> None:
        for button in [self._up_button, self._digit_button, self._down_button]:
            button.setEnabled(False)
            button.setStyleSheet("""
                QPushButton {
                    color: red;
                    background-color: transparent;
                    border: none;
                    padding: 0px;
                }
            """)

    def _style_selected(self) -> None:
        self._digit_button.setProperty("selected", True)
        self._digit_button.style().unpolish(self._digit_button)
        self._digit_button.style().polish(self._digit_button)

    def _style_unselected(self) -> None:
        self._digit_button.setProperty("selected", False)
        self._digit_button.style().unpolish(self._digit_button)
        self._digit_button.style().polish(self._digit_button)

    def _style_hovered(self) -> None:
        for button in [self._up_button, self._down_button]:
            button.setVisible(True)

    def _style_unhovered(self) -> None:
        for button in [self._up_button, self._down_button]:
            button.setVisible(False)

    def _get_text(self) -> str:
        return self._value

    def _initial_style(self) -> None:
        for button in [self._up_button, self._digit_button, self._down_button]:
            button.setFlat(True)
            button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            button.setFixedWidth(get_digit_width())

        self._digit_button.setFixedHeight(_get_digit_height())
        font = self._digit_button.font()
        font.setPointSize(DIGIT_FONT_SIZE)
        self._digit_button.setFont(font)

        for button in [self._up_button, self._down_button]:
            font = button.font()
            font.setBold(True)
            font.setPointSize(ARROW_FONT_SIZE)
            button.setFont(font)
            button.setFixedHeight(_get_arrow_height())
            button.setVisible(False)

            retain_policy = button.sizePolicy()
            retain_policy.setRetainSizeWhenHidden(True)
            button.setSizePolicy(retain_policy)


def get_digit_width() -> int:
    global _WIDTH
    if _WIDTH is None:
        default_font = QApplication.font()
        default_font.setPointSize(DIGIT_FONT_SIZE)
        font_metrics = QFontMetrics(default_font)
        _WIDTH = max(font_metrics.horizontalAdvance(c) for c in "0123456789-")
    return _WIDTH


def _get_arrow_height() -> int:
    global _ARROW_HEIGHT
    if _ARROW_HEIGHT is None:
        default_font = QApplication.font()
        font_metrics = QFontMetrics(default_font)
        _ARROW_HEIGHT = font_metrics.capHeight() + font_metrics.leading()
    return _ARROW_HEIGHT


def _get_digit_height() -> int:
    global _DIGIT_HEIGHT
    if _DIGIT_HEIGHT is None:
        default_font = QApplication.font()
        default_font.setPointSize(DIGIT_FONT_SIZE)
        font_metrics = QFontMetrics(default_font)
        _DIGIT_HEIGHT = font_metrics.ascent()

    return _DIGIT_HEIGHT
