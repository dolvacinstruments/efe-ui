from PySide6.QtWidgets import QDialog, QHBoxLayout, QLineEdit, QPushButton, QVBoxLayout, QWidget


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
        layout.addWidget(self.device_name_edit)

        self.device_ip_edit = QLineEdit(self)
        self.device_ip_edit.setPlaceholderText("Enter device IP")
        layout.addWidget(self.device_ip_edit)

        button_layout = QHBoxLayout()
        add_button = QPushButton("Add", self)
        add_button.clicked.connect(self.accept)
        button_layout.addWidget(add_button)

        cancel_button = QPushButton("Cancel", self)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

    def get_data(self) -> tuple[str, str]:
        return self.device_name_edit.text().strip(), self.device_ip_edit.text().strip()
