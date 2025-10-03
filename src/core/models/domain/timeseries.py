"""Time series data model."""

from datetime import datetime
from typing import Optional, Dict
from pydantic import BaseModel, Field, field_validator, model_validator
import pandas as pd

from src.core.models.domain.data_quality import DataQuality


class TimeSeriesData(BaseModel):
    """Time series data container with quality metrics."""

    parameter: str = Field(..., description="Parameter name (temperature, co2, etc.)")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    data: pd.DataFrame = Field(..., description="DataFrame with timestamp index and values")
    source_file: Optional[str] = Field(None, description="Source file path")
    period_start: Optional[datetime] = Field(None, description="Start of data period")
    period_end: Optional[datetime] = Field(None, description="End of data period")
    data_quality: DataQuality = Field(default_factory=DataQuality, description="Data quality metrics")
    resolution: str = Field(default="H", description="Data resolution (pandas frequency string)")

    model_config = {"arbitrary_types_allowed": True}

    @field_validator('data')
    @classmethod
    def validate_dataframe(cls, v):
        if not isinstance(v, pd.DataFrame):
            raise ValueError("data must be a pandas DataFrame")

        if not isinstance(v.index, pd.DatetimeIndex):
            raise ValueError("DataFrame must have a DatetimeIndex")

        return v

    @model_validator(mode="after")
    def extract_period_and_quality(self):
        """Extract data period and calculate quality metrics."""
        if self.data is not None and not self.data.empty:
            self.period_start = self.data.index.min().to_pydatetime()
            self.period_end = self.data.index.max().to_pydatetime()

            # Calculate data quality
            if self.parameter in self.data.columns:
                series = self.data[self.parameter]
                total = len(series)
                missing = series.isna().sum()
                completeness = ((total - missing) / total * 100) if total > 0 else 0

                self.data_quality.completeness = completeness
                self.data_quality.missing_count = int(missing)
                self.data_quality.total_count = total
                self.data_quality.calculate_quality_score()

        return self

    def get_statistics(self) -> Dict[str, float]:
        """Calculate basic statistics for the timeseries."""
        if self.parameter not in self.data.columns:
            return {}

        series = self.data[self.parameter].dropna()
        if len(series) == 0:
            return {}

        return {
            'mean': float(series.mean()),
            'std': float(series.std()),
            'min': float(series.min()),
            'max': float(series.max()),
            'median': float(series.median()),
            'count': int(len(series))
        }
