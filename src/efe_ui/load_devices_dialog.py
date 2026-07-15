import json

from pydantic import BaseModel, RootModel, ValidationError
from PySide6.QtWidgets import QFileDialog, QMessageBox, QWidget


class LoadDevicesDialog(QFileDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
        self.setFileMode(QFileDialog.FileMode.ExistingFile)
        self.setNameFilter("JSON Files (*.json);;All Files (*)")

    def get_data(self) -> DevicesConfig | None:
        if self.exec():
            selected_files = self.selectedFiles()
            if not selected_files:
                return None

            file_path = selected_files[0]

            try:
                with open(file_path, encoding="utf-8") as file:
                    raw = json.load(file)

                validated = DevicesConfig.model_validate(raw)

                return validated

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

        return None


class DeviceConfig(BaseModel):
    name: str
    ip: str


class DevicesConfig(RootModel[list[DeviceConfig]]):
    pass
