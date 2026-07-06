from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLineEdit, QVBoxLayout, QWidget


class AddDeviceDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Add Device")
        self.setModal(True)
        self.setup_ui()

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
        ip_range = r"(?:[0-1]?[0-9]?[0-9]|2[0-4][0-9]|25[0-5])"
        ip_regex = QRegularExpression(f"^{ip_range}\\.{ip_range}\\.{ip_range}\\.{ip_range}$")

        self.device_ip_edit = QLineEdit(self)
        self.device_ip_edit.setPlaceholderText("Enter device IP")
        self.device_ip_edit.textChanged.connect(self._check_input_state)

        validator = QRegularExpressionValidator(ip_regex, self)

        self.device_ip_edit.setValidator(validator)

        layout.addWidget(self.device_ip_edit)

    def _check_input_state(self) -> None:
        name_valid = bool(self.device_name_edit.text().strip())
        ip_valid = self.device_ip_edit.hasAcceptableInput()
        self._button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(name_valid and ip_valid)

    def get_data(self) -> tuple[str, str]:
        return self.device_name_edit.text().strip(), self.device_ip_edit.text().strip()
