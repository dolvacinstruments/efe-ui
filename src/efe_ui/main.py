import logging
import signal
import sys
from importlib.resources import files

from PySide6.QtCore import QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from efe_ui.args import get_args
from efe_ui.main_window import MainWindow


def handle_signal(signum: int, _) -> None:  # noqa: ANN001
    QApplication.quit()


def main() -> None:
    app = QApplication(sys.argv)
    app.setOrganizationName("Dolvac Instruments")
    app.setOrganizationDomain("dolvac.com")

    if sys.platform == "win32":
        import ctypes

        app_id = "dolvac.efe_ui"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)

    app.setWindowIcon(QIcon(get_icon_path()))

    if get_args().debug:
        logging.basicConfig(level=logging.INFO)
        app.setStyleSheet("""
            QWidget {
                border: 1px solid red;
            }
            QPushButton {
                border: 1px solid blue;
            }
        """)

    window = MainWindow()
    window.show()

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)
    timer = QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    sys.exit(app.exec())


def get_icon_path() -> str:
    path = files("efe_ui.assets").joinpath("icon.svg")
    return str(path)


if __name__ == "__main__":
    main()
