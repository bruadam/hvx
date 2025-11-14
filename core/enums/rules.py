"""
Rule and standard-related enums.
"""

from enum import Enum


class RuleOperator(str, Enum):
    LT = "<"
    LE = "<="
    GT = ">"
    GE = ">="
    BETWEEN = "between"
    OUTSIDE_RANGE = "outside_range"
    EQ = "=="
    NE = "!="


class Season(str, Enum):
    SUMMER = "summer"
    WINTER = "winter"
    TRANSITION = "transition"
    ALL_YEAR = "all_year"


class StandardType(str, Enum):
    EN16798 = "EN16798"
    TAIL = "TAIL"
    ASHRAE55 = "ASHRAE55"
    INTERNAL = "internal"


class DynamicFunctionType(str, Enum):
    RUNNING_MEAN_TEMP = "running_mean_temperature"
    ADAPTIVE_COMFORT = "adaptive_comfort"


__all__ = [
    "RuleOperator",
    "Season",
    "StandardType",
    "DynamicFunctionType",
]
