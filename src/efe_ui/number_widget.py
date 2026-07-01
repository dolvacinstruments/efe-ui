from enum import Enum

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QEnterEvent, QFocusEvent, QFontMetrics, QKeyEvent, QWheelEvent
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

_WIDTH = None
_ARROW_HEIGHT = None
_DIGIT_HEIGHT = None

DIGIT_FONT_SIZE = 20
ARROW_FONT_SIZE = 8


class NumberWidget(QWidget):
    def __init__(
        self,
        digit_count: int = 3,
        point_position: int | None = None,
        min_value: float = 0,
        max_value: float = 456,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.digit_count = digit_count
        self.point_position = point_position
        self.digits: list[DigitWidget] = []
        self.value: float = 0
        self.min_value = min_value
        self.max_value = max_value

        self._selected_digit: int | None = None

        self.setup_ui()

    def setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1)

        for i in range(self.digit_count):
            digit_widget = DigitWidget(self, i)
            self.digits.append(digit_widget)

        for i, digit_widget in enumerate(reversed(self.digits)):
            if self.point_position is not None and i == self.digit_count - self.point_position:
                dot_label = self.create_dot()
                layout.addWidget(dot_label, alignment=Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(digit_widget, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

    def create_dot(self) -> QLabel:
        dot_label = QLabel(".", self)
        font = dot_label.font()
        font.setPointSize(DIGIT_FONT_SIZE)
        dot_label.setFont(font)
        dot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return dot_label

    def calculate_multiplier(self, digit_index: int) -> float:
        if self.point_position is not None:
            return 10 ** (digit_index - self.point_position)
        else:
            return 10**digit_index

    def set_value(self, value: float) -> None:
        self.value = value
        for i, digit_widget in enumerate(self.digits):
            digit_value = int(abs(value) / self.calculate_multiplier(i)) % 10
            digit_widget.set_value(digit_value)

    def customEvent(self, event: QEvent) -> None:
        if isinstance(event, DigitEvent):
            self.handle_digit_event(event.digit_index, event.update_type)
        else:
            super().customEvent(event)

    def handle_digit_event(self, digit_index: int, event_type: DigitEventType) -> None:
        mult = self.calculate_multiplier(digit_index)
        if event_type == DigitEventType.INCREMENT:
            new_value = self.value + mult
            self.set_value(min(new_value, self.max_value))
        elif event_type == DigitEventType.DECREMENT:
            new_value = self.value - mult
            self.set_value(max(new_value, self.min_value))
        elif event_type == DigitEventType.VALUE:
            self.setFocus()
            self.select_digit(digit_index)

    def focusInEvent(self, event: QFocusEvent) -> None:
        super().focusInEvent(event)
        print(f"Focus in: {event}")
        self.select_digit(0)

    def focusOutEvent(self, event: QFocusEvent) -> None:
        super().focusOutEvent(event)
        print(f"Focus out: {event}")
        self.clear_selection()

    def clear_selection(self) -> None:
        for digit in self.digits:
            digit.set_selected(False)
        self._selected_digit = None

    def select_digit(self, digit_index: int) -> None:
        self.clear_selection()
        self._selected_digit = digit_index
        self.digits[digit_index].set_selected(True)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if self._selected_digit is not None:
            if event.key() == Qt.Key.Key_Left:
                if self._selected_digit < len(self.digits) - 1:
                    self.select_digit(self._selected_digit + 1)
            elif event.key() == Qt.Key.Key_Right:
                if self._selected_digit > 0:
                    self.select_digit(self._selected_digit - 1)
            elif event.key() == Qt.Key.Key_Up:
                self.handle_digit_event(self._selected_digit, DigitEventType.INCREMENT)
            elif event.key() == Qt.Key.Key_Down:
                self.handle_digit_event(self._selected_digit, DigitEventType.DECREMENT)
            elif event.text().isdigit():
                digit_value = int(event.text())
                mult = self.calculate_multiplier(self._selected_digit)
                current_digit_value = int(abs(self.value) / mult) % 10
                new_value = self.value - (current_digit_value * mult) + (digit_value * mult)
                self.set_value(min(max(new_value, self.min_value), self.max_value))
            elif event.key() == Qt.Key.Key_Escape:
                self.clear_selection()
                self.clearFocus()
        else:
            super().keyPressEvent(event)


class DigitWidget(QWidget):
    def __init__(self, parent: QWidget | None = None, index: int = 0, value: int = 0) -> None:
        super().__init__(parent)

        self._index = index
        self._hovered_over = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

        self.up_button = self.create_button("︿", True)
        self.digit_button = self.create_button("0", False)
        self.down_button = self.create_button("﹀", True)

        self.up_button.clicked.connect(lambda: self.send_digit_event(DigitEventType.INCREMENT))
        self.digit_button.clicked.connect(lambda: self.send_digit_event(DigitEventType.VALUE))
        self.down_button.clicked.connect(lambda: self.send_digit_event(DigitEventType.DECREMENT))

        layout.addWidget(self.up_button, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.digit_button, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.down_button, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setCursor(Qt.CursorShape.SizeVerCursor)

    def create_button(self, text: str, is_arrow: bool = False) -> QPushButton:
        button = QPushButton(text, self)
        button.setFlat(True)
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
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button.setFixedWidth(_get_width())
        if is_arrow:
            font = button.font()
            font.setBold(True)
            font.setPointSize(ARROW_FONT_SIZE)
            button.setFont(font)
            button.setFixedHeight(_get_arrow_height())
            button.setVisible(False)

            retain_policy = button.sizePolicy()
            retain_policy.setRetainSizeWhenHidden(True)
            button.setSizePolicy(retain_policy)
        else:
            font = button.font()
            font.setPointSize(DIGIT_FONT_SIZE)
            button.setFont(font)
            button.setFixedHeight(_get_digit_height())
            button.installEventFilter(self)
        return button

    def set_value(self, value: int) -> None:
        self.digit_button.setText(str(value))

    def send_digit_event(self, event_type: DigitEventType) -> None:
        event = DigitEvent(self._index, event_type)
        if (parent := self.parent()) is not None:
            QApplication.postEvent(parent, event)

    def enterEvent(self, event: QEnterEvent) -> None:
        super().enterEvent(event)
        self.up_button.setVisible(True)
        self.down_button.setVisible(True)
        self._hovered_over = True

    def leaveEvent(self, event: QEvent) -> None:
        super().leaveEvent(event)
        self.up_button.setVisible(False)
        self.down_button.setVisible(False)
        self._hovered_over = False

    def wheelEvent(self, event: QWheelEvent) -> None:
        delta = event.angleDelta().y()
        if delta > 0:
            self.send_digit_event(DigitEventType.INCREMENT)
        elif delta < 0:
            self.send_digit_event(DigitEventType.DECREMENT)

    def is_hovered_over(self) -> bool:
        return self._hovered_over

    def set_selected(self, selected: bool) -> None:
        self.digit_button.setProperty("selected", selected)
        self.digit_button.style().unpolish(self.digit_button)
        self.digit_button.style().polish(self.digit_button)
        self.digit_button.update()


class DigitEventType(Enum):
    INCREMENT = 1
    DECREMENT = 2
    VALUE = 3


class DigitEvent(QEvent):
    EVENT_TYPE = QEvent.Type(QEvent.registerEventType())

    def __init__(self, digit_index: int, update_type: DigitEventType) -> None:
        super().__init__(self.EVENT_TYPE)
        self.digit_index = digit_index
        self.update_type = update_type


def _get_width() -> int:
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
