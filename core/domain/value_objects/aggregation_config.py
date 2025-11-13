"""Aggregation configuration value objects."""

from typing import Any

from pydantic import BaseModel, Field, field_validator

from core.domain.enums.aggregation_method import (
    AggregationStrategy,
    ParameterAggregationMethod,
    SpatialAggregationMethod,
)
from core.domain.enums.parameter_type import ParameterType


class AggregationConfig(BaseModel):
    """
    Configuration for IEQ assessment aggregation.

    Defines how to combine multiple parameters and multiple spaces
    into building-level compliance categories and scores.
    """

    # Strategy selection
    strategy: AggregationStrategy = Field(
        default=AggregationStrategy.BALANCED_COMPLIANCE,
        description="Pre-defined aggregation strategy or CUSTOM"
    )

    # Method overrides (used when strategy=CUSTOM)
    parameter_method: ParameterAggregationMethod | None = Field(
        default=None,
        description="Custom parameter aggregation method (overrides strategy default)"
    )
    spatial_method: SpatialAggregationMethod | None = Field(
        default=None,
        description="Custom spatial aggregation method (overrides strategy default)"
    )

    # Weighting configuration
    parameter_weights: dict[ParameterType, float] = Field(
        default_factory=dict,
        description="Custom parameter weights for weighted aggregation"
    )
    room_weights: dict[str, float] = Field(
        default_factory=dict,
        description="Custom room weights (room_id -> weight) for weighted spatial aggregation"
    )

    # Filtering
    critical_room_ids: set[str] = Field(
        default_factory=set,
        description="Room IDs considered critical (for CRITICAL_SPACES_ONLY method)"
    )
    excluded_room_ids: set[str] = Field(
        default_factory=set,
        description="Room IDs to exclude from building aggregation"
    )
    excluded_parameters: set[ParameterType] = Field(
        default_factory=set,
        description="Parameters to exclude from aggregation"
    )

    # EN 16798-1 thresholds
    category_1_threshold: float = Field(
        default=95.0,
        ge=0,
        le=100,
        description="% occupied time required for Category I (default 95%)"
    )
    category_2_threshold: float = Field(
        default=90.0,
        ge=0,
        le=100,
        description="% occupied time required for Category II (default 90%)"
    )
    category_3_threshold: float = Field(
        default=85.0,
        ge=0,
        le=100,
        description="% occupied time required for Category III (default 85%)"
    )

    @field_validator('parameter_weights')
    @classmethod
    def validate_weights_sum_to_one(cls, v: dict[ParameterType, float]) -> dict[ParameterType, float]:
        """Validate that parameter weights sum to approximately 1.0."""
        if v and abs(sum(v.values()) - 1.0) > 0.01:
            raise ValueError(
                f"Parameter weights must sum to 1.0, got {sum(v.values()):.3f}"
            )
        return v

    def get_effective_parameter_method(self) -> ParameterAggregationMethod:
        """Get the effective parameter aggregation method."""
        if self.strategy == AggregationStrategy.CUSTOM and self.parameter_method:
            return self.parameter_method
        return self.strategy.parameter_method

    def get_effective_spatial_method(self) -> SpatialAggregationMethod:
        """Get the effective spatial aggregation method."""
        if self.strategy == AggregationStrategy.CUSTOM and self.spatial_method:
            return self.spatial_method
        return self.strategy.spatial_method

    def get_parameter_weights(self) -> dict[ParameterType, float]:
        """Get effective parameter weights."""
        if self.parameter_weights:
            return self.parameter_weights

        # Return default weights if using weighted method
        param_method = self.get_effective_parameter_method()
        if param_method == ParameterAggregationMethod.WEIGHTED_AVERAGE:
            return param_method.default_weights

        return {}

    def should_include_room(self, room_id: str, is_critical: bool = False) -> bool:
        """
        Check if a room should be included in building aggregation.

        Args:
            room_id: Room identifier
            is_critical: Whether the room is marked as critical

        Returns:
            True if room should be included
        """
        # Check exclusion list
        if room_id in self.excluded_room_ids:
            return False

        # Check critical spaces filter
        spatial_method = self.get_effective_spatial_method()
        if spatial_method == SpatialAggregationMethod.CRITICAL_SPACES_ONLY:
            return room_id in self.critical_room_ids or is_critical

        return True

    def should_include_parameter(self, parameter: ParameterType) -> bool:
        """Check if a parameter should be included in aggregation."""
        return parameter not in self.excluded_parameters

    @classmethod
    def strict_compliance(cls) -> 'AggregationConfig':
        """Create config for strict EN 16798-1 compliance."""
        return cls(strategy=AggregationStrategy.STRICT_COMPLIANCE)

    @classmethod
    def balanced_compliance(cls) -> 'AggregationConfig':
        """Create config for balanced compliance assessment."""
        return cls(strategy=AggregationStrategy.BALANCED_COMPLIANCE)

    @classmethod
    def performance_tracking(cls) -> 'AggregationConfig':
        """Create config for performance tracking."""
        return cls(strategy=AggregationStrategy.PERFORMANCE_TRACKING)

    @classmethod
    def quick_assessment(cls) -> 'AggregationConfig':
        """Create config for quick assessment."""
        return cls(strategy=AggregationStrategy.QUICK_ASSESSMENT)

    def to_dict(self) -> dict:
        """Export configuration as dictionary."""
        return {
            "strategy": self.strategy.value,
            "parameter_method": (
                self.get_effective_parameter_method().value
            ),
            "spatial_method": (
                self.get_effective_spatial_method().value
            ),
            "thresholds": {
                "category_1": self.category_1_threshold,
                "category_2": self.category_2_threshold,
                "category_3": self.category_3_threshold,
            },
            "filtering": {
                "critical_rooms": len(self.critical_room_ids),
                "excluded_rooms": len(self.excluded_room_ids),
                "excluded_parameters": [p.value for p in self.excluded_parameters],
            },
        }


class ParameterCategoryResult(BaseModel):
    """Results of category assessment for a single parameter in a single location."""

    parameter: ParameterType = Field(..., description="Parameter assessed")
    location_id: str = Field(..., description="Room/space identifier")

    # Time-in-category data
    percent_in_cat1: float = Field(ge=0, le=100, description="% time in Category I limits")
    percent_in_cat2: float = Field(ge=0, le=100, description="% time in Category II limits")
    percent_in_cat3: float = Field(ge=0, le=100, description="% time in Category III limits")

    # Derived category
    category: str = Field(..., description="I, II, III, or IV")

    # Additional metrics
    total_occupied_hours: float = Field(ge=0, description="Total occupied time analyzed")
    data_quality_score: float = Field(ge=0, le=100, description="Data completeness/quality")

    @classmethod
    def from_time_in_category(
        cls,
        parameter: ParameterType,
        location_id: str,
        percent_in_cat1: float,
        percent_in_cat2: float,
        percent_in_cat3: float,
        total_occupied_hours: float = 0.0,
        data_quality_score: float = 100.0,
        cat1_threshold: float = 95.0,
        cat2_threshold: float = 90.0,
        cat3_threshold: float = 85.0,
    ) -> 'ParameterCategoryResult':
        """
        Create result from time-in-category percentages.

        Applies EN 16798-1 category logic with configurable thresholds.
        """
        # Determine category
        if percent_in_cat1 >= cat1_threshold:
            category = "I"
        elif percent_in_cat2 >= cat2_threshold:
            category = "II"
        elif percent_in_cat3 >= cat3_threshold:
            category = "III"
        else:
            category = "IV"

        return cls(
            parameter=parameter,
            location_id=location_id,
            percent_in_cat1=percent_in_cat1,
            percent_in_cat2=percent_in_cat2,
            percent_in_cat3=percent_in_cat3,
            category=category,
            total_occupied_hours=total_occupied_hours,
            data_quality_score=data_quality_score,
        )

    @property
    def category_numeric(self) -> int:
        """Get numeric category (1-4) for aggregation."""
        mapping = {"I": 1, "II": 2, "III": 3, "IV": 4}
        return mapping.get(self.category, 4)

    @property
    def compliance_rate(self) -> float:
        """Get overall compliance rate (percent in Category I-III)."""
        return self.percent_in_cat3  # Cat III includes I and II


class RoomAggregationResult(BaseModel):
    """Aggregated IEQ results for a single room/space."""

    room_id: str = Field(..., description="Room identifier")
    room_name: str = Field(default="", description="Room name")

    # Parameter-level results
    parameter_results: dict[ParameterType, ParameterCategoryResult] = Field(
        default_factory=dict,
        description="Results per parameter"
    )

    # Aggregated category (worst-parameter method)
    overall_category: str = Field(..., description="I, II, III, or IV")

    # Continuous score (weighted-average method)
    ieq_score: float = Field(ge=0, le=100, description="Overall IEQ score 0-100%")

    # Metadata
    total_occupied_hours: float = Field(ge=0, description="Total occupied hours")
    floor_area_m2: float | None = Field(default=None, ge=0, description="Floor area")
    is_critical_space: bool = Field(default=False, description="Designated as critical space")

    @property
    def category_numeric(self) -> int:
        """Get numeric category (1-4)."""
        mapping = {"I": 1, "II": 2, "III": 3, "IV": 4}
        return mapping.get(self.overall_category, 4)

    def get_worst_parameter(self) -> ParameterType | None:
        """Get the parameter with worst (highest) category."""
        if not self.parameter_results:
            return None

        worst_param = max(
            self.parameter_results.items(),
            key=lambda x: x[1].category_numeric
        )
        return worst_param[0]

    def get_parameter_summary(self) -> dict[str, Any]:
        """Get summary of parameter performance."""
        worst_param = self.get_worst_parameter()
        return {
            "total_parameters": len(self.parameter_results),
            "category_I_params": sum(
                1 for r in self.parameter_results.values() if r.category == "I"
            ),
            "category_II_params": sum(
                1 for r in self.parameter_results.values() if r.category == "II"
            ),
            "category_III_params": sum(
                1 for r in self.parameter_results.values() if r.category == "III"
            ),
            "category_IV_params": sum(
                1 for r in self.parameter_results.values() if r.category == "IV"
            ),
            "worst_parameter": worst_param.value if worst_param else None,
        }
