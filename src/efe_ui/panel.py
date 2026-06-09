from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
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

_LABEL_WIDTH = 180
_PAD = 12


class Panel(QWidget):
    set_clicked = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        grid = QGridLayout(self)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(_PAD)
        grid.setVerticalSpacing(6)

        # header row
        self._read_dot = QLabel("●")
        self._read_dot.hide()
        measure_header = QHBoxLayout()
        measure_header.setSpacing(4)
        measure_header.addWidget(self._read_dot)
        measure_header.addWidget(QLabel("Measurements"))
        measure_header.addStretch()

        setpoint_header = QHBoxLayout()
        setpoint_header.addWidget(QLabel("Setpoints"))
        setpoint_header.addStretch()

        grid.addLayout(measure_header, 0, 0)
        grid.addLayout(setpoint_header, 0, 1)

        self._read_displays: list[QLineEdit] = []
        self._digit_edits: list[DigitEdit] = []
        self._set_buttons: list[QPushButton] = []

        for i in range(len(_READ_VARIABLES)):
            # measurement cell
            measure_row = QHBoxLayout()
            measure_row.setSpacing(8)
            rlabel = QLabel(f"{_READ_VARIABLES[i]}:")
            rlabel.setFixedWidth(_LABEL_WIDTH)
            measure_row.addWidget(rlabel)
            display = QLineEdit()
            display.setReadOnly(True)
            display.setPlaceholderText("—")
            self._read_displays.append(display)
            measure_row.addWidget(display, stretch=1)
            grid.addLayout(measure_row, i + 1, 0)

            # setpoint cell
            setpoint_row = QHBoxLayout()
            setpoint_row.setSpacing(8)
            slabel = QLabel(f"{_WRITE_VARIABLES[i]}:")
            slabel.setFixedWidth(_LABEL_WIDTH)
            setpoint_row.addWidget(slabel)
            de = DigitEdit(integer_digits=1, decimal_places=3)
            self._digit_edits.append(de)
            setpoint_row.addWidget(de)
            setpoint_row.addSpacing(8)
            btn = QPushButton("Set")
            btn.setFixedWidth(40)
            btn.clicked.connect(self._make_set_slot(i))
            self._set_buttons.append(btn)
            setpoint_row.addWidget(btn)
            setpoint_row.addStretch()
            grid.addLayout(setpoint_row, i + 1, 1)

        grid.setRowStretch(len(_READ_VARIABLES) + 1, 1)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

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
