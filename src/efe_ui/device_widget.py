from functools import partial

from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtWidgets import QHBoxLayout, QMessageBox, QSizePolicy, QVBoxLayout, QWidget

from efe_ui.channel_widget import (
    ChannelWidget,
)
from efe_ui.constants import CHANNEL_COUNT, VariableType
from efe_ui.device import EFE, DeviceMeasured, DeviceStatus, DeviceStatusKind
from efe_ui.number_widget import Value
from efe_ui.ui_helpers import create_title_bar_button, create_title_bar_label


class DeviceWidget(QWidget):
    disconnect_requested = Signal()

    def __init__(self, device_name: str, ip: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._device_name = device_name
        self._ip = ip
        self._channel_widgets: list[ChannelWidget] = []
        self._last_status: DeviceStatus | None = None
        self._msgbox: QMessageBox | None = None
        self._setup_device()
        self._setup_ui()
        self._connect_signals()

    def _setup_device(self) -> None:
        self._device = EFE(self._ip)
        self._thread = QThread(self)
        self._device.moveToThread(self._thread)
        self._thread.started.connect(self._device.start_loop)
        self._thread.start()

    def _setup_ui(self) -> None:
        self.setObjectName("device_widget")
        self.setStyleSheet("""
            #device_widget {
                border: 1px solid palette(mid);
            }
        """)
        self.setContentsMargins(0, 0, 0, 0)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._add_title_bar(layout)

        ch_layout = QHBoxLayout()
        ch_layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(ch_layout)
        for i in range(CHANNEL_COUNT):
            channel_widget = ChannelWidget(f"{self._device_name}.{i + 1}")
            ch_layout.addWidget(channel_widget)
            self._channel_widgets.append(channel_widget)

    def _add_title_bar(self, layout: QVBoxLayout) -> None:
        title_bar = QWidget()
        layout.addWidget(title_bar, alignment=Qt.AlignmentFlag.AlignTop)

        title_bar.setStyleSheet("""
            QWidget {
                background-color: palette(mid);
            }
        """)
        title_bar.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        title_layout = QHBoxLayout()
        title_bar.setLayout(title_layout)
        title_label = create_title_bar_label(f"{self._device_name} ({self._ip})")
        title_layout.addWidget(title_label)
        title_layout.setContentsMargins(10, 0, 10, 0)

        self._status_label = create_title_bar_label("Connecting...")
        self._status_label.setStyleSheet("color: red;")
        title_layout.addWidget(self._status_label)

        title_layout.addStretch(1)

        self._disconnect_button = create_title_bar_button("REMOVE")
        title_layout.addWidget(self._disconnect_button)

    def _connect_signals(self) -> None:
        self._disconnect_button.clicked.connect(self.disconnect_from_device)
        self.disconnect_requested.connect(self._device.stop_worker)
        self._device.measured_updated.connect(self.handle_measured_update)
        self._device.status_updated.connect(self.update_device_status)
        self._device.force_disable.connect(self.handle_force_disable)
        self._thread.finished.connect(self._handle_thread_exit)

        for i, channel_widget in enumerate(self._channel_widgets):
            channel_widget.value_changed.connect(partial(self._device.set_value, i))
            channel_widget.is_disabled_changed.connect(partial(self._device.set_disabled, i))
            channel_widget.is_high_range_changed.connect(partial(self._device.set_high_range, i))

    @Slot()
    def disconnect_from_device(self) -> None:
        self.disconnect_requested.emit()

    @Slot()
    def _handle_thread_exit(self) -> None:
        self.setParent(None)
        self.deleteLater()

    @Slot(DeviceMeasured)
    def handle_measured_update(self, measured: DeviceMeasured) -> None:
        for i in range(CHANNEL_COUNT):
            channel_widget = self._channel_widgets[i]
            channel_widget.set_measure_value(VariableType.VOLTAGE_C, measured.voltage_c[i])
            channel_widget.set_measure_value(VariableType.CURRENT_C, measured.current[i])
            channel_widget.set_measure_value(VariableType.VOLTAGE_E, measured.voltage_e[i])
            channel_widget.set_cathode_state(measured.state_c[i])
            channel_widget.set_extraction_state(measured.state_e[i])

    @Slot()
    def handle_force_disable(self) -> None:
        for i in range(CHANNEL_COUNT):
            self._channel_widgets[i].set_is_disabled(True)

    @Slot(VariableType, float, int)
    def set_set_value(self, variable_type: VariableType, value: float, channel: int) -> None:
        if channel < 0 or channel >= CHANNEL_COUNT:
            raise ValueError(f"Channel {channel} is out of range. Must be between 0 and {CHANNEL_COUNT - 1}.")
        self._channel_widgets[channel].set_set_value(variable_type, Value(value))

    @Slot(bool, int)
    def set_is_disabled(self, is_disabled: bool, channel: int) -> None:
        if channel < 0 or channel >= CHANNEL_COUNT:
            raise ValueError(f"Channel {channel} is out of range. Must be between 0 and {CHANNEL_COUNT - 1}.")
        self._channel_widgets[channel].set_is_disabled(is_disabled)

    @Slot(bool, int)
    def set_is_high_range(self, is_high_range: bool, channel: int) -> None:
        if channel < 0 or channel >= CHANNEL_COUNT:
            raise ValueError(f"Channel {channel} is out of range. Must be between 0 and {CHANNEL_COUNT - 1}.")
        self._channel_widgets[channel].set_is_high_range(is_high_range)

    @Slot(DeviceStatus)
    def update_device_status(self, status: DeviceStatus) -> None:
        if self._last_status is not None and self._last_status.message == status.message:
            return  # No change in status, do nothing
        self._last_status = status
        if status.kind == DeviceStatusKind.OK:
            self._status_label.setText("")
        elif status.kind == DeviceStatusKind.DISCONNECTED:
            self._status_label.setText("Disconnected")
        elif status.kind == DeviceStatusKind.CONNECTION_ERROR:
            self._status_label.setText(f"Connection Error: {status.message}")
        else:
            if self._msgbox:
                self._msgbox.close()

            self._msgbox = QMessageBox(self)
            self._msgbox.setIcon(QMessageBox.Icon.Critical)
            self._msgbox.setWindowTitle("Device Error")
            self._msgbox.setText(f"Device {self._device_name} ({self._ip}) encountered an error: {status.message}")

            self._msgbox.show()

    def get_ip(self) -> str:
        return self._ip

    def get_name(self) -> str:
        return self._device_name
