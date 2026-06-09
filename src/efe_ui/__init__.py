import sys

from PySide6.QtWidgets import QApplication

from efe_ui.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("efe-ui")
    app.setOrganizationName("efe")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
