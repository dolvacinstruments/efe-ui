from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPaintEvent
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QStyle,
    QStyleOption,
    QVBoxLayout,
    QWidget,
)

from efe_ui.constants import BLUE, DIGIT_FONT_SIZE, ORANGE, TITLE_BAR_FONT_SIZE, VIOLET, YELLOW
from efe_ui.number_widget import NumberWidget

VOLTAGE_MIN_V = -1200
VOLTAGE_MAX_V = -5
VOLTAGE_DIGITS_MEASURE = 5
VOLTAGE_DIGITS_SET = 4
VOLTAGE_POINT_MEASURE = 1
VOLTAGE_POINT_SET = 0

CURRENT_HIGH_MAX = 100
CURRENT_HIGH_MIN = 0
CURRENT_HIGH_POINT_MEASURE = 2
CURRENT_HIGH_POINT_SET = 1
CURRENT_LOW_MAX = 10
CURRENT_LOW_MIN = 0
CURRENT_LOW_POINT_MEASURE = 3
CURRENT_LOW_POINT_SET = 2
CURRENT_DIGITS_MEASURE = 5
CURRENT_DIGITS_SET = 4


class ChannelWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.is_diode_mode = True
        self.is_high_range = True
        self.is_disabled = True

        self.setup_ui()
        self.connect_signals()

    def setup_ui(self) -> None:
        self.setObjectName("channel_widget")
        self.setStyleSheet("""
            #channel_widget {
                border: 1px solid palette(mid);
            }
        """)
        self.setContentsMargins(0, 0, 0, 0)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.add_title_bar(layout)
        self.add_numbers(layout)

    def add_title_bar(self, layout: QVBoxLayout) -> None:
        title_bar = QWidget(self)
        title_bar.setStyleSheet("""
            QWidget {
                background-color: palette(mid);
            }
        """)
        layout.addWidget(title_bar)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(0, 0, 0, 0)

        left_layout = QHBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(5)
        left_layout.setSizeConstraint(QHBoxLayout.SizeConstraint.SetMinimumSize)

        self.enable_button = TitleBarButton("🔴", "🟢", ORANGE, BLUE)
        left_layout.addWidget(self.enable_button)

        self.channel_label = self.create_title_bar_label("CH: 1.1")
        left_layout.addWidget(self.channel_label)

        title_layout.addLayout(left_layout)

        title_layout.addStretch()

        right_layout = QHBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(5)
        right_layout.setSizeConstraint(QHBoxLayout.SizeConstraint.SetMinimumSize)

        range_label = self.create_title_bar_label("R:")
        right_layout.addWidget(range_label)

        self.range_button = TitleBarButton("HIGH", "LOW", ORANGE, BLUE)
        right_layout.addWidget(self.range_button)

        mode_label = self.create_title_bar_label("M:")
        right_layout.addWidget(mode_label)

        self.mode_button = TitleBarButton("DIODE", "TRIODE", VIOLET, YELLOW)
        right_layout.addWidget(self.mode_button)

        title_layout.addLayout(right_layout)

    def create_title_bar_label(self, text: str) -> QLabel:
        label = QLabel(text, self)
        font = label.font()
        font.setPointSize(TITLE_BAR_FONT_SIZE)
        font.setBold(True)
        label.setFont(font)
        return label

    def add_numbers(self, layout: QVBoxLayout) -> None:
        widget = QWidget(self)
        layout.addWidget(widget)
        self.grid = QGridLayout()
        widget.setLayout(self.grid)

        self.grid.setSizeConstraint(QGridLayout.SizeConstraint.SetFixedSize)
        self.grid.setContentsMargins(10, 10, 10, 10)
        self.grid.setHorizontalSpacing(10)
        self.grid.setVerticalSpacing(0)

        measure_label = QLabel("Measure:", self)
        self.grid.addWidget(measure_label, 0, 1, alignment=Qt.AlignmentFlag.AlignCenter)
        set_label = QLabel("Set:", self)
        self.grid.addWidget(set_label, 0, 2, alignment=Qt.AlignmentFlag.AlignCenter)

        self.add_vc_row(self.grid)
        self.add_i_row(self.grid)

    def add_vc_row(self, grid: QGridLayout) -> None:
        self.vc_measure_widget = NumberWidget(
            digit_count=VOLTAGE_DIGITS_MEASURE,
            point_position=VOLTAGE_POINT_MEASURE,
            min_value=VOLTAGE_MIN_V,
            max_value=VOLTAGE_MAX_V,
            editable=False,
            parent=self,
        )
        self.vc_set_widget = NumberWidget(
            digit_count=VOLTAGE_DIGITS_SET,
            point_position=VOLTAGE_POINT_SET,
            min_value=VOLTAGE_MIN_V,
            max_value=VOLTAGE_MAX_V,
            editable=True,
            parent=self,
        )
        self.vc_set_widget.set_value(-5)
        self.add_row(grid, 1, self.vc_measure_widget, self.vc_set_widget, "V<sub>C</sub>:", "V")

    def add_i_row(self, grid: QGridLayout) -> None:
        if self.is_high_range:
            self.i_measure_widget = NumberWidget(
                digit_count=CURRENT_DIGITS_MEASURE,
                point_position=CURRENT_HIGH_POINT_MEASURE,
                min_value=CURRENT_HIGH_MIN,
                max_value=CURRENT_HIGH_MAX,
                editable=False,
                parent=self,
            )
            self.i_set_widget = NumberWidget(
                digit_count=CURRENT_DIGITS_SET,
                point_position=CURRENT_HIGH_POINT_SET,
                min_value=CURRENT_HIGH_MIN,
                max_value=CURRENT_HIGH_MAX,
                editable=True,
                parent=self,
            )
        else:
            self.i_measure_widget = NumberWidget(
                digit_count=CURRENT_DIGITS_MEASURE,
                point_position=CURRENT_LOW_POINT_MEASURE,
                min_value=CURRENT_LOW_MIN,
                max_value=CURRENT_LOW_MAX,
                editable=False,
                parent=self,
            )
            self.i_set_widget = NumberWidget(
                digit_count=CURRENT_DIGITS_SET,
                point_position=CURRENT_LOW_POINT_SET,
                min_value=CURRENT_LOW_MIN,
                max_value=CURRENT_LOW_MAX,
                editable=True,
                parent=self,
            )
        self.add_row(grid, 2, self.i_measure_widget, self.i_set_widget, "I:", "μA")

    def add_vce_row(self, grid: QGridLayout) -> None:
        self.vce_measure_widget = NumberWidget(
            digit_count=VOLTAGE_DIGITS_MEASURE,
            point_position=VOLTAGE_POINT_MEASURE,
            min_value=VOLTAGE_MIN_V,
            max_value=VOLTAGE_MAX_V,
            editable=False,
            parent=self,
        )
        self.vce_set_widget = NumberWidget(
            digit_count=VOLTAGE_DIGITS_SET,
            point_position=VOLTAGE_POINT_SET,
            min_value=VOLTAGE_MIN_V,
            max_value=VOLTAGE_MAX_V,
            editable=True,
            parent=self,
        )
        self.vce_set_widget.set_value(-5)
        self.add_row(grid, 3, self.vce_measure_widget, self.vce_set_widget, "V<sub>CE</sub>:", "V")

    def add_row(
        self, grid: QGridLayout, row: int, measure: NumberWidget, set: NumberWidget, label_text: str, unit: str
    ) -> None:
        label = QLabel(label_text, self)
        font = label.font()
        font.setPointSize(DIGIT_FONT_SIZE)
        label.setFont(font)
        label.setFixedWidth(_get_row_label_width())
        label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        unit_label = QLabel(unit, self)
        font = unit_label.font()
        font.setPointSize(DIGIT_FONT_SIZE)
        unit_label.setFont(font)
        unit_label.setFixedWidth(_get_row_unit_width())
        unit_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self.clean_row(grid, row)

        measure.set_disabled(self.is_disabled)

        grid.addWidget(label, row, 0, alignment=Qt.AlignmentFlag.AlignRight)
        grid.addWidget(measure, row, 1, alignment=Qt.AlignmentFlag.AlignRight)
        grid.addWidget(set, row, 2, alignment=Qt.AlignmentFlag.AlignRight)
        grid.addWidget(unit_label, row, 3, alignment=Qt.AlignmentFlag.AlignLeft)

    def clean_row(self, grid: QGridLayout, row: int) -> None:
        for i in range(4):
            item = grid.itemAtPosition(row, i)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    grid.removeWidget(widget)
                    widget.deleteLater()

    def connect_signals(self) -> None:
        self.enable_button.clicked.connect(self.toggle_enable)
        self.range_button.clicked.connect(self.toggle_range)
        self.mode_button.clicked.connect(self.toggle_mode)

    def toggle_enable(self) -> None:
        self.is_disabled = not self.is_disabled
        self.enable_button.set_state(self.is_disabled)
        self.vc_measure_widget.set_disabled(self.is_disabled)
        self.i_measure_widget.set_disabled(self.is_disabled)
        if hasattr(self, "vce_measure_widget") and self.vce_measure_widget is not None:
            self.vce_measure_widget.set_disabled(self.is_disabled)

    def toggle_range(self) -> None:
        self.is_high_range = not self.is_high_range
        self.range_button.set_state(self.is_high_range)
        self.add_i_row(self.grid)

    def toggle_mode(self) -> None:
        self.is_diode_mode = not self.is_diode_mode
        self.mode_button.set_state(self.is_diode_mode)
        if self.is_diode_mode:
            self.clean_row(self.grid, 3)
            self.vce_measure_widget = None
            self.vce_set_widget = None
        else:
            self.add_vce_row(self.grid)

    def paintEvent(self, event: QPaintEvent) -> None:
        opt = QStyleOption()
        opt.initFrom(self)

        painter = QPainter(self)
        self.style().drawPrimitive(QStyle.PrimitiveElement.PE_Widget, opt, painter, self)

        super().paintEvent(event)


class TitleBarButton(QPushButton):
    def __init__(self, text: str, alt_text: str, color: str, alt_color: str, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self._standard_text = text
        self._alt_text = alt_text
        self._color = color
        self._alt_color = alt_color

        self._state = True

        self.setFlat(True)
        self.set_style()
        font = self.font()
        font.setPointSize(TITLE_BAR_FONT_SIZE)
        self.setFont(font)
        metrics = self.fontMetrics()
        width = max(metrics.horizontalAdvance(text), metrics.horizontalAdvance(alt_text)) + 10
        self.setFixedWidth(width)

    def set_style(self) -> None:
        color = self._color if self._state else self._alt_color

        self.setStyleSheet(f"""
            QPushButton {{
                color: {color};
                font-weight: bold;
                padding-left: 0px;
                padding-right: 0px;
                margin: 0px;
            }}
            QPushButton:hover {{
                    color: palette(midlight);
            }}
        """)

    def set_state(self, state: bool) -> None:
        self._state = state
        self.setText(self._standard_text if state else self._alt_text)
        self.set_style()


ROW_LABEL_WIDTH: int | None = None


def _get_row_label_width() -> int:
    global ROW_LABEL_WIDTH
    if ROW_LABEL_WIDTH is None:
        label = QLabel("V<sub>CE</sub>:")
        font = label.font()
        font.setPointSize(DIGIT_FONT_SIZE)
        label.setFont(font)
        ROW_LABEL_WIDTH = label.sizeHint().width()
    return ROW_LABEL_WIDTH


ROW_UNIT_WIDTH: int | None = None


def _get_row_unit_width() -> int:
    global ROW_UNIT_WIDTH
    if ROW_UNIT_WIDTH is None:
        label = QLabel("μA")
        font = label.font()
        font.setPointSize(DIGIT_FONT_SIZE)
        label.setFont(font)
        metrics = label.fontMetrics()
        width = metrics.horizontalAdvance(label.text())
        ROW_UNIT_WIDTH = width
    return ROW_UNIT_WIDTH
