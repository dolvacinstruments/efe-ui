from pathlib import Path

from PySide6.QtWidgets import QFileDialog, QWidget


class SaveDevicesDialog(QFileDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        self.setFileMode(QFileDialog.FileMode.AnyFile)
        self.setNameFilter("JSON Files (*.json);;All Files (*)")

    def get_path(self) -> Path | None:
        if self.exec():
            selected_files = self.selectedFiles()
            if not selected_files:
                return None
            file_path = selected_files[0]
            return Path(file_path)

        return None
