"""Building-level aggregator."""

from datetime import datetime
from typing import Any

from core.domain.enums.priority import Priority
from core.domain.enums.status import Status
from core.domain.models.building import Building
from core.domain.models.building_analysis import BuildingAnalysis
from core.domain.models.room_analysis import RoomAnalysis
from core.domain.value_objects.recommendation import Recommendation


class BuildingAggregator:
    """Aggregate room analyses into building-level analysis."""

    @staticmethod
    def aggregate(
        building: Building,
        room_analyses: list[RoomAnalysis],
    ) -> BuildingAnalysis:
        """
        Aggregate multiple room analyses into building analysis.

        Args:
            building: Building entity
            room_analyses: List of room analysis results

        Returns:
            BuildingAnalysis with aggregated metrics
        """
        if not room_analyses:
            return BuildingAggregator._create_empty_analysis(building)

        # Initialize building analysis
        analysis = BuildingAnalysis(
            building_id=building.id,
            building_name=building.name,
            analysis_timestamp=datetime.now(),
            status=Status.COMPLETED,
        )

        # Collect structure references
        analysis.room_ids = [ra.room_id for ra in room_analyses]
        analysis.level_ids = list({ra.level_id for ra in room_analyses if ra.level_id})
        analysis.room_count = len(room_analyses)
        analysis.level_count = len(analysis.level_ids)

        # Calculate average metrics
        analysis.avg_compliance_rate = BuildingAggregator._calculate_avg_compliance(
            room_analyses
        )
        analysis.avg_quality_score = BuildingAggregator._calculate_avg_quality(
            room_analyses
        )

        # Aggregate test results across rooms
        analysis.test_aggregations = BuildingAggregator._aggregate_test_results(
            room_analyses
        )

        # Aggregate parameter statistics
        analysis.parameter_statistics = BuildingAggregator._aggregate_parameter_stats(
            room_analyses
        )

        # Identify best and worst performing rooms
        analysis.best_performing_rooms = BuildingAggregator._rank_rooms(
            room_analyses, ascending=False, top_n=5
        )
        analysis.worst_performing_rooms = BuildingAggregator._rank_rooms(
            room_analyses, ascending=True, top_n=5
        )

        # Aggregate issues and recommendations
        analysis.critical_issues = BuildingAggregator._aggregate_issues(room_analyses)
        analysis.recommendations = BuildingAggregator._aggregate_recommendations(
            room_analyses
        )

        return analysis

    @staticmethod
    def _calculate_avg_compliance(room_analyses: list[RoomAnalysis]) -> float:
        """Calculate average compliance rate across rooms."""
        if not room_analyses:
            return 0.0

        total = sum(ra.overall_compliance_rate for ra in room_analyses)
        return total / len(room_analyses)

    @staticmethod
    def _calculate_avg_quality(room_analyses: list[RoomAnalysis]) -> float:
        """Calculate average data quality score across rooms."""
        if not room_analyses:
            return 0.0

        total = sum(ra.data_quality_score for ra in room_analyses)
        return total / len(room_analyses)

    @staticmethod
    def _aggregate_test_results(
        room_analyses: list[RoomAnalysis]
    ) -> dict[str, dict[str, Any]]:
        """Aggregate test results across all rooms."""
        test_aggs = {}

        # Collect all test IDs
        all_test_ids: set[str] = set()
        for ra in room_analyses:
            all_test_ids.update(ra.compliance_results.keys())

        # Aggregate each test
        for test_id in all_test_ids:
            rates = []
            total_violations = 0
            rooms_tested = 0

            for ra in room_analyses:
                if test_id in ra.compliance_results:
                    result = ra.compliance_results[test_id]
                    rates.append(result.compliance_rate)
                    total_violations += result.violation_count
                    rooms_tested += 1

            if rooms_tested > 0:
                test_aggs[test_id] = {
                    "avg_compliance_rate": sum(rates) / len(rates),
                    "min_compliance_rate": min(rates),
                    "max_compliance_rate": max(rates),
                    "total_violations": total_violations,
                    "rooms_tested": rooms_tested,
                    "rooms_passed": sum(1 for r in rates if r >= 95),
                }

        return test_aggs

    @staticmethod
    def _aggregate_parameter_stats(
        room_analyses: list[RoomAnalysis]
    ) -> dict[str, dict[str, float]]:
        """Aggregate parameter statistics across rooms."""
        param_stats = {}

        # Collect all parameters
        all_params: set[str] = set()
        for ra in room_analyses:
            all_params.update(ra.parameter_statistics.keys())

        # Aggregate each parameter
        for param in all_params:
            means = []
            mins = []
            maxs = []

            for ra in room_analyses:
                if param in ra.parameter_statistics:
                    stats = ra.parameter_statistics[param]
                    if "mean" in stats:
                        means.append(stats["mean"])
                    if "min" in stats:
                        mins.append(stats["min"])
                    if "max" in stats:
                        maxs.append(stats["max"])

            if means:
                param_stats[param] = {
                    "building_avg": sum(means) / len(means),
                    "building_min": min(mins) if mins else 0,
                    "building_max": max(maxs) if maxs else 0,
                    "rooms_with_data": len(means),
                }

        return param_stats

    @staticmethod
    def _rank_rooms(
        room_analyses: list[RoomAnalysis],
        ascending: bool = True,
        top_n: int = 5,
    ) -> list[dict[str, Any]]:
        """Rank rooms by compliance rate."""
        sorted_rooms = sorted(
            room_analyses,
            key=lambda ra: ra.overall_compliance_rate,
            reverse=not ascending,
        )

        return [
            {
                "room_id": ra.room_id,
                "room_name": ra.room_name,
                "compliance_rate": round(ra.overall_compliance_rate, 2),
                "test_count": ra.test_count,
                "violations": ra.total_violations,
            }
            for ra in sorted_rooms[:top_n]
        ]

    @staticmethod
    def _aggregate_issues(room_analyses: list[RoomAnalysis]) -> list[str]:
        """Aggregate critical issues from rooms."""
        issues = set()

        for ra in room_analyses:
            for issue in ra.critical_issues:
                # Generalize room-specific issues to building level
                generalized = issue.replace(f"Room {ra.room_name}: ", "")
                issues.add(generalized)

        return sorted(issues)[:10]  # Top 10 issues

    @staticmethod
    @staticmethod
    def _aggregate_recommendations(room_analyses: list[RoomAnalysis]) -> list[Recommendation]:
        """Aggregate recommendations from rooms."""
        # Count frequency of similar recommendations by title
        rec_counts: dict[str, tuple[Recommendation, int]] = {}

        for ra in room_analyses:
            for rec in ra.recommendations:
                # Group by title
                title = rec.title
                if title in rec_counts:
                    count = rec_counts[title][1] + 1
                    rec_counts[title] = (rec, count)
                else:
                    rec_counts[title] = (rec, 1)

        # Sort by frequency and return top recommendations
        sorted_recs = sorted(
            rec_counts.values(),
            key=lambda x: x[1],
            reverse=True
        )

        # Return top 10 recommendations, prioritizing high-priority ones
        result = [rec for rec, count in sorted_recs[:10]]

        # Sort by priority within the result
        priority_order = {Priority.CRITICAL: 0, Priority.HIGH: 1, Priority.MEDIUM: 2, Priority.LOW: 3}
        result.sort(key=lambda r: priority_order.get(r.priority, 99))

        return result

    @staticmethod
    def _create_empty_analysis(building: Building) -> BuildingAnalysis:
        """Create empty analysis when no room data available."""
        return BuildingAnalysis(
            building_id=building.id,
            building_name=building.name,
            status=Status.FAILED,
            critical_issues=["No room analyses available"],
        )
