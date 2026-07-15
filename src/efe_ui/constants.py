from dataclasses import dataclass
from enum import Enum

CHANNEL_COUNT = 4

DIGIT_FONT_SIZE = 16
ARROW_FONT_SIZE = 8
TITLE_BAR_FONT_SIZE = 10


class VariableType(Enum):
    VOLTAGE_C = 1
    CURRENT = 2
    VOLTAGE_CE = 3
    CURRENT_C = 4


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
    maximum=-5.0,
    digit_count_measure=5,
    digit_count_set=4,
    point_position_measure=1,
    point_position_set=0,
)

I_HIGH_ROW = RowConfig(
    label="I:",
    unit="μA",
    minimum=0.0,
    maximum=100.0,
    digit_count_measure=5,
    digit_count_set=4,
    point_position_measure=2,
    point_position_set=1,
)

I_LOW_ROW = RowConfig(
    label="I:",
    unit="μA",
    minimum=0.0,
    maximum=10.0,
    digit_count_measure=5,
    digit_count_set=4,
    point_position_measure=3,
    point_position_set=2,
)

VCE_ROW = RowConfig(
    label="V<sub>E</sub>:",
    unit="V",
    minimum=-1200.0,
    maximum=-5.0,
    digit_count_measure=5,
    digit_count_set=4,
    point_position_measure=1,
    point_position_set=0,
)

I_C_HIGH_ROW = RowConfig(
    label="I<sub>C</sub>:",
    unit="μA",
    minimum=0.0,
    maximum=100.0,
    digit_count_measure=5,
    digit_count_set=4,
    point_position_measure=2,
    point_position_set=1,
    readable=False,
)

I_C_LOW_ROW = RowConfig(
    label="I<sub>C</sub>:",
    unit="μA",
    minimum=0.0,
    maximum=10.0,
    digit_count_measure=5,
    digit_count_set=4,
    point_position_measure=3,
    point_position_set=2,
    readable=False,
)
