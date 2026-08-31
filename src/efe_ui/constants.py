from dataclasses import dataclass
from enum import Enum

CHANNEL_COUNT = 4

DIGIT_FONT_SIZE = 16
ARROW_FONT_SIZE = 8
TITLE_BAR_FONT_SIZE = 10


class VariableType(Enum):
    VOLTAGE_C = 1
    CURRENT_C = 2
    VOLTAGE_E = 3
    CURRENT_E = 4


@dataclass
class RowConfig:
    label: str
    unit: str
    minimum: float
    maximum: float
    digit_count_measure: int
    digit_count_set: int
    point_position_measure: int
    point_position_set: int
    readable: bool = True


VC_ROW = RowConfig(
    label="V<sub>C</sub>:",
    unit="V",
    minimum=-1200.0,
    maximum=-5,
    digit_count_measure=5,
    digit_count_set=4,
    point_position_measure=1,
    point_position_set=0,
)

VE_ROW = RowConfig(
    label="V<sub>E</sub>:",
    unit="V",
    minimum=-1200.0,
    maximum=-5,
    digit_count_measure=5,
    digit_count_set=4,
    point_position_measure=1,
    point_position_set=0,
)

IC_HIGH_ROW = RowConfig(
    label="I<sub>C</sub>:",
    unit="μA",
    minimum=-100.0,
    maximum=0,
    digit_count_measure=5,
    digit_count_set=4,
    point_position_measure=2,
    point_position_set=1,
)

IC_LOW_ROW = RowConfig(
    label="I<sub>C</sub>:",
    unit="μA",
    minimum=-1.0,
    maximum=0,
    digit_count_measure=5,
    digit_count_set=4,
    point_position_measure=4,
    point_position_set=3,
)

IE_HIGH_ROW = RowConfig(
    label="I<sub>E</sub>:",
    unit="μA",
    minimum=-100.0,
    maximum=0,
    digit_count_measure=5,
    digit_count_set=4,
    point_position_measure=2,
    point_position_set=1,
    readable=False,
)

IE_LOW_ROW = RowConfig(
    label="I<sub>E</sub>:",
    unit="μA",
    minimum=-1.0,
    maximum=0,
    digit_count_measure=5,
    digit_count_set=4,
    point_position_measure=4,
    point_position_set=3,
    readable=False,
)
