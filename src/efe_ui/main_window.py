from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QWidget

from .channel_widget import ChannelWidget


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("EFE-UI")

        self.setup_ui()

    def setup_ui(self) -> None:
        container = QWidget(self)
        self.setCentralWidget(container)
        layout = QHBoxLayout(container)
        layout.addWidget(ChannelWidget(self))
