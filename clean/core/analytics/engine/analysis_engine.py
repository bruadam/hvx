"""Main analysis engine."""

import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime

from core.domain.models.room import Room
from core.domain.models.room_analysis import RoomAnalysis
from core.domain.models.compliance_result import ComplianceResult
from core.domain.enums.parameter_type import ParameterType
from core.domain.enums.standard_type import StandardType
from core.domain.enums.status import Status
from core.domain.enums.priority import Priority
from core.domain.value_objects.compliance_threshold import ComplianceThreshold
from core.domain.value_objects.recommendation import Recommendation
from core.analytics.evaluators.threshold_evaluator import ThresholdEvaluator
from core.analytics.metrics.statistical_metrics import StatisticalMetrics
from core.analytics.metrics.data_quality_metrics import DataQualityMetrics
from core.analytics.filters.opening_hours_filter import OpeningHoursFilter
from core.analytics.filters.seasonal_filter import SeasonalFilter


class AnalysisEngine:
    """
    Main analytics engine for IEQ analysis.

    Coordinates evaluation, filtering, and aggregation of IEQ data.
    """

    def __init__(self):
        """Initialize analysis engine."""
        self.evaluators: Dict[str, Any] = {}

    def analyze_room(
        self,
        room: Room,
        tests: Optional[List[Dict[str, Any]]] = None,
        apply_filters: bool = True,
    ) -> RoomAnalysis:
        """
        Perform complete analysis of room data.

        Args:
            room: Room entity with time series data
            tests: List of test configurations to run
                  Each test should have: test_id, parameter, standard, threshold
            apply_filters: Whether to apply time filters

        Returns:
            RoomAnalysis with complete results
        """
        if not room.has_data:
            return self._create_empty_analysis(room)

        # Initialize analysis
        analysis = RoomAnalysis(
            room_id=room.id,
            room_name=room.name,
            level_id=room.level_id,
            building_id=room.building_id,
            data_time_range=room.data_time_range,
            status=Status.IN_PROGRESS,
        )

        # Calculate data quality
        analysis.data_completeness = room.get_data_completeness()
        analysis.data_quality_score = self._calculate_room_quality_score(room)

        # Calculate parameter statistics
        for parameter in room.available_parameters:
            series = room.get_parameter_data(parameter)
            if series is not None:
                stats = StatisticalMetrics.calculate_basic_statistics(series)
                analysis.parameter_statistics[parameter.value] = stats

        # Run compliance tests
        if tests:
            for test_config in tests:
                try:
                    result = self._run_single_test(room, test_config, apply_filters)
                    standard = test_config.get("standard", "").lower()
                    analysis.add_compliance_result(
                        test_id=result.test_id,
                        result=result,
                        standard=standard if standard else None,
                    )
                except Exception as e:
                    # Log error but continue with other tests
                    print(f"Error running test {test_config.get('test_id')}: {e}")

        # Generate recommendations
        analysis.recommendations = self._generate_recommendations(analysis)

        # Identify critical issues
        analysis.critical_issues = self._identify_critical_issues(analysis)

        analysis.status = Status.COMPLETED
        return analysis

    def _run_single_test(
        self,
        room: Room,
        test_config: Dict[str, Any],
        apply_filters: bool,
    ) -> ComplianceResult:
        """Run a single compliance test."""
        # Extract test configuration
        test_id = test_config["test_id"]
        parameter = test_config["parameter"]
        if isinstance(parameter, str):
            parameter = ParameterType(parameter)

        standard = test_config["standard"]
        if isinstance(standard, str):
            standard = StandardType(standard)

        # Get parameter data
        data = room.get_parameter_data(parameter)
        if data is None:
            raise ValueError(f"Parameter {parameter.value} not available in room data")

        # Apply filters if requested
        if apply_filters and "filter" in test_config:
            filter_config = test_config["filter"]
            # Handle both string and dict filter configs
            if isinstance(filter_config, str):
                # Convert string filter name to dict format
                filter_dict = {"type": filter_config}
                # Check if period is also specified
                if "period" in test_config:
                    filter_dict["period"] = test_config["period"]
                filter_config = filter_dict
            
            data = self._apply_filter(
                pd.DataFrame({parameter.value: data}),
                filter_config
            )[parameter.value]

        # Create threshold from config
        threshold_config = test_config["threshold"]
        threshold = self._create_threshold(threshold_config)

        # Create and run evaluator
        evaluator = ThresholdEvaluator(
            standard=standard,
            threshold=threshold,
            compliance_level=test_config.get("compliance_level", 95.0),
        )

        return evaluator.evaluate(data, parameter, test_id)

    def _create_threshold(self, threshold_config: Dict[str, Any]) -> ComplianceThreshold:
        """Create ComplianceThreshold from configuration."""
        if "lower" in threshold_config and "upper" in threshold_config:
            return ComplianceThreshold(
                lower_limit=threshold_config["lower"],
                upper_limit=threshold_config["upper"],
                threshold_type="bidirectional",
                unit=threshold_config.get("unit", ""),
            )
        elif "lower" in threshold_config:
            return ComplianceThreshold(
                lower_limit=threshold_config["lower"],
                upper_limit=None,
                threshold_type="unidirectional_min",
                unit=threshold_config.get("unit", ""),
            )
        elif "upper" in threshold_config:
            return ComplianceThreshold(
                lower_limit=None,
                upper_limit=threshold_config["upper"],
                threshold_type="unidirectional_max",
                unit=threshold_config.get("unit", ""),
            )
        else:
            raise ValueError("Threshold must have at least 'lower' or 'upper' limit")

    def _apply_filter(self, df: pd.DataFrame, filter_config: Dict[str, Any]) -> pd.DataFrame:
        """Apply data filter based on configuration.
        
        Args:
            df: DataFrame to filter
            filter_config: Can be either:
                - A string with filter name (e.g., "opening_hours", "seasonal")
                - A dict with "type" and additional config
        
        Returns:
            Filtered DataFrame
        """
        # Handle string filter names
        if isinstance(filter_config, str):
            filter_type = filter_config
            filter_kwargs = {}
        else:
            filter_type = filter_config.get("type", "none")
            filter_kwargs = filter_config

        if filter_type == "opening_hours":
            filter_obj = OpeningHoursFilter(
                opening_hours=filter_kwargs.get("hours"),
                holidays=filter_kwargs.get("holidays"),
            )
            return filter_obj.apply(df)
        elif filter_type == "seasonal":
            filter_obj = SeasonalFilter(filter_kwargs.get("period", "all_year"))
            return filter_obj.apply(df)
        else:
            return df

    def _calculate_room_quality_score(self, room: Room) -> float:
        """Calculate overall room data quality score."""
        if not room.has_data:
            return 0.0

        scores = []
        for parameter in room.available_parameters:
            series = room.get_parameter_data(parameter)
            if series is not None:
                score = DataQualityMetrics.calculate_quality_score(series)
                scores.append(score)

        return sum(scores) / len(scores) if scores else 0.0

    def _generate_recommendations(self, analysis: RoomAnalysis) -> List[Recommendation]:
        """Generate recommendations based on analysis results."""
        recommendations = []

        # Check overall compliance
        if analysis.overall_compliance_rate < 70:
            recommendations.append(
                Recommendation(
                    title="Overall Compliance Low",
                    description=f"Overall compliance is low ({analysis.overall_compliance_rate:.1f}%). "
                    "Consider immediate remedial actions.",
                    priority=Priority.HIGH if analysis.overall_compliance_rate < 50 else Priority.MEDIUM
                )
            )

        # Check specific test failures
        for test_id, result in analysis.compliance_results.items():
            if not result.is_compliant:
                param = result.parameter.display_name
                recommendations.append(
                    Recommendation(
                        title=f"{param} Compliance Issue",
                        description=f"{param} compliance is {result.compliance_rate:.1f}%. "
                        f"Review and improve {param} control systems.",
                        priority=Priority.HIGH if result.compliance_rate < 50 else Priority.MEDIUM
                    )
                )

        # Check data quality
        if analysis.data_quality_score < 70:
            recommendations.append(
                Recommendation(
                    title="Data Quality Issue",
                    description=f"Data quality is low ({analysis.data_quality_score:.1f}%). "
                    "Check sensors and data collection systems.",
                    priority=Priority.MEDIUM
                )
            )

        return recommendations

    def _identify_critical_issues(self, analysis: RoomAnalysis) -> List[str]:
        """Identify critical issues requiring immediate attention."""
        issues = []

        for test_id, result in analysis.compliance_results.items():
            if result.compliance_rate < 50:
                severity_breakdown = result.get_severity_breakdown()
                if severity_breakdown.get("critical", 0) > 0:
                    issues.append(
                        f"CRITICAL: {result.parameter.display_name} has {severity_breakdown['critical']} "
                        f"critical violations. Immediate action required."
                    )

        return issues

    def _create_empty_analysis(self, room: Room) -> RoomAnalysis:
        """Create empty analysis result when no data available."""
        return RoomAnalysis(
            room_id=room.id,
            room_name=room.name,
            level_id=room.level_id,
            building_id=room.building_id,
            status=Status.FAILED,
            critical_issues=["No data available for analysis"],
        )
