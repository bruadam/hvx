"""Room analysis results model."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
from pydantic import BaseModel, Field
import json

from src.core.models.enums import Status
from src.core.models.results.test_result import TestResult


class RoomAnalysis(BaseModel):
    """Analysis results for a single room."""

    # Identification
    room_id: str = Field(..., description="Unique room identifier")
    room_name: str = Field(..., description="Human-readable room name")
    building_id: str = Field(..., description="Building identifier")
    level_id: Optional[str] = Field(None, description="Level/floor identifier")

    # Analysis metadata
    analysis_timestamp: datetime = Field(default_factory=datetime.now, description="When analysis was performed")
    data_period_start: Optional[datetime] = Field(None, description="Start of analyzed data period")
    data_period_end: Optional[datetime] = Field(None, description="End of analyzed data period")
    status: Status = Field(default=Status.COMPLETED, description="Analysis status")

    # Test results
    test_results: Dict[str, TestResult] = Field(default_factory=dict, description="Results by test name")

    # Overall metrics
    overall_compliance_rate: float = Field(default=0.0, description="Overall compliance rate", ge=0, le=100)
    overall_quality_score: float = Field(default=0.0, description="Overall data quality score", ge=0, le=100)

    # Data quality
    data_completeness: float = Field(default=0.0, description="Data completeness percentage", ge=0, le=100)
    parameters_analyzed: List[str] = Field(default_factory=list, description="Parameters included in analysis")

    # Aggregated statistics
    statistics: Dict[str, Dict[str, float]] = Field(default_factory=dict, description="Stats by parameter")

    # Weather correlation summary
    weather_correlation_summary: Dict[str, Any] = Field(
        default_factory=dict,
        description="Summary of weather correlations with non-compliance across all tests"
    )

    # Issues and recommendations
    critical_issues: List[str] = Field(default_factory=list, description="Critical issues found")
    recommendations: List[str] = Field(default_factory=list, description="Overall recommendations")

    # EN16798-1 Category assignment
    en16798_category: Optional[str] = Field(None, description="Assigned EN16798-1 category (Cat I/II/III/IV)")
    en16798_category_confidence: Optional[float] = Field(None, description="Confidence in category assignment (0-100)", ge=0, le=100)

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    def add_test_result(self, test_name: str, result: TestResult) -> None:
        """Add a test result."""
        self.test_results[test_name] = result

    def calculate_overall_metrics(self) -> None:
        """Calculate overall compliance and quality metrics."""
        if self.test_results:
            compliance_rates = [r.compliance_rate for r in self.test_results.values()]
            self.overall_compliance_rate = sum(compliance_rates) / len(compliance_rates)

    def save_to_json(self, filepath: Path) -> None:
        """Save analysis to JSON file."""
        data = self.model_dump(mode='json')
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    @classmethod
    def load_from_json(cls, filepath: Path) -> 'RoomAnalysis':
        """Load analysis from JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls(**data)
