from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPaintEvent
from PySide6.QtWidgets import QHBoxLayout, QSizePolicy, QStyle, QStyleOption, QVBoxLayout, QWidget

from efe_ui.channel_widget import ChannelWidget
from efe_ui.ui_helpers import create_title_bar_button, create_title_bar_label

CHANNEL_COUNT = 4


class DeviceWidget(QWidget):
    def __init__(self, device_name: str, ip: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._device_name = device_name
        self._ip = ip
        self.setup_ui()
        self.connect_signals()

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
            channel_widget = ChannelWidget(self)
            channel_widget.set_channel_number(f"{self._device_name}.{i + 1}")
            ch_layout.addWidget(channel_widget)

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

    def handle_disconnect(self) -> None:
        self.setParent(None)
        self.deleteLater()

    def paintEvent(self, event: QPaintEvent) -> None:
        opt = QStyleOption()
        opt.initFrom(self)

        painter = QPainter(self)
        self.style().drawPrimitive(QStyle.PrimitiveElement.PE_Widget, opt, painter, self)

        super().paintEvent(event)
