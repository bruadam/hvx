"""Building analysis result model."""

from datetime import datetime
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

from core.domain.enums.status import Status
from core.domain.value_objects.recommendation import Recommendation


class BuildingAnalysis(BaseModel):
    """
    Aggregated analysis results for a building.

    Summarizes room-level analyses and provides building-wide insights.
    """

    # Identity
    building_id: str = Field(..., description="Building identifier")
    building_name: str = Field(..., description="Building name")

    # Analysis metadata
    analysis_timestamp: datetime = Field(
        default_factory=datetime.now, description="When analysis was performed"
    )
    status: Status = Field(default=Status.COMPLETED, description="Analysis status")

    # Structure references
    level_ids: List[str] = Field(default_factory=list, description="Level IDs analyzed")
    room_ids: List[str] = Field(default_factory=list, description="Room IDs analyzed")
    level_count: int = Field(default=0, description="Number of levels")
    room_count: int = Field(default=0, description="Number of rooms analyzed")

    # Aggregated metrics
    avg_compliance_rate: float = Field(
        default=0.0, ge=0, le=100, description="Average compliance across all rooms"
    )
    avg_quality_score: float = Field(
        default=0.0, ge=0, le=100, description="Average data quality score"
    )

    # Test aggregations (test_id -> aggregated metrics)
    test_aggregations: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, description="Aggregated results per test across building"
    )

    # Rankings
    best_performing_rooms: List[Dict[str, Any]] = Field(
        default_factory=list, description="Top performing rooms"
    )
    worst_performing_rooms: List[Dict[str, Any]] = Field(
        default_factory=list, description="Worst performing rooms"
    )

    # Statistics by parameter
    parameter_statistics: Dict[str, Dict[str, float]] = Field(
        default_factory=dict, description="Building-wide statistics per parameter"
    )

    # Issues and recommendations
    critical_issues: List[str] = Field(default_factory=list, description="Building-wide issues")
    recommendations: List[Recommendation] = Field(
        default_factory=list, description="Building-wide recommendations"
    )

    # Climate correlation (if weather data available)
    climate_correlations: Dict[str, float] = Field(
        default_factory=dict, description="Correlations with outdoor climate"
    )

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    model_config = {"arbitrary_types_allowed": True}  # Allow Recommendation

    @property
    def total_violations(self) -> int:
        """Get total violations from test aggregations."""
        return sum(
            agg.get("total_violations", 0) for agg in self.test_aggregations.values()
        )

    @property
    def compliance_grade(self) -> str:
        """Get letter grade based on compliance rate."""
        if self.avg_compliance_rate >= 95:
            return "A"
        elif self.avg_compliance_rate >= 85:
            return "B"
        elif self.avg_compliance_rate >= 75:
            return "C"
        elif self.avg_compliance_rate >= 65:
            return "D"
        else:
            return "F"

    def get_room_ranking(self, by: str = "compliance") -> List[Dict[str, Any]]:
        """
        Get ranked list of rooms.

        Args:
            by: Ranking criteria ('compliance' or 'quality')

        Returns:
            List of room summaries sorted by criteria
        """
        if by == "compliance":
            return sorted(
                self.best_performing_rooms + self.worst_performing_rooms,
                key=lambda r: r.get("compliance_rate", 0),
                reverse=True,
            )
        elif by == "quality":
            return sorted(
                self.best_performing_rooms + self.worst_performing_rooms,
                key=lambda r: r.get("quality_score", 0),
                reverse=True,
            )
        else:
            return []

    def to_summary_dict(self) -> Dict[str, Any]:
        """Get summary as dictionary."""
        return {
            "building_id": self.building_id,
            "building_name": self.building_name,
            "status": self.status.value,
            "analysis_timestamp": self.analysis_timestamp.isoformat(),
            "level_count": self.level_count,
            "room_count": self.room_count,
            "avg_compliance_rate": round(self.avg_compliance_rate, 2),
            "compliance_grade": self.compliance_grade,
            "avg_quality_score": round(self.avg_quality_score, 2),
            "total_violations": self.total_violations,
            "test_count": len(self.test_aggregations),
            "critical_issues_count": len(self.critical_issues),
            "recommendations_count": len(self.recommendations),
        }

    def __str__(self) -> str:
        """String representation."""
        return (
            f"BuildingAnalysis(building={self.building_name}, "
            f"rooms={self.room_count}, "
            f"compliance={self.avg_compliance_rate:.1f}% [{self.compliance_grade}])"
        )
