"""Base dataset models for sensor and metering data.

Provides common structure for time-series data from various sources:
- Environmental sensors (temperature, humidity, CO2)
- Metering points (electricity, gas, water)
- Climate stations (outdoor weather)
- Occupancy sensors
"""

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import BaseModel, Field

from core.domain.models.base.base_entity import BaseEntity
from core.domain.value_objects.time_range import TimeRange


class SensorDataset(BaseEntity[pd.DataFrame]):
    """
    Base class for sensor/metering data management.

    Supports:
    - Time-series data from any sensor type
    - Data quality tracking
    - Temporal coverage
    - Parameter availability
    - Data completeness calculation

    Can be used for:
    - Environmental sensors (IEQ monitoring)
    - Metering points (utility consumption)
    - Climate stations (weather data)
    - Occupancy sensors (people counting)
    - Any time-series measurement
    """

    # Sensor/measurement type
    sensor_type: str = Field(
        ...,
        description="Type of sensor/measurement (environmental, metering, climate, occupancy)"
    )

    measurement_type: str = Field(
        ...,
        description="What is being measured (temperature, electricity, etc.)"
    )

    # Data source
    data_source: Path | str | None = Field(
        default=None,
        description="Path to source data file or data source identifier"
    )

    loaded_at: datetime = Field(
        default_factory=datetime.now,
        description="When dataset was loaded"
    )

    # Time series data
    time_series_data: pd.DataFrame | None = Field(
        default=None,
        description="Time series measurement data",
        exclude=True,  # Don't serialize DataFrame in JSON
    )

    # Temporal coverage
    data_start: datetime | None = Field(
        default=None,
        description="Earliest measurement timestamp"
    )

    data_end: datetime | None = Field(
        default=None,
        description="Latest measurement timestamp"
    )

    # Data quality
    data_quality_score: float = Field(
        default=0.0,
        ge=0,
        le=100,
        description="Overall data quality score (0-100%)"
    )

    # Spatial context (optional)
    location_id: str | None = Field(
        default=None,
        description="Location identifier (room, building, etc.)"
    )

    location_type: str | None = Field(
        default=None,
        description="Type of location (room, building, outdoor, etc.)"
    )

    model_config = {"arbitrary_types_allowed": True}

    @property
    def has_data(self) -> bool:
        """Check if dataset has time series data loaded."""
        return self.time_series_data is not None and not self.time_series_data.empty

    @property
    def data_time_range(self) -> TimeRange | None:
        """Get time range of available data."""
        if self.data_start and self.data_end:
            return TimeRange(start=self.data_start, end=self.data_end)
        return None

    @property
    def available_parameters(self) -> list[str]:
        """Get list of available parameters in data."""
        if not self.has_data or self.time_series_data is None:
            return []
        return list(self.time_series_data.columns)

    @property
    def measurement_count(self) -> int:
        """Get total number of measurements (rows)."""
        if not self.has_data or self.time_series_data is None:
            return 0
        return len(self.time_series_data)

    def get_parameter_data(self, parameter: str) -> pd.Series | None:
        """
        Get time series data for a specific parameter.

        Args:
            parameter: Parameter name to retrieve

        Returns:
            pandas Series with parameter data, or None if not available
        """
        if not self.has_data or self.time_series_data is None:
            return None

        if parameter in self.time_series_data.columns:
            return self.time_series_data[parameter]
        return None

    def get_data_completeness(self, parameter: str | None = None) -> float:
        """
        Calculate data completeness (percentage of non-null values).

        Args:
            parameter: Specific parameter to check, or None for overall completeness

        Returns:
            Completeness as percentage (0-100)
        """
        if not self.has_data or self.time_series_data is None:
            return 0.0

        if parameter:
            series = self.get_parameter_data(parameter)
            if series is None:
                return 0.0
            return float((series.notna().sum() / len(series)) * 100)

        # Overall completeness across all columns
        total_cells = self.time_series_data.size
        if total_cells == 0:
            return 0.0
        non_null_cells = self.time_series_data.notna().sum().sum()
        return float((non_null_cells / total_cells) * 100)

    def get_measurement_count_for_parameter(self, parameter: str) -> int:
        """
        Get count of non-null measurements for a parameter.

        Args:
            parameter: Parameter name

        Returns:
            Number of valid measurements
        """
        if not self.has_data or self.time_series_data is None:
            return 0

        series = self.get_parameter_data(parameter)
        if series is None:
            return 0
        return int(series.notna().sum())

    def filter_by_time_range(self, time_range: TimeRange) -> "SensorDataset":
        """
        Create a new dataset with data filtered to time range.

        Args:
            time_range: Time range to filter to

        Returns:
            New SensorDataset instance with filtered data
        """
        if not self.has_data or self.time_series_data is None:
            return self

        # Filter DataFrame by time range
        mask = (
            (self.time_series_data.index >= time_range.start) &
            (self.time_series_data.index <= time_range.end)
        )
        filtered_df = self.time_series_data[mask].copy()

        # Create new dataset instance with filtered data
        return self.model_copy(
            update={
                "time_series_data": filtered_df,
                "data_start": filtered_df.index.min() if not filtered_df.empty else None,
                "data_end": filtered_df.index.max() if not filtered_df.empty else None,
            }
        )

    def calculate_statistics(self, parameter: str) -> dict[str, float] | None:
        """
        Calculate basic statistics for a parameter.

        Args:
            parameter: Parameter name

        Returns:
            Dictionary with statistics (mean, std, min, max, median, etc.)
        """
        series = self.get_parameter_data(parameter)
        if series is None or series.empty:
            return None

        return {
            "mean": float(series.mean()),
            "std": float(series.std()),
            "min": float(series.min()),
            "max": float(series.max()),
            "median": float(series.median()),
            "q25": float(series.quantile(0.25)),
            "q75": float(series.quantile(0.75)),
            "count": int(series.notna().sum()),
        }

    def get_summary(self) -> dict[str, Any]:
        """Get summary information about this dataset."""
        summary = super().get_summary()
        summary.update({
            "sensor_type": self.sensor_type,
            "measurement_type": self.measurement_type,
            "location_id": self.location_id,
            "location_type": self.location_type,
            "has_data": self.has_data,
            "measurement_count": self.measurement_count,
            "available_parameters": self.available_parameters,
            "data_completeness_pct": round(self.get_data_completeness(), 2) if self.has_data else 0.0,
            "data_quality_score": round(self.data_quality_score, 2),
            "data_time_range": {
                "start": self.data_start.isoformat() if self.data_start else None,
                "end": self.data_end.isoformat() if self.data_end else None,
            } if self.has_data else None,
            "data_source": str(self.data_source) if self.data_source else None,
            "loaded_at": self.loaded_at.isoformat(),
        })
        return summary

    def __str__(self) -> str:
        """String representation."""
        return (
            f"{self.__class__.__name__}("
            f"type={self.sensor_type}, "
            f"measurement={self.measurement_type}, "
            f"has_data={self.has_data})"
        )
