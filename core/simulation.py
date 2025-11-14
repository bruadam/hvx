"""
Simulation Models

Models for simulation definitions, runs, and comparisons.
"""

from __future__ import annotations
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .enums import AnalysisType, ModelType
from .analysis import BaseAnalysis


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


__all__ = [
    "SimulationModel",
    "SimulationRun",
    "PredictionComparison",
]
