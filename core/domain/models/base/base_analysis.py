"""Base analysis models for aggregated results.

Provides common structure for room, building, and portfolio analysis results.
"""

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

from core.domain.enums.aggregation_method import AggregationStrategy
from core.domain.enums.parameter_type import ParameterType
from core.domain.enums.status import Status
from core.domain.value_objects.aggregation_config import AggregationConfig
from core.domain.value_objects.recommendation import Recommendation


TEntity = TypeVar("TEntity")
TChildAnalysis = TypeVar("TChildAnalysis")


class BaseAnalysis(BaseModel, Generic[TEntity, TChildAnalysis]):
    """
    Base class for all analysis results.

    Provides common structure for:
    - Room analysis
    - Building analysis
    - Portfolio analysis
    - Any custom analysis aggregations

    Generic types:
    - TEntity: The entity being analyzed (Room, Building, etc.)
    - TChildAnalysis: Type of child analysis results (e.g., BuildingAnalysis has RoomAnalysis children)
    """

    # Entity identification
    entity_id: str = Field(
        ...,
        description="Unique identifier of entity being analyzed"
    )

    entity_name: str = Field(
        ...,
        description="Human-readable name of entity"
    )

    # Analysis metadata
    analysis_timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When analysis was performed"
    )

    status: Status = Field(
        default=Status.COMPLETED,
        description="Analysis status"
    )

    # Additional metadata
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata and context"
    )

    model_config = {"arbitrary_types_allowed": True}

    def to_summary_dict(self) -> dict[str, Any]:
        """
        Get summary as dictionary.

        Override in subclasses to add analysis-specific summary fields.

        Returns:
            Dictionary with analysis summary
        """
        return {
            "entity_id": self.entity_id,
            "entity_name": self.entity_name,
            "status": self.status.value,
            "analysis_timestamp": self.analysis_timestamp.isoformat(),
        }

    def __str__(self) -> str:
        """String representation."""
        return (
            f"{self.__class__.__name__}("
            f"entity={self.entity_name}, "
            f"status={self.status.value})"
        )


class MetricsAnalysis(BaseAnalysis[TEntity, TChildAnalysis]):
    """
    Extended analysis with compliance metrics and recommendations.

    Adds common analysis outputs:
    - Compliance/quality scores
    - Test results and aggregations
    - Parameter statistics
    - Issues and recommendations
    - Violation tracking

    Used for room, building, and portfolio analysis.
    """

    # Aggregated metrics
    compliance_rate: float = Field(
        default=0.0,
        ge=0,
        le=100,
        description="Overall compliance rate (0-100%)"
    )

    quality_score: float = Field(
        default=0.0,
        ge=0,
        le=100,
        description="Data quality score (0-100%)"
    )

    # Standard-specific compliance
    standard_compliance: dict[str, Any] = Field(
        default_factory=dict,
        description="Standard-specific compliance data (e.g., EN 16798-1 category, TAIL rating)"
    )

    # Aggregation configuration for standards
    aggregation_strategy: AggregationStrategy = Field(
        default=AggregationStrategy.STRICT_COMPLIANCE,
        description="Default aggregation strategy for multi-parameter/multi-space analysis"
    )

    # Child entity references
    child_ids: list[str] = Field(
        default_factory=list,
        description="IDs of child entities analyzed"
    )

    child_count: int = Field(
        default=0,
        ge=0,
        description="Number of child entities"
    )

    # Test results aggregation
    test_aggregations: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="Aggregated results per test"
    )

    # Parameter statistics
    parameter_statistics: dict[str, dict[str, float]] = Field(
        default_factory=dict,
        description="Statistics per parameter (mean, std, min, max, etc.)"
    )

    # Rankings/comparisons
    best_performing_children: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Top performing child entities"
    )

    worst_performing_children: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Worst performing child entities"
    )

    # Issues and recommendations
    critical_issues: list[str] = Field(
        default_factory=list,
        description="Critical issues identified"
    )

    recommendations: list[Recommendation] = Field(
        default_factory=list,
        description="Recommended actions"
    )

    @property
    def total_violations(self) -> int:
        """
        Get total violations across all tests.

        Returns:
            Total number of violations
        """
        return sum(
            agg.get("total_violations", 0)
            for agg in self.test_aggregations.values()
        )

    @property
    def test_count(self) -> int:
        """Get number of tests performed."""
        return len(self.test_aggregations)

    @property
    def has_issues(self) -> bool:
        """Check if there are any critical issues."""
        return len(self.critical_issues) > 0

    @property
    def has_recommendations(self) -> bool:
        """Check if there are any recommendations."""
        return len(self.recommendations) > 0

    @property
    def compliance_grade(self) -> str:
        """
        Get letter grade based on compliance rate.

        Returns:
            Letter grade: A, B, C, D, or F
        """
        if self.compliance_rate >= 95:
            return "A"
        elif self.compliance_rate >= 85:
            return "B"
        elif self.compliance_rate >= 75:
            return "C"
        elif self.compliance_rate >= 65:
            return "D"
        else:
            return "F"

    def get_severity_breakdown(self) -> dict[str, int]:
        """
        Get breakdown of violations by severity across all tests.

        Returns:
            Dictionary mapping severity to count
        """
        breakdown = {"minor": 0, "moderate": 0, "major": 0, "critical": 0}

        for test_agg in self.test_aggregations.values():
            severity_data = test_agg.get("severity_breakdown", {})
            for severity, count in severity_data.items():
                if severity in breakdown:
                    breakdown[severity] += count

        return breakdown

    def get_parameter_summary(self, parameter: str) -> dict[str, Any] | None:
        """
        Get summary statistics for a specific parameter.

        Args:
            parameter: Parameter name

        Returns:
            Statistics dictionary, or None if parameter not found
        """
        return self.parameter_statistics.get(parameter)

    def get_test_result(self, test_id: str) -> dict[str, Any] | None:
        """
        Get aggregated result for a specific test.

        Args:
            test_id: Test identifier

        Returns:
            Test aggregation dictionary, or None if test not found
        """
        return self.test_aggregations.get(test_id)

    def add_recommendation(self, recommendation: Recommendation) -> None:
        """
        Add a recommendation to the analysis.

        Args:
            recommendation: Recommendation to add
        """
        self.recommendations.append(recommendation)

    def add_issue(self, issue: str) -> None:
        """
        Add a critical issue to the analysis.

        Args:
            issue: Issue description
        """
        if issue not in self.critical_issues:
            self.critical_issues.append(issue)

    def set_standard_compliance(self, standard: str, compliance_data: dict[str, Any]) -> None:
        """
        Set standard-specific compliance data.

        Supports multiple standards:
        - EN 16798-1: Indoor environmental quality categories (I, II, III, IV)
        - TAIL: Thermal, Acoustic, Indoor Air Quality, Lumious environment rating
$
        Args:
            standard: Standard identifier (e.g., 'en16798-1', 'tail')
            compliance_data: Standard-specific compliance data
        """
        self.standard_compliance[standard] = compliance_data

    def get_standard_compliance(self, standard: str) -> dict[str, Any] | None:
        """
        Get standard-specific compliance data.

        Args:
            standard: Standard identifier (e.g., 'en16798-1', 'tail')

        Returns:
            Compliance data dictionary, or None if standard not evaluated
        """
        return self.standard_compliance.get(standard)

    def get_en16798_category(self) -> str | None:
        """
        Get EN 16798-1 achieved category.

        Returns:
            Category ('I', 'II', 'III', 'IV'), or None if not evaluated
        """
        en16798_data = self.get_standard_compliance("en16798-1")
        if en16798_data:
            return en16798_data.get("achieved_category")
        return None

    def get_tail_rating(self) -> str | None:
        """
        Get TAIL rating.

        Returns:
            TAIL rating (e.g., 'I', 'II', 'III', 'IV'), or None if not evaluated
        """
        tail_data = self.get_standard_compliance("tail")
        if tail_data:
            # Try 'rating' first (for aggregated data), then 'overall_rating_label' (for calculated data)
            rating = tail_data.get("rating") or tail_data.get("overall_rating_label")
            return rating
        return None

    def set_aggregation_strategy(self, strategy: AggregationStrategy) -> None:
        """
        Set the aggregation strategy for standard compliance calculation.

        Args:
            strategy: Aggregation strategy to use
        """
        self.aggregation_strategy = strategy

    def aggregate_child_standard_compliance(
        self,
        child_analyses: list[Any],
        standard: str = "both",
    ) -> None:
        """
        Aggregate standard compliance from child analyses.

        Aggregates both EN 16798-1 and TAIL ratings from children using the
        configured aggregation strategy.

        Args:
            child_analyses: List of child analysis objects (RoomAnalysis or BuildingAnalysis)
            standard: Which standard to aggregate ('en16798-1', 'tail', or 'both')
        """
        if not child_analyses:
            return

        # Determine aggregation method from strategy
        spatial_method = self.aggregation_strategy.spatial_method

        # Map spatial method to aggregation approach
        if spatial_method.value == "worst_space":
            agg_method = "worst"
        elif spatial_method.value in ["occupant_weighted", "area_weighted"]:
            agg_method = "weighted_average"
        else:
            agg_method = "average"

        # Aggregate EN 16798-1 ratings
        if standard in ["en16798-1", "both"]:
            self._aggregate_en16798_from_children(child_analyses, agg_method)

        # Aggregate TAIL ratings
        if standard in ["tail", "both"]:
            self._aggregate_tail_from_children(child_analyses, agg_method)

    def _aggregate_en16798_from_children(
        self,
        child_analyses: list[Any],
        aggregation_method: str,
    ) -> None:
        """
        Aggregate EN 16798-1 ratings from child analyses.
        
        Args:
            child_analyses: List of child analysis objects
            aggregation_method: 'worst', 'average', or 'weighted_average'
        """
        child_categories = []
        child_scores = []

        for child in child_analyses:
            en16798_data = child.get_standard_compliance("en16798-1")
            if en16798_data and "achieved_category" in en16798_data:
                category = en16798_data["achieved_category"]
                if category:
                    child_categories.append(category)
                    score = en16798_data.get("ieq_score", 0.0)
                    child_scores.append(score)

        if not child_categories:
            return

        # Map categories to numeric for aggregation
        category_to_numeric = {"i": 1, "ii": 2, "iii": 3, "iv": 4}
        numeric_to_category = {1: "i", 2: "ii", 3: "iii", 4: "iv"}

        numeric_categories = [
            category_to_numeric.get(cat.lower(), 4) for cat in child_categories
        ]

        # Aggregate based on method
        if aggregation_method == "worst":
            aggregated_category_numeric = max(numeric_categories)
            aggregated_score = min(child_scores) if child_scores else 0.0
        elif aggregation_method == "average":
            aggregated_category_numeric = round(
                sum(numeric_categories) / len(numeric_categories)
            )
            aggregated_score = sum(child_scores) / len(child_scores) if child_scores else 0.0
        else:  # weighted_average
            aggregated_category_numeric = round(
                sum(numeric_categories) / len(numeric_categories)
            )
            aggregated_score = sum(child_scores) / len(child_scores) if child_scores else 0.0

        aggregated_category = numeric_to_category[aggregated_category_numeric]

        # Store aggregated EN 16798-1 data
        en16798_data = {
            "standard": "en16798-1",
            "achieved_category": aggregated_category,
            "ieq_score": aggregated_score,
            "aggregation_method": aggregation_method,
            "child_categories": child_categories,
            "child_count": len(child_categories),
        }

        self.set_standard_compliance("en16798-1", en16798_data)

    def _aggregate_tail_from_children(
        self,
        child_analyses: list[Any],
        aggregation_method: str,
    ) -> None:
        """
        Aggregate TAIL ratings from child analyses.
        
        Args:
            child_analyses: List of child analysis objects
            aggregation_method: 'worst', 'average', or 'weighted_average'
        """
        from core.analytics.calculators.tail_calculator import TAILRatingCalculator

        child_tail_ratings = []

        for child in child_analyses:
            tail_data = child.get_standard_compliance("tail")
            if tail_data:
                child_tail_ratings.append(tail_data)

        if not child_tail_ratings:
            return

        # Use TAILRatingCalculator to aggregate
        aggregated_tail = TAILRatingCalculator.aggregate_ratings(
            child_tail_ratings, aggregation_method
        )

        # Store aggregated TAIL data
        self.set_standard_compliance("tail", aggregated_tail)

    # ============================================================================
    # Direct calculation from Room data
    # ============================================================================

    def calculate_en16798_from_room_data(
        self,
        room: Any,  # Room entity
        outdoor_running_mean_temp: float | None = None,
        season: str = "heating",
    ) -> None:
        """
        Calculate EN 16798-1 compliance directly from room-level time series data.

        This method analyzes the room's time series data to determine which
        EN 16798-1 category is achieved based on actual measurements.

        Args:
            room: Room entity with time_series_data
            outdoor_running_mean_temp: Running mean outdoor temperature for adaptive comfort
            season: "heating" or "cooling" season
        """
        from core.analytics.calculators.en16798_calculator import (
            EN16798StandardCalculator,
            EN16798RoomMetadata,
        )
        from core.domain.enums.en16798_category import EN16798Category

        # Check if room has data
        if not hasattr(room, 'has_data') or not room.has_data:
            return

        # Create room metadata from room entity
        room_metadata = EN16798RoomMetadata(
            room_type=room.room_type or "office",
            floor_area=room.area or 20.0,
            volume=room.volume,
            occupancy_count=room.occupancy,
            ventilation_type=room.ventilation_type,
            pollution_level=room.pollution_level,
            activity_level=room.activity_level,
        )

        # Get available parameters from room data
        import pandas as pd
        df = room.time_series_data
        if df is None or df.empty:
            return

        # Calculate compliance for each category by checking percentage of time within limits
        category_compliance = {}
        parameter_compliance = {}  # Store per-parameter compliance for each category
        
        for category in [
            EN16798Category.CATEGORY_I,
            EN16798Category.CATEGORY_II,
            EN16798Category.CATEGORY_III,
            EN16798Category.CATEGORY_IV,
        ]:
            compliant_hours = 0
            total_hours = len(df)
            
            if total_hours == 0:
                continue

            # Get thresholds for this category
            temp_thresholds = EN16798StandardCalculator.get_temperature_thresholds(
                category, season, outdoor_running_mean_temp, room_metadata.ventilation_type
            )
            co2_threshold = EN16798StandardCalculator.get_co2_threshold(category)
            humidity_thresholds = EN16798StandardCalculator.get_humidity_thresholds(category)

            # Check each row for compliance
            compliant_mask = pd.Series([True] * len(df), index=df.index)
            
            # Initialize parameter compliance tracking for this category
            if category.value not in parameter_compliance:
                parameter_compliance[category.value] = {}

            # Temperature compliance
            if 'temperature' in df.columns:
                temp_compliant = (
                    (df['temperature'] >= temp_thresholds['lower']) &
                    (df['temperature'] <= temp_thresholds['upper'])
                )
                temp_compliance_rate = (temp_compliant.sum() / total_hours) * 100
                parameter_compliance[category.value]['temperature'] = {
                    'compliance_rate': round(temp_compliance_rate, 2),
                    'threshold_lower': temp_thresholds['lower'],
                    'threshold_upper': temp_thresholds['upper']
                }
                compliant_mask = compliant_mask & temp_compliant

            # CO2 compliance
            if 'co2' in df.columns:
                co2_compliant = df['co2'] <= co2_threshold
                co2_compliance_rate = (co2_compliant.sum() / total_hours) * 100
                parameter_compliance[category.value]['co2'] = {
                    'compliance_rate': round(co2_compliance_rate, 2),
                    'threshold': co2_threshold
                }
                compliant_mask = compliant_mask & co2_compliant

            # Humidity compliance (if available)
            if 'humidity' in df.columns:
                humidity_compliant = (
                    (df['humidity'] >= humidity_thresholds['lower']) &
                    (df['humidity'] <= humidity_thresholds['upper'])
                )
                humidity_compliance_rate = (humidity_compliant.sum() / total_hours) * 100
                parameter_compliance[category.value]['humidity'] = {
                    'compliance_rate': round(humidity_compliance_rate, 2),
                    'threshold_lower': humidity_thresholds['lower'],
                    'threshold_upper': humidity_thresholds['upper']
                }
                compliant_mask = compliant_mask & humidity_compliant

            # Calculate compliance rate
            compliant_hours = compliant_mask.sum()
            compliance_rate = (compliant_hours / total_hours) * 100

            category_compliance[category.value] = compliance_rate

        # Determine achieved category (highest category with >= 95% compliance)
        # Note: Category IV is the default/worst category - any room that doesn't meet
        # Cat I, II, or III should be classified as Cat IV
        achieved_category = None
        for category in [
            EN16798Category.CATEGORY_I,
            EN16798Category.CATEGORY_II,
            EN16798Category.CATEGORY_III,
        ]:
            if category_compliance.get(category.value, 0) >= 95.0:
                achieved_category = category.value
                break
        
        # If no category met the 95% threshold, assign Category IV (worst/default)
        if achieved_category is None:
            achieved_category = EN16798Category.CATEGORY_IV.value

        # Calculate overall IEQ score (weighted average of parameter compliance)
        parameter_scores = []
        if 'temperature' in df.columns:
            # For simplicity, use Category II compliance for temperature
            cat2_temp = EN16798StandardCalculator.get_temperature_thresholds(
                EN16798Category.CATEGORY_II, season, outdoor_running_mean_temp, room_metadata.ventilation_type
            )
            temp_compliance = (
                (df['temperature'] >= cat2_temp['lower']) &
                (df['temperature'] <= cat2_temp['upper'])
            ).sum() / len(df) * 100
            parameter_scores.append(temp_compliance)

        if 'co2' in df.columns:
            cat2_co2 = EN16798StandardCalculator.get_co2_threshold(EN16798Category.CATEGORY_II)
            co2_compliance = (df['co2'] <= cat2_co2).sum() / len(df) * 100
            parameter_scores.append(co2_compliance)

        if 'humidity' in df.columns:
            cat2_humidity = EN16798StandardCalculator.get_humidity_thresholds(EN16798Category.CATEGORY_II)
            humidity_compliance = (
                (df['humidity'] >= cat2_humidity['lower']) &
                (df['humidity'] <= cat2_humidity['upper'])
            ).sum() / len(df) * 100
            parameter_scores.append(humidity_compliance)

        ieq_score = sum(parameter_scores) / len(parameter_scores) if parameter_scores else 0.0

        # Store EN 16798-1 compliance data
        en16798_data = {
            "standard": "en16798-1",
            "achieved_category": achieved_category,
            "category_compliance": category_compliance,
            "parameter_compliance": parameter_compliance,  # Add per-parameter compliance
            "ieq_score": round(ieq_score, 2),
            "season": season,
            "adaptive_comfort": outdoor_running_mean_temp is not None,
            "outdoor_running_mean_temp": outdoor_running_mean_temp,
            "calculation_method": "time_series_analysis",
            "total_hours_analyzed": len(df),
        }

        self.set_standard_compliance("en16798-1", en16798_data)

    def calculate_tail_from_room_data(
        self,
        room: Any,  # Room entity
        parameter_thresholds: dict[str, dict[str, float]] | None = None,
        building_type: Any | None = None,  # BuildingType enum
        room_type: Any | None = None,  # RoomType enum
    ) -> None:
        """
        Calculate TAIL rating directly from room-level time series data.

        This method analyzes the room's time series data to determine TAIL ratings
        for each category (Thermal, Acoustic, Indoor Air Quality, Luminous).

        Args:
            room: Room entity with time_series_data
            parameter_thresholds: Optional custom thresholds for parameters
                                 Format: {parameter: {'lower': val, 'upper': val}}
                                 If None, loads from TAIL config files
            building_type: BuildingType enum for building-specific config
            room_type: RoomType enum for room-specific config
        """
        from core.analytics.calculators.tail_calculator import TAILRatingCalculator
        from core.domain.enums.tail_config import tail_config_loader
        from core.domain.enums.parameter_type import ParameterType

        # Check if room has data
        if not hasattr(room, 'has_data') or not room.has_data:
            return

        import pandas as pd
        df = room.time_series_data
        if df is None or df.empty:
            return

        # Load thresholds from config if not provided
        if parameter_thresholds is None:
            parameter_thresholds = {}
            
            # Map common column names to ParameterType
            column_to_param_map = {
                'temperature': ParameterType.TEMPERATURE,
                'temp': ParameterType.TEMPERATURE,
                'humidity': ParameterType.HUMIDITY,
                'humid': ParameterType.HUMIDITY,
                'rh': ParameterType.HUMIDITY,
                'co2': ParameterType.CO2,
                'pm25': ParameterType.PM25,
                'pm2.5': ParameterType.PM25,
                'voc': ParameterType.VOC,
                'formaldehyde': ParameterType.FORMALDEHYDE,
                'benzene': ParameterType.BENZENE,
                'radon': ParameterType.RADON,
                'noise': ParameterType.NOISE,
                'sound': ParameterType.NOISE,
                'illuminance': ParameterType.ILLUMINANCE,
                'lux': ParameterType.ILLUMINANCE,
                'daylight_factor': ParameterType.DAYLIGHT_FACTOR,
            }
            
            # Load threshold for each parameter found in the data
            for col in df.columns:
                if col.lower() in ['timestamp', 'time']:
                    continue
                    
                col_lower = col.lower()
                if col_lower in column_to_param_map:
                    param_type = column_to_param_map[col_lower]
                    
                    try:
                        # Get config from YAML
                        param_config = tail_config_loader.get_parameter_config(
                            param_type, 
                            building_type=building_type,
                            room_type=room_type
                        )
                        
                        if param_config and 'thresholds' in param_config:
                            thresholds = param_config['thresholds']
                            
                            # Convert YAML config to simple lower/upper format
                            # Using "green" (best) thresholds as the target range
                            if 'green' in thresholds:
                                green = thresholds['green']
                                parameter_thresholds[col] = {
                                    'lower': green.get('min', float('-inf')),
                                    'upper': green.get('max', float('inf'))
                                }
                            # Fallback for older format
                            elif 'category_1_min' in thresholds or 'category_1_max' in thresholds:
                                parameter_thresholds[col] = {
                                    'lower': thresholds.get('category_1_min', float('-inf')),
                                    'upper': thresholds.get('category_1_max', float('inf'))
                                }
                    except (KeyError, ValueError, FileNotFoundError) as e:
                        # If config not found, use fallback defaults
                        print(f"Warning: Could not load TAIL config for {col}: {e}")
                        # Use simple defaults as fallback
                        fallback_thresholds = self._get_fallback_thresholds()
                        if col_lower in fallback_thresholds:
                            parameter_thresholds[col] = fallback_thresholds[col_lower]

        # Calculate compliance for each parameter
        parameter_compliance = {}
        
        for param in df.columns:
            if param in ['timestamp', 'time']:
                continue

            param_data = df[param]
            
            # Get threshold for this parameter
            if param in parameter_thresholds:
                threshold = parameter_thresholds[param]
                lower = threshold.get('lower', float('-inf'))
                upper = threshold.get('upper', float('inf'))

                # Calculate compliance
                compliant = (param_data >= lower) & (param_data <= upper)
                compliance_rate = (compliant.sum() / len(param_data)) * 100
            else:
                # No threshold defined, assume 100% compliance
                compliance_rate = 100.0

            parameter_compliance[param] = compliance_rate

        # Use TAILRatingCalculator to determine ratings
        tail_result = TAILRatingCalculator.calculate_from_measured_values(
            measured_values={
                param: df[param].mean() for param in parameter_compliance.keys()
            },
            thresholds=parameter_thresholds,
        )

        # Enhance with compliance rates
        for param, compliance in parameter_compliance.items():
            if param in tail_result['parameters']:
                tail_result['parameters'][param]['compliance_rate'] = round(compliance, 2)
                tail_result['parameters'][param]['rating'] = TAILRatingCalculator.compliance_to_rating(compliance)
                tail_result['parameters'][param]['rating_label'] = TAILRatingCalculator.rating_to_label(
                    tail_result['parameters'][param]['rating']
                )

        # Recalculate category ratings based on compliance
        category_ratings = {"thermal": [], "acoustic": [], "iaq": [], "luminous": []}
        
        for param, compliance in parameter_compliance.items():
            category = TAILRatingCalculator.get_parameter_category(param)
            if category:
                rating = TAILRatingCalculator.compliance_to_rating(compliance)
                category_ratings[category].append(rating)

        # Calculate category ratings (worst parameter in category)
        tail_categories = {}
        for category, ratings in category_ratings.items():
            if ratings:
                worst_rating = max(ratings)  # Worst rating (highest number)
                avg_compliance = sum([
                    parameter_compliance[p] for p in parameter_compliance
                    if TAILRatingCalculator.get_parameter_category(p) == category
                ]) / len(ratings)
                
                tail_categories[category] = {
                    "rating": worst_rating,
                    "rating_label": TAILRatingCalculator.rating_to_label(worst_rating),
                    "average_compliance": round(avg_compliance, 2),
                    "parameter_count": len(ratings),
                }
            else:
                tail_categories[category] = {
                    "rating": None,
                    "rating_label": "N/A",
                    "average_compliance": 0.0,
                    "parameter_count": 0,
                }

        # Overall rating (worst category)
        measured_categories = [
            cat["rating"] for cat in tail_categories.values() if cat["rating"] is not None
        ]
        overall_rating = max(measured_categories) if measured_categories else None

        # Store TAIL compliance data
        tail_data = {
            "overall_rating": overall_rating,
            "overall_rating_label": TAILRatingCalculator.rating_to_label(overall_rating),
            "categories": tail_categories,
            "parameters": {
                param: {
                    "compliance_rate": round(compliance, 2),
                    "rating": TAILRatingCalculator.compliance_to_rating(compliance),
                    "rating_label": TAILRatingCalculator.rating_to_label(
                        TAILRatingCalculator.compliance_to_rating(compliance)
                    ),
                }
                for param, compliance in parameter_compliance.items()
            },
            "calculation_method": "time_series_analysis",
            "total_hours_analyzed": len(df),
        }

        self.set_standard_compliance("tail", tail_data)

    @staticmethod
    def _get_fallback_thresholds() -> dict[str, dict[str, float]]:
        """
        Get fallback thresholds when TAIL config cannot be loaded.
        
        These are simple defaults based on common standards.
        """
        return {
            # Thermal parameters
            'temperature': {'lower': 20.0, 'upper': 26.0},
            'temp': {'lower': 20.0, 'upper': 26.0},
            'humidity': {'lower': 30, 'upper': 60},
            'humid': {'lower': 30, 'upper': 60},
            'rh': {'lower': 30, 'upper': 60},
            # Indoor Air Quality parameters
            'co2': {'lower': 0, 'upper': 970},  # Green threshold from TAIL
            'voc': {'lower': 0, 'upper': 500},
            'formaldehyde': {'lower': 0, 'upper': 30},
            'benzene': {'lower': 0, 'upper': 2},
            'radon': {'lower': 0, 'upper': 100},
            # Luminous parameters
            'lux': {'lower': 300, 'upper': 500},
            'illuminance': {'lower': 300, 'upper': 500},
            'daylight_factor': {'lower': 2.0, 'upper': 5.0},
            # Acoustic parameters
            'noise': {'lower': 0, 'upper': 35},
            'sound': {'lower': 0, 'upper': 35},
        }

    # ============================================================================
    # EN 16798-1 Category Utilities
    # ============================================================================

    @staticmethod
    def category_to_numeric(category: str) -> int:
        """
        Convert EN 16798-1 category to numeric value.
        
        Args:
            category: Category string ('I', 'II', 'III', 'IV')
            
        Returns:
            Numeric value (1=I, 2=II, 3=III, 4=IV)
        """
        mapping = {"i": 1, "ii": 2, "iii": 3, "iv": 4}
        return mapping.get(category.lower(), 4)

    @staticmethod
    def numeric_to_category(numeric: int) -> str:
        """
        Convert numeric value to EN 16798-1 category.
        
        Args:
            numeric: Numeric value (1-4)
            
        Returns:
            Category string ('i', 'ii', 'iii', 'iv')
        """
        mapping = {1: "i", 2: "ii", 3: "iii", 4: "iv"}
        return mapping.get(numeric, "iv")

    def score_to_category(
        self,
        score: float,
        config: AggregationConfig | None = None,
    ) -> str:
        """
        Convert a compliance score (0-100%) to EN 16798-1 category.

        Args:
            score: Compliance score (0-100%)
            config: Aggregation config with thresholds (uses defaults if None)

        Returns:
            Category: 'i', 'ii', 'iii', or 'iv'
        """
        if config is None:
            config = AggregationConfig.balanced_compliance()

        if score >= config.category_1_threshold:
            return "i"
        elif score >= config.category_2_threshold:
            return "ii"
        elif score >= config.category_3_threshold:
            return "iii"
        else:
            return "iv"

    # ============================================================================
    # Generic Aggregation Methods
    # ============================================================================

    def get_compliance_category(
        self,
        percent_in_cat1: float,
        percent_in_cat2: float,
        percent_in_cat3: float,
        cat1_threshold: float = 95.0,
        cat2_threshold: float = 90.0,
        cat3_threshold: float = 85.0,
    ) -> str:
        """
        Determine EN 16798-1 category compliance based on time within category limits.

        Args:
            percent_in_cat1: % of occupied time within Category I limits
            percent_in_cat2: % of occupied time within Category II limits
            percent_in_cat3: % of occupied time within Category III limits
            cat1_threshold: Threshold for Category I (default 95%)
            cat2_threshold: Threshold for Category II (default 90%)
            cat3_threshold: Threshold for Category III (default 85%)

        Returns:
            'I', 'II', 'III', or 'IV' (non-compliant)
        """
        if percent_in_cat1 >= cat1_threshold:
            return "I"
        elif percent_in_cat2 >= cat2_threshold:
            return "II"
        elif percent_in_cat3 >= cat3_threshold:
            return "III"
        else:
            return "IV"

    def aggregate_parameters_worst_case(
        self,
        room_results: dict[ParameterType, str]
    ) -> str:
        """
        Aggregate multiple parameters using worst-parameter method.

        Conservative EN 16798-1 approach: room category = worst parameter category.

        Args:
            room_results: Dict mapping ParameterType -> category ("I", "II", "III", "IV")

        Returns:
            Overall room category (worst among all parameters)
        """
        if not room_results:
            return "IV"

        worst_numeric = max(
            self.category_to_numeric(cat)
            for cat in room_results.values()
        )

        return self.numeric_to_category(worst_numeric).upper()

    def aggregate_parameters_weighted(
        self,
        room_results: dict[ParameterType, float],
        weights: dict[ParameterType, float] | None = None,
    ) -> float:
        """
        Aggregate multiple parameters using weighted average.

        Produces continuous IEQ score (0-100%) instead of categorical result.

        Args:
            room_results: Dict mapping ParameterType -> compliance rate (0-100%)
            weights: Optional custom weights (must sum to 1.0)

        Returns:
            Weighted IEQ score (0-100%)
        """
        if not room_results:
            return 0.0

        # Use provided weights or defaults
        if weights is None:
            from core.domain.enums.aggregation_method import ParameterAggregationMethod
            param_method = ParameterAggregationMethod.WEIGHTED_AVERAGE
            weights = param_method.default_weights

        # Calculate weighted sum
        weighted_sum = 0.0
        total_weight = 0.0

        for param, score in room_results.items():
            weight = weights.get(param, 0.0)
            if weight > 0:
                weighted_sum += weight * score
                total_weight += weight

        # Normalize
        if total_weight > 0:
            return weighted_sum / total_weight
        else:
            # Fallback to unweighted average
            return sum(room_results.values()) / len(room_results)

    def aggregate_spaces_worst_case(
        self,
        space_categories: dict[str, str]
    ) -> str:
        """
        Aggregate multiple spaces using worst-space method.

        Strict compliance: overall category = worst space category.

        Args:
            space_categories: Dict mapping space_id -> category ("I", "II", "III", "IV")

        Returns:
            Overall category (worst among all spaces)
        """
        if not space_categories:
            return "IV"

        worst_numeric = max(
            self.category_to_numeric(cat)
            for cat in space_categories.values()
        )

        return self.numeric_to_category(worst_numeric).upper()

    def aggregate_spaces_occupant_weighted(
        self,
        space_scores: dict[str, float],
        occupancy_hours: dict[str, float],
    ) -> float:
        """
        Aggregate multiple spaces using occupant-weighted method.

        Weight each space by occupancy hours - most representative of occupant experience.

        Args:
            space_scores: Dict mapping space_id -> IEQ score (0-100%)
            occupancy_hours: Dict mapping space_id -> total occupied hours

        Returns:
            Occupant-weighted IEQ score (0-100%)
        """
        if not space_scores or not occupancy_hours:
            return 0.0

        weighted_sum = 0.0
        total_hours = 0.0

        for space_id, score in space_scores.items():
            hours = occupancy_hours.get(space_id, 0.0)
            if hours > 0:
                weighted_sum += score * hours
                total_hours += hours

        if total_hours > 0:
            return weighted_sum / total_hours
        else:
            return sum(space_scores.values()) / len(space_scores)

    def aggregate_spaces_area_weighted(
        self,
        space_scores: dict[str, float],
        space_areas: dict[str, float],
    ) -> float:
        """
        Aggregate multiple spaces using area-weighted method.

        Weight each space by floor area - practical when occupancy data unavailable.

        Args:
            space_scores: Dict mapping space_id -> IEQ score (0-100%)
            space_areas: Dict mapping space_id -> floor area (m²)

        Returns:
            Area-weighted IEQ score (0-100%)
        """
        if not space_scores or not space_areas:
            return 0.0

        weighted_sum = 0.0
        total_area = 0.0

        for space_id, score in space_scores.items():
            area = space_areas.get(space_id, 0.0)
            if area > 0:
                weighted_sum += score * area
                total_area += area

        if total_area > 0:
            return weighted_sum / total_area
        else:
            return sum(space_scores.values()) / len(space_scores)

    # ============================================================================
    # Summary and String Representation
    # ============================================================================

    def to_summary_dict(self) -> dict[str, Any]:
        """Get summary including metrics."""
        summary = super().to_summary_dict()
        summary.update({
            "child_count": self.child_count,
            "compliance_rate": round(self.compliance_rate, 2),
            "compliance_grade": self.compliance_grade,
            "quality_score": round(self.quality_score, 2),
            "total_violations": self.total_violations,
            "test_count": self.test_count,
            "critical_issues_count": len(self.critical_issues),
            "recommendations_count": len(self.recommendations),
            "severity_breakdown": self.get_severity_breakdown(),
            "aggregation_strategy": self.aggregation_strategy.value,
        })
        
        # Add standard compliance if available
        if self.standard_compliance:
            summary["standard_compliance"] = {}
            
            # EN 16798-1
            en16798_category = self.get_en16798_category()
            if en16798_category:
                summary["standard_compliance"]["en16798_1"] = {
                    "category": en16798_category,
                    "full_data": self.get_standard_compliance("en16798-1"),
                }
            
            # TAIL
            tail_rating = self.get_tail_rating()
            if tail_rating:
                summary["standard_compliance"]["tail"] = {
                    "rating": tail_rating,
                    "full_data": self.get_standard_compliance("tail"),
                }
        
        return summary

    def __str__(self) -> str:
        """String representation."""
        return (
            f"{self.__class__.__name__}("
            f"entity={self.entity_name}, "
            f"children={self.child_count}, "
            f"compliance={self.compliance_rate:.1f}% [{self.compliance_grade}])"
        )
