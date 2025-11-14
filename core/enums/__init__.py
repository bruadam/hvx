"""
Enum package

Provides grouped enum definitions for spatial, sensor, rules, analysis, and access domains.
"""

from .spatial import (
    SpatialEntityType,
    VentilationType,
    BuildingType,
    RoomType,
    OpeningHoursProfile,
)
from .sensors import MetricType, TimeSeriesType, SensorSourceType, PointType
from .rules import RuleOperator, Season, StandardType, DynamicFunctionType
from .analysis import AggregatorType, AnalysisStatus, AnalysisType, ModelType
from .access import PermissionScope, UserRole
from .energy import EnergyCarrier, FuelUnit, PrimaryEnergyScope
from .country import CountryCode

__all__ = [
    "SpatialEntityType",
    "VentilationType",
    "BuildingType",
    "RoomType",
    "OpeningHoursProfile",
    "MetricType",
    "TimeSeriesType",
    "SensorSourceType",
    "PointType",
    "RuleOperator",
    "Season",
    "StandardType",
    "DynamicFunctionType",
    "AggregatorType",
    "AnalysisStatus",
    "AnalysisType",
    "ModelType",
    "PermissionScope",
    "UserRole",
    "EnergyCarrier",
    "FuelUnit",
    "PrimaryEnergyScope",
    "CountryCode",
]
