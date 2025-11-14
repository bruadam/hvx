"""
Metering and Time Series Models

Models for sensors, metering points, and time series data.
"""

from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .enums import (
    MetricType,
    PointType,
    TimeSeriesType,
    SensorSourceType,
    EnergyCarrier,
)


class SensorSource(BaseModel):
    """
    Describes how data for a sensor is obtained (API, CSV, streaming, etc.).
    """

    id: str
    type: SensorSourceType
    config: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SensorDefinition(BaseModel):
    """
    Canonical description of a physical or virtual sensor.
    """

    id: str
    spatial_entity_id: str

    metric: MetricType
    parameter: str  # semantic role, e.g. "temperature", "co2", "setpoint"
    unit: str

    name: Optional[str] = None
    description: Optional[str] = None
    timezone: Optional[str] = None

    brick_point_uri: Optional[str] = None
    haystack_tags: List[str] = Field(default_factory=list)
    ifc_guid: Optional[str] = None

    sources: List[SensorSource] = Field(default_factory=list)

    weight: Optional[float] = None
    priority: Optional[int] = None
    accuracy: Optional[float] = None

    metadata: Dict[str, Any] = Field(default_factory=dict)


class SensorGroup(BaseModel):
    """
    Collection of sensors measuring the same semantic parameter.
    """

    parameter: str
    metric: MetricType
    sensors: List[SensorDefinition] = Field(default_factory=list)
    aggregation_method: str = "average"

    def add_sensor(self, sensor: SensorDefinition) -> None:
        """Add sensor to the group, replacing existing by ID."""
        existing_ids = {s.id for s in self.sensors}
        if sensor.id in existing_ids:
            self.sensors = [s for s in self.sensors if s.id != sensor.id]
        self.sensors.append(sensor)

    def aggregate(
        self,
        readings: Dict[str, float],
        method: Optional[str] = None,
        weights_override: Optional[Dict[str, float]] = None,
    ) -> Optional[float]:
        """
        Aggregate readings from sensors in the group.

        Args:
            readings: Mapping of sensor_id -> latest value.
            method: Override aggregation method.
            weights_override: Optional mapping of sensor_id -> weight.
        """
        method_to_use = (method or self.aggregation_method or "average").lower()
        values: List[float] = []
        weights: List[float] = []

        for sensor in self.sensors:
            if sensor.id not in readings:
                continue
            values.append(readings[sensor.id])
            weight = (
                (weights_override or {}).get(sensor.id)
                or sensor.weight
                or 1.0
            )
            weights.append(weight)

        if not values:
            return None

        if method_to_use == "average":
            return sum(values) / len(values)

        if method_to_use == "weighted_average":
            total_weight = sum(weights)
            if total_weight == 0:
                return sum(values) / len(values)
            return sum(v * w for v, w in zip(values, weights)) / total_weight

        if method_to_use == "median":
            sorted_vals = sorted(values)
            mid = len(sorted_vals) // 2
            if len(sorted_vals) % 2 == 0:
                return (sorted_vals[mid - 1] + sorted_vals[mid]) / 2
            return sorted_vals[mid]

        if method_to_use == "max":
            return max(values)

        if method_to_use == "min":
            return min(values)

        # Default fallback
        return values[-1]


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

    sensor_id: Optional[str] = None  # link to SensorDefinition if applicable
    parameter: Optional[str] = None

    timeseries_ids: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TimeSeriesRecord(BaseModel):
    """
    Represents a single timestamped measurement from a sensor.
    """

    timestamp: datetime
    value: float
    sensor_id: str

    quality: Optional[float] = None
    type: TimeSeriesType = TimeSeriesType.MEASURED
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SensorSeries(BaseModel):
    """
    Lightweight in-memory container for a sequence of sensor records.
    """

    sensor_id: str
    records: List[TimeSeriesRecord] = Field(default_factory=list)

    def add_record(self, record: TimeSeriesRecord) -> None:
        if record.sensor_id != self.sensor_id:
            raise ValueError("Record sensor_id does not match series sensor_id")
        self.records.append(record)

    def latest(self) -> Optional[TimeSeriesRecord]:
        if not self.records:
            return None
        return max(self.records, key=lambda r: r.timestamp)


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

    # Aggregation configuration
    target_resolution_seconds: Optional[int] = Field(
        default=None,
        description="Target resolution for automatic aggregation (in seconds)"
    )
    aggregation_method: Optional[str] = Field(
        default=None,
        description="Method for aggregating to target resolution"
    )


class EnergyMeter(BaseModel):
    """
    Energy meter for tracking consumption by carrier.

    Supports multiple resolutions (hourly, daily, monthly, yearly).
    """
    id: str
    spatial_entity_id: str
    carrier: EnergyCarrier

    name: Optional[str] = None
    description: Optional[str] = None

    # Meter readings
    current_reading_kwh: Optional[float] = Field(default=None, ge=0)
    last_reading_timestamp: Optional[datetime] = None

    # Time series references (by resolution)
    hourly_timeseries_id: Optional[str] = None
    daily_timeseries_id: Optional[str] = None
    monthly_timeseries_id: Optional[str] = None
    yearly_timeseries_id: Optional[str] = None

    # Meter metadata
    meter_number: Optional[str] = None
    utility_provider: Optional[str] = None
    tariff_name: Optional[str] = None

    # Physical unit conversion
    physical_unit: Optional[str] = None  # e.g., "m3", "liter", "kg"
    conversion_factor_to_kwh: Optional[float] = None

    metadata: Dict[str, Any] = Field(default_factory=dict)


class EnergyMeterReading(BaseModel):
    """
    Individual energy meter reading with timestamp.
    """
    meter_id: str
    timestamp: datetime
    value_kwh: float
    reading_type: str = Field(
        default="cumulative",
        description="Type of reading: cumulative, interval, instantaneous"
    )

    quality: Optional[float] = Field(default=None, ge=0, le=1)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AggregatedEnergyData(BaseModel):
    """
    Aggregated energy consumption data for a specific period.
    """
    spatial_entity_id: str
    carrier: EnergyCarrier
    period_start: datetime
    period_end: datetime
    resolution: str  # "hourly", "daily", "monthly", "yearly"

    total_kwh: float = Field(ge=0)
    average_kwh: Optional[float] = None
    peak_kwh: Optional[float] = None

    # Breakdown by time
    hourly_data: Optional[List[float]] = None
    daily_data: Optional[List[float]] = None
    monthly_data: Optional[List[float]] = None

    metadata: Dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "SensorSource",
    "SensorDefinition",
    "SensorGroup",
    "MeteringPoint",
    "SensorSeries",
    "TimeSeriesRecord",
    "TimeSeries",
    "EnergyMeter",
    "EnergyMeterReading",
    "AggregatedEnergyData",
]
