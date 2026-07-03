from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QPainter, QPaintEvent
from PySide6.QtWidgets import (
    QApplication,
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

from efe_ui.constants import (
    DIGIT_FONT_SIZE,
    I_C_HIGH_ROW,
    I_C_LOW_ROW,
    I_HIGH_ROW,
    I_LOW_ROW,
    TITLE_BAR_FONT_SIZE,
    VC_ROW,
    VCE_ROW,
    RowConfig,
    VariableType,
)
from efe_ui.number_widget import NumberChangedEvent, NumberWidget
from efe_ui.ui_helpers import create_title_bar_label


class ChannelWidget(QWidget):
    def __init__(
        self, parent: QWidget | None = None, channel_number: int | None = None, device_name: str | None = None
    ) -> None:
        super().__init__(parent)

        self._is_diode_mode = True
        self._is_high_range = True
        self._is_disabled = True

        self._channel_number = channel_number
        self._device_name = device_name

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
        title_bar.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        layout.addWidget(title_bar)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSizeConstraint(QHBoxLayout.SizeConstraint.SetMinimumSize)
        self.enable_button = TitleBarButton("🔴", "🟢")
        title_layout.addWidget(self.enable_button)
        self.channel_label = create_title_bar_label(
            "Global"
            if self._channel_number is None or self._device_name is None
            else f"CH: {self._device_name}.{self._channel_number + 1}"
        )
        title_layout.addWidget(self.channel_label)

        title_layout.addStretch()

        range_layout = QHBoxLayout()
        range_layout.setContentsMargins(0, 0, 0, 0)
        range_layout.setSpacing(1)
        range_layout.setSizeConstraint(QHBoxLayout.SizeConstraint.SetMinimumSize)
        title_layout.addLayout(range_layout)

        range_label = create_title_bar_label("Range:", bold=False)
        range_layout.addWidget(range_label)

        self.range_button = TitleBarButton("H 🟧", "L 🟦")
        range_layout.addWidget(self.range_button)

        mode_layout = QHBoxLayout()
        mode_layout.setContentsMargins(0, 0, 0, 0)
        mode_layout.setSpacing(1)
        mode_layout.setSizeConstraint(QHBoxLayout.SizeConstraint.SetMinimumSize)
        title_layout.addLayout(mode_layout)

        mode_label = create_title_bar_label("Mode:", bold=False)
        mode_layout.addWidget(mode_label)

        self.mode_button = TitleBarButton("D 🟪", "T 🟨")
        mode_layout.addWidget(self.mode_button)

    def add_numbers(self, layout: QVBoxLayout) -> None:
        self.grid = QGridLayout()
        layout.addLayout(self.grid)

        self.grid.setSizeConstraint(QGridLayout.SizeConstraint.SetFixedSize)
        self.grid.setContentsMargins(10, 0, 10, 10)
        self.grid.setHorizontalSpacing(10)
        self.grid.setVerticalSpacing(0)

        if self._channel_number is not None:
            measure_label = QLabel("Measure:", self)
            self.grid.addWidget(measure_label, 0, 1, alignment=Qt.AlignmentFlag.AlignCenter)
        set_label = QLabel("Set:", self)
        self.grid.addWidget(
            set_label, 0, 2 if self._channel_number is not None else 1, alignment=Qt.AlignmentFlag.AlignCenter
        )

        self.vc_measure_widget, self.vc_set_widget = self.add_row(self.grid, 1, VC_ROW)
        self.i_measure_widget, self.i_set_widget = self.add_row(self.grid, 2, I_HIGH_ROW)

    def add_row(self, grid: QGridLayout, row: int, config: RowConfig) -> tuple[NumberWidget | None, NumberWidget]:
        self.clean_row(grid, row)

        label = QLabel(config.label, self)
        font = label.font()
        font.setPointSize(DIGIT_FONT_SIZE)
        label.setFont(font)
        label.setFixedWidth(_get_row_label_width())
        label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        grid.addWidget(label, row, 0, alignment=Qt.AlignmentFlag.AlignRight)

        if config.readable and self._channel_number is not None:
            measure_widget = NumberWidget(
                config.digit_count_measure, config.point_position_measure, config.minimum, config.maximum, False, self
            )
            measure_widget.set_disabled(self._is_disabled)
            grid.addWidget(measure_widget, row, 1, alignment=Qt.AlignmentFlag.AlignRight)
        else:
            measure_widget = None

        set_widget = NumberWidget(
            config.digit_count_set, config.point_position_set, config.minimum, config.maximum, True, self
        )
        grid.addWidget(
            set_widget, row, 2 if self._channel_number is not None else 1, alignment=Qt.AlignmentFlag.AlignRight
        )

        unit_label = QLabel(config.unit, self)
        font = unit_label.font()
        font.setPointSize(DIGIT_FONT_SIZE)
        unit_label.setFont(font)
        unit_label.setFixedWidth(_get_row_unit_width())
        unit_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        grid.addWidget(
            unit_label, row, 3 if self._channel_number is not None else 2, alignment=Qt.AlignmentFlag.AlignLeft
        )

        return measure_widget, set_widget

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
        self._is_disabled = not self._is_disabled
        print(f"ChannelWidget: toggle_enable: {self._is_disabled}")
        self.enable_button.set_state(self._is_disabled)
        if self.vc_measure_widget is not None:
            self.vc_measure_widget.set_disabled(self._is_disabled)
        else:
            print("ChannelWidget: toggle_enable: vc_measure_widget is None")
        if self.i_measure_widget is not None:
            self.i_measure_widget.set_disabled(self._is_disabled)
        else:
            print("ChannelWidget: toggle_enable: i_measure_widget is None")
        if hasattr(self, "vce_measure_widget") and self.vce_measure_widget is not None:
            self.vce_measure_widget.set_disabled(self._is_disabled)
        else:
            print("ChannelWidget: toggle_enable: vce_measure_widget is None")
        if hasattr(self, "i_c_measure_widget") and self.i_c_measure_widget is not None:
            self.i_c_measure_widget.set_disabled(self._is_disabled)
        else:
            print("ChannelWidget: toggle_enable: i_c_measure_widget is None")

        event = ChannelEnableEvent(
            not self._is_disabled, self._channel_number if self._channel_number is not None else 0
        )
        if (parent := self.parent()) is not None:
            QApplication.postEvent(parent, event)

    def toggle_range(self) -> None:
        self._is_high_range = not self._is_high_range
        self.range_button.set_state(self._is_high_range)
        value = self.i_set_widget.get_value()
        m, s = self.add_row(self.grid, 2, I_HIGH_ROW if self._is_high_range else I_LOW_ROW)
        self.i_measure_widget, self.i_set_widget = self.add_row(
            self.grid, 2, I_HIGH_ROW if self._is_high_range else I_LOW_ROW
        )
        if not self._is_diode_mode:
            self.i_c_measure_widget, self.i_c_set_widget = self.add_row(
                self.grid, 4, I_C_HIGH_ROW if self._is_high_range else I_C_LOW_ROW
            )

        if (parent := self.parent()) is not None:
            event = ChannelRangeEvent(
                self._is_high_range, self._channel_number if self._channel_number is not None else 0
            )
            QApplication.postEvent(parent, event)
        self.i_set_widget.set_value(value)

    def toggle_mode(self) -> None:
        self._is_diode_mode = not self._is_diode_mode
        self.mode_button.set_state(self._is_diode_mode)
        if self._is_diode_mode:
            self.clean_row(self.grid, 3)
            self.clean_row(self.grid, 4)
            self.vce_measure_widget = None
            self.vce_set_widget = None
            self.i_c_measure_widget = None
            self.i_c_set_widget = None
            self.updateGeometry()
        else:
            self.vce_measure_widget, self.vce_set_widget = self.add_row(self.grid, 3, VCE_ROW)

            self.i_c_measure_widget, self.i_c_set_widget = self.add_row(
                self.grid, 4, I_C_HIGH_ROW if self._is_high_range else I_C_LOW_ROW
            )
            self.updateGeometry()
            event = ChannelModeEvent(
                self._is_diode_mode, self._channel_number if self._channel_number is not None else 0
            )
            if (parent := self.parent()) is not None:
                QApplication.postEvent(parent, event)

        event = ChannelModeEvent(self._is_diode_mode, self._channel_number if self._channel_number is not None else 0)
        if (parent := self.parent()) is not None:
            QApplication.postEvent(parent, event)

    def set_channel_number(self, channel_number: str) -> None:
        self.channel_label.setText(f"CH: {channel_number}")

    def paintEvent(self, event: QPaintEvent) -> None:
        opt = QStyleOption()
        opt.initFrom(self)

        painter = QPainter(self)
        self.style().drawPrimitive(QStyle.PrimitiveElement.PE_Widget, opt, painter, self)

        super().paintEvent(event)

    def set_variable(self, variable_type: VariableType, value: float) -> None:
        if variable_type == VariableType.VOLTAGE_C and self.vc_measure_widget is not None:
            self.vc_measure_widget.set_value(value)
        elif variable_type == VariableType.CURRENT and self.i_measure_widget is not None:
            self.i_measure_widget.set_value(value)
        elif variable_type == VariableType.VOLTAGE_CE and self.vce_measure_widget is not None:
            self.vce_measure_widget.set_value(value)
        elif variable_type == VariableType.CURRENT_C and self.i_c_measure_widget is not None:
            self.i_c_measure_widget.set_value(value)

    def customEvent(self, event: QEvent) -> None:
        if isinstance(event, NumberChangedEvent):
            event_type: VariableType | None = None
            if event.source == self.vc_set_widget:
                event_type = VariableType.VOLTAGE_C
            elif event.source == self.i_set_widget:
                event_type = VariableType.CURRENT
            elif hasattr(self, "vce_set_widget") and event.source == self.vce_set_widget:
                event_type = VariableType.VOLTAGE_CE
            elif hasattr(self, "i_c_set_widget") and event.source == self.i_c_set_widget:
                event_type = VariableType.CURRENT_C
            if event_type is not None and (parent := self.parent()) is not None:
                event = ChannelVariableEvent(
                    event_type, event.value, self._channel_number if self._channel_number is not None else 0
                )
                QApplication.postEvent(parent, event)
        else:
            super().customEvent(event)


class ChannelVariableEvent(QEvent):
    EVENT_TYPE = QEvent.Type(QEvent.registerEventType())

    def __init__(self, variable_type: VariableType, value: float, channel: int) -> None:
        super().__init__(self.EVENT_TYPE)
        self.variable_type = variable_type
        self.value = value
        self.channel = channel


class ChannelEnableEvent(QEvent):
    EVENT_TYPE = QEvent.Type(QEvent.registerEventType())

    def __init__(self, is_enabled: bool, channel: int) -> None:
        super().__init__(self.EVENT_TYPE)
        self.is_enabled = is_enabled
        self.channel = channel


class ChannelRangeEvent(QEvent):
    EVENT_TYPE = QEvent.Type(QEvent.registerEventType())

    def __init__(self, is_high_range: bool, channel: int) -> None:
        super().__init__(self.EVENT_TYPE)
        self.is_high_range = is_high_range
        self.channel = channel


class ChannelModeEvent(QEvent):
    EVENT_TYPE = QEvent.Type(QEvent.registerEventType())

    def __init__(self, is_diode_mode: bool, channel: int) -> None:
        super().__init__(self.EVENT_TYPE)
        self.is_diode_mode = is_diode_mode
        self.channel = channel


class TitleBarButton(QPushButton):
    def __init__(self, text: str, alt_text: str, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self._standard_text = text
        self._alt_text = alt_text

        self._state = True

        self.setFlat(True)
        self.setStyleSheet("""
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
        font = self.font()
        font.setPointSize(TITLE_BAR_FONT_SIZE)
        self.setFont(font)
        metrics = self.fontMetrics()
        width = max(metrics.horizontalAdvance(text), metrics.horizontalAdvance(alt_text)) + 5
        self.setFixedWidth(width)

    def set_state(self, state: bool) -> None:
        self._state = state
        self.setText(self._standard_text if state else self._alt_text)


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
