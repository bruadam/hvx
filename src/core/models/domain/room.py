"""Room model."""

from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, field_validator
import numpy as np

from src.core.models.enums import RoomType
from src.core.models.domain.timeseries import TimeSeriesData
from src.core.models.domain.data_quality import DataQuality


class Room(BaseModel):
    """Enhanced room model with timeseries data."""

    id: str = Field(..., description="Unique room identifier")
    name: str = Field(..., description="Human-readable room name")
    building_id: str = Field(..., description="ID of the building this room belongs to")
    level_id: Optional[str] = Field(None, description="ID of the level/floor this room belongs to")
    room_type: Optional[RoomType] = Field(None, description="Type of room")
    area_m2: Optional[float] = Field(None, description="Room area in square meters", gt=0)
    volume_m3: Optional[float] = Field(None, description="Room volume in cubic meters", gt=0)
    capacity_people: Optional[int] = Field(None, description="Maximum occupancy", gt=0)
    tags: List[str] = Field(default_factory=list, description="Custom tags for room classification")

    # Sensor data
    timeseries: Dict[str, TimeSeriesData] = Field(default_factory=dict, description="Sensor timeseries data")
    source_files: List[str] = Field(default_factory=list, description="Source sensor file paths")
    data_period_start: Optional[datetime] = Field(None, description="Start of sensor data period")
    data_period_end: Optional[datetime] = Field(None, description="End of sensor data period")

    @field_validator('id', 'name', 'building_id')
    @classmethod
    def validate_non_empty_strings(cls, v):
        if not v or not v.strip():
            raise ValueError("String fields cannot be empty")
        return v.strip()

    def add_timeseries(self, parameter: str, ts: TimeSeriesData) -> None:
        """Add a timeseries for a sensor parameter."""
        self.timeseries[parameter] = ts

        # Update period boundaries
        if ts.period_start:
            if not self.data_period_start or ts.period_start < self.data_period_start:
                self.data_period_start = ts.period_start

        if ts.period_end:
            if not self.data_period_end or ts.period_end > self.data_period_end:
                self.data_period_end = ts.period_end

    def get_parameter(self, parameter: str) -> Optional[TimeSeriesData]:
        """Get timeseries for a specific parameter."""
        return self.timeseries.get(parameter)

    def get_data_quality(self) -> Dict[str, DataQuality]:
        """Get data quality metrics for all parameters."""
        return {param: ts.data_quality for param, ts in self.timeseries.items()}

    def get_overall_quality_score(self) -> float:
        """Calculate overall data quality score (0-100)."""
        if not self.timeseries:
            return 0.0

        completeness_scores = [ts.data_quality.completeness for ts in self.timeseries.values()]
        return float(np.mean(completeness_scores)) if completeness_scores else 0.0
