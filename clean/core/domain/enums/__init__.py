"""Domain enumerations."""

from core.domain.enums.parameter_type import ParameterType
from core.domain.enums.standard_type import StandardType
from core.domain.enums.status import Status
from core.domain.enums.building_type import BuildingType
from core.domain.enums.measurement_type import MeasurementType
from core.domain.enums.tail_category import TAILCategory
from core.domain.enums.room_type import RoomType
from core.domain.enums.tail_config import (
    TAILConfig,
    TAILParameterConfig,
    ParameterThreshold,
    TAILConfigLoader,
    tail_config_loader,
)

__all__ = [
    "ParameterType",
    "StandardType",
    "Status",
    "BuildingType",
    "MeasurementType",
    "TAILCategory",
    "RoomType",
    "TAILConfig",
    "TAILParameterConfig",
    "ParameterThreshold",
    "TAILConfigLoader",
    "tail_config_loader",
]
