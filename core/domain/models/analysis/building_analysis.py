"""Building analysis result model."""

from typing import Any

from pydantic import Field

from core.domain.enums.aggregation_method import (
    ParameterAggregationMethod,
    SpatialAggregationMethod,
)
from core.domain.enums.parameter_type import ParameterType
from core.domain.models.base.base_analysis import MetricsAnalysis
from core.domain.models.analysis.room_analysis import RoomAnalysis
from core.domain.value_objects.aggregation_config import (
    AggregationConfig,
    RoomAggregationResult,
)


class BuildingAnalysis(MetricsAnalysis[None, RoomAnalysis]):
    """
    Aggregated analysis results for a building.

    Summarizes room-level analyses and provides building-wide insights.
    Extends MetricsAnalysis with EN 16798-1 aggregation and building-specific features.
    """

    # Structure references (building-specific)
    level_ids: list[str] = Field(default_factory=list, description="Level IDs analyzed")

    # EN 16798-1 Category Assessment (building-specific)
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

    # Room-level aggregation results (building-specific)
    room_aggregations: dict[str, RoomAggregationResult] = Field(
        default_factory=dict,
        description="Detailed aggregation results per room"
    )

    # Parameter-level building statistics (building-specific)
    parameter_categories: dict[ParameterType, str] = Field(
        default_factory=dict,
        description="Building-level category per parameter (I, II, III, IV)"
    )
    parameter_scores: dict[ParameterType, float] = Field(
        default_factory=dict,
        description="Building-level compliance score per parameter (0-100%)"
    )

    # Climate correlation (building-specific)
    climate_correlations: dict[str, float] = Field(
        default_factory=dict, description="Correlations with outdoor climate"
    )

    # Aliases for backward compatibility
    @property
    def building_id(self) -> str:
        """Alias for entity_id."""
        return self.entity_id

    @property
    def building_name(self) -> str:
        """Alias for entity_name."""
        return self.entity_name

    @property
    def room_ids(self) -> list[str]:
        """Alias for child_ids."""
        return self.child_ids

    @property
    def room_count(self) -> int:
        """Alias for child_count."""
        return self.child_count

    @property
    def level_count(self) -> int:
        """Get number of levels."""
        return len(self.level_ids)

    @property
    def avg_compliance_rate(self) -> float:
        """Alias for compliance_rate."""
        return self.compliance_rate

    @property
    def avg_quality_score(self) -> float:
        """Alias for quality_score."""
        return self.quality_score

    def _score_to_category(
        self,
        score: float,
        config: AggregationConfig | None = None,
    ) -> str:
        """
        Deprecated: Use score_to_category() from MetricsAnalysis base class.
        Kept for backward compatibility.
        """
        return self.score_to_category(score, config)

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
                    self.parameter_categories[param] = self.score_to_category(
                        self.parameter_scores[param], config
                    ).upper()

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
                    self.parameter_categories[param] = self.score_to_category(
                        self.parameter_scores[param], config
                    ).upper()

                else:  # SIMPLE_AVERAGE or CRITICAL_SPACES_ONLY
                    # Simple average across rooms
                    self.parameter_scores[param] = (
                        sum(param_room_scores.values()) / len(param_room_scores)
                    )
                    # Convert score to category
                    self.parameter_categories[param] = self.score_to_category(
                        self.parameter_scores[param], config
                    ).upper()

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
                self.building_category = self.score_to_category(
                    self.building_ieq_score or 0.0, config
                ).upper()

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
            self.building_ieq_score = self.compliance_rate
            self.building_category = self.score_to_category(
                self.compliance_rate, config
            ).upper()

    def set_en16798_compliance(
        self,
        aggregation_config: AggregationConfig | None = None,
    ) -> None:
        """
        Calculate and set EN 16798-1 standard compliance for the building.

        This method aggregates room-level EN 16798-1 categories using the configured
        aggregation method to determine the building-level category.

        Args:
            aggregation_config: Aggregation configuration (uses current or balanced_compliance if None)
        """
        if aggregation_config is None:
            aggregation_config = self.aggregation_config or AggregationConfig.balanced_compliance()
        
        # Apply the full aggregation strategy
        self.apply_aggregation_strategy(aggregation_config)
        
        # Store EN 16798-1 specific compliance data
        en16798_data = {
            "standard": "en16798-1",
            "achieved_category": self.building_category,
            "ieq_score": self.building_ieq_score,
            "aggregation_method": {
                "parameter": aggregation_config.get_effective_parameter_method().value,
                "spatial": aggregation_config.get_effective_spatial_method().value,
                "strategy": aggregation_config.strategy.value,
            },
            "parameter_categories": {
                param.value: category
                for param, category in self.parameter_categories.items()
            },
            "parameter_scores": {
                param.value: score
                for param, score in self.parameter_scores.items()
            },
            "room_count": len(self.room_aggregations),
        }
        
        self.set_standard_compliance("en16798-1", en16798_data)

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
                self.best_performing_children + self.worst_performing_children,
                key=lambda r: r.get("compliance_rate", 0),
                reverse=True,
            )
        elif by == "quality":
            return sorted(
                self.best_performing_children + self.worst_performing_children,
                key=lambda r: r.get("quality_score", 0),
                reverse=True,
            )
        else:
            return []

    def to_summary_dict(self) -> dict[str, Any]:
        """Get summary as dictionary."""
        summary = super().to_summary_dict()
        summary.update({
            "building_id": self.building_id,
            "building_name": self.building_name,
            "level_count": self.level_count,
            "room_count": self.room_count,
            "avg_compliance_rate": round(self.avg_compliance_rate, 2),
            "avg_quality_score": round(self.avg_quality_score, 2),
        })

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
