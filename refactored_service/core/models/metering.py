"""
Metering and Time Series Models

Models for metering points (sensors, meters) and time series data.
"""

from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .enums import MetricType, PointType, TimeSeriesType


class MeteringPoint(BaseModel):
    """
    Metering point representing a sensor, meter, or measurement location.

    Links to a spatial entity and stores references to time series data.
    """
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
    """
    Time series data container.

    Stores metadata about time series data. Actual data values
    can be stored in metadata or in a separate time series database.
    """
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


__all__ = [
    "MeteringPoint",
    "TimeSeries",
]
