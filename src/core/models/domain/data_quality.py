"""Data quality metrics model."""

from typing import Dict, List, Any
from pydantic import BaseModel, Field


class DataQuality(BaseModel):
    """Data quality metrics."""

    completeness: float = Field(default=0.0, description="Data completeness percentage (0-100)", ge=0, le=100)
    missing_count: int = Field(default=0, description="Number of missing values", ge=0)
    total_count: int = Field(default=0, description="Total number of expected values", ge=0)
    gaps: List[Dict[str, Any]] = Field(default_factory=list, description="List of data gaps (start, end, duration)")
    quality_score: str = Field(default="Unknown", description="Qualitative quality score (High/Medium/Low)")

    def calculate_quality_score(self) -> None:
        """Calculate qualitative quality score based on completeness."""
        if self.completeness >= 90:
            self.quality_score = "High"
        elif self.completeness >= 75:
            self.quality_score = "Medium"
        elif self.completeness >= 50:
            self.quality_score = "Low"
        else:
            self.quality_score = "Very Low"
