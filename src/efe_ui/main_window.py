from PySide6.QtCore import Qt, QTimer, Signal, Slot
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from efe_ui.instrument import Instrument

_READ_VARIABLES = ["VOLTAGE_CATHODE", "VOLTAGE_EMITTER", "CURRENT_L", "CURRENT_H"]
_WRITE_VARIABLES = [
    "VOLTAGE_CATHODE",
    "VOLTAGE_EMITTER",
    "CURRENT_EMITTER",
    "CURRENT_CATHODE",
]
_POLL_INTERVAL_MS = 200

_READ_DISPLAY_STYLE = """
    QLineEdit {
        background: palette(window);
        border: 1px solid palette(mid);
        border-radius: 3px;
        padding: 2px 6px;
    }
"""


class MainWindow(QMainWindow):
    status_changed = Signal(bool)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("efe-ui")
        self.resize(640, 520)

        self._instrument = Instrument()

        self._poll_timer = QTimer()
        self._poll_timer.timeout.connect(self._poll_reads)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        root.addLayout(self._build_connection_bar())

        self._read_displays: list[QLineEdit] = []
        self._write_inputs: list[QDoubleSpinBox] = []
        self._set_buttons: list[QPushButton] = []

        self._build_panel(root)

        root.addStretch()

        self.status_changed.connect(self._on_status_changed)

    def _build_connection_bar(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(8)

        layout.addWidget(QLabel("IP Address:"))

        self._ip_input = QLineEdit()
        self._ip_input.setText("192.168.2.123")
        self._ip_input.setMaximumWidth(160)
        layout.addWidget(self._ip_input)

        layout.addWidget(QLabel("Port:"))

        self._port_input = QSpinBox()
        self._port_input.setRange(1, 65535)
        self._port_input.setValue(8080)
        self._port_input.setMaximumWidth(90)
        layout.addWidget(self._port_input)

        self._connect_btn = QPushButton("Connect")
        self._connect_btn.clicked.connect(self._toggle_connection)
        layout.addWidget(self._connect_btn)

        self._status_label = QLabel("Disconnected")
        self._status_label.setProperty("connected", False)
        layout.addWidget(self._status_label)

        layout.addStretch()
        return layout

    def _build_panel(self, root: QVBoxLayout) -> None:
        panel = QHBoxLayout()
        panel.setSpacing(12)
        panel.addWidget(self._build_read_group())
        panel.addWidget(self._build_write_group())
        root.addLayout(panel)

    def _build_read_group(self) -> QGroupBox:
        group = QGroupBox("Measurements")
        layout = QVBoxLayout(group)
        layout.setSpacing(6)

        header = QHBoxLayout()
        self._read_dot = QLabel("●")
        self._read_dot.setStyleSheet("color: #cc0000; font-size: 14px;")
        self._read_dot.hide()
        header.addWidget(self._read_dot)
        header.addStretch()
        layout.addLayout(header)

        for name in _READ_VARIABLES:
            row = QHBoxLayout()
            row.setSpacing(6)
            row.addWidget(QLabel(f"{name}:"))
            display = QLineEdit()
            display.setReadOnly(True)
            display.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            display.setStyleSheet(_READ_DISPLAY_STYLE)
            display.setPlaceholderText("—")
            self._read_displays.append(display)
            row.addWidget(display, stretch=1)
            layout.addLayout(row)

        return group

    def _build_write_group(self) -> QGroupBox:
        group = QGroupBox("Setpoints")
        layout = QVBoxLayout(group)
        layout.setSpacing(6)

        for name in _WRITE_VARIABLES:
            row = QHBoxLayout()
            row.setSpacing(6)
            row.addWidget(QLabel(f"{name}:"))
            inp = QDoubleSpinBox()
            inp.setRange(-99999, 99999)
            inp.setDecimals(1)
            inp.setSingleStep(0.1)
            self._write_inputs.append(inp)
            row.addWidget(inp, stretch=1)
            btn = QPushButton("Set")
            btn.setEnabled(False)
            btn.clicked.connect(self._make_set_slot(len(self._write_inputs) - 1))
            self._set_buttons.append(btn)
            row.addWidget(btn)
            layout.addLayout(row)

        return group

    def _make_set_slot(self, index: int):
        @Slot()
        def _set() -> None:
            name = _WRITE_VARIABLES[index]
            value = self._write_inputs[index].value()
            try:
                self._instrument.write(f"SOURCE:{name} {value}")
            except Exception:
                pass

        return _set

    @Slot()
    def _poll_reads(self) -> None:
        all_ok = True
        for i, name in enumerate(_READ_VARIABLES):
            try:
                value = self._instrument.query(f"MEASURE:{name}?")
                self._read_displays[i].setText(value)
            except Exception:
                self._read_displays[i].setText("Error")
                all_ok = False

        if all_ok:
            self._read_dot.setStyleSheet("color: #00cc44; font-size: 14px;")
        else:
            self._read_dot.setStyleSheet("color: #cc0000; font-size: 14px;")

    @Slot()
    def _toggle_connection(self) -> None:
        if self._instrument.connected:
            self._instrument.disconnect()
            self._poll_timer.stop()
            self.status_changed.emit(False)
        else:
            self._connect()

    def _connect(self) -> None:
        host = self._ip_input.text().strip()
        if not host:
            self._status_label.setText("Enter an IP address")
            return
        port = self._port_input.value()

        self._connect_btn.setEnabled(False)
        self._status_label.setText("Connecting...")
        self._status_label.setProperty("connected", False)

        try:
            self._instrument.connect(host, port)
        except Exception:
            self._status_label.setText("Connection failed")
            self._status_label.setProperty("connected", False)
            self._connect_btn.setEnabled(True)
            return

        self._poll_timer.start(_POLL_INTERVAL_MS)
        self.status_changed.emit(True)

    @Slot(bool)
    def _on_status_changed(self, connected: bool) -> None:
        if connected:
            self._status_label.setText(f"Connected to {self._instrument.address}")
            self._status_label.setProperty("connected", True)
            self._connect_btn.setEnabled(True)
            self._connect_btn.setText("Disconnect")
            self._ip_input.setEnabled(False)
            self._port_input.setEnabled(False)
            self._read_dot.show()
        else:
            self._status_label.setText("Disconnected")
            self._status_label.setProperty("connected", False)
            self._connect_btn.setEnabled(True)
            self._connect_btn.setText("Connect")
            self._ip_input.setEnabled(True)
            self._port_input.setEnabled(True)
            self._read_dot.hide()

        for btn in self._set_buttons:
            btn.setEnabled(connected)
