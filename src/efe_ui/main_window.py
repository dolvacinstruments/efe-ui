import json
from functools import partial
from pathlib import Path

from platformdirs import user_data_dir
from pydantic import ValidationError
from PySide6.QtCore import QObject, QSize, Qt, QThread, QTimer
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QAbstractScrollArea,
    QDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from efe_ui.add_device_dialog import AddDeviceDialog
from efe_ui.channel_widget import ChannelWidget
from efe_ui.config import DevicesConfig
from efe_ui.constants import CHANNEL_COUNT
from efe_ui.device_logs import DeviceLogs
from efe_ui.device_widget import DeviceWidget
from efe_ui.load_devices_dialog import LoadDevicesDialog
from efe_ui.main import ARGS
from efe_ui.save_devices_dialog import SaveDevicesDialog

APP_NAME = "EFE-UI"


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("EFE-UI")

        self.setup_ui()
        self.setup_menu()
        path = Path(user_data_dir(appname=APP_NAME, ensure_exists=True)) / "devices.json"
        if path.exists():
            self.load_config(path)
        if ARGS is not None and ARGS.log:
            self._log_thread = QThread(self)
            self._device_logs = DeviceLogs()
            self._device_logs.moveToThread(self._log_thread)
            self._log_thread.started.connect(self._device_logs.loop)
            self._log_thread.start()

    def setup_ui(self) -> None:
        container = QWidget(self)
        self.setCentralWidget(container)
        layout = QHBoxLayout(container)
        layout.setSizeConstraint(QHBoxLayout.SizeConstraint.SetMinimumSize)

        self.add_device_area(layout)

        self._global_widget = ChannelWidget("Global", write_only=True)
        layout.addWidget(self._global_widget, alignment=Qt.AlignmentFlag.AlignHCenter)

        layout.addStretch(1)

    def setup_menu(self) -> None:
        menu_bar = self.menuBar()
        devices_menu = menu_bar.addMenu("Devices")

        add_device_action = QAction("Add Device...", self)
        add_device_action.setShortcut("Ctrl+N")
        add_device_action.triggered.connect(self.show_add_device_dialog)
        devices_menu.addAction(add_device_action)

        load_devices_action = QAction("Add Devices from file...", self)
        load_devices_action.triggered.connect(self.show_load_devices_dialog)
        devices_menu.addAction(load_devices_action)

        save_devices_action = QAction("Save Devices to file...", self)
        save_devices_action.triggered.connect(self.show_save_devices_dialog)
        devices_menu.addAction(save_devices_action)

    def show_add_device_dialog(self) -> None:
        dialog = AddDeviceDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name, ip = dialog.get_data()
            self.add_device_widget(ip, name)

    def show_load_devices_dialog(self) -> None:
        dialog = LoadDevicesDialog(self)
        file_path = dialog.get_path()
        if file_path is not None:
            self.load_config(file_path)

    def show_save_devices_dialog(self) -> None:
        dialog = SaveDevicesDialog(self)
        file_path = dialog.get_path()
        if file_path is not None:
            self.save_config(file_path)

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
        device_widget.destroyed.connect(self.handle_destroyed)

        for i in range(CHANNEL_COUNT):
            self._global_widget.is_disabled_changed.connect(partial(device_widget.set_is_disabled, channel=i))
            self._global_widget.is_diode_mode_changed.connect(partial(device_widget.set_is_diode_mode, channel=i))
            self._global_widget.is_high_range_changed.connect(partial(device_widget.set_is_high_range, channel=i))
            self._global_widget.value_changed.connect(partial(device_widget.set_set_value, channel=i))

        self.save_auto_config()

    def save_auto_config(self) -> None:
        self.save_config(Path(user_data_dir(appname=APP_NAME, ensure_exists=True)) / "devices.json")

    def save_config(self, path: Path) -> None:
        ips = []
        names = []
        for widget in self.area_widget.findChildren(DeviceWidget):
            ips.append(widget.get_ip())
            names.append(widget.get_name())
        try:
            DevicesConfig.from_lists(names, ips).to_file(path)
        except Exception as e:
            QMessageBox.critical(self.parentWidget(), "Error", f"Could not save file:\n{str(e)}")

    def load_config(self, file_path: Path) -> None:
        try:
            devices_config = DevicesConfig.from_file(file_path)
            for device in devices_config.root:
                self.add_device_widget(device.ip, device.name)

        except json.JSONDecodeError:
            QMessageBox.critical(self.parentWidget(), "Error", "Invalid JSON format!")
        except ValidationError as e:
            error_msg = f"Data validation failed for {file_path}:\n\n"
            for err in e.errors():
                loc = " -> ".join(str(line) for line in err["loc"])
                msg = err["msg"]
                error_msg += f"{loc}: {msg}\n"
            QMessageBox.critical(self.parentWidget(), "Error", error_msg)
        except Exception as e:
            QMessageBox.critical(self.parentWidget(), "Error", f"Could not read file:\n{str(e)}")

    def handle_destroyed(self, obj: QObject) -> None:
        QTimer.singleShot(0, self.save_auto_config)  # Delay saving to ensure the widget is fully destroyedjd


class FitScrollArea(QScrollArea):
    def sizeHint(self) -> QSize:
        base_hint = super().sizeHint()
        if (widget := self.widget()) is not None:
            canvas_width = widget.minimumSizeHint().width()
            scrollbar_width = self.verticalScrollBar().sizeHint().width()
            return QSize(canvas_width + scrollbar_width + 10, base_hint.height())
        return base_hint
