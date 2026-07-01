from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QWidget

from efe_ui.number_widget import NumberWidget


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("EFE-UI")

        self.setup_ui()

    def setup_ui(self) -> None:
        container = QWidget(self)
        self.setCentralWidget(container)
        layout = QHBoxLayout(container)
        number_widget = NumberWidget(digit_count=4, point_position=1, min_value=0, max_value=120, parent=self)
        layout.addWidget(number_widget)
