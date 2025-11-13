"""
Enumeration Types

All enum types used throughout the refactored service.
"""

from enum import Enum


class SpatialEntityType(str, Enum):
    PORTFOLIO = "portfolio"
    BUILDING = "building"
    FLOOR = "floor"
    ROOM = "room"
    ZONE = "zone"


class VentilationType(str, Enum):
    NATURAL = "natural"
    MECHANICAL = "mechanical"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class MetricType(str, Enum):
    TEMPERATURE = "temperature"
    CO2 = "co2"
    HUMIDITY = "humidity"
    ILLUMINANCE = "illuminance"
    NOISE = "noise"
    ENERGY = "energy"
    POWER = "power"
    WATER = "water"
    CLIMATE_TEMP = "climate_temperature"
    CLIMATE_HUMIDITY = "climate_humidity"
    OTHER = "other"


class TimeSeriesType(str, Enum):
    MEASURED = "measured"
    SIMULATED = "simulated"
    DERIVED = "derived"
    CLIMATE = "climate"


class PointType(str, Enum):
    SENSOR = "sensor"
    METER = "meter"
    SIMULATED_POINT = "simulated_point"
    DERIVED_POINT = "derived_point"
    WEATHER_STATION = "weather_station"


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


class AggregatorType(str, Enum):
    WORST = "worst"
    BEST = "best"
    AVERAGE = "average"
    WEIGHTED_AVERAGE = "weighted_average"
    MULTI_PROPERTY_WEIGHTED = "multi_property_weighted"


class DynamicFunctionType(str, Enum):
    RUNNING_MEAN_TEMP = "running_mean_temperature"
    ADAPTIVE_COMFORT = "adaptive_comfort"


class AnalysisStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisType(str, Enum):
    TEST_RESULT = "test_result"
    COMPLIANCE = "compliance"
    AGGREGATED = "aggregated"
    FORECAST = "forecast"
    ENERGY_SIGNATURE = "energy_signature"
    SIMULATION_RUN = "simulation_run"
    OTHER = "other"


class ModelType(str, Enum):
    ENERGY_MODEL = "energy_model"
    COMFORT_MODEL = "comfort_model"
    CLIMATE_MODEL = "climate_model"
    FORECAST_MODEL = "forecast_model"
    DATA_DRIVEN_MODEL = "data_driven_model"


__all__ = [
    "SpatialEntityType",
    "VentilationType",
    "MetricType",
    "TimeSeriesType",
    "PointType",
    "RuleOperator",
    "Season",
    "StandardType",
    "AggregatorType",
    "DynamicFunctionType",
    "AnalysisStatus",
    "AnalysisType",
    "ModelType",
]
