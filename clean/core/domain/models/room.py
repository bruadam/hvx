"""Room domain entity."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

import pandas as pd
from pydantic import BaseModel, Field

from core.domain.value_objects.measurement import Measurement
from core.domain.value_objects.time_range import TimeRange
from core.domain.enums.parameter_type import ParameterType


class Room(BaseModel):
    """
    Room entity representing a physical space with environmental measurements.

    This is a rich domain model that contains both data and behavior.
    """

    # Identity
    id: str = Field(..., description="Unique room identifier")
    name: str = Field(..., description="Human-readable room name")

    # Hierarchy
    level_id: Optional[str] = Field(default=None, description="Parent level ID")
    building_id: Optional[str] = Field(default=None, description="Parent building ID")

    # Metadata
    area: Optional[float] = Field(default=None, ge=0, description="Floor area in m²")
    volume: Optional[float] = Field(default=None, ge=0, description="Volume in m³")
    occupancy: Optional[int] = Field(default=None, ge=0, description="Typical occupancy count")

    # Data
    data_file_path: Optional[Path] = Field(default=None, description="Path to source data file")
    time_series_data: Optional[pd.DataFrame] = Field(
        default=None,
        description="Time series environmental data",
        exclude=True,  # Don't serialize DataFrame in JSON
    )

    # Temporal coverage
    data_start: Optional[datetime] = Field(default=None, description="Earliest measurement")
    data_end: Optional[datetime] = Field(default=None, description="Latest measurement")

    # Additional attributes
    attributes: Dict[str, str] = Field(
        default_factory=dict, description="Custom attributes (e.g., room type, orientation)"
    )

    model_config = {"arbitrary_types_allowed": True}  # Allow pandas DataFrame

    @property
    def has_data(self) -> bool:
        """Check if room has time series data loaded."""
        return self.time_series_data is not None and not self.time_series_data.empty

    @property
    def data_time_range(self) -> Optional[TimeRange]:
        """Get time range of available data."""
        if self.data_start and self.data_end:
            return TimeRange(start=self.data_start, end=self.data_end)
        return None

    @property
    def available_parameters(self) -> List[ParameterType]:
        """Get list of available parameter types in data."""
        if not self.has_data:
            return []

        available = []
        if self.time_series_data is not None:
            for param in ParameterType:
                if param.value in self.time_series_data.columns:
                    available.append(param)
        return available

    def get_parameter_data(self, parameter: ParameterType) -> Optional[pd.Series]:
        """
        Get time series data for a specific parameter.

        Args:
            parameter: Parameter type to retrieve

        Returns:
            pandas Series with parameter data, or None if not available
        """
        if not self.has_data or self.time_series_data is None:
            return None

        if parameter.value in self.time_series_data.columns:
            return self.time_series_data[parameter.value]
        return None

    def get_data_completeness(self, parameter: Optional[ParameterType] = None) -> float:
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
        return float((self.time_series_data.notna().sum().sum() / self.time_series_data.size) * 100)

    def get_measurement_count(self, parameter: Optional[ParameterType] = None) -> int:
        """
        Get count of measurements.

        Args:
            parameter: Specific parameter to count, or None for total rows

        Returns:
            Number of measurements
        """
        if not self.has_data or self.time_series_data is None:
            return 0

        if parameter:
            series = self.get_parameter_data(parameter)
            if series is None:
                return 0
            return int(series.notna().sum())

        return len(self.time_series_data)

    def filter_by_time_range(self, time_range: TimeRange) -> "Room":
        """
        Create a new Room instance with data filtered to time range.

        Args:
            time_range: Time range to filter to

        Returns:
            New Room instance with filtered data
        """
        if not self.has_data or self.time_series_data is None:
            return self

        # Filter DataFrame by time range
        mask = (self.time_series_data.index >= time_range.start) & (
            self.time_series_data.index <= time_range.end
        )
        filtered_df = self.time_series_data[mask].copy()

        # Create new room instance with filtered data
        return self.model_copy(
            update={
                "time_series_data": filtered_df,
                "data_start": filtered_df.index.min() if not filtered_df.empty else None,
                "data_end": filtered_df.index.max() if not filtered_df.empty else None,
            }
        )

    def get_summary(self) -> Dict[str, Any]:
        """Get summary information about this room."""
        return {
            "id": self.id,
            "name": self.name,
            "level_id": self.level_id,
            "building_id": self.building_id,
            "area_m2": self.area,
            "volume_m3": self.volume,
            "has_data": self.has_data,
            "measurement_count": self.get_measurement_count() if self.has_data else 0,
            "available_parameters": [p.value for p in self.available_parameters],
            "data_completeness_pct": (
                round(self.get_data_completeness(), 2) if self.has_data else 0.0
            ),
            "data_time_range": (
                {
                    "start": self.data_start.isoformat() if self.data_start else None,
                    "end": self.data_end.isoformat() if self.data_end else None,
                }
                if self.has_data
                else None
            ),
        }

    def __str__(self) -> str:
        """String representation."""
        return f"Room(id={self.id}, name={self.name}, has_data={self.has_data})"

    def __repr__(self) -> str:
        """Repr representation."""
        return (
            f"Room(id={self.id!r}, name={self.name!r}, "
            f"parameters={[p.value for p in self.available_parameters]})"
        )
