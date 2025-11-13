from __future__ import annotations

from datetime import datetime, date
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ============================================================
#  ENUMS
# ============================================================

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


# ============================================================
#  SPATIAL ENTITIES
# ============================================================

class SpatialEntity(BaseModel):
    id: str
    name: str
    type: SpatialEntityType

    parent_ids: List[str] = Field(default_factory=list)
    child_ids: List[str] = Field(default_factory=list)

    # Context for rule selection
    country: Optional[str] = None        # e.g. "EU", "US", "DK"
    region: Optional[str] = None         # e.g. "NA", "Nordic", state, etc.
    climate_zone: Optional[str] = None   # any scheme you want

    # Semantic building metadata
    building_type: Optional[str] = None  # e.g. "office", "school", ...
    room_type: Optional[str] = None      # e.g. "classroom", "meeting_room"
    ventilation_type: Optional[VentilationType] = VentilationType.UNKNOWN

    area_m2: Optional[float] = None
    volume_m3: Optional[float] = None
    design_occupancy: Optional[int] = None

    metadata: Dict[str, Any] = Field(default_factory=dict)


class Portfolio(SpatialEntity):
    type: SpatialEntityType = SpatialEntityType.PORTFOLIO


class Building(SpatialEntity):
    type: SpatialEntityType = SpatialEntityType.BUILDING


class Floor(SpatialEntity):
    type: SpatialEntityType = SpatialEntityType.FLOOR


class Room(SpatialEntity):
    type: SpatialEntityType = SpatialEntityType.ROOM


class Zone(SpatialEntity):
    type: SpatialEntityType = SpatialEntityType.ZONE


# ============================================================
#  DATA SOURCES: METERING POINTS & TIMESERIES
# ============================================================

class MeteringPoint(BaseModel):
    id: str
    name: str
    type: PointType
    spatial_entity_id: str

    metric: MetricType
    unit: str
    timezone: Optional[str] = None

    timeseries_ids: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TimeSeries(BaseModel):
    id: str
    point_id: str
    type: TimeSeriesType
    metric: MetricType
    unit: str

    start: Optional[datetime] = None
    end: Optional[datetime] = None
    granularity_seconds: Optional[int] = None

    source: Optional[str] = None  # e.g. "sensor", "bms", "simulation", "analytics"
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================
#  AGGREGATORS
# ============================================================

class Aggregator(BaseModel):
    id: str
    name: str
    type: AggregatorType

    # For weighted aggregators: list of properties to use as weights
    # e.g. ["area_m2"], or ["area_m2", "design_occupancy"]
    weight_properties: List[str] = Field(default_factory=list)

    # Optional config (e.g. tie-breaking rules, normalization, etc.)
    config: Dict[str, Any] = Field(default_factory=dict)


# ============================================================
#  TEST RULES & APPLICABILITY
# ============================================================

class ApplicabilityCondition(BaseModel):
    """
    Generic applicability condition.
    All fields are ANDed inside one condition;
    multiple conditions in a RuleSet are usually ORed.
    """
    id: str

    countries: Optional[List[str]] = None      # ["EU"], ["US"], ["DK"]
    regions: Optional[List[str]] = None        # ["NA", "Nordic", "California"]
    climate_zones: Optional[List[str]] = None  # ["Cfb", "Dfb", etc.]

    building_types: Optional[List[str]] = None
    room_types: Optional[List[str]] = None

    min_area_m2: Optional[float] = None
    max_area_m2: Optional[float] = None

    ventilation_types: Optional[List[VentilationType]] = None
    seasons: Optional[List[Season]] = None

    dynamic_functions: Optional[List[DynamicFunctionType]] = None

    # Free-form; e.g. {"min_year_built": 1980}
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TestRule(BaseModel):
    """
    Reusable rule definition like:
    - Temperature < 26°C with tolerance 100h/year
    - 20°C <= Temperature <= 26°C with tolerance 100h/year
    - CO2 < 1000ppm for 95% occupied hours
    """
    id: str
    name: str
    description: Optional[str] = None

    metric: MetricType
    operator: RuleOperator

    # For simple comparisons
    target_value: Optional[float] = None

    # For ranges (between / outside_range)
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None

    # Tolerance settings
    tolerance_hours: Optional[float] = None          # e.g. 100 hours
    tolerance_percentage: Optional[float] = None     # e.g. 20% of occupied time

    # Time window expressed in ISO8601 or descriptive strings
    # e.g. "P1Y", "P1M", "P7D"
    time_window: Optional[str] = None

    # When to apply: "occupied", "always", or custom tags
    applies_during: Optional[str] = None

    # For adaptive/dynamic rules: expression references
    # These would be interpreted by the engine, not Pydantic
    dynamic_lower_expr: Optional[str] = None
    dynamic_upper_expr: Optional[str] = None

    metadata: Dict[str, Any] = Field(default_factory=dict)


class RuleSet(BaseModel):
    """
    Bundle of rules (e.g. EN16798 Cat II, ASHRAE 55, internal corporate standard)
    with applicability conditions.
    """
    id: str
    name: str
    standard: StandardType
    description: Optional[str] = None

    # e.g. "Category II", "Office", "InternalPolicyA"
    category: Optional[str] = None

    rules: List[TestRule] = Field(default_factory=list)
    applicability_conditions: List[ApplicabilityCondition] = Field(default_factory=list)

    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================
#  ANALYTICS: BASE & SPECIALIZED
# ============================================================

class BaseAnalysis(BaseModel):
    id: str
    name: str
    type: AnalysisType

    spatial_entity_id: str

    rule_set_id: Optional[str] = None
    metering_point_ids: List[str] = Field(default_factory=list)
    timeseries_ids: List[str] = Field(default_factory=list)

    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    status: AnalysisStatus = AnalysisStatus.PENDING
    error_message: Optional[str] = None

    metadata: Dict[str, Any] = Field(default_factory=dict)


class TestResult(BaseAnalysis):
    """
    Result of executing a single TestRule on a given spatial entity.
    """
    type: AnalysisType = AnalysisType.TEST_RESULT

    rule_id: str

    out_of_range_hours: Optional[float] = None
    out_of_range_percentage: Optional[float] = None

    pass_: bool = Field(..., alias="pass")
    details: Dict[str, Any] = Field(default_factory=dict)


class ComplianceAnalysis(BaseAnalysis):
    """
    Runs a RuleSet for a spatial entity and aggregates multiple TestResults.
    """
    type: AnalysisType = AnalysisType.COMPLIANCE

    test_result_ids: List[str] = Field(default_factory=list)
    overall_pass: Optional[bool] = None

    # e.g. aggregated EN16798 category, EPC rating, etc.
    summary_results: Dict[str, Any] = Field(default_factory=dict)


class AggregatedAnalysis(BaseAnalysis):
    """
    Aggregation of child analyses across children entities.
    Example: building-level EN16798 result aggregated from room-level results.
    """
    type: AnalysisType = AnalysisType.AGGREGATED

    child_analysis_ids: List[str] = Field(default_factory=list)
    aggregator_id: str

    aggregation_results: Dict[str, Any] = Field(default_factory=dict)


class ForecastAnalysis(BaseAnalysis):
    type: AnalysisType = AnalysisType.FORECAST

    model_id: Optional[str] = None
    forecast_timeseries_ids: List[str] = Field(default_factory=list)


class EnergySignatureAnalysis(BaseAnalysis):
    type: AnalysisType = AnalysisType.ENERGY_SIGNATURE

    # Typically uses climate TS + energy TS
    model_id: Optional[str] = None
    regression_params: Dict[str, Any] = Field(default_factory=dict)
    r2: Optional[float] = None


# ============================================================
#  SIMULATION MODELS & RUNS
# ============================================================

class SimulationModel(BaseModel):
    """
    Abstract model definition (energy model, comfort model, forecast model, etc).
    """
    id: str
    name: str
    type: ModelType

    spatial_entity_id: Optional[str] = None  # the entity the model is built for

    input_timeseries_ids: List[str] = Field(default_factory=list)
    output_timeseries_ids: List[str] = Field(default_factory=list)

    version: Optional[str] = None
    training_start: Optional[date] = None
    training_end: Optional[date] = None

    parameters: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SimulationRun(BaseAnalysis):
    """
    Concrete run of a SimulationModel (can also be seen as an Analysis).
    """
    type: AnalysisType = AnalysisType.SIMULATION_RUN

    model_id: str
    scenario_name: Optional[str] = None

    # Mapping from logical input names to timeseries IDs, etc.
    input_mapping: Dict[str, str] = Field(default_factory=dict)

    # Output TS produced by this run
    output_timeseries_ids: List[str] = Field(default_factory=list)


class PredictionComparison(BaseModel):
    """
    Links simulated timeseries to measured timeseries and stores error metrics.
    """
    id: str

    measured_timeseries_id: str
    simulated_timeseries_id: str

    period_start: datetime
    period_end: datetime

    rmse: Optional[float] = None
    mape: Optional[float] = None
    bias: Optional[float] = None

    other_metrics: Dict[str, Any] = Field(default_factory=dict)
