from functools import partial

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFocusEvent, QKeyEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLayout,
    QWidget,
)

from efe_ui.digit_widget import DigitWidget, get_digit_width

from .constants import DIGIT_FONT_SIZE


class NumberWidget(QWidget):
    number_changed = Signal(object)

    def __init__(
        self,
        value: float | None,
        digit_count: int,
        point_position: int | None,
        min_value: float,
        max_value: float,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._value: float | None = value
        self._editable = True
        self._selected_digit: int | None = None

        self._digit_count = digit_count
        self._point_position = point_position
        self._min_value = self._clamp_range(min_value)
        self._max_value = self._clamp_range(max_value)

        self._digits: list[DigitWidget] = []

        self._setup_ui()

    def set_value(self, value: float | None) -> None:
        if value is not None:
            value = max(min(value, self._max_value), self._min_value)
        if value == self._value:
            return

        self._value = value

        self._update_value_display()
        self.number_changed.emit(self._value)

    def set_min_max(self, min_value: float, max_value: float) -> None:
        self._min_value = self._clamp_range(min_value)
        self._max_value = self._clamp_range(max_value)
        if self._value is not None:
            self.set_value(self._value)

    def set_point_position(self, point_position: int | None) -> None:
        if self._selected_digit is not None:
            self.select_digit(None)
        self._point_position = point_position
        self._setup_number()
        self._update_value_display()

    def set_digit_count(self, digit_count: int) -> None:
        if self._selected_digit is not None:
            self.select_digit(None)
        self._digit_count = digit_count
        self._setup_number()
        self._update_value_display()

    def get_value(self) -> float | None:
        return self._value

    def set_editable(self, editable: bool) -> None:
        self._editable = editable
        for digit in self._digits:
            digit.set_editable(editable)

    def _setup_ui(self) -> None:
        self.hlayout = QHBoxLayout(self)
        self.setLayout(self.hlayout)
        self.hlayout.setContentsMargins(0, 0, 0, 0)
        self.hlayout.setSpacing(1)
        self.hlayout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

        self._sign_label = self._create_sign()
        self.hlayout.addWidget(self._sign_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self._dot_label: QLabel | None = None
        self._setup_number()

    def _setup_number(self) -> None:
        # Clear previous widgets
        if self._dot_label is not None:
            self.hlayout.removeWidget(self._dot_label)
            self._dot_label.deleteLater()
            self._dot_label = None

        for digit in self._digits:
            self.hlayout.removeWidget(digit)
            digit.deleteLater()
        self._digits.clear()

        # Create new digits and add
        for i in range(self._digit_count):
            digit_widget = DigitWidget(self, editable=self._editable)
            self._digits.append(digit_widget)
            self.hlayout.addWidget(digit_widget, alignment=Qt.AlignmentFlag.AlignCenter)
            digit_widget.clicked.connect(partial(self.handle_clicked, self._digit_count - i - 1))
            digit_widget.incremented.connect(partial(self.handle_increment, self._digit_count - i - 1))
            digit_widget.decremented.connect(partial(self.handle_decrement, self._digit_count - i - 1))

        # Create dot and instert
        if self._point_position is not None and 0 < self._point_position < self._digit_count:
            self._dot_label = self._create_dot()
            dot_index = self._digit_count - self._point_position
            self.hlayout.insertWidget(dot_index + 1, self._dot_label, alignment=Qt.AlignmentFlag.AlignCenter)

    def _update_value_display(self) -> None:
        for i, digit_widget in enumerate(reversed(self._digits)):
            if self._value is None:
                digit_widget.set_value(None)
            else:
                digit_value = int(abs(self._value) / self._calculate_multiplier(i)) % 10
                digit_widget.set_value(digit_value)

        self._sign_label.setVisible(self._value is not None and self._value < 0)

    def _create_dot(self) -> QLabel:
        dot_label = QLabel(".", self)
        font = dot_label.font()
        font.setPointSize(DIGIT_FONT_SIZE)
        dot_label.setFont(font)
        dot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dot_label.setFixedWidth(get_digit_width())
        return dot_label

    def _create_sign(self) -> QLabel:
        sign_label = QLabel("-", self)
        font = sign_label.font()
        font.setPointSize(DIGIT_FONT_SIZE)
        sign_label.setFont(font)
        sign_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        retain_policy = sign_label.sizePolicy()
        retain_policy.setRetainSizeWhenHidden(True)
        sign_label.setSizePolicy(retain_policy)
        return sign_label

    def _calculate_multiplier(self, digit_index: int) -> float:
        if self._point_position is not None:
            return 10 ** (digit_index - self._point_position)
        else:
            return 10**digit_index

    def _clamp_range(self, value: float) -> float:
        if self._point_position is not None:
            m = 10 ** (self._digit_count - self._point_position) - 10 ** (-self._point_position)
        else:
            m = 10**self._digit_count - 1
        return max(min(value, m), -m)

    def handle_increment(self, digit_index: int) -> None:
        mult = self._calculate_multiplier(digit_index)
        value = self._value + mult if self._value is not None else mult
        self.set_value(value)

    def handle_decrement(self, digit_index: int) -> None:
        mult = self._calculate_multiplier(digit_index)
        value = self._value - mult if self._value is not None else -mult
        self.set_value(value)

    def handle_clicked(self, digit_index: int) -> None:
        self.select_digit(digit_index)

    def focusInEvent(self, event: QFocusEvent) -> None:
        super().focusInEvent(event)
        self.select_digit(self._selected_digit if self._selected_digit is not None else 0)

    def focusOutEvent(self, event: QFocusEvent) -> None:
        super().focusOutEvent(event)
        self.select_digit(None)

    def select_digit(self, digit: int | None) -> None:
        for d in self._digits:
            d.set_selected(False)
        self._selected_digit = digit
        if digit is not None:
            self._digits[-digit - 1].set_selected(True)
            self.setFocus()
        else:
            self.clearFocus()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if self._selected_digit is not None and self._value is not None and self._editable:
            if event.key() == Qt.Key.Key_Left:
                if self._selected_digit < len(self._digits) - 1:
                    self.select_digit(self._selected_digit + 1)
                else:
                    self.focusPreviousChild()

            elif event.key() == Qt.Key.Key_Right:
                if self._selected_digit > 0:
                    self.select_digit(self._selected_digit - 1)
                else:
                    self.focusNextChild()

            elif event.key() == Qt.Key.Key_Up:
                self.handle_increment(self._selected_digit)

            elif event.key() == Qt.Key.Key_Down:
                self.handle_decrement(self._selected_digit)

            elif event.text().isdigit():
                digit_value = int(event.text())
                mult = self._calculate_multiplier(self._selected_digit)
                current_digit_value = int(abs(self._value) / mult) % 10
                value = self._value - (current_digit_value * mult) + (digit_value * mult)
                self.set_value(value)

            elif event.key() == Qt.Key.Key_Escape:
                self.select_digit(None)
                self.clearFocus()
        else:
            super().keyPressEvent(event)
