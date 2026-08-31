from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLayout, QPushButton, QSizePolicy, QWidget

from efe_ui.constants import TITLE_BAR_FONT_SIZE
from efe_ui.ui_helpers import get_text_width, set_font


class CircleWidget(QWidget):
    def __init__(self, diameter: int, color: QColor, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._diameter = diameter
        self._color = color
        self.setFixedSize(diameter, diameter)

    def set_color(self, color: QColor) -> None:
        self._color = color
        self.update()

    def paintEvent(self, _: QEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(self._color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, self._diameter, self._diameter)


class SquareWidget(QWidget):
    def __init__(self, size: int, color: QColor, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._size = size
        self._color = color
        self.setFixedSize(size, size)

    def set_color(self, color: QColor) -> None:
        self._color = color
        self.update()

    def paintEvent(self, _: QEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(self._color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(0, 0, self._size, self._size)


class TitleBarSwitch(QWidget):
    state_changed = Signal(bool)

    def __init__(
        self,
        label: str,
        text_true: str,
        text_false: str,
        color_true: QColor,
        color_false: QColor,
        use_square: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._label = label
        self._text_true = text_true
        self._text_false = text_false
        self._color_true = color_true
        self._color_false = color_false
        self._use_square = use_square

        self._state = True

        self._setup_ui()
        self._connect_signals()
        self.set_state(self._state)

    def set_state(self, state: bool) -> None:
        self._state = state
        self.clickable_label.setText(self._text_true if state else self._text_false)
        self.indicator.set_color(self._color_true if state else self._color_false)
        self.state_changed.emit(state)

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        self.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)

        self._add_label(layout)
        self._add_button(layout)

    def _add_label(self, layout: QHBoxLayout) -> None:
        if not self._label:
            return
        label = QLabel(self._label, self)
        layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        set_font(label, TITLE_BAR_FONT_SIZE)
        label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

    def _add_button(self, layout: QHBoxLayout) -> None:
        self.button = QPushButton()
        layout.addWidget(self.button, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.button.setFlat(True)
        # self.button.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.button.setStyleSheet("""
            QPushButton {
                padding: 0px;
                margin: 0px;
                border-radius: 0px;
            }
            QPushButton:hover {
                background-color: palette(midlight);
            }
            QLabel {
                background-color: transparent;
            }
            """)
        blayout = QHBoxLayout(self.button)
        blayout.setContentsMargins(2, 0, 2, 0)
        blayout.setSpacing(4)
        blayout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)

        self.clickable_label = QLabel(self._text_true if self._state else self._text_false, self.button)
        font = self.clickable_label.font()
        font.setBold(True)
        font.setPointSize(TITLE_BAR_FONT_SIZE)
        self.clickable_label.setFont(font)
        label_width = get_text_width(self.clickable_label, [self._text_true, self._text_false])
        self.clickable_label.setFixedWidth(label_width)
        self.clickable_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        blayout.addWidget(self.clickable_label, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        indicator_size = 12
        if self._use_square:
            self.indicator = SquareWidget(
                indicator_size, self._color_true if self._state else self._color_false, self.button
            )
        else:
            self.indicator = CircleWidget(
                indicator_size, self._color_true if self._state else self._color_false, self.button
            )
        self.indicator.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        blayout.addWidget(self.indicator, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        total_width = (
            label_width
            + indicator_size
            + blayout.spacing()
            + blayout.contentsMargins().left()
            + blayout.contentsMargins().right()
        )
        self.button.setFixedWidth(total_width)

    def _connect_signals(self) -> None:
        self.button.clicked.connect(lambda: self.set_state(not self._state))
