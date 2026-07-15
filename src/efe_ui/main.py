import argparse
import signal
import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from efe_ui.main_window import MainWindow


def parse_args() -> tuple[argparse.Namespace, list[str]]:
    arg_parser = argparse.ArgumentParser(description="EFE-UI")
    arg_parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Enable debug mod",
    )
    args = arg_parser.parse_known_args()
    return args


def handle_signal(signum: int, _) -> None:  # noqa: ANN001
    QApplication.quit()


def main() -> None:
    args, unknown_args = parse_args()

    app = QApplication(sys.argv)
    app.setApplicationName("EFE-UI")
    app.setOrganizationName("Dolvac")
    app.setOrganizationDomain("dolvac.com")

    if args.debug:
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
