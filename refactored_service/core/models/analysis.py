"""
Analysis Models

Models for various types of analyses (test results, compliance, aggregated, etc.).
"""

from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .enums import AnalysisStatus, AnalysisType


class BaseAnalysis(BaseModel):
    """
    Base class for all analysis types.

    Represents an analysis performed on a spatial entity using
    metering points and time series data.
    """
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
    "BaseAnalysis",
    "TestResult",
    "ComplianceAnalysis",
    "AggregatedAnalysis",
    "ForecastAnalysis",
    "EnergySignatureAnalysis",
]
