from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from efe_ui.digit_edit import DigitEdit

_READ_VARIABLES = ["VOLTAGE_CATHODE", "VOLTAGE_EMITTER", "CURRENT_L", "CURRENT_H"]
_WRITE_VARIABLES = [
    "VOLTAGE_CATHODE",
    "VOLTAGE_EMITTER",
    "CURRENT_EMITTER",
    "CURRENT_CATHODE",
]


class Panel(QWidget):
    set_clicked = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        layout.addWidget(self._build_measurements())
        layout.addWidget(self._build_setpoints())

    def _build_measurements(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        header = QHBoxLayout()
        self._read_dot = QLabel("●")
        header.addWidget(self._read_dot)
        self._read_dot.hide()
        header.addWidget(QLabel("Measurements"))
        header.addStretch()
        layout.addLayout(header)

        self._read_displays: list[QLineEdit] = []

        for name in _READ_VARIABLES:
            row = QHBoxLayout()
            row.setSpacing(4)
            row.addWidget(QLabel(f"{name}:"))
            display = QLineEdit()
            display.setReadOnly(True)
            display.setPlaceholderText("—")
            self._read_displays.append(display)
            row.addWidget(display, stretch=1)
            layout.addLayout(row)

        layout.addStretch()
        return w

    def _build_setpoints(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        header = QHBoxLayout()
        header.addWidget(QLabel("Setpoints"))
        header.addStretch()
        layout.addLayout(header)

        self._digit_edits: list[DigitEdit] = []
        self._set_buttons: list[QPushButton] = []

        for i, name in enumerate(_WRITE_VARIABLES):
            row = QHBoxLayout()
            row.setSpacing(4)
            row.addWidget(QLabel(f"{name}:"))
            de = DigitEdit(integer_digits=1, decimal_places=3)
            self._digit_edits.append(de)
            row.addWidget(de)
            btn = QPushButton("Set")
            btn.clicked.connect(self._make_set_slot(i))
            self._set_buttons.append(btn)
            row.addWidget(btn)
            row.addStretch()
            layout.addLayout(row)

        layout.addStretch()
        return w

    def _make_set_slot(self, index: int):
        @Slot()
        def _set() -> None:
            self.set_clicked.emit(index)

        return _set

    def update_readout(self, index: int, value: str, ok: bool) -> None:
        self._read_displays[index].setText(value)
        if not ok:
            self._read_dot.hide()
        elif all(d.text() not in ("Error", "—") for d in self._read_displays):
            self._read_dot.show()

    def set_all_read_ok(self, ok: bool) -> None:
        self._read_dot.setVisible(ok)

    def set_connected(self, connected: bool) -> None:
        for de in self._digit_edits:
            de.set_connected(connected)
        for btn in self._set_buttons:
            btn.setEnabled(connected)
        if not connected:
            self._read_dot.hide()
            for d in self._read_displays:
                d.setText("—")

    def digit_edit(self, index: int) -> DigitEdit:
        return self._digit_edits[index]
