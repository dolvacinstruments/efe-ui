from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QAbstractScrollArea,
    QDialog,
    QHBoxLayout,
    QMainWindow,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from efe_ui.add_device_dialog import AddDeviceDialog
from efe_ui.channel_widget import ChannelWidget
from efe_ui.device_widget import DeviceWidget


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("EFE-UI")

        self.setup_ui()
        self.setup_menu()

    def setup_ui(self) -> None:
        container = QWidget(self)
        self.setCentralWidget(container)
        layout = QHBoxLayout(container)
        layout.setSizeConstraint(QHBoxLayout.SizeConstraint.SetMinimumSize)

        self.add_device_area(layout)

        layout.addWidget(ChannelWidget("Global", write_only=True), alignment=Qt.AlignmentFlag.AlignHCenter)

        layout.addStretch(1)

    def setup_menu(self) -> None:
        menu_bar = self.menuBar()
        devices_menu = menu_bar.addMenu("Devices")
        add_device_action = QAction("Add Device...", self)
        add_device_action.setShortcut("Ctrl+N")
        add_device_action.triggered.connect(self.show_add_device_dialog)
        devices_menu.addAction(add_device_action)

    def show_add_device_dialog(self) -> None:
        dialog = AddDeviceDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name, ip = dialog.get_data()
            self.add_device_widget(ip, name)

    def add_device_area(self, layout: QHBoxLayout) -> None:
        self.scroll_area = FitScrollArea(self)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.scroll_area.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.area_widget = QWidget(self.scroll_area)
        self.area_widget.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)
        self.area_layout = QVBoxLayout(self.area_widget)
        self.area_layout.setSizeConstraint(QVBoxLayout.SizeConstraint.SetMinimumSize)
        self.area_layout.setContentsMargins(5, 5, 5, 5)
        self.area_layout.addStretch()

        self.scroll_area.setWidget(self.area_widget)

        layout.addWidget(self.scroll_area)

    def add_device_widget(self, ip: str, name: str) -> None:
        device_widget = DeviceWidget(name, ip, self)
        self.area_layout.addWidget(device_widget)
        self.scroll_area.updateGeometry()


class FitScrollArea(QScrollArea):
    def sizeHint(self) -> QSize:
        base_hint = super().sizeHint()
        if (widget := self.widget()) is not None:
            canvas_width = widget.minimumSizeHint().width()
            scrollbar_width = self.verticalScrollBar().sizeHint().width()
            return QSize(canvas_width + scrollbar_width + 10, base_hint.height())
        return base_hint
