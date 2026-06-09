from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class _DigitLabel(QLabel):
    scrolled = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedSize(24, 20)

    def wheelEvent(self, event) -> None:
        delta = 1 if event.angleDelta().y() > 0 else -1
        self.scrolled.emit(delta)


class DigitEdit(QWidget):
    value_changed = Signal(float)

    def __init__(
        self,
        integer_digits: int = 1,
        decimal_places: int = 3,
        initial_value: float = 0.0,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._integer_digits = integer_digits
        self._decimal_places = decimal_places
        self._scale = 10**decimal_places
        self._total_digit_cols = integer_digits + decimal_places
        self._min_raw = 0
        self._max_raw = 2500
        self._connected = False

        self._value = initial_value

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._digit_labels: list[_DigitLabel] = []
        self._up_buttons: list[QPushButton] = []
        self._down_buttons: list[QPushButton] = []
        self._digit_scales: list[int] = []

        for pos in range(self._total_digit_cols):
            if pos == integer_digits and decimal_places > 0:
                sep = QLabel(".")
                sep.setFixedWidth(8)
                sep.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(sep)

            scale = 10 ** (self._total_digit_cols - 1 - pos)
            self._digit_scales.append(scale)

            col = QVBoxLayout()
            col.setSpacing(0)

            up = QPushButton("▴")
            up.setFixedSize(24, 10)
            up.clicked.connect(self._make_up(pos))
            col.addWidget(up)
            self._up_buttons.append(up)

            label = _DigitLabel()
            label.scrolled.connect(self._make_scroll(pos))
            col.addWidget(label)
            self._digit_labels.append(label)

            down = QPushButton("▾")
            down.setFixedSize(24, 10)
            down.clicked.connect(self._make_down(pos))
            col.addWidget(down)
            self._down_buttons.append(down)

            layout.addLayout(col)

        self.set_value(initial_value)

    def set_connected(self, connected: bool) -> None:
        self._connected = connected
        for btn in self._up_buttons + self._down_buttons:
            btn.setEnabled(connected)
        for lbl in self._digit_labels:
            lbl.setEnabled(connected)

    def value(self) -> float:
        return self._value

    def set_value(self, value: float) -> None:
        self._value = max(0.0, min(value, self._max_raw / self._scale))
        self._refresh()
        self.value_changed.emit(self._value)

    def _raw(self) -> int:
        return round(self._value * self._scale)

    def _refresh(self) -> None:
        raw = self._raw()
        for i, label in enumerate(self._digit_labels):
            digit = (raw // self._digit_scales[i]) % 10
            label.setText(str(digit))

    def _change(self, index: int, delta: int) -> None:
        if not self._connected:
            return
        raw = self._raw()
        step = self._digit_scales[index]
        new_raw = raw + delta * step
        if new_raw < self._min_raw or new_raw > self._max_raw:
            return
        self._value = new_raw / self._scale
        self._refresh()
        self.value_changed.emit(self._value)

    def _make_up(self, index: int):
        def _up() -> None:
            self._change(index, 1)

        return _up

    def _make_down(self, index: int):
        def _down() -> None:
            self._change(index, -1)

        return _down

    def _make_scroll(self, index: int):
        def _on_scroll(delta: int) -> None:
            self._change(index, delta)

        return _on_scroll
