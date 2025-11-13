"""Aggregation methods for IEQ assessment."""

from enum import Enum


class ParameterAggregationMethod(str, Enum):
    """
    Methods for aggregating multiple parameters into a single room/space assessment.

    Used when combining thermal, air quality, lighting, and acoustic parameters
    into an overall IEQ category or score for a single location.
    """

    WORST_PARAMETER = "worst_parameter"
    """
    Take the worst (highest) category among all parameters.
    Conservative approach - ensures no poor parameter is hidden.
    Category I = 1, II = 2, III = 3, IV = 4.
    RoomCategory = max(Cat_temp, Cat_CO2, Cat_illuminance, ...)
    """

    WEIGHTED_AVERAGE = "weighted_average"
    """
    Calculate weighted average of parameter compliance rates.
    Produces continuous IEQ score (0-100) instead of categorical result.
    IEQscore = Σ(w_p × f_p) / Σ(w_p)
    where w_p = parameter weight, f_p = compliance fraction
    """

    UNWEIGHTED_AVERAGE = "unweighted_average"
    """
    Simple average of all parameter compliance rates.
    Equal weight to all parameters.
    IEQscore = Σ(f_p) / n
    """

    @property
    def description(self) -> str:
        """Get detailed description of aggregation method."""
        descriptions = {
            self.WORST_PARAMETER: (
                "Conservative EN 16798-1 compliant method. "
                "Building/room category is limited by worst-performing parameter. "
                "Best for compliance reporting and certification."
            ),
            self.WEIGHTED_AVERAGE: (
                "Continuous scoring method with parameter importance weighting. "
                "Produces 0-100% overall IEQ score. "
                "Best for performance tracking and benchmarking."
            ),
            self.UNWEIGHTED_AVERAGE: (
                "Simple average across all parameters with equal weights. "
                "Quick overview metric, less nuanced than weighted approach."
            ),
        }
        return descriptions.get(self, "")

    @property
    def default_weights(self) -> dict:
        """Get default parameter weights for weighted aggregation methods."""
        from core.domain.enums.parameter_type import ParameterType

        # Based on typical research and certification practice
        # Thermal and air quality tend to dominate occupant comfort
        return {
            ParameterType.TEMPERATURE: 0.35,      # Thermal comfort is critical
            ParameterType.CO2: 0.25,              # Air quality proxy
            ParameterType.HUMIDITY: 0.10,         # Part of thermal comfort
            ParameterType.ILLUMINANCE: 0.15,      # Visual comfort
            ParameterType.NOISE: 0.10,            # Acoustic comfort
            ParameterType.PM25: 0.05,             # Health-related
            # Other parameters can be added with appropriate weights
        }


class SpatialAggregationMethod(str, Enum):
    """
    Methods for aggregating multiple rooms/spaces into building-level assessment.

    Used when combining room-level results into an overall building category or score.
    """

    WORST_SPACE = "worst_space"
    """
    Building category determined by worst-performing space.
    Strict interpretation - if any critical space fails, building fails.
    BuildingCategory = max(RoomCategory_1, RoomCategory_2, ...)
    """

    OCCUPANT_WEIGHTED = "occupant_weighted"
    """
    Weight each room by occupancy hours.
    F_building = Σ(t_i,occ × f_i) / Σ(t_i,occ)
    where t_i,occ = occupied hours in room i
    More representative of actual occupant experience.
    """

    AREA_WEIGHTED = "area_weighted"
    """
    Weight each room by floor area.
    F_building = Σ(A_i × f_i) / Σ(A_i)
    where A_i = area of room i
    Useful when occupancy data is not available.
    """

    SIMPLE_AVERAGE = "simple_average"
    """
    Unweighted average across all rooms.
    F_building = Σ(f_i) / n
    Treats all spaces equally regardless of size or occupancy.
    """

    CRITICAL_SPACES_ONLY = "critical_spaces_only"
    """
    Only evaluate designated critical spaces (e.g., open offices, classrooms).
    Ignores auxiliary spaces like corridors, storage, etc.
    Building category = aggregation of critical spaces only.
    """

    @property
    def description(self) -> str:
        """Get detailed description of spatial aggregation method."""
        descriptions = {
            self.WORST_SPACE: (
                "Conservative approach for certification. "
                "Building limited by worst room performance. "
                "Ensures no poor space is overlooked."
            ),
            self.OCCUPANT_WEIGHTED: (
                "Most representative of actual occupant experience. "
                "Large/heavily-used spaces have more influence. "
                "Requires occupancy hour data per room. "
                "Recommended for performance assessment."
            ),
            self.AREA_WEIGHTED: (
                "Practical alternative when occupancy data unavailable. "
                "Larger spaces have more influence on building score. "
                "Can overweight large storage/circulation spaces."
            ),
            self.SIMPLE_AVERAGE: (
                "Quick overview treating all spaces equally. "
                "May not reflect actual building performance if rooms vary greatly in size/use."
            ),
            self.CRITICAL_SPACES_ONLY: (
                "Focus on occupied workspace only. "
                "Excludes auxiliary spaces from evaluation. "
                "Requires designation of which spaces are critical."
            ),
        }
        return descriptions.get(self, "")

    @property
    def requires_weights(self) -> bool:
        """Check if this method requires weighting data."""
        return self in [
            self.OCCUPANT_WEIGHTED,
            self.AREA_WEIGHTED,
        ]


class AggregationStrategy(str, Enum):
    """
    Complete aggregation strategy combining parameter and spatial methods.

    Pre-defined strategies for common use cases.
    """

    STRICT_COMPLIANCE = "strict_compliance"
    """
    Worst-parameter + Worst-space.
    Most conservative approach for EN 16798-1 compliance reporting.
    """

    BALANCED_COMPLIANCE = "balanced_compliance"
    """
    Worst-parameter + Occupant-weighted.
    Conservative parameter assessment, realistic spatial weighting.
    """

    PERFORMANCE_TRACKING = "performance_tracking"
    """
    Weighted-average parameters + Occupant-weighted spaces.
    Continuous scoring for monitoring and improvement.
    """

    QUICK_ASSESSMENT = "quick_assessment"
    """
    Unweighted-average parameters + Simple-average spaces.
    Fast overview without detailed weighting.
    """

    CUSTOM = "custom"
    """
    Custom combination of parameter and spatial aggregation methods.
    Allows full flexibility in defining assessment approach.
    """

    @property
    def parameter_method(self) -> ParameterAggregationMethod:
        """Get the parameter aggregation method for this strategy."""
        mapping = {
            self.STRICT_COMPLIANCE: ParameterAggregationMethod.WORST_PARAMETER,
            self.BALANCED_COMPLIANCE: ParameterAggregationMethod.WORST_PARAMETER,
            self.PERFORMANCE_TRACKING: ParameterAggregationMethod.WEIGHTED_AVERAGE,
            self.QUICK_ASSESSMENT: ParameterAggregationMethod.UNWEIGHTED_AVERAGE,
        }
        return mapping.get(self, ParameterAggregationMethod.WORST_PARAMETER)

    @property
    def spatial_method(self) -> SpatialAggregationMethod:
        """Get the spatial aggregation method for this strategy."""
        mapping = {
            self.STRICT_COMPLIANCE: SpatialAggregationMethod.WORST_SPACE,
            self.BALANCED_COMPLIANCE: SpatialAggregationMethod.OCCUPANT_WEIGHTED,
            self.PERFORMANCE_TRACKING: SpatialAggregationMethod.OCCUPANT_WEIGHTED,
            self.QUICK_ASSESSMENT: SpatialAggregationMethod.SIMPLE_AVERAGE,
        }
        return mapping.get(self, SpatialAggregationMethod.WORST_SPACE)

    @property
    def description(self) -> str:
        """Get detailed description of the strategy."""
        descriptions = {
            self.STRICT_COMPLIANCE: (
                "Most conservative approach for compliance certification. "
                "Building category limited by worst parameter in worst space. "
                "Use for: Official compliance reporting, certification applications."
            ),
            self.BALANCED_COMPLIANCE: (
                "Conservative parameter assessment with realistic spatial weighting. "
                "Balances strict compliance with occupant experience. "
                "Use for: Internal compliance tracking, retrofit prioritization."
            ),
            self.PERFORMANCE_TRACKING: (
                "Continuous scoring optimized for monitoring improvements. "
                "Weighted parameters and occupant-weighted spaces. "
                "Use for: KPI dashboards, performance benchmarking, trend analysis."
            ),
            self.QUICK_ASSESSMENT: (
                "Simple averaging for rapid overview. "
                "All parameters and spaces weighted equally. "
                "Use for: Initial screening, quick comparisons."
            ),
            self.CUSTOM: (
                "User-defined combination of aggregation methods. "
                "Full flexibility to match specific assessment needs."
            ),
        }
        return descriptions.get(self, "")

    @property
    def use_cases(self) -> list[str]:
        """Get recommended use cases for this strategy."""
        use_cases = {
            self.STRICT_COMPLIANCE: [
                "EN 16798-1 compliance certification",
                "BREEAM/LEED IEQ credits",
                "Building permit submissions",
                "Legal compliance documentation",
            ],
            self.BALANCED_COMPLIANCE: [
                "Internal compliance monitoring",
                "Retrofit investment prioritization",
                "Facility management reporting",
                "Tenant satisfaction analysis",
            ],
            self.PERFORMANCE_TRACKING: [
                "Continuous IEQ monitoring",
                "Performance benchmarking",
                "KPI dashboards",
                "Year-over-year comparisons",
                "Before/after intervention studies",
            ],
            self.QUICK_ASSESSMENT: [
                "Initial building screening",
                "Portfolio-wide comparisons",
                "High-level feasibility studies",
            ],
            self.CUSTOM: [
                "Research studies with specific methodologies",
                "Specialized certification schemes",
                "Custom client requirements",
            ],
        }
        return use_cases.get(self, [])
