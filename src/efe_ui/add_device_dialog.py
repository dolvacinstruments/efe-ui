import time

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLineEdit, QVBoxLayout, QWidget
from zeroconf import (
    ServiceBrowser,
    ServiceStateChange,
    Zeroconf,
)


class AddDeviceDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Add Device")
        self.setModal(True)
        self.setup_ui()
        self.start_mdns_listener()

    def __del__(self) -> None:
        if hasattr(self, "zeroconf"):
            self.zeroconf.close()

    def setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        self.device_name_edit = QLineEdit(self)
        self.device_name_edit.setPlaceholderText("Enter device name")
        self.device_name_edit.textChanged.connect(self._check_input_state)
        layout.addWidget(self.device_name_edit)

        self._create_ip_input(layout)

        self._button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self
        )
        self._button_box.accepted.connect(self.accept)
        self._button_box.rejected.connect(self.reject)
        self._button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

        layout.addWidget(self._button_box)

    def _create_ip_input(self, layout: QVBoxLayout) -> None:
        self.device_ip_edit = QLineEdit(self)
        self.device_ip_edit.setPlaceholderText("Enter device address")
        self.device_ip_edit.textChanged.connect(self._check_input_state)

        layout.addWidget(self.device_ip_edit)

    def _check_input_state(self) -> None:
        name_valid = bool(self.device_name_edit.text().strip())
        ip_valid = self.device_ip_edit.hasAcceptableInput()
        self._button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(name_valid and ip_valid)

    def get_data(self) -> tuple[str, str]:
        return self.device_name_edit.text().strip(), self.device_ip_edit.text().strip()

    def mdns_listener(self, zeroconf: Zeroconf, service_type: str, name: str, state_change: ServiceStateChange) -> None:
        print(f"Service {name} of type {service_type} state changed: {state_change}")
        if state_change is ServiceStateChange.Added:
            info = zeroconf.get_service_info(service_type, name)
            print(f"Info from zeroconf.get_service_info: {info!r}")

            if info:
                addresses = [f"{addr}:{int(info.port)}" for addr in info.parsed_scoped_addresses()]
                print(f"  Addresses: {', '.join(addresses)}")
                print(f"  Weight: {info.weight}, priority: {info.priority}")
                print(f"  Server: {info.server}")
                if info.properties:
                    print("  Properties are:")
                    for key, value in info.properties.items():
                        print(f"    {key!r}: {value!r}")
                else:
                    print("  No properties")
            else:
                print("  No info")
            print("\n")

    def start_mdns_listener(self) -> None:
        self.zeroconf = Zeroconf()
        self.browser = ServiceBrowser(self.zeroconf, "_scpi._tcp.local.", [self.mdns_listener])
