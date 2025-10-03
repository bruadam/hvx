"""IEQ sensor data model."""

from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, Field, field_validator, model_validator
import pandas as pd

from src.core.models.enums import IEQParameter


class IEQData(BaseModel):
    """Model for processed IEQ sensor data."""

    room_id: str = Field(..., description="Room identifier")
    building_id: str = Field(..., description="Building identifier")
    data: pd.DataFrame = Field(..., description="DataFrame with timestamp index and IEQ measurements")
    source_files: List[str] = Field(default_factory=list, description="Original source file paths")
    processing_timestamp: datetime = Field(default_factory=datetime.now, description="When data was processed")
    data_period_start: Optional[datetime] = Field(None, description="Start of data period")
    data_period_end: Optional[datetime] = Field(None, description="End of data period")
    resolution: str = Field(default="H", description="Data resolution (pandas frequency string)")
    quality_score: Optional[float] = Field(None, description="Data quality score (0-1)", ge=0, le=1)

    model_config = {"arbitrary_types_allowed": True}

    @field_validator('data')
    @classmethod
    def validate_dataframe(cls, v):
        if not isinstance(v, pd.DataFrame):
            raise ValueError("data must be a pandas DataFrame")

        if v.empty:
            raise ValueError("DataFrame cannot be empty")

        # Check for timestamp index
        if not isinstance(v.index, pd.DatetimeIndex):
            raise ValueError("DataFrame must have a DatetimeIndex")

        return v

    @model_validator(mode="after")
    def extract_data_period(self):
        data = self.data
        if data is not None and not data.empty:
            self.data_period_start = data.index.min().to_pydatetime()
            self.data_period_end = data.index.max().to_pydatetime()

        return self

    def get_measurement_columns(self) -> List[str]:
        """Get columns that contain measurement data."""
        measurement_params = [param.value for param in IEQParameter.get_measurement_parameters()]
        return [col for col in self.data.columns if any(param in col.lower() for param in measurement_params)]

    def get_data_completeness(self) -> Dict[str, float]:
        """Calculate data completeness for each column."""
        return {
            col: (self.data[col].count() / len(self.data))
            for col in self.data.columns
        }

    def resample_data(self, frequency: str) -> 'IEQData':
        """Resample data to different frequency."""
        resampled_data = self.data.resample(frequency).mean()

        return IEQData(
            room_id=self.room_id,
            building_id=self.building_id,
            data=resampled_data,
            source_files=self.source_files,
            resolution=frequency,
            quality_score=self.quality_score,
            data_period_start=None,  # Will be set by model_validator
            data_period_end=None     # Will be set by model_validator
        )
