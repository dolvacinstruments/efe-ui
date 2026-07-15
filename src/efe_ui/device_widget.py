from functools import partial

from PySide6.QtCore import QMetaObject, Qt, QThread, Signal, Slot
from PySide6.QtWidgets import QHBoxLayout, QSizePolicy, QVBoxLayout, QWidget

from efe_ui.channel_widget import (
    ChannelWidget,
)
from efe_ui.constants import CHANNEL_COUNT, VariableType
from efe_ui.device import EFE, DeviceMeasured, DeviceSetup, DeviceStatus, DeviceStatusKind
from efe_ui.ui_helpers import create_title_bar_button, create_title_bar_label


class DeviceWidget(QWidget):
    disconnect_requested = Signal()

    def __init__(self, device_name: str, ip: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._device_name = device_name
        self._ip = ip
        self._channel_widgets: list[ChannelWidget] = []
        self._setup_device()
        self._setup_ui()
        self._connect_signals()
        QMetaObject.invokeMethod(self._device, "start_loop", Qt.ConnectionType.QueuedConnection)

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
        title_layout.addWidget(self._status_label)

        title_layout.addStretch(1)

        self._disconnect_button = create_title_bar_button("REMOVE")
        title_layout.addWidget(self._disconnect_button)

    def _connect_signals(self) -> None:
        self._disconnect_button.clicked.connect(self.disconnect_from_device)
        self.disconnect_requested.connect(self._device.stop_worker)
        self._device.measured_updated.connect(self.handle_measured_update)
        self._device.status_updated.connect(self.update_device_status)
        self._device.setup_updated.connect(self.handle_setup_update)
        self._thread.finished.connect(self._handle_thread_exit)

        for i, channel_widget in enumerate(self._channel_widgets):
            channel_widget.value_changed.connect(partial(self._device.set_value, i))
            channel_widget.is_disabled_changed.connect(partial(self._device.set_disabled, i))
            channel_widget.is_high_range_changed.connect(partial(self._device.set_high_range, i))
            channel_widget.is_diode_mode_changed.connect(partial(self._device.set_diode_mode, i))

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

    @Slot(DeviceSetup)
    def handle_setup_update(self, setup: DeviceSetup) -> None:
        for i in range(CHANNEL_COUNT):
            channel_widget = self._channel_widgets[i]
            channel_widget.set_is_disabled(setup.is_disabled[i])
            channel_widget.set_is_diode_mode(setup.is_diode_mode[i])
            channel_widget.set_is_high_range(setup.is_high_range[i])
            channel_widget.set_set_value(VariableType.VOLTAGE_C, setup.voltage_c[i])
            channel_widget.set_set_value(VariableType.CURRENT_C, setup.current_c[i])
            channel_widget.set_set_value(VariableType.VOLTAGE_E, setup.voltage_e[i])
            channel_widget.set_set_value(VariableType.CURRENT_E, setup.current_e[i])

    @Slot(VariableType, float, int)
    def set_set_value(self, variable_type: VariableType, value: float, channel: int) -> None:
        if channel < 0 or channel >= CHANNEL_COUNT:
            raise ValueError(f"Channel {channel} is out of range. Must be between 0 and {CHANNEL_COUNT - 1}.")
        self._channel_widgets[channel].set_set_value(variable_type, value)

    @Slot(bool, int)
    def set_is_disabled(self, is_disabled: bool, channel: int) -> None:
        if channel < 0 or channel >= CHANNEL_COUNT:
            raise ValueError(f"Channel {channel} is out of range. Must be between 0 and {CHANNEL_COUNT - 1}.")
        self._channel_widgets[channel].set_is_disabled(is_disabled)

    @Slot(bool, int)
    def set_is_diode_mode(self, is_diode_mode: bool, channel: int) -> None:
        if channel < 0 or channel >= CHANNEL_COUNT:
            raise ValueError(f"Channel {channel} is out of range. Must be between 0 and {CHANNEL_COUNT - 1}.")
        self._channel_widgets[channel].set_is_diode_mode(is_diode_mode)

    @Slot(bool, int)
    def set_is_high_range(self, is_high_range: bool, channel: int) -> None:
        if channel < 0 or channel >= CHANNEL_COUNT:
            raise ValueError(f"Channel {channel} is out of range. Must be between 0 and {CHANNEL_COUNT - 1}.")
        self._channel_widgets[channel].set_is_high_range(is_high_range)

    @Slot(DeviceStatus)
    def update_device_status(self, status: DeviceStatus) -> None:
        if status.kind == DeviceStatusKind.OK:
            self._status_label.setText("OK")
        elif status.kind == DeviceStatusKind.DISCONNECTED:
            self._status_label.setText("Disconnected")
        else:
            self._status_label.setText(f"Error: {status.message}")
