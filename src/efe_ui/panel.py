from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QWidget,
)

from efe_ui.digit_edit import DigitEdit, Readout

_READ_VARIABLES = ["VOLTAGE_CATHODE", "VOLTAGE_EMITTER", "CURRENT_L", "CURRENT_H"]
_WRITE_VARIABLES = [
    "VOLTAGE_CATHODE",
    "VOLTAGE_EMITTER",
    "CURRENT_EMITTER",
    "CURRENT_CATHODE",
]

_ALL_LABELS = [f"{n}:" for n in _READ_VARIABLES + _WRITE_VARIABLES]
_PAD = 8
_GAP = 4


class Panel(QWidget):
    set_clicked = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        label_w = self._label_width()

        grid = QGridLayout(self)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(_PAD)
        grid.setVerticalSpacing(6)

        measure_header = QHBoxLayout()
        measure_header.addWidget(QLabel("Measurements"))
        measure_header.addStretch()

        setpoint_header = QHBoxLayout()
        setpoint_header.addWidget(QLabel("Setpoints"))
        setpoint_header.addStretch()

        grid.addLayout(measure_header, 0, 0)
        grid.addLayout(setpoint_header, 0, 1)

        self._readouts: list[Readout] = []
        self._digit_edits: list[DigitEdit] = []

        for i in range(len(_READ_VARIABLES)):
            measure_row = QHBoxLayout()
            measure_row.setSpacing(_GAP)
            rlabel = QLabel(f"{_READ_VARIABLES[i]}:")
            rlabel.setFixedWidth(label_w)
            rlabel.setAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            measure_row.addWidget(rlabel)
            ro = Readout(integer_digits=1, decimal_places=4)
            self._readouts.append(ro)
            measure_row.addWidget(ro)
            measure_row.addStretch()
            grid.addLayout(measure_row, i + 1, 0)

            setpoint_row = QHBoxLayout()
            setpoint_row.setSpacing(_GAP)
            slabel = QLabel(f"{_WRITE_VARIABLES[i]}:")
            slabel.setFixedWidth(label_w)
            slabel.setAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            setpoint_row.addWidget(slabel)
            de = DigitEdit(integer_digits=1, decimal_places=3)
            de.edit_committed.connect(self._make_set_slot(i))
            self._digit_edits.append(de)
            setpoint_row.addWidget(de)
            setpoint_row.addStretch()
            grid.addLayout(setpoint_row, i + 1, 1)

        grid.setRowStretch(len(_READ_VARIABLES) + 1, 1)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        self.set_connected(False)

    def _label_width(self) -> int:
        dummy = QLabel()
        dummy.setFont(self.font())
        fm = dummy.fontMetrics()
        return max(fm.horizontalAdvance(s) for s in _ALL_LABELS) + 2

    def _make_set_slot(self, index: int):
        def _fire() -> None:
            self.set_clicked.emit(index)

        return _fire

    def update_readout(self, index: int, value: str) -> None:
        try:
            self._readouts[index].set_value(float(value))
        except ValueError:
            pass

    def set_connected(self, connected: bool) -> None:
        for de in self._digit_edits:
            de.set_connected(connected)
        for ro in self._readouts:
            ro.setEnabled(connected)
        if not connected:
            for ro in self._readouts:
                ro.set_value(0.0)

    def digit_edit(self, index: int) -> DigitEdit:
        return self._digit_edits[index]
