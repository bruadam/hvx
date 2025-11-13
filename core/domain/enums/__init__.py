"""Domain enumerations."""

from core.domain.enums.aggregation_method import (
    AggregationStrategy,
    ParameterAggregationMethod,
    SpatialAggregationMethod,
)
from core.domain.enums.building_type import BuildingType
from core.domain.enums.building_type_config import (
    BuildingTypeConfig,
    BuildingTypeConfigLoader,
    building_type_config_loader,
)
from core.domain.enums.en16798_category import EN16798Category
from core.domain.enums.measurement_type import MeasurementType
from core.domain.enums.occupancy import ActivityLevel, OccupancyDensity
from core.domain.enums.parameter_type import ParameterType
from core.domain.enums.pollution_level import PollutionLevel
from core.domain.enums.room_type import RoomType
from core.domain.enums.standard_type import StandardType
from core.domain.enums.status import Status
from core.domain.enums.tail_category import TAILCategory
from core.domain.enums.tail_config import (
    ParameterThreshold,
    TAILConfig,
    TAILConfigLoader,
    TAILParameterConfig,
    tail_config_loader,
)
from core.domain.enums.ventilation import VentilationType

__all__ = [
    "ParameterType",
    "StandardType",
    "Status",
    "BuildingType",
    "BuildingTypeConfig",
    "BuildingTypeConfigLoader",
    "building_type_config_loader",
    "MeasurementType",
    "TAILCategory",
    "RoomType",
    "TAILConfig",
    "TAILParameterConfig",
    "ParameterThreshold",
    "TAILConfigLoader",
    "tail_config_loader",
    "ParameterAggregationMethod",
    "SpatialAggregationMethod",
    "AggregationStrategy",
    "VentilationType",
    "EN16798Category",
    "PollutionLevel",
    "ActivityLevel",
    "OccupancyDensity",
]
