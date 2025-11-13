"""Portfolio analysis result model."""

from typing import Any

from pydantic import Field

from core.domain.enums.aggregation_method import SpatialAggregationMethod
from core.domain.models.base.base_analysis import MetricsAnalysis
from core.domain.models.analysis.building_analysis import BuildingAnalysis


class PortfolioAnalysis(MetricsAnalysis[None, BuildingAnalysis]):
    """
    Aggregated analysis results for a portfolio of buildings.

    Provides portfolio-wide insights and cross-building comparisons.
    Extends MetricsAnalysis with portfolio-specific features.
    """

    # Portfolio-specific fields
    total_room_count: int = Field(default=0, description="Total rooms across all buildings")

    # Building comparisons (portfolio-specific)
    building_summaries: dict[str, dict[str, Any]] = Field(
        default_factory=dict, description="Summary for each building"
    )

    # Aliases for backward compatibility
    @property
    def portfolio_id(self) -> str:
        """Alias for entity_id."""
        return self.entity_id

    @property
    def portfolio_name(self) -> str:
        """Alias for entity_name."""
        return self.entity_name

    @property
    def building_ids(self) -> list[str]:
        """Alias for child_ids."""
        return self.child_ids

    @property
    def building_count(self) -> int:
        """Alias for child_count."""
        return self.child_count

    @property
    def avg_compliance_rate(self) -> float:
        """Alias for compliance_rate."""
        return self.compliance_rate

    @property
    def avg_quality_score(self) -> float:
        """Alias for quality_score."""
        return self.quality_score

    @property
    def common_issues(self) -> list[str]:
        """Alias for critical_issues."""
        return self.critical_issues

    @property
    def portfolio_recommendations(self) -> list:
        """Alias for recommendations."""
        return self.recommendations

    @property
    def best_performing_buildings(self) -> list[dict[str, Any]]:
        """Alias for best_performing_children."""
        return self.best_performing_children

    @property
    def worst_performing_buildings(self) -> list[dict[str, Any]]:
        """Alias for worst_performing_children."""
        return self.worst_performing_children

    def get_building_comparison(self) -> list[dict[str, Any]]:
        """Get side-by-side comparison of all buildings."""
        return sorted(
            self.building_summaries.values(),
            key=lambda b: b.get("avg_compliance_rate", 0),
            reverse=True,
        )

    def set_en16798_compliance(
        self,
        spatial_method: SpatialAggregationMethod = SpatialAggregationMethod.WORST_SPACE,
    ) -> None:
        """
        Calculate and set EN 16798-1 standard compliance for the portfolio.

        This method aggregates building-level EN 16798-1 categories using the configured
        spatial aggregation method to determine the portfolio-level category.

        Args:
            spatial_method: Method to aggregate buildings (default: WORST_SPACE for conservative approach)
        """
        if not self.building_summaries:
            self.set_standard_compliance("en16798-1", {
                "standard": "en16798-1",
                "achieved_category": "IV",
                "aggregation_method": spatial_method.value,
                "building_count": 0,
            })
            return
        
        # Extract building categories from summaries
        building_categories = {}
        building_scores = {}
        
        for building_id, summary in self.building_summaries.items():
            # Get EN 16798 data from building if available
            if "en16798_category" in summary:
                building_categories[building_id] = summary["en16798_category"]
            if "ieq_score" in summary:
                building_scores[building_id] = summary["ieq_score"]
        
        # Determine portfolio category based on spatial method
        portfolio_category = "IV"
        portfolio_score = None
        
        if building_categories:
            if spatial_method == SpatialAggregationMethod.WORST_SPACE:
                # Portfolio category = worst building category
                portfolio_category = self.aggregate_spaces_worst_case(building_categories)
                
            elif spatial_method == SpatialAggregationMethod.SIMPLE_AVERAGE and building_scores:
                # Simple average of building scores
                portfolio_score = sum(building_scores.values()) / len(building_scores)
                # Convert score to category
                portfolio_category = self.score_to_category(portfolio_score).upper()
        
        # Store EN 16798-1 specific compliance data
        en16798_data = {
            "standard": "en16798-1",
            "achieved_category": portfolio_category,
            "portfolio_ieq_score": portfolio_score,
            "aggregation_method": spatial_method.value,
            "building_count": len(building_categories),
            "building_categories": building_categories,
        }
        
        self.set_standard_compliance("en16798-1", en16798_data)

    def to_summary_dict(self) -> dict[str, Any]:
        """Get summary as dictionary."""
        summary = super().to_summary_dict()
        summary.update({
            "portfolio_id": self.portfolio_id,
            "portfolio_name": self.portfolio_name,
            "building_count": self.building_count,
            "total_room_count": self.total_room_count,
            "avg_compliance_rate": round(self.avg_compliance_rate, 2),
            "avg_quality_score": round(self.avg_quality_score, 2),
            "common_issues_count": len(self.common_issues),
            "recommendations_count": len(self.portfolio_recommendations),
        })
        return summary

    def __str__(self) -> str:
        """String representation."""
        return (
            f"PortfolioAnalysis(portfolio={self.portfolio_name}, "
            f"buildings={self.building_count}, "
            f"compliance={self.avg_compliance_rate:.1f}% [{self.compliance_grade}])"
        )
