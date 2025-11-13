"""Room domain entity."""

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pandas as pd
from pydantic import Field

from core.domain.enums.occupancy import ActivityLevel
from core.domain.enums.parameter_type import ParameterType
from core.domain.enums.pollution_level import PollutionLevel
from core.domain.enums.ventilation import VentilationType
from core.domain.models.base.base_entity import BaseEntity
from core.domain.value_objects.time_range import TimeRange

if TYPE_CHECKING:
    from core.domain.models.analysis.room_analysis import RoomAnalysis
    from core.domain.models.validation.compliance_result import ComplianceResult
    from core.domain.value_objects.compliance_threshold import ComplianceThreshold
    from core.domain.value_objects.recommendation import Recommendation


class Room(BaseEntity[None]):
    """
    Room entity representing a physical space with environmental measurements.

    This is a rich domain model that contains both data and behavior.
    Inherits id, name, attributes, timestamps, and physical properties from BaseEntity.
    Physical properties (area, volume, occupancy, orientations, etc.) are stored at the room level.
    """

    # Hierarchy
    level_id: str | None = Field(default=None, description="Parent level ID")
    building_id: str | None = Field(default=None, description="Parent building ID")

    # EN 16798-1 specific metadata
    room_type: str | None = Field(default=None, description="Room type (office, classroom, etc.)")
    ventilation_type: VentilationType | None = Field(
        default=None, description="Type of ventilation system"
    )
    pollution_level: PollutionLevel | None = Field(
        default=None, description="Building pollution level for ventilation calculations"
    )
    activity_level: ActivityLevel | None = Field(
        default=None, description="Occupant activity level (metabolic rate)"
    )

    # Data
    data_file_path: Path | None = Field(default=None, description="Path to source data file")
    time_series_data: pd.DataFrame | None = Field(
        default=None,
        description="Time series environmental data",
        exclude=True,  # Don't serialize DataFrame in JSON
    )

    # Temporal coverage
    data_start: datetime | None = Field(default=None, description="Earliest measurement")
    data_end: datetime | None = Field(default=None, description="Latest measurement")

    model_config = {"arbitrary_types_allowed": True}  # Allow pandas DataFrame

    @property
    def has_data(self) -> bool:
        """Check if room has time series data loaded."""
        return self.time_series_data is not None and not self.time_series_data.empty

    @property
    def data_time_range(self) -> TimeRange | None:
        """Get time range of available data."""
        if self.data_start and self.data_end:
            return TimeRange(start=self.data_start, end=self.data_end)
        return None

    @property
    def available_parameters(self) -> list[ParameterType]:
        """Get list of available parameter types in data."""
        if not self.has_data:
            return []

        available = []
        if self.time_series_data is not None:
            for param in ParameterType:
                if param.value in self.time_series_data.columns:
                    available.append(param)
        return available

    def get_parameter_data(self, parameter: ParameterType) -> pd.Series | None:
        """
        Get time series data for a specific parameter.

        Args:
            parameter: Parameter type to retrieve

        Returns:
            pandas Series with parameter data, or None if not available
        """
        if not self.has_data or self.time_series_data is None:
            return None

        if parameter.value in self.time_series_data.columns:
            return self.time_series_data[parameter.value]
        return None

    def get_data_completeness(self, parameter: ParameterType | None = None) -> float:
        """
        Calculate data completeness (percentage of non-null values).

        Args:
            parameter: Specific parameter to check, or None for overall completeness

        Returns:
            Completeness as percentage (0-100)
        """
        if not self.has_data or self.time_series_data is None:
            return 0.0

        if parameter:
            series = self.get_parameter_data(parameter)
            if series is None:
                return 0.0
            return float((series.notna().sum() / len(series)) * 100)

        # Overall completeness across all columns
        return float((self.time_series_data.notna().sum().sum() / self.time_series_data.size) * 100)

    def get_measurement_count(self, parameter: ParameterType | None = None) -> int:
        """
        Get count of measurements.

        Args:
            parameter: Specific parameter to count, or None for total rows

        Returns:
            Number of measurements
        """
        if not self.has_data or self.time_series_data is None:
            return 0

        if parameter:
            series = self.get_parameter_data(parameter)
            if series is None:
                return 0
            return int(series.notna().sum())

        return len(self.time_series_data)

    def filter_by_time_range(self, time_range: TimeRange) -> "Room":
        """
        Create a new Room instance with data filtered to time range.

        Args:
            time_range: Time range to filter to

        Returns:
            New Room instance with filtered data
        """
        if not self.has_data or self.time_series_data is None:
            return self

        # Filter DataFrame by time range
        mask = (self.time_series_data.index >= time_range.start) & (
            self.time_series_data.index <= time_range.end
        )
        filtered_df = self.time_series_data[mask].copy()

        # Create new room instance with filtered data
        return self.model_copy(
            update={
                "time_series_data": filtered_df,
                "data_start": filtered_df.index.min() if not filtered_df.empty else None,
                "data_end": filtered_df.index.max() if not filtered_df.empty else None,
            }
        )

    def get_summary(self) -> dict[str, Any]:
        """Get summary information about this room."""
        # Get base summary from BaseEntity
        summary = super().get_summary()
        
        # Add room-specific information
        summary.update({
            "level_id": self.level_id,
            "building_id": self.building_id,
            "metadata": {
                "area_m2": self.area,
                "volume_m3": self.volume,
                "occupancy": self.occupancy,
                "glass_to_wall_ratio": self.glass_to_wall_ratio,
                "last_renovation_year": self.last_renovation_year,
                "room_type": self.room_type,
                "ventilation_type": self.ventilation_type.value
                if self.ventilation_type
                else None,
                "pollution_level": self.pollution_level.value
                if self.pollution_level
                else None,
                "activity_level": self.activity_level.value
                if self.activity_level
                else None,
            },
            "has_data": self.has_data,
            "measurement_count": self.get_measurement_count() if self.has_data else 0,
            "available_parameters": [p.value for p in self.available_parameters],
            "data_completeness_pct": (
                round(self.get_data_completeness(), 2) if self.has_data else 0.0
            ),
            "data_time_range": (
                {
                    "start": self.data_start.isoformat() if self.data_start else None,
                    "end": self.data_end.isoformat() if self.data_end else None,
                }
                if self.has_data
                else None
            ),
        })
        
        return summary
    
    def compute_metrics(
        self,
        tests: list[dict[str, Any]] | None = None,
        standards: list[str] | None = None,
        apply_filters: bool = True,
        force_recompute: bool = False
    ) -> "RoomAnalysis | None":
        """
        Perform complete self-analysis of room data.
        
        Computes compliance metrics, statistics, quality scores, and recommendations.
        Results are cached in computed_metrics dict.
        
        Args:
            tests: List of test configurations to run (optional)
                  Each test should have: test_id, parameter, standard, threshold
            standards: List of standards to compute (e.g., ['en16798', 'tail']).
                      If None and tests provided, extracts from tests.
            apply_filters: Whether to apply time filters to data
            force_recompute: If True, recompute even if metrics already cached
            
        Returns:
            RoomAnalysis object with all computed metrics, or None if no data available
            
        Examples:
            # Simple analysis with auto-detection
            room.time_series_data = load_data(...)
            analysis = room.compute_metrics()
            
            # Analysis with specific tests
            tests = [
                {
                    'test_id': 'temp_comfort',
                    'parameter': 'temperature',
                    'standard': 'en16798-1',
                    'threshold': {'lower': 20, 'upper': 26},
                    'compliance_level': 95.0
                }
            ]
            analysis = room.compute_metrics(tests=tests)
            
            # Access cached results
            print(room.get_metric('overall_compliance_rate'))
            print(room.get_metric('data_quality_score'))
        """
        # Check if we have data to analyze
        if not self.has_data:
            # Return empty analysis for rooms without data
            from core.domain.models.analysis.room_analysis import RoomAnalysis
            from core.domain.enums.status import Status
            
            return RoomAnalysis(
                entity_id=self.id,
                entity_name=self.name,
                level_id=self.level_id,
                building_id=self.building_id,
                status=Status.FAILED,
                critical_issues=["No data available for analysis"]
            )
        
        # Return cached results if available and not forcing recompute
        if not force_recompute and self.has_metric('room_analysis'):
            return self.get_metric('room_analysis')
        
        # Import analytics components
        from core.analytics.evaluators.threshold_evaluator import ThresholdEvaluator
        from core.analytics.filters.opening_hours_filter import OpeningHoursFilter
        from core.analytics.filters.seasonal_filter import SeasonalFilter
        from core.analytics.metrics.data_quality_metrics import DataQualityMetrics
        from core.analytics.metrics.statistical_metrics import StatisticalMetrics
        from core.domain.enums.parameter_type import ParameterType
        from core.domain.enums.priority import Priority
        from core.domain.enums.standard_type import StandardType
        from core.domain.enums.status import Status
        from core.domain.models.analysis.room_analysis import RoomAnalysis
        from core.domain.value_objects.compliance_threshold import ComplianceThreshold
        from core.domain.value_objects.recommendation import Recommendation
        
        # Initialize analysis
        analysis = RoomAnalysis(
            entity_id=self.id,
            entity_name=self.name,
            level_id=self.level_id,
            building_id=self.building_id,
            data_time_range=self.data_time_range,
            status=Status.IN_PROGRESS,
        )
        
        # Calculate data quality
        analysis.data_completeness = self.get_data_completeness()
        analysis.quality_score = self._calculate_quality_score()
        
        # Calculate parameter statistics
        for parameter in self.available_parameters:
            series = self.get_parameter_data(parameter)
            if series is not None:
                stats = StatisticalMetrics.calculate_basic_statistics(series)
                analysis.parameter_statistics[parameter.value] = stats
        
        # Run compliance tests if provided
        if tests:
            for test_config in tests:
                try:
                    result = self._run_single_test(test_config, apply_filters)
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
        
        # Cache the analysis object
        self.set_metric('room_analysis', analysis)
        self.metrics_computed_at = datetime.now()
        
        return analysis
    
    def _calculate_quality_score(self) -> float:
        """Calculate overall room data quality score."""
        if not self.has_data:
            return 0.0
        
        from core.analytics.metrics.data_quality_metrics import DataQualityMetrics
        
        scores = []
        for parameter in self.available_parameters:
            series = self.get_parameter_data(parameter)
            if series is not None:
                score = DataQualityMetrics.calculate_quality_score(series)
                scores.append(score)
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def _run_single_test(
        self,
        test_config: dict[str, Any],
        apply_filters: bool,
    ) -> "ComplianceResult":
        """Run a single compliance test on room data."""
        from core.analytics.evaluators.threshold_evaluator import ThresholdEvaluator
        from core.analytics.filters.opening_hours_filter import OpeningHoursFilter
        from core.analytics.filters.seasonal_filter import SeasonalFilter
        from core.domain.enums.parameter_type import ParameterType
        from core.domain.enums.standard_type import StandardType
        from core.domain.value_objects.compliance_threshold import ComplianceThreshold
        
        # Extract test configuration
        test_id = test_config["test_id"]
        parameter = test_config["parameter"]
        if isinstance(parameter, str):
            parameter = ParameterType(parameter)
        
        standard = test_config["standard"]
        if isinstance(standard, str):
            standard = StandardType(standard)
        
        # Get parameter data
        data = self.get_parameter_data(parameter)
        if data is None:
            raise ValueError(f"Parameter {parameter.value} not available in room data")
        
        # Apply filters if requested
        if apply_filters and "filter" in test_config:
            filter_config = test_config["filter"]
            # Handle both string and dict filter configs
            if isinstance(filter_config, str):
                filter_dict = {"type": filter_config}
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
    
    def _create_threshold(self, threshold_config: dict[str, Any]) -> "ComplianceThreshold":
        """Create ComplianceThreshold from configuration."""
        from core.domain.value_objects.compliance_threshold import ComplianceThreshold
        
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
    
    def _apply_filter(self, df: pd.DataFrame, filter_config: dict[str, Any]) -> pd.DataFrame:
        """Apply data filter based on configuration."""
        from core.analytics.filters.opening_hours_filter import OpeningHoursFilter
        from core.analytics.filters.seasonal_filter import SeasonalFilter
        
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
    
    def _generate_recommendations(self, analysis: "RoomAnalysis") -> list["Recommendation"]:
        """Generate recommendations based on analysis results."""
        from core.domain.enums.priority import Priority
        from core.domain.value_objects.recommendation import Recommendation
        
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
        for _test_id, result in analysis.compliance_results.items():
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
        if analysis.quality_score < 70:
            recommendations.append(
                Recommendation(
                    title="Data Quality Issue",
                    description=f"Data quality is low ({analysis.quality_score:.1f}%). "
                    "Check sensors and data collection systems.",
                    priority=Priority.MEDIUM
                )
            )
        
        return recommendations
    
    def _identify_critical_issues(self, analysis: "RoomAnalysis") -> list[str]:
        """Identify critical issues requiring immediate attention."""
        issues = []
        
        for _test_id, result in analysis.compliance_results.items():
            if result.compliance_rate < 50:
                severity_breakdown = result.get_severity_breakdown()
                if severity_breakdown.get("critical", 0) > 0:
                    issues.append(
                        f"CRITICAL: {result.parameter.display_name} has {severity_breakdown['critical']} "
                        f"critical violations. Immediate action required."
                    )
        
        return issues
    
    def get_analysis(self) -> "RoomAnalysis | None":
        """
        Get cached analysis results.
        
        Returns:
            Cached RoomAnalysis or None if not computed
        """
        return self.get_metric('room_analysis')

