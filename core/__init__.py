"""
Core Models Package

All core model classes for the refactored service.

Models are organized into separate modules:
- enums: All enumeration types
- base_entities: Base SpatialEntity and Zone
- entities: Enhanced Portfolio, Building, Floor, Room
- metering: MeteringPoint and TimeSeries
- aggregators: Aggregator
- rules: ApplicabilityCondition, TestRule, RuleSet
- analysis: All analysis types
- simulation: Simulation models and runs
"""

# Import all enums
from .enums import (
    SpatialEntityType,
    BuildingType,
    RoomType,
    VentilationType,
    MetricType,
    TimeSeriesType,
    SensorSourceType,
    PointType,
    RuleOperator,
    Season,
    StandardType,
    AggregatorType,
    DynamicFunctionType,
    AnalysisStatus,
    AnalysisType,
    ModelType,
    PermissionScope,
    UserRole,
    EnergyCarrier,
    FuelUnit,
    PrimaryEnergyScope,
    OpeningHoursProfile,
    CountryCode,
)

# Import base entities
from .spacial_entity import (
    SpatialEntity,
)

# Import enhanced entities
from .entities import (
    Portfolio,
    Building,
    Floor,
    Room,
)

# Import metering
from .metering import (
    SensorSource,
    SensorDefinition,
    SensorGroup,
    MeteringPoint,
    SensorSeries,
    TimeSeriesRecord,
    TimeSeries,
)

# Import aggregators
from .aggregators import (
    Aggregator,
)

# Import access control
from .access import (
    UserProfile,
    AccessControlEntry,
    ResourceReference,
    UserContext,
)

# Import rules
from .rules import (
    StandardDefinition,
    RuleClause,
    ApplicabilityCondition,
    TestRule,
    RuleSet,
    CountryRuleProfile,
)

# Import analysis
from .analysis import (
    AnalysisContext,
    AnalysisResult,
    SimulationResult,
    StateSnapshot,
    BaseAnalysis,
    TestResult,
    ComplianceAnalysis,
    AggregatedAnalysis,
    ForecastAnalysis,
    EnergySignatureAnalysis,
)

# Import simulation
from .simulation import (
    SimulationModel,
    SimulationRun,
    PredictionComparison,
)

# Energy conversions
from .energy import (
    FuelProperty,
    PrimaryEnergyFactor,
    EnergyUse,
    PrimaryEnergyComponent,
    PrimaryEnergyBreakdown,
    EnergyConversionService,
)

# Import schedules
from .schedules import (
    get_opening_profile_for_building_type,
    generate_occupancy_mask,
)

# Config accessors
from .config import (
    CONFIG_DATA_DIR,
    list_filters,
    load_filter_config,
    list_periods,
    load_period_config,
    load_holiday_config,
    load_epc_thresholds,
)

# Filters
from .filters import (
    TimeFilter,
    TimeRange,
    OpeningHoursFilter,
    SeasonalFilter,
)


# Re-export all
__all__ = [
    # Enums
    "SpatialEntityType",
    "BuildingType",
    "RoomType",
    "VentilationType",
    "MetricType",
    "TimeSeriesType",
    "SensorSourceType",
    "PointType",
    "RuleOperator",
    "Season",
    "StandardType",
    "SpatialGranularity",
    "AggregatorType",
    "DynamicFunctionType",
    "AnalysisStatus",
    "AnalysisType",
    "ModelType",
    "PermissionScope",
    "UserRole",
    "EnergyCarrier",
    "FuelUnit",
    "PrimaryEnergyScope",
    "OpeningHoursProfile",
    "CountryCode",

    # Base entities
    "SpatialEntity",

    # Enhanced entities
    "Portfolio",
    "Building",
    "Floor",
    "Room",

    # Metering
    "SensorSource",
    "SensorDefinition",
    "SensorGroup",
    "MeteringPoint",
    "SensorSeries",
    "TimeSeriesRecord",
    "TimeSeries",

    # Aggregators
    "Aggregator",

    # Access
    "UserProfile",
    "AccessControlEntry",
    "ResourceReference",
    "UserContext",

    # Rules
    "StandardDefinition",
    "RuleClause",
    "ApplicabilityCondition",
    "TestRule",
    "RuleSet",
    "CountryRuleProfile",

    # Analysis
    "AnalysisContext",
    "AnalysisResult",
    "SimulationResult",
    "StateSnapshot",
    "BaseAnalysis",
    "TestResult",
    "ComplianceAnalysis",
    "AggregatedAnalysis",
    "ForecastAnalysis",
    "EnergySignatureAnalysis",

    # Simulation
    "SimulationModel",
    "SimulationRun",
    "PredictionComparison",

    # Energy
    "FuelProperty",
    "PrimaryEnergyFactor",
    "EnergyUse",
    "PrimaryEnergyComponent",
    "PrimaryEnergyBreakdown",
    "EnergyConversionService",

    # Schedules
    "get_opening_profile_for_building_type",
    "generate_occupancy_mask",

    # Config
    "CONFIG_DATA_DIR",
    "list_filters",
    "load_filter_config",
    "list_periods",
    "load_period_config",
    "load_holiday_config",
    "load_epc_thresholds",

    # Filters
    "TimeFilter",
    "TimeRange",
    "OpeningHoursFilter",
    "SeasonalFilter",
]
