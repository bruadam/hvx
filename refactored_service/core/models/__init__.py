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
    VentilationType,
    MetricType,
    TimeSeriesType,
    PointType,
    RuleOperator,
    Season,
    StandardType,
    AggregatorType,
    DynamicFunctionType,
    AnalysisStatus,
    AnalysisType,
    ModelType,
)

# Import base entities
from .base_entities import (
    SpatialEntity,
    Zone,
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
    MeteringPoint,
    TimeSeries,
)

# Import aggregators
from .aggregators import (
    Aggregator,
)

# Import rules
from .rules import (
    ApplicabilityCondition,
    TestRule,
    RuleSet,
)

# Import analysis
from .analysis import (
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


# Re-export all
__all__ = [
    # Enums
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

    # Base entities
    "SpatialEntity",
    "Zone",

    # Enhanced entities
    "Portfolio",
    "Building",
    "Floor",
    "Room",

    # Metering
    "MeteringPoint",
    "TimeSeries",

    # Aggregators
    "Aggregator",

    # Rules
    "ApplicabilityCondition",
    "TestRule",
    "RuleSet",

    # Analysis
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
]
