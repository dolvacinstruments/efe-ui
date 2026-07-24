import copy
from functools import partial

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from efe_ui.constants import (
    DIGIT_FONT_SIZE,
    IC_HIGH_ROW,
    IC_LOW_ROW,
    IE_HIGH_ROW,
    IE_LOW_ROW,
    VC_ROW,
    VE_ROW,
    RowConfig,
    VariableType,
)
from efe_ui.number_widget import NumberWidget
from efe_ui.title_bar_switch import TitleBarSwitch
from efe_ui.ui_helpers import create_title_bar_label


class ChannelWidget(QWidget):
    is_disabled_changed = Signal(bool)
    is_diode_mode_changed = Signal(bool)
    is_high_range_changed = Signal(bool)
    value_changed = Signal(VariableType, float)

    def __init__(
        self,
        channel_name: str,
        write_only: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._is_diode_mode = True
        self._is_high_range = True
        self._is_disabled = True
        self._is_write_only = write_only

        self._channel_name = channel_name

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
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
        self._add_title_bar(layout)
        self._add_numbers(layout)

    def _add_title_bar(self, layout: QVBoxLayout) -> None:
        title_bar = QWidget(self)
        layout.addWidget(title_bar, alignment=Qt.AlignmentFlag.AlignTop)
        title_bar.setStyleSheet("""
            QWidget {
                background-color: palette(mid);
            }
        """)
        title_bar.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        title_layout = QHBoxLayout(title_bar)
        title_bar.setLayout(title_layout)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(5)

        self.enable_switch = TitleBarSwitch("", "OFF 🔴", "ON 🟢")
        title_layout.addWidget(self.enable_switch)

        self.channel_label = create_title_bar_label(self._channel_name)
        title_layout.addWidget(self.channel_label)

        title_layout.addStretch()

        self.range_switch = TitleBarSwitch("Range:", "H 🟧", "L 🟦")
        title_layout.addWidget(self.range_switch)

        self.mode_switch = TitleBarSwitch("Mode:", "D 🟪", "T 🟨")
        title_layout.addWidget(self.mode_switch)

    def _add_numbers(self, layout: QVBoxLayout) -> None:
        self.grid = QGridLayout()
        layout.addLayout(self.grid)

        self.grid.setSizeConstraint(QGridLayout.SizeConstraint.SetFixedSize)
        self.grid.setContentsMargins(10, 0, 10, 10)
        self.grid.setHorizontalSpacing(10)
        self.grid.setVerticalSpacing(0)

        if not self._is_write_only:
            measure_label = QLabel("Measure:", self)
            self.grid.addWidget(measure_label, 0, 1, alignment=Qt.AlignmentFlag.AlignCenter)

        set_label = QLabel("Set:", self)
        self.grid.addWidget(set_label, 0, 2, alignment=Qt.AlignmentFlag.AlignCenter)

        self.vc_measure_widget, self.vc_set_widget = self._add_row(
            self.grid, 1, self._modify_row_config(VC_ROW, self._is_write_only)
        )
        self.ic_measure_widget, self.ic_set_widget = self._add_row(
            self.grid, 2, self._modify_row_config(IC_HIGH_ROW, self._is_write_only)
        )
        self.ve_measure_widget, self.ve_set_widget = self._add_row(
            self.grid, 3, self._modify_row_config(VE_ROW, self._is_write_only)
        )
        self.ie_measure_widget, self.ie_set_widget = self._add_row(
            self.grid, 4, self._modify_row_config(IE_HIGH_ROW, self._is_write_only)
        )

        self.set_row_hide(3, True, False)
        self.set_row_hide(4, True, False)

    def _modify_row_config(self, config: RowConfig, write_only: bool) -> RowConfig:
        if write_only:
            modified_config = copy.copy(config)
            modified_config.readable = False
            return modified_config
        return config

    def _add_row(self, grid: QGridLayout, row: int, config: RowConfig) -> tuple[NumberWidget, NumberWidget]:
        label = QLabel(config.label, self)
        font = label.font()
        font.setPointSize(DIGIT_FONT_SIZE)
        label.setFont(font)
        label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        grid.addWidget(label, row, 0, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        measure_widget = NumberWidget(
            None, config.digit_count_measure, config.point_position_measure, -float("inf"), float("inf"), False, self
        )
        measure_widget.set_editable(False)
        if not config.readable:
            measure_widget.hide()
        grid.addWidget(measure_widget, row, 1, alignment=Qt.AlignmentFlag.AlignRight)

        set_widget = NumberWidget(
            None, config.digit_count_set, config.point_position_set, config.minimum, config.maximum, True, self
        )
        set_widget.set_editable(True)
        set_widget.set_value(0)
        grid.addWidget(set_widget, row, 2, alignment=Qt.AlignmentFlag.AlignRight)

        unit_label = QLabel(config.unit, self)
        font = unit_label.font()
        font.setPointSize(DIGIT_FONT_SIZE)
        unit_label.setFont(font)
        unit_label.setFixedWidth(_get_row_unit_width())
        unit_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        grid.addWidget(unit_label, row, 3, alignment=Qt.AlignmentFlag.AlignLeft)

        return measure_widget, set_widget

    def _connect_signals(self) -> None:
        self.enable_switch.state_changed.connect(self._change_is_disabled)
        self.range_switch.state_changed.connect(self._change_is_high_range)
        self.mode_switch.state_changed.connect(self._change_is_diode_mode)

        self.vc_set_widget.number_changed.connect(partial(self.value_changed.emit, VariableType.VOLTAGE_C))
        self.ic_set_widget.number_changed.connect(partial(self.value_changed.emit, VariableType.CURRENT_C))
        self.ve_set_widget.number_changed.connect(partial(self.value_changed.emit, VariableType.VOLTAGE_E))
        self.ie_set_widget.number_changed.connect(partial(self.value_changed.emit, VariableType.CURRENT_E))

    def _change_is_disabled(self, state: bool) -> None:
        self._is_disabled = state
        if self._is_disabled:
            self.vc_measure_widget.set_value(None)
            self.ic_measure_widget.set_value(None)
            self.ve_measure_widget.set_value(None)
            self.ie_measure_widget.set_value(None)
        self.is_disabled_changed.emit(state)

    def _change_is_high_range(self, state: bool) -> None:
        self._is_high_range = state
        if self._is_high_range:
            self.ic_measure_widget.set_point_position(IC_HIGH_ROW.point_position_measure)
            self.ic_set_widget.set_point_position(IC_HIGH_ROW.point_position_set)
            self.ie_measure_widget.set_point_position(IE_HIGH_ROW.point_position_measure)
            self.ie_set_widget.set_point_position(IE_HIGH_ROW.point_position_set)

            self.ic_measure_widget.set_min_max(IC_HIGH_ROW.minimum, IC_HIGH_ROW.maximum)
            self.ic_set_widget.set_min_max(IC_HIGH_ROW.minimum, IC_HIGH_ROW.maximum)
            self.ie_measure_widget.set_min_max(IE_HIGH_ROW.minimum, IE_HIGH_ROW.maximum)
            self.ie_set_widget.set_min_max(IE_HIGH_ROW.minimum, IE_HIGH_ROW.maximum)
        else:
            self.ic_measure_widget.set_point_position(IC_LOW_ROW.point_position_measure)
            self.ic_set_widget.set_point_position(IC_LOW_ROW.point_position_set)
            self.ie_measure_widget.set_point_position(IE_LOW_ROW.point_position_measure)
            self.ie_set_widget.set_point_position(IE_LOW_ROW.point_position_set)

            self.ic_measure_widget.set_min_max(IC_LOW_ROW.minimum, IC_LOW_ROW.maximum)
            self.ic_set_widget.set_min_max(IC_LOW_ROW.minimum, IC_LOW_ROW.maximum)
            self.ie_measure_widget.set_min_max(IE_LOW_ROW.minimum, IE_LOW_ROW.maximum)
            self.ie_set_widget.set_min_max(IE_LOW_ROW.minimum, IE_LOW_ROW.maximum)
        self.is_high_range_changed.emit(state)

    def _change_is_diode_mode(self, state: bool) -> None:
        self._is_diode_mode = state
        self.set_row_hide(3, self._is_diode_mode, self._is_write_only)
        self.set_row_hide(4, self._is_diode_mode, True)

        self.is_diode_mode_changed.emit(self._is_diode_mode)

    def set_row_hide(self, row: int, hide: bool, skip_measure_row: bool = False) -> None:
        for col in range(4):
            if skip_measure_row and col == 1:
                continue
            item = self.grid.itemAtPosition(row, col)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    widget.setVisible(not hide)

    def set_measure_value(self, variable_type: VariableType, value: float | None) -> None:
        if variable_type == VariableType.VOLTAGE_C:
            self.vc_measure_widget.set_value(value)
        elif variable_type == VariableType.CURRENT_C:
            self.ic_measure_widget.set_value(value)
        elif variable_type == VariableType.VOLTAGE_E:
            self.ve_measure_widget.set_value(value)

    def set_set_value(self, variable_type: VariableType, value: float) -> None:
        if variable_type == VariableType.VOLTAGE_C:
            print(f"Setting VC value to {value}")
            self.vc_set_widget.set_value(value)
        elif variable_type == VariableType.CURRENT_C:
            self.ic_set_widget.set_value(value)
        elif variable_type == VariableType.VOLTAGE_E:
            self.ve_set_widget.set_value(value)
        elif variable_type == VariableType.CURRENT_E:
            self.ie_set_widget.set_value(value)

    def set_is_disabled(self, is_disabled: bool) -> None:
        self.enable_switch.set_state(is_disabled)

    def set_is_diode_mode(self, is_diode_mode: bool) -> None:
        self.mode_switch.set_state(is_diode_mode)

    def set_is_high_range(self, is_high_range: bool) -> None:
        self.range_switch.set_state(is_high_range)

    def is_disabled(self) -> bool:
        return self._is_disabled


ROW_LABEL_WIDTH: int | None = None


def _get_row_label_width() -> int:
    global ROW_LABEL_WIDTH
    if ROW_LABEL_WIDTH is None:
        label = QLabel("V<sub>C</sub>:")
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
