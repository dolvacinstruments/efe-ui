import logging
import signal
import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from efe_ui.args import get_args
from efe_ui.main_window import MainWindow


def handle_signal(signum: int, _) -> None:  # noqa: ANN001
    QApplication.quit()


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("EFE-UI")
    app.setOrganizationName("Dolvac")
    app.setOrganizationDomain("dolvac.com")

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


if __name__ == "__main__":
    main()
