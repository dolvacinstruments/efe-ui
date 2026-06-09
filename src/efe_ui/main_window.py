from PySide6.QtCore import QTimer, Signal, Slot
from PySide6.QtWidgets import (
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
from efe_ui.panel import Panel

_READ_VARIABLES = ["VOLTAGE_CATHODE", "VOLTAGE_EMITTER", "CURRENT_L", "CURRENT_H"]
_WRITE_VARIABLES = [
    "VOLTAGE_CATHODE",
    "VOLTAGE_EMITTER",
    "CURRENT_EMITTER",
    "CURRENT_CATHODE",
]
_POLL_INTERVAL_MS = 200


class MainWindow(QMainWindow):
    status_changed = Signal(bool)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("efe-ui")
        self.resize(750, 400)

        self._instrument = Instrument()

        self._poll_timer = QTimer()
        self._poll_timer.timeout.connect(self._poll_reads)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        root.addLayout(self._build_connection_bar())

        self._panel = Panel()
        self._panel.set_clicked.connect(self._on_set)
        root.addWidget(self._panel, stretch=1)

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

    @Slot(int)
    def _on_set(self, index: int) -> None:
        name = _WRITE_VARIABLES[index]
        value = self._panel.digit_edit(index).value()
        try:
            self._instrument.write(f"SOURCE:{name} {value}")
        except Exception:
            pass

    @Slot()
    def _poll_reads(self) -> None:
        all_ok = True
        for i, name in enumerate(_READ_VARIABLES):
            try:
                value = self._instrument.query(f"MEASURE:{name}?")
                self._panel.update_readout(i, value, True)
            except Exception:
                self._panel.update_readout(i, "Error", False)
                all_ok = False
        self._panel.set_all_read_ok(all_ok)

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
        self._panel.set_connected(connected)
        if connected:
            self._status_label.setText(f"Connected to {self._instrument.address}")
            self._status_label.setProperty("connected", True)
            self._connect_btn.setEnabled(True)
            self._connect_btn.setText("Disconnect")
            self._ip_input.setEnabled(False)
            self._port_input.setEnabled(False)
        else:
            self._status_label.setText("Disconnected")
            self._status_label.setProperty("connected", False)
            self._connect_btn.setEnabled(True)
            self._connect_btn.setText("Connect")
            self._ip_input.setEnabled(True)
            self._port_input.setEnabled(True)
