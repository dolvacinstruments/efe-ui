from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QSizePolicy, QWidget

from efe_ui.constants import TITLE_BAR_FONT_SIZE
from efe_ui.ui_helpers import get_text_width, set_font


class TitleBarSwitch(QWidget):
    state_changed = Signal(bool)

    def __init__(self, label: str, text_true: str, text_false: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._label = label
        self._text_true = text_true
        self._text_false = text_false

        self._state = True

        self._setup_ui()
        self._connect_signals()
        self.set_state(self._state)

    def set_state(self, state: bool) -> None:
        self._state = state
        self.button.setText(self._text_true if state else self._text_false)
        self.state_changed.emit(state)

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        self.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)

        self._add_label(layout)
        self._add_button(layout)

    def _add_label(self, layout: QHBoxLayout) -> None:
        label = QLabel(self._label, self)
        layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        set_font(label, TITLE_BAR_FONT_SIZE)
        label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

    def _add_button(self, layout: QHBoxLayout) -> None:
        self.button = QPushButton()
        layout.addWidget(self.button, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.button.setFlat(True)
        self.button.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                padding-left: 0px;
                padding-right: 0px;
                margin: 0px;
            }
            QPushButton:hover {
                    color: palette(midlight);
            }
        """)
        set_font(self.button, TITLE_BAR_FONT_SIZE, bold=True)
        self.button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.button.setFixedWidth(get_text_width(self.button, [self._text_true, self._text_false]))

    def _connect_signals(self) -> None:
        self.button.clicked.connect(lambda: self.set_state(not self._state))
