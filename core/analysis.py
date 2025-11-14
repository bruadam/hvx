"""
Analysis Models

Models for various types of analyses (test results, compliance, aggregated, etc.).
"""

from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from .enums import AnalysisStatus, AnalysisType, SpatialEntityType


class AnalysisContext(BaseModel):
    """
    Describes the context in which an analysis was performed.
    """

    spatial_entity_id: str
    spatial_level: SpatialEntityType
    sensor_parameters: List[str] = Field(default_factory=list)
    standard_ids: List[str] = Field(default_factory=list)
    season: Optional[str] = None
    climate_inputs_ref: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AnalysisResult(BaseModel):
    """
    Generic analysis result payload for portfolio/building/room analytics.
    """

    id: str
    analysis_type: AnalysisType
    context: AnalysisContext

    issued_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None

    source_standard: Optional[str] = None
    model_version: Optional[str] = None
    confidence: Optional[float] = None

    results: Dict[str, Any] = Field(default_factory=dict)
    provenance: Dict[str, Any] = Field(default_factory=dict)


class SimulationResult(AnalysisResult):
    """
    Specialized analysis result for simulation outputs (RC, ML, etc.).
    """

    simulation_model_id: Optional[str] = None
    scenario_name: Optional[str] = None
    output_timeseries_ids: List[str] = Field(default_factory=list)


class StateSnapshot(BaseModel):
    """
    Materialized state of a spatial entity at a given time.
    """

    id: str
    spatial_entity_id: str
    analysis_result_id: str
    state: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None


class BaseAnalysis(BaseModel):
    """
    Base class for all analysis types.

    Represents an analysis performed on a spatial entity using
    metering points and time series data.
    """
    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    type: AnalysisType

    spatial_entity_id: str

    rule_set_id: Optional[str] = None
    metering_point_ids: List[str] = Field(default_factory=list)
    timeseries_ids: List[str] = Field(default_factory=list)

    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    status: AnalysisStatus = AnalysisStatus.PENDING
    error_message: Optional[str] = None

    metadata: Dict[str, Any] = Field(default_factory=dict)
    context: Optional[AnalysisContext] = None


class TestResult(BaseAnalysis):
    """
    Result of executing a single TestRule on a given spatial entity.
    """
    type: AnalysisType = AnalysisType.TEST_RESULT

    rule_id: str

    out_of_range_hours: Optional[float] = None
    out_of_range_percentage: Optional[float] = None

    successful: Optional[bool] = None
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
    """
    Forecast analysis using a prediction model.
    """
    type: AnalysisType = AnalysisType.FORECAST

    model_id: Optional[str] = None
    forecast_timeseries_ids: List[str] = Field(default_factory=list)


class EnergySignatureAnalysis(BaseAnalysis):
    """
    Energy signature analysis (energy vs. temperature regression).
    """
    type: AnalysisType = AnalysisType.ENERGY_SIGNATURE

    # Typically uses climate TS + energy TS
    model_id: Optional[str] = None
    regression_params: Dict[str, Any] = Field(default_factory=dict)
    r2: Optional[float] = None


__all__ = [
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
]
