import math
from dataclasses import dataclass
from enum import Enum, auto
from functools import partial
from typing import Self, Literal

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFocusEvent, QKeyEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLayout,
    QWidget,
)

from efe_ui.digit_widget import DigitWidget, get_digit_width

from .constants import DIGIT_FONT_SIZE


class ValueCondition(Enum):
    NORMAL = auto()
    OVERLOAD = auto()
    INVALID = auto()


@dataclass(order=True, frozen=True)
class Value:
    number: float
    condition: ValueCondition = ValueCondition.NORMAL

    def __post_init__(self) -> None:
        if math.isnan(self.number != self.number):
            object.__setattr__(self, "condition", ValueCondition.INVALID)
        elif self.number >= 9.9e37 or self.number <= -9.9e37:
            object.__setattr__(self, "condition", ValueCondition.OVERLOAD)

    @classmethod
    def invalid(cls) -> Self:
        return cls(float("nan"), ValueCondition.INVALID)

    def is_ok(self) -> bool:
        return self.condition == ValueCondition.NORMAL

    def is_overload(self) -> bool:
        return self.condition == ValueCondition.OVERLOAD

    def is_invalid(self) -> bool:
        return self.condition == ValueCondition.INVALID

    def get(self) -> float:
        return self.number

    def __float__(self) -> float:
        return float(self.number)


NumberWidgetBackgroundColor = Literal["red", "green", "transparent"]


class NumberWidget(QWidget):
    number_changed = Signal(object)

    def __init__(
        self,
        value: Value,
        digit_count: int,
        point_position: int | None,
        min_value: float,
        max_value: float,
        editable: bool = True,
        invert_controls: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._editable = editable
        self._invert_controls = invert_controls
        self._selected_digit: int | None = None

        self._digit_count = digit_count
        self._point_position = point_position
        self._min_value = self._clamp_range(min_value)
        self._max_value = self._clamp_range(max_value)

        self._digits: list[DigitWidget] = []

        self._setup_ui()
        self._value = Value(0)
        self.set_value(value)

        self.background_color: NumberWidgetBackgroundColor = "transparent"

    def set_value(self, value: Value | float | int) -> None:
        old_value = self._value

        if isinstance(value, float | int):
            self._value = Value(value, self._value.condition)
        elif isinstance(value, Value):
            self._value = value

        if self._editable:
            self._value = self.clamp_value(self._value)

        self._update_value_display()
        if self._value != old_value:
            self.number_changed.emit(self._value)

    def set_min_max(self, min_value: float, max_value: float) -> None:
        self._min_value = self._clamp_range(min_value)
        self._max_value = self._clamp_range(max_value)
        self.set_value(self._value)

    def set_point_position(self, point_position: int | None) -> None:
        if self._selected_digit is not None:
            self.select_digit(None)
        self._point_position = point_position
        self._setup_number()
        self.set_min_max(self._min_value, self._max_value)
        self.set_value(self._value)

    def set_digit_count(self, digit_count: int) -> None:
        if self._selected_digit is not None:
            self.select_digit(None)
        self._digit_count = digit_count
        self._setup_number()
        self.set_min_max(self._min_value, self._max_value)
        self.set_value(self._value)

    def get_value(self) -> Value:
        return self._value

    def set_editable(self, editable: bool) -> None:
        self._editable = editable
        for digit in self._digits:
            digit.set_editable(editable)

    def _setup_ui(self) -> None:
        self.hlayout = QHBoxLayout(self)
        self.setLayout(self.hlayout)
        self.hlayout.setContentsMargins(3, 0, 3, 0)
        self.hlayout.setSpacing(1)
        self.hlayout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

        self._sign_label = self._create_sign()
        self.hlayout.addWidget(self._sign_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self._dot_label: QLabel | None = None
        self._setup_number()

        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAutoFillBackground(True)

        self.setStyleSheet("""
            NumberWidget[bg_state="red"] { 
                background-color: rgba(255, 0, 0, 0.157); 
                border-radius: 5px; 
            }
            NumberWidget[bg_state="green"] { 
                background-color: rgba(0, 255, 0, 0.078); 
                border-radius: 5px; 
            }
            NumberWidget[bg_state="transparent"] { 
                background-color: transparent; 
                border-radius: 5px; 
            }
        """)

    def set_background_color(self, color_name: NumberWidgetBackgroundColor) -> None:
        if color_name == self.background_color:
            return

        self.background_color = color_name
        self.setProperty("bg_state", color_name)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

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
            digit_widget = DigitWidget(self)
            digit_widget.set_editable(self._editable)
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
        if (
            self._value.is_overload()
            and len(self._digits) > 1
            and (self._value.get() <= float("-inf") or self._value.get() >= float("inf"))
        ):
            self._digits[-1].set_value("O")
            self._digits[-2].set_value("L")
            for digit_widget in self._digits[:-2]:
                digit_widget.setVisible(False)
            for digit_widget in self._digits:
                digit_widget.set_error(True)
            if self._dot_label is not None:
                self._dot_label.setVisible(False)

        elif self._value.is_overload():
            self._update_digits()
            for digit_widget in self._digits:
                digit_widget.set_error(True)

        elif self._value.is_invalid():
            for digit_widget in self._digits:
                digit_widget.set_error(False)
                digit_widget.set_value("-")
                digit_widget.setVisible(True)
            if self._dot_label is not None:
                self._dot_label.setVisible(False)

        elif self._value.is_ok():
            self._update_digits()
            if self._dot_label is not None:
                self._dot_label.setVisible(True)
            for digit_widget in self._digits:
                digit_widget.set_error(False)
                digit_widget.setVisible(True)

        self._sign_label.setVisible(self.calculate_sign_visibility())

    def _update_digits(self) -> None:
        for i, digit_widget in enumerate(reversed(self._digits)):
            if self._value.is_ok() or self._value.is_overload():
                rounded = round(self._value.get(), self._digit_count)
                digit_value = int(round(abs(rounded) / self._calculate_multiplier(i), self._digit_count)) % 10
                digit_widget.set_value(str(digit_value))

    def calculate_sign_visibility(self) -> bool:
        if self._invert_controls:
            if self._value.is_invalid():
                return True
            else:
                return self._value.get() <= 0
        else:
            if self._value.is_invalid():
                return False
            else:
                return self._value.get() < 0

    def _create_dot(self) -> QLabel:
        dot_label = QLabel(".", self)
        font = dot_label.font()
        font.setPointSize(DIGIT_FONT_SIZE)
        dot_label.setFont(font)
        dot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dot_label.setFixedWidth(get_digit_width())
        retain_policy = dot_label.sizePolicy()
        retain_policy.setRetainSizeWhenHidden(True)
        dot_label.setSizePolicy(retain_policy)
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

    def clamp_value(self, value: Value) -> Value:
        return Value(max(min(value.get(), self._max_value), self._min_value), value.condition)

    def handle_increment(self, digit_index: int) -> None:
        mult = self._calculate_multiplier(digit_index)
        new_value = self._value.get() + mult if not self._invert_controls else self._value.get() - mult
        self.set_value(new_value)

    def handle_decrement(self, digit_index: int) -> None:
        mult = self._calculate_multiplier(digit_index)
        new_value = self._value.get() - mult if not self._invert_controls else self._value.get() + mult
        self.set_value(new_value)

    def handle_clicked(self, digit_index: int) -> None:
        self.select_digit(digit_index)

    def focusInEvent(self, event: QFocusEvent) -> None:
        super().focusInEvent(event)
        digit = self._selected_digit if self._selected_digit is not None else 0
        self._update_digit_selection(digit)

    def focusOutEvent(self, event: QFocusEvent) -> None:
        super().focusOutEvent(event)
        self._update_digit_selection(None)

    def select_digit(self, digit: int | None) -> None:
        self._update_digit_selection(digit)
        if digit is not None:
            self.setFocus()

    def _update_digit_selection(self, digit: int | None) -> None:
        for d in self._digits:
            d.set_selected(False)
        self._selected_digit = digit
        if digit is not None and 0 <= digit < len(self._digits):
            self._digits[-digit - 1].set_selected(True)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if self._selected_digit is not None and self._value.is_ok() and self._editable:
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
                current_val = self._value.get()
                mag = abs(current_val)
                current_digit_value = int(round(mag, 10) // mult) % 10
                new_mag = mag - (current_digit_value * mult) + (digit_value * mult)
                if current_val < 0:
                    new_value = -new_mag
                elif current_val > 0:
                    new_value = new_mag
                else:
                    new_value = -new_mag if self._invert_controls else new_mag

                if self._selected_digit > 0:
                    self.select_digit(self._selected_digit - 1)
                else:
                    self.focusNextChild()

                self.set_value(new_value)

            elif event.key() == Qt.Key.Key_Escape:
                self.select_digit(None)
                self.clearFocus()
        else:
            super().keyPressEvent(event)
