import logging

from PySide6.QtCore import QObject, Qt, Signal, Slot
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)
from zeroconf import (
    ServiceBrowser,
    ServiceStateChange,
    Zeroconf,
)

logger = logging.getLogger(__name__)


class DeviceListener(QObject):
    device_added = Signal(str, str, str, str)
    device_removed = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.zeroconf = Zeroconf()
        self.browser = ServiceBrowser(self.zeroconf, "_scpi._tcp.local.", [self.mdns_listener])

    def mdns_listener(self, zeroconf: Zeroconf, service_type: str, name: str, state_change: ServiceStateChange) -> None:
        logger.info(f"Service {name} of type {service_type} state changed: {state_change}")
        if state_change is ServiceStateChange.Added:
            info = zeroconf.get_service_info(service_type, name)
            logger.info(f"Info from zeroconf.get_service_info: {info!r}")

            if info is not None and info.port is not None:
                addresses = [f"{addr}:{int(info.port)}" for addr in info.parsed_scoped_addresses()]
                logger.info(f"  Addresses: {', '.join(addresses)}")
                logger.info(f"  Weight: {info.weight}, priority: {info.priority}")
                logger.info(f"  Server: {info.server}")
                if info.properties:
                    logger.info("  Properties are:")
                    for key, value in info.properties.items():
                        logger.info(f"    {key!r}: {value!r}")
                else:
                    logger.info("  No properties")

                self.device_added.emit(
                    name,
                    info.properties.get(b'user_name', b'').decode('utf-8') if info.properties else "",
                    addresses[0].split(":")[0] if addresses else "",
                    info.server.split(".")[0] if info.server else "",
                )
            else:
                logger.info("  No info")
            logger.info("\n")

        if state_change is ServiceStateChange.Removed:
            self.device_removed.emit(name)
            logger.info(f"Service {name} removed")

    def __del__(self) -> None:
        if hasattr(self, "zeroconf"):
            self.zeroconf.close()


class AddDeviceDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Add Device")
        self.setModal(True)
        self._setup_ui()
        self.listener = self._setup_listener()

    def _setup_listener(self) -> DeviceListener:
        listener = DeviceListener(self)
        listener.device_added.connect(self._device_added)
        listener.device_removed.connect(self._device_removed)
        return listener

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        self.device_name_edit = QLineEdit(self)
        self.device_name_edit.setPlaceholderText("Enter device name")
        self.device_name_edit.textChanged.connect(self._check_input_state)
        layout.addWidget(self.device_name_edit)

        self.device_ip_edit = QLineEdit(self)
        self.device_ip_edit.setPlaceholderText("Enter device address")
        self.device_ip_edit.textChanged.connect(self._check_input_state)
        layout.addWidget(self.device_ip_edit)

        label = QLabel("Discovered devices (click to select):", self)
        layout.addWidget(label)

        self.device_list = QListWidget(self)
        layout.addWidget(self.device_list)
        self.device_list.itemClicked.connect(self._device_selected)
        self.spinner_item = self._create_spinner_item()
        self.device_list.addItem(self.spinner_item)

        self._button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self
        )
        self._button_box.accepted.connect(self.accept)
        self._button_box.rejected.connect(self.reject)
        self._button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

        layout.addWidget(self._button_box)

    @Slot(str)
    def _device_removed(self, name: str) -> None:
        for i in range(self.device_list.count()):
            item = self.device_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole)[0] == name:
                self.device_list.takeItem(i)
                break

    @Slot(str, str, str, str)
    def _device_added(self, name: str, username: str, address: str, server: str) -> None:
        item = QListWidgetItem(f"{username if username else ''} {server} ({address})")
        item.setData(Qt.ItemDataRole.UserRole, (name, username, address, server))
        spinner_row = self.device_list.row(self.spinner_item)
        if spinner_row != -1:
            self.device_list.insertItem(spinner_row, item)
        else:
            self.device_list.addItem(item)

    @Slot(QListWidgetItem)
    def _device_selected(self, item: QListWidgetItem) -> None:
        name, username, address, server = item.data(Qt.ItemDataRole.UserRole)
        self.device_name_edit.setText(username if username else server)
        self.device_ip_edit.setText(address)

    @Slot(str, str)
    def _check_input_state(self) -> None:
        name_valid = bool(self.device_name_edit.text().strip())
        ip_valid = self.device_ip_edit.hasAcceptableInput()
        self._button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(name_valid and ip_valid)

    def get_data(self) -> tuple[str, str]:
        return self.device_name_edit.text().strip(), self.device_ip_edit.text().strip()

    def _create_spinner_item(self) -> QListWidgetItem:
        item = QListWidgetItem("Searching...")
        flags = item.flags()
        flags &= ~Qt.ItemFlag.ItemIsSelectable
        flags &= ~Qt.ItemFlag.ItemIsEnabled
        item.setFlags(flags)
        return item
