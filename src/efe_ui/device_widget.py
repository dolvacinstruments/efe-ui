from PySide6.QtCore import QEvent, QMetaObject, Qt, QThread, Signal, Slot
from PySide6.QtGui import QPainter, QPaintEvent
from PySide6.QtWidgets import QHBoxLayout, QSizePolicy, QStyle, QStyleOption, QVBoxLayout, QWidget

from efe_ui.channel_widget import (
    ChannelEnableEvent,
    ChannelModeEvent,
    ChannelRangeEvent,
    ChannelVariableEvent,
    ChannelWidget,
)
from efe_ui.constants import CHANNEL_COUNT, VariableType
from efe_ui.device import Device
from efe_ui.ui_helpers import create_title_bar_button, create_title_bar_label


class DeviceWidget(QWidget):
    variable_set = Signal(VariableType, float, int)
    enable_set = Signal(bool, int)
    high_range_set = Signal(bool, int)
    diode_mode_set = Signal(bool, int)

    def __init__(self, device_name: str, ip: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._device_name = device_name
        self._ip = ip
        self._channel_widgets: list[ChannelWidget] = []
        self.setup_device()
        self.setup_ui()
        self.connect_signals()
        QMetaObject.invokeMethod(self._device, "start_loop", Qt.ConnectionType.QueuedConnection)

    def setup_device(self) -> None:
        self._device = Device(self._ip)
        self._thread = QThread(self)
        self._device.moveToThread(self._thread)
        self._thread.start()

    def setup_ui(self) -> None:
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

        self.add_title_bar(layout)

        ch_layout = QHBoxLayout()
        ch_layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(ch_layout)
        for i in range(CHANNEL_COUNT):
            channel_widget = ChannelWidget(self, channel_number=i, device_name=self._device_name)
            ch_layout.addWidget(channel_widget)
            self._channel_widgets.append(channel_widget)

    def add_title_bar(self, layout: QVBoxLayout) -> None:
        title_bar = QWidget(self)
        title_bar.setStyleSheet("""
            QWidget {
                background-color: palette(mid);
            }
        """)
        title_bar.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        layout.addWidget(title_bar)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        title_layout = QHBoxLayout(title_bar)
        title_label = create_title_bar_label(f"{self._device_name} ({self._ip})")
        title_layout.addWidget(title_label)
        title_layout.setContentsMargins(10, 0, 10, 0)

        title_layout.addStretch(1)

        self.disconnect_button = create_title_bar_button("REMOVE")
        title_layout.addWidget(self.disconnect_button)

    def connect_signals(self) -> None:
        self.disconnect_button.clicked.connect(self.handle_disconnect)
        self.variable_set.connect(self._device.set_value)
        self.enable_set.connect(self._device.set_enabled)
        self.high_range_set.connect(self._device.set_high_range)
        self.diode_mode_set.connect(self._device.set_diode_mode)
        self._device.variable_updated.connect(self.update_device_values)

    def handle_disconnect(self) -> None:
        self.setParent(None)
        self.deleteLater()

    def paintEvent(self, event: QPaintEvent) -> None:
        opt = QStyleOption()
        opt.initFrom(self)

        painter = QPainter(self)
        self.style().drawPrimitive(QStyle.PrimitiveElement.PE_Widget, opt, painter, self)

        super().paintEvent(event)

    def customEvent(self, event: QEvent) -> None:
        if event.type() == ChannelVariableEvent.EVENT_TYPE:
            if isinstance(event, ChannelVariableEvent):
                self.variable_set.emit(event.variable_type, event.value, event.channel)
        elif event.type() == ChannelEnableEvent.EVENT_TYPE:
            if isinstance(event, ChannelEnableEvent):
                self.enable_set.emit(event.is_enabled, event.channel)
        elif event.type() == ChannelModeEvent.EVENT_TYPE:
            if isinstance(event, ChannelModeEvent):
                self.diode_mode_set.emit(event.is_diode_mode, event.channel)
        elif event.type() == ChannelRangeEvent.EVENT_TYPE:
            if isinstance(event, ChannelRangeEvent):
                self.high_range_set.emit(event.is_high_range, event.channel)
        else:
            super().customEvent(event)

    @Slot(VariableType, float, int)
    def update_device_values(self, variable_type: VariableType, value: float, channel: int) -> None:
        if channel < 0 or channel >= CHANNEL_COUNT:
            return

        channel_widget = self._channel_widgets[channel]
        channel_widget.set_variable(variable_type, value)
