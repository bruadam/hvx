"""Portfolio-level aggregator."""

from datetime import datetime
from typing import Any

from core.domain.enums.priority import Priority
from core.domain.enums.status import Status
from core.domain.models.building_analysis import BuildingAnalysis
from core.domain.models.portfolio_analysis import PortfolioAnalysis
from core.domain.value_objects.recommendation import Recommendation


class PortfolioAggregator:
    """Aggregate building analyses into portfolio-level analysis."""

    @staticmethod
    def aggregate(
        portfolio_id: str,
        portfolio_name: str,
        building_analyses: list[BuildingAnalysis],
    ) -> PortfolioAnalysis:
        """
        Aggregate multiple building analyses into portfolio analysis.

        Args:
            portfolio_id: Portfolio identifier
            portfolio_name: Portfolio name
            building_analyses: List of building analysis results

        Returns:
            PortfolioAnalysis with aggregated metrics
        """
        if not building_analyses:
            return PortfolioAggregator._create_empty_analysis(
                portfolio_id, portfolio_name
            )

        # Initialize portfolio analysis
        analysis = PortfolioAnalysis(
            portfolio_id=portfolio_id,
            portfolio_name=portfolio_name,
            analysis_timestamp=datetime.now(),
            status=Status.COMPLETED,
        )

        # Collect structure references
        analysis.building_ids = [ba.building_id for ba in building_analyses]
        analysis.building_count = len(building_analyses)
        analysis.total_room_count = sum(ba.room_count for ba in building_analyses)

        # Calculate average metrics
        analysis.avg_compliance_rate = PortfolioAggregator._calculate_avg_compliance(
            building_analyses
        )
        analysis.avg_quality_score = PortfolioAggregator._calculate_avg_quality(
            building_analyses
        )

        # Create building summaries
        analysis.building_summaries = PortfolioAggregator._create_building_summaries(
            building_analyses
        )

        # Aggregate test results across portfolio
        analysis.test_aggregations = PortfolioAggregator._aggregate_test_results(
            building_analyses
        )

        # Aggregate parameter statistics
        analysis.parameter_statistics = PortfolioAggregator._aggregate_parameter_stats(
            building_analyses
        )

        # Identify best and worst performing buildings
        analysis.best_performing_buildings = PortfolioAggregator._rank_buildings(
            building_analyses, ascending=False, top_n=5
        )
        analysis.worst_performing_buildings = PortfolioAggregator._rank_buildings(
            building_analyses, ascending=True, top_n=5
        )

        # Aggregate issues and recommendations
        analysis.common_issues = PortfolioAggregator._identify_common_issues(
            building_analyses
        )
        analysis.portfolio_recommendations = PortfolioAggregator._generate_portfolio_recommendations(
            analysis
        )

        return analysis

    @staticmethod
    def _calculate_avg_compliance(building_analyses: list[BuildingAnalysis]) -> float:
        """Calculate average compliance rate across buildings."""
        if not building_analyses:
            return 0.0

        # Weight by room count
        total_weighted = sum(
            ba.avg_compliance_rate * ba.room_count for ba in building_analyses
        )
        total_rooms = sum(ba.room_count for ba in building_analyses)

        return total_weighted / total_rooms if total_rooms > 0 else 0.0

    @staticmethod
    def _calculate_avg_quality(building_analyses: list[BuildingAnalysis]) -> float:
        """Calculate average data quality score across buildings."""
        if not building_analyses:
            return 0.0

        total_weighted = sum(
            ba.avg_quality_score * ba.room_count for ba in building_analyses
        )
        total_rooms = sum(ba.room_count for ba in building_analyses)

        return total_weighted / total_rooms if total_rooms > 0 else 0.0

    @staticmethod
    def _create_building_summaries(
        building_analyses: list[BuildingAnalysis]
    ) -> dict[str, dict[str, Any]]:
        """Create summary for each building."""
        summaries = {}

        for ba in building_analyses:
            summaries[ba.building_id] = {
                "building_name": ba.building_name,
                "room_count": ba.room_count,
                "avg_compliance_rate": round(ba.avg_compliance_rate, 2),
                "compliance_grade": ba.compliance_grade,
                "avg_quality_score": round(ba.avg_quality_score, 2),
                "total_violations": ba.total_violations,
                "critical_issues_count": len(ba.critical_issues),
            }

        return summaries

    @staticmethod
    def _aggregate_test_results(
        building_analyses: list[BuildingAnalysis]
    ) -> dict[str, dict[str, Any]]:
        """Aggregate test results across all buildings."""
        test_aggs = {}

        # Collect all test IDs
        all_test_ids: set[str] = set()
        for ba in building_analyses:
            all_test_ids.update(ba.test_aggregations.keys())

        # Aggregate each test
        for test_id in all_test_ids:
            rates = []
            total_violations = 0
            buildings_tested = 0

            for ba in building_analyses:
                if test_id in ba.test_aggregations:
                    agg = ba.test_aggregations[test_id]
                    rates.append(agg["avg_compliance_rate"])
                    total_violations += agg.get("total_violations", 0)
                    buildings_tested += 1

            if buildings_tested > 0:
                test_aggs[test_id] = {
                    "portfolio_avg_compliance": sum(rates) / len(rates),
                    "min_building_compliance": min(rates),
                    "max_building_compliance": max(rates),
                    "total_violations": total_violations,
                    "buildings_tested": buildings_tested,
                }

        return test_aggs

    @staticmethod
    def _aggregate_parameter_stats(
        building_analyses: list[BuildingAnalysis]
    ) -> dict[str, dict[str, float]]:
        """Aggregate parameter statistics across portfolio."""
        param_stats = {}

        # Collect all parameters
        all_params: set[str] = set()
        for ba in building_analyses:
            all_params.update(ba.parameter_statistics.keys())

        # Aggregate each parameter
        for param in all_params:
            building_avgs = []
            all_mins = []
            all_maxs = []

            for ba in building_analyses:
                if param in ba.parameter_statistics:
                    stats = ba.parameter_statistics[param]
                    if "building_avg" in stats:
                        building_avgs.append(stats["building_avg"])
                    if "building_min" in stats:
                        all_mins.append(stats["building_min"])
                    if "building_max" in stats:
                        all_maxs.append(stats["building_max"])

            if building_avgs:
                param_stats[param] = {
                    "portfolio_avg": sum(building_avgs) / len(building_avgs),
                    "portfolio_min": min(all_mins) if all_mins else 0,
                    "portfolio_max": max(all_maxs) if all_maxs else 0,
                    "buildings_with_data": len(building_avgs),
                }

        return param_stats

    @staticmethod
    def _rank_buildings(
        building_analyses: list[BuildingAnalysis],
        ascending: bool = True,
        top_n: int = 5,
    ) -> list[dict[str, Any]]:
        """Rank buildings by compliance rate."""
        sorted_buildings = sorted(
            building_analyses,
            key=lambda ba: ba.avg_compliance_rate,
            reverse=not ascending,
        )

        return [
            {
                "building_id": ba.building_id,
                "building_name": ba.building_name,
                "compliance_rate": round(ba.avg_compliance_rate, 2),
                "compliance_grade": ba.compliance_grade,
                "room_count": ba.room_count,
                "total_violations": ba.total_violations,
            }
            for ba in sorted_buildings[:top_n]
        ]

    @staticmethod
    def _identify_common_issues(building_analyses: list[BuildingAnalysis]) -> list[str]:
        """Identify issues common across multiple buildings."""
        issue_counts: dict[str, int] = {}

        for ba in building_analyses:
            for issue in ba.critical_issues:
                issue_counts[issue] = issue_counts.get(issue, 0) + 1

        # Return issues present in multiple buildings
        common = [
            f"{issue} (affects {count} buildings)"
            for issue, count in issue_counts.items()
            if count > 1
        ]

        return sorted(common, key=lambda x: int(x.split("(affects ")[1].split(" ")[0]), reverse=True)[:10]

    @staticmethod
    def _generate_portfolio_recommendations(
        analysis: PortfolioAnalysis
    ) -> list[Recommendation]:
        """Generate portfolio-level recommendations."""
        recommendations = []

        # Overall portfolio compliance
        if analysis.avg_compliance_rate < 80:
            recommendations.append(
                Recommendation(
                    title="Portfolio Compliance Below Target",
                    description=f"Portfolio compliance is {analysis.avg_compliance_rate:.1f}%. "
                    "Consider portfolio-wide IEQ improvement program.",
                    priority=Priority.HIGH if analysis.avg_compliance_rate < 60 else Priority.MEDIUM
                )
            )

        # Building-specific recommendations
        if len(analysis.worst_performing_buildings) > 0:
            worst = analysis.worst_performing_buildings[0]
            recommendations.append(
                Recommendation(
                    title="Priority Building for Improvement",
                    description=f"Prioritize improvements for {worst['building_name']} "
                    f"(compliance: {worst['compliance_rate']:.1f}%).",
                    priority=Priority.HIGH
                )
            )

        # Data quality recommendations
        if analysis.avg_quality_score < 75:
            recommendations.append(
                Recommendation(
                    title="Data Quality Improvement Needed",
                    description=f"Data quality is suboptimal ({analysis.avg_quality_score:.1f}%). "
                    "Implement portfolio-wide sensor maintenance program.",
                    priority=Priority.MEDIUM
                )
            )

        return recommendations

    @staticmethod
    def _create_empty_analysis(
        portfolio_id: str, portfolio_name: str
    ) -> PortfolioAnalysis:
        """Create empty analysis when no building data available."""
        return PortfolioAnalysis(
            portfolio_id=portfolio_id,
            portfolio_name=portfolio_name,
            status=Status.FAILED,
            common_issues=["No building analyses available"],
        )
