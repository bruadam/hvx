"""Portfolio analysis result model."""

from datetime import datetime
from typing import Dict, List, Any
from pydantic import BaseModel, Field

from core.domain.enums.status import Status
from core.domain.value_objects.recommendation import Recommendation


class PortfolioAnalysis(BaseModel):
    """
    Aggregated analysis results for a portfolio of buildings.

    Provides portfolio-wide insights and cross-building comparisons.
    """

    # Identity
    portfolio_id: str = Field(..., description="Portfolio identifier")
    portfolio_name: str = Field(..., description="Portfolio name")

    # Analysis metadata
    analysis_timestamp: datetime = Field(
        default_factory=datetime.now, description="When analysis was performed"
    )
    status: Status = Field(default=Status.COMPLETED, description="Analysis status")

    # Structure references
    building_ids: List[str] = Field(default_factory=list, description="Building IDs analyzed")
    building_count: int = Field(default=0, description="Number of buildings")
    total_room_count: int = Field(default=0, description="Total rooms across all buildings")

    # Aggregated metrics
    avg_compliance_rate: float = Field(
        default=0.0, ge=0, le=100, description="Average compliance across portfolio"
    )
    avg_quality_score: float = Field(
        default=0.0, ge=0, le=100, description="Average data quality across portfolio"
    )

    # Building comparisons
    building_summaries: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, description="Summary for each building"
    )

    # Rankings
    best_performing_buildings: List[Dict[str, Any]] = Field(
        default_factory=list, description="Top performing buildings"
    )
    worst_performing_buildings: List[Dict[str, Any]] = Field(
        default_factory=list, description="Worst performing buildings"
    )

    # Portfolio-wide statistics
    parameter_statistics: Dict[str, Dict[str, float]] = Field(
        default_factory=dict, description="Portfolio-wide statistics per parameter"
    )

    # Test aggregations across portfolio
    test_aggregations: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, description="Aggregated results per test across portfolio"
    )

    # Issues and recommendations
    common_issues: List[str] = Field(
        default_factory=list, description="Issues common across buildings"
    )
    portfolio_recommendations: List[Recommendation] = Field(
        default_factory=list, description="Portfolio-level recommendations"
    )

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    model_config = {"arbitrary_types_allowed": True}  # Allow Recommendation

    @property
    def total_violations(self) -> int:
        """Get total violations across portfolio."""
        return sum(
            agg.get("total_violations", 0) for agg in self.test_aggregations.values()
        )

    @property
    def compliance_grade(self) -> str:
        """Get letter grade based on portfolio compliance rate."""
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

    def get_building_comparison(self) -> List[Dict[str, Any]]:
        """Get side-by-side comparison of all buildings."""
        return sorted(
            list(self.building_summaries.values()),
            key=lambda b: b.get("avg_compliance_rate", 0),
            reverse=True,
        )

    def to_summary_dict(self) -> Dict[str, Any]:
        """Get summary as dictionary."""
        return {
            "portfolio_id": self.portfolio_id,
            "portfolio_name": self.portfolio_name,
            "status": self.status.value,
            "analysis_timestamp": self.analysis_timestamp.isoformat(),
            "building_count": self.building_count,
            "total_room_count": self.total_room_count,
            "avg_compliance_rate": round(self.avg_compliance_rate, 2),
            "compliance_grade": self.compliance_grade,
            "avg_quality_score": round(self.avg_quality_score, 2),
            "total_violations": self.total_violations,
            "test_count": len(self.test_aggregations),
            "common_issues_count": len(self.common_issues),
            "recommendations_count": len(self.portfolio_recommendations),
        }

    def __str__(self) -> str:
        """String representation."""
        return (
            f"PortfolioAnalysis(portfolio={self.portfolio_name}, "
            f"buildings={self.building_count}, "
            f"compliance={self.avg_compliance_rate:.1f}% [{self.compliance_grade}])"
        )
