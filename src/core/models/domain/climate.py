"""Climate data model."""

from datetime import datetime
from typing import Optional, Dict
from pydantic import BaseModel, Field

from src.core.models.domain.timeseries import TimeSeriesData


class ClimateData(BaseModel):
    """Climate data for a building."""

    building_id: str = Field(..., description="Building identifier")
    source_file: Optional[str] = Field(None, description="Source climate file path")
    timeseries: Dict[str, TimeSeriesData] = Field(default_factory=dict, description="Climate parameters timeseries")
    period_start: Optional[datetime] = Field(None, description="Start of climate data period")
    period_end: Optional[datetime] = Field(None, description="End of climate data period")

    def add_timeseries(self, parameter: str, ts: TimeSeriesData) -> None:
        """Add a timeseries for a climate parameter."""
        self.timeseries[parameter] = ts

        # Update period boundaries
        if ts.period_start:
            if not self.period_start or ts.period_start < self.period_start:
                self.period_start = ts.period_start

        if ts.period_end:
            if not self.period_end or ts.period_end > self.period_end:
                self.period_end = ts.period_end

    def get_parameter(self, parameter: str) -> Optional[TimeSeriesData]:
        """Get timeseries for a specific parameter."""
        return self.timeseries.get(parameter)
