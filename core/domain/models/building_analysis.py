"""Building analysis result model."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from core.domain.enums.aggregation_method import (
    ParameterAggregationMethod,
    SpatialAggregationMethod,
)
from core.domain.enums.parameter_type import ParameterType
from core.domain.enums.status import Status
from core.domain.value_objects.aggregation_config import (
    AggregationConfig,
    RoomAggregationResult,
)
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
    level_ids: list[str] = Field(default_factory=list, description="Level IDs analyzed")
    room_ids: list[str] = Field(default_factory=list, description="Room IDs analyzed")
    level_count: int = Field(default=0, description="Number of levels")
    room_count: int = Field(default=0, description="Number of rooms analyzed")

    # Aggregated metrics
    avg_compliance_rate: float = Field(
        default=0.0, ge=0, le=100, description="Average compliance across all rooms"
    )
    avg_quality_score: float = Field(
        default=0.0, ge=0, le=100, description="Average data quality score"
    )

    # EN 16798-1 Category Assessment
    aggregation_config: AggregationConfig | None = Field(
        default=None,
        description="Configuration used for multi-parameter and multi-space aggregation"
    )
    building_category: str | None = Field(
        default=None,
        description="Overall building category (I, II, III, or IV) based on aggregation"
    )
    building_ieq_score: float | None = Field(
        default=None,
        ge=0,
        le=100,
        description="Continuous IEQ score 0-100% (when using weighted aggregation)"
    )

    # Room-level aggregation results
    room_aggregations: dict[str, RoomAggregationResult] = Field(
        default_factory=dict,
        description="Detailed aggregation results per room"
    )

    # Parameter-level building statistics
    parameter_categories: dict[ParameterType, str] = Field(
        default_factory=dict,
        description="Building-level category per parameter (I, II, III, IV)"
    )
    parameter_scores: dict[ParameterType, float] = Field(
        default_factory=dict,
        description="Building-level compliance score per parameter (0-100%)"
    )

    # Test aggregations (test_id -> aggregated metrics)
    test_aggregations: dict[str, dict[str, Any]] = Field(
        default_factory=dict, description="Aggregated results per test across building"
    )

    # Rankings
    best_performing_rooms: list[dict[str, Any]] = Field(
        default_factory=list, description="Top performing rooms"
    )
    worst_performing_rooms: list[dict[str, Any]] = Field(
        default_factory=list, description="Worst performing rooms"
    )

    # Statistics by parameter
    parameter_statistics: dict[str, dict[str, float]] = Field(
        default_factory=dict, description="Building-wide statistics per parameter"
    )

    # Issues and recommendations
    critical_issues: list[str] = Field(default_factory=list, description="Building-wide issues")
    recommendations: list[Recommendation] = Field(
        default_factory=list, description="Building-wide recommendations"
    )

    # Climate correlation (if weather data available)
    climate_correlations: dict[str, float] = Field(
        default_factory=dict, description="Correlations with outdoor climate"
    )

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    model_config = {"arbitrary_types_allowed": True}  # Allow Recommendation

    @property
    def total_violations(self) -> int:
        """Get total violations from test aggregations."""
        return sum(
            agg.get("total_violations", 0) for agg in self.test_aggregations.values()
        )

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

        category_to_numeric = {"I": 1, "II": 2, "III": 3, "IV": 4}
        numeric_to_category = {1: "I", 2: "II", 3: "III", 4: "IV"}

        worst_numeric = max(
            category_to_numeric.get(cat, 4)
            for cat in room_results.values()
        )

        return numeric_to_category[worst_numeric]

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
        room_categories: dict[str, str]
    ) -> str:
        """
        Aggregate multiple rooms using worst-space method.

        Strict compliance: building category = worst room category.

        Args:
            room_categories: Dict mapping room_id -> category ("I", "II", "III", "IV")

        Returns:
            Overall building category (worst among all rooms)
        """
        if not room_categories:
            return "IV"

        category_to_numeric = {"I": 1, "II": 2, "III": 3, "IV": 4}
        numeric_to_category = {1: "I", 2: "II", 3: "III", 4: "IV"}

        worst_numeric = max(
            category_to_numeric.get(cat, 4)
            for cat in room_categories.values()
        )

        return numeric_to_category[worst_numeric]

    def aggregate_spaces_occupant_weighted(
        self,
        room_scores: dict[str, float],
        occupancy_hours: dict[str, float],
    ) -> float:
        """
        Aggregate multiple rooms using occupant-weighted method.

        Weight each room by occupancy hours - most representative of occupant experience.

        Args:
            room_scores: Dict mapping room_id -> IEQ score (0-100%)
            occupancy_hours: Dict mapping room_id -> total occupied hours

        Returns:
            Occupant-weighted building IEQ score (0-100%)
        """
        if not room_scores or not occupancy_hours:
            return 0.0

        weighted_sum = 0.0
        total_hours = 0.0

        for room_id, score in room_scores.items():
            hours = occupancy_hours.get(room_id, 0.0)
            if hours > 0:
                weighted_sum += score * hours
                total_hours += hours

        if total_hours > 0:
            return weighted_sum / total_hours
        else:
            return sum(room_scores.values()) / len(room_scores)

    def aggregate_spaces_area_weighted(
        self,
        room_scores: dict[str, float],
        room_areas: dict[str, float],
    ) -> float:
        """
        Aggregate multiple rooms using area-weighted method.

        Weight each room by floor area - practical when occupancy data unavailable.

        Args:
            room_scores: Dict mapping room_id -> IEQ score (0-100%)
            room_areas: Dict mapping room_id -> floor area (m²)

        Returns:
            Area-weighted building IEQ score (0-100%)
        """
        if not room_scores or not room_areas:
            return 0.0

        weighted_sum = 0.0
        total_area = 0.0

        for room_id, score in room_scores.items():
            area = room_areas.get(room_id, 0.0)
            if area > 0:
                weighted_sum += score * area
                total_area += area

        if total_area > 0:
            return weighted_sum / total_area
        else:
            return sum(room_scores.values()) / len(room_scores)

    def _score_to_category(
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
            Category: "I", "II", "III", or "IV"
        """
        if config is None:
            config = AggregationConfig.balanced_compliance()

        if score >= config.category_1_threshold:
            return "I"
        elif score >= config.category_2_threshold:
            return "II"
        elif score >= config.category_3_threshold:
            return "III"
        else:
            return "IV"

    def apply_aggregation_strategy(
        self,
        config: AggregationConfig | None = None,
    ) -> None:
        """
        Apply aggregation strategy to compute building-level category and score.

        This is the main method that orchestrates the full aggregation process:
        1. Filter rooms and parameters based on config
        2. Aggregate parameters within each room
        3. Aggregate rooms to building level
        4. Store results

        Args:
            config: Aggregation configuration (uses balanced_compliance if None)
        """
        if config is None:
            config = AggregationConfig.balanced_compliance()

        self.aggregation_config = config

        # Get effective methods
        config.get_effective_parameter_method()
        spatial_method = config.get_effective_spatial_method()

        # Full aggregation logic
        if self.room_aggregations:
            # Filter rooms based on configuration
            filtered_rooms = {
                room_id: result
                for room_id, result in self.room_aggregations.items()
                if config.should_include_room(room_id, result.is_critical_space)
            }

            if not filtered_rooms:
                # No rooms to aggregate - set defaults
                self.building_category = "IV"
                self.building_ieq_score = 0.0
                return

            # --- Step 1: Aggregate building-level parameter statistics ---
            # Collect all parameters across all rooms
            all_parameters = set()
            for room_result in filtered_rooms.values():
                all_parameters.update(room_result.parameter_results.keys())

            # Filter parameters based on configuration
            included_parameters = {
                param for param in all_parameters
                if config.should_include_parameter(param)
            }

            # For each parameter, aggregate across rooms
            for param in included_parameters:
                # Collect room-level results for this parameter
                param_room_results = {}
                param_room_scores = {}

                for room_id, room_result in filtered_rooms.items():
                    if param in room_result.parameter_results:
                        param_result = room_result.parameter_results[param]
                        param_room_results[room_id] = param_result.category
                        param_room_scores[room_id] = param_result.compliance_rate

                if not param_room_results:
                    continue

                # Aggregate parameter across rooms using spatial method
                if spatial_method == SpatialAggregationMethod.WORST_SPACE:
                    # Building parameter category = worst room for this parameter
                    self.parameter_categories[param] = self.aggregate_spaces_worst_case(
                        param_room_results
                    )
                    # Use worst score as well
                    self.parameter_scores[param] = min(param_room_scores.values())

                elif spatial_method == SpatialAggregationMethod.OCCUPANT_WEIGHTED:
                    # Weight by occupancy hours
                    occupancy = {
                        room_id: filtered_rooms[room_id].total_occupied_hours
                        for room_id in param_room_scores.keys()
                    }
                    self.parameter_scores[param] = self.aggregate_spaces_occupant_weighted(
                        param_room_scores, occupancy
                    )
                    # Convert score to category using thresholds
                    self.parameter_categories[param] = self._score_to_category(
                        self.parameter_scores[param], config
                    )

                elif spatial_method == SpatialAggregationMethod.AREA_WEIGHTED:
                    # Weight by floor area
                    areas = {
                        room_id: filtered_rooms[room_id].floor_area_m2 or 0.0
                        for room_id in param_room_scores.keys()
                    }
                    self.parameter_scores[param] = self.aggregate_spaces_area_weighted(
                        param_room_scores, areas
                    )
                    # Convert score to category
                    self.parameter_categories[param] = self._score_to_category(
                        self.parameter_scores[param], config
                    )

                else:  # SIMPLE_AVERAGE or CRITICAL_SPACES_ONLY
                    # Simple average across rooms
                    self.parameter_scores[param] = (
                        sum(param_room_scores.values()) / len(param_room_scores)
                    )
                    # Convert score to category
                    self.parameter_categories[param] = self._score_to_category(
                        self.parameter_scores[param], config
                    )

            # --- Step 2: Aggregate room categories to building level ---
            # Use filtered room-level overall categories and scores
            room_categories = {
                room_id: result.overall_category
                for room_id, result in filtered_rooms.items()
            }

            room_scores = {
                room_id: result.ieq_score
                for room_id, result in filtered_rooms.items()
            }

            # Determine building category based on spatial method
            if spatial_method == SpatialAggregationMethod.WORST_SPACE:
                self.building_category = self.aggregate_spaces_worst_case(room_categories)
            else:
                # For weighted methods, use the IEQ score to derive category
                # First calculate the building IEQ score
                if spatial_method == SpatialAggregationMethod.OCCUPANT_WEIGHTED:
                    occupancy = {
                        room_id: result.total_occupied_hours
                        for room_id, result in filtered_rooms.items()
                    }
                    self.building_ieq_score = self.aggregate_spaces_occupant_weighted(
                        room_scores, occupancy
                    )
                elif spatial_method == SpatialAggregationMethod.AREA_WEIGHTED:
                    areas = {
                        room_id: result.floor_area_m2 or 0.0
                        for room_id, result in filtered_rooms.items()
                    }
                    self.building_ieq_score = self.aggregate_spaces_area_weighted(
                        room_scores, areas
                    )
                else:  # SIMPLE_AVERAGE or CRITICAL_SPACES_ONLY
                    self.building_ieq_score = (
                        sum(room_scores.values()) / len(room_scores)
                        if room_scores else 0.0
                    )

                # Convert building IEQ score to category
                self.building_category = self._score_to_category(
                    self.building_ieq_score or 0.0, config
                )

            # For WORST_SPACE, also calculate IEQ score (even though category is from worst room)
            if spatial_method == SpatialAggregationMethod.WORST_SPACE and self.building_ieq_score is None:
                # Use simple average for informational purposes
                self.building_ieq_score = (
                    sum(room_scores.values()) / len(room_scores)
                    if room_scores else 0.0
                )
        else:
            # No room aggregations available - fall back to avg_compliance_rate
            # This handles legacy use cases or partial implementations
            self.building_ieq_score = self.avg_compliance_rate
            self.building_category = self._score_to_category(
                self.avg_compliance_rate, config
            )

    def get_aggregation_summary(self) -> dict[str, Any]:
        """Get summary of aggregation configuration and results."""
        if not self.aggregation_config:
            return {}

        return {
            "strategy": self.aggregation_config.strategy.value,
            "parameter_method": self.aggregation_config.get_effective_parameter_method().value,
            "spatial_method": self.aggregation_config.get_effective_spatial_method().value,
            "building_category": self.building_category,
            "building_ieq_score": round(self.building_ieq_score, 2) if self.building_ieq_score else None,
            "rooms_evaluated": len(self.room_aggregations),
            "parameters_evaluated": len(self.parameter_categories),
            "thresholds": {
                "category_I": self.aggregation_config.category_1_threshold,
                "category_II": self.aggregation_config.category_2_threshold,
                "category_III": self.aggregation_config.category_3_threshold,
            },
        }

    def get_room_ranking(self, by: str = "compliance") -> list[dict[str, Any]]:
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

    def to_summary_dict(self) -> dict[str, Any]:
        """Get summary as dictionary."""
        summary = {
            "building_id": self.building_id,
            "building_name": self.building_name,
            "status": self.status.value,
            "analysis_timestamp": self.analysis_timestamp.isoformat(),
            "level_count": self.level_count,
            "room_count": self.room_count,
            "avg_compliance_rate": round(self.avg_compliance_rate, 2),
            "avg_quality_score": round(self.avg_quality_score, 2),
            "total_violations": self.total_violations,
            "test_count": len(self.test_aggregations),
            "critical_issues_count": len(self.critical_issues),
            "recommendations_count": len(self.recommendations),
        }

        # Add aggregation results if available
        if self.aggregation_config:
            summary["aggregation"] = self.get_aggregation_summary()

        return summary

    def __str__(self) -> str:
        """String representation."""
        base = (
            f"BuildingAnalysis(building={self.building_name}, "
            f"rooms={self.room_count}, "
            f"compliance={self.avg_compliance_rate:.1f}%"
        )

        if self.building_category:
            base += f", category={self.building_category}"

        if self.building_ieq_score is not None:
            base += f", IEQ_score={self.building_ieq_score:.1f}"

        return base + ")"
