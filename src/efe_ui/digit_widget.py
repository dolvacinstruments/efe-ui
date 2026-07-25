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

    def __init__(self, parent: QWidget | None = None, editable: bool = False, selected: bool = False) -> None:
        super().__init__(parent)

        self._value: int | None = None

        self._is_editable = editable
        self._is_selected = selected
        self._is_hovered_over = False

        self._setup_ui()
        self._connect_signals()

    def set_value(self, value: None | int) -> None:
        if value is not None and not (0 <= value <= 9):
            raise ValueError("Digit value must be between 0 and 9 or None.")
        self._value = value
        self._digit_button.setText(self._get_text())

        if value is None:
            self._style_non_editable()
            self._style_unhovered()
            self._style_unselected()
        else:
            if self._is_editable:
                self._style_editable()
                if self._is_hovered_over:
                    self._style_hovered()
            if self._is_selected:
                self._style_selected()

    def set_editable(self, editable: bool) -> None:
        self._is_editable = editable
        if editable:
            self._style_editable()
            if self._is_hovered_over:
                self._style_hovered()
            if self._is_selected:
                self._style_selected()
        else:
            self._style_non_editable()
            if self._is_hovered_over:
                self._style_unhovered()
            if self._is_selected:
                self._is_selected = False
                self._style_unselected()

    def set_selected(self, selected: bool) -> None:
        if not self._is_editable:
            raise RuntimeError("Cannot select a digit that is not editable.")
        self._is_selected = selected
        if selected:
            self._style_selected()
        else:
            self._style_unselected()

    def is_hovered_over(self) -> bool:
        return self._is_hovered_over

    def enterEvent(self, event: QEnterEvent) -> None:
        super().enterEvent(event)
        self._is_hovered_over = True
        if self._is_editable:
            self._style_hovered()

    def leaveEvent(self, event: QEvent) -> None:
        super().leaveEvent(event)
        self._is_hovered_over = False
        self._style_unhovered()

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

    def _connect_signals(self) -> None:
        self._up_button.clicked.connect(self.incremented)
        self._digit_button.clicked.connect(self.clicked)
        self._down_button.clicked.connect(self.decremented)

    def _style_editable(self) -> None:
        for button in [self._up_button, self._digit_button, self._down_button]:
            button.setEnabled(True)
            button.setStyleSheet("""
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

    def _style_non_editable(self) -> None:
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
        if self._value is None:
            return "-"
        else:
            if not 0 <= self._value <= 9:
                raise ValueError("Digit value must be between 0 and 9 or None.")
            return str(self._value)

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
        _WIDTH = max(font_metrics.horizontalAdvance(c) for c in "0123456789")
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
