"""Test result model."""

from typing import Optional, List, Dict, Union, Any
from pydantic import BaseModel, Field

from src.core.models.enums import Severity


class TestResult(BaseModel):
    """Result of a single test/rule evaluation."""

    test_name: str = Field(..., description="Name of the test")
    description: Optional[str] = Field(None, description="Test description")
    parameter: str = Field(..., description="Parameter being tested (temperature, co2, etc.)")

    # Compliance metrics
    compliance_rate: float = Field(..., description="Compliance rate as percentage (0-100)", ge=0, le=100)
    total_hours: int = Field(..., description="Total hours evaluated", ge=0)
    compliant_hours: int = Field(..., description="Hours in compliance", ge=0)
    non_compliant_hours: int = Field(..., description="Hours not in compliance", ge=0)

    # Threshold information
    threshold: Optional[Union[float, Dict[str, float]]] = Field(None, description="Threshold value(s) applied")
    threshold_type: Optional[str] = Field(None, description="Type of threshold (above, below, range)")

    # Statistics
    statistics: Dict[str, float] = Field(default_factory=dict, description="Statistical metrics")

    # Severity and recommendations
    severity: Severity = Field(default=Severity.INFO, description="Severity level")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations for improvement")

    # Metadata
    period: Optional[str] = Field(None, description="Time period analyzed (all_year, summer, etc.)")
    filter_applied: Optional[str] = Field(None, description="Filter applied (opening_hours, etc.)")

    # Weather correlations with non-compliance
    weather_correlations: Dict[str, float] = Field(
        default_factory=dict,
        description="Correlation coefficients between non-compliance and weather factors (outdoor_temp, radiation, sunshine)"
    )
    non_compliance_weather_stats: Dict[str, Dict[str, float]] = Field(
        default_factory=dict,
        description="Weather statistics during non-compliant periods (mean, min, max for each weather parameter)"
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump()
