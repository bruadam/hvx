"""
Unified analysis engine for building portfolio analytics.

Orchestrates all calculations across a portfolio of buildings, floors, and rooms.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import pandas as pd

from ..calculators.en16798_calculator import (
    EN16798Calculator,
    EN16798Category,
    VentilationType,
    PollutionLevel,
)
from ..calculators.tail_calculator import TAILCalculator
from ..calculators.ventilation_calculator import VentilationCalculator
from ..calculators.occupancy_calculator import OccupancyCalculator
from ..calculators.rc_thermal_model import (
    RCThermalModel,
    RCModelParameters,
    RCModelType,
)


class AnalysisType(str, Enum):
    """Types of analyses to perform."""
    EN16798 = "en16798"
    TAIL = "tail"
    VENTILATION = "ventilation"
    OCCUPANCY = "occupancy"
    RC_MODEL = "rc_model"
    ALL = "all"


@dataclass
class SpaceData:
    """Data for a single space (room/zone)."""
    id: str
    name: str
    type: str  # "room", "zone", "floor", "building"

    # Physical properties
    area_m2: float
    volume_m3: Optional[float] = None
    window_area_m2: Optional[float] = None
    occupancy_count: Optional[int] = None

    # Building properties
    room_type: Optional[str] = None
    ventilation_type: VentilationType = VentilationType.MECHANICAL
    pollution_level: PollutionLevel = PollutionLevel.NON_LOW
    construction_type: str = "medium"  # light, medium, heavy

    # Time series data
    temperature: Optional[pd.Series] = None
    co2: Optional[pd.Series] = None
    humidity: Optional[pd.Series] = None
    outdoor_temperature: Optional[pd.Series] = None
    solar_irradiance: Optional[pd.Series] = None

    # Metadata
    parent_id: Optional[str] = None
    child_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalysisConfig:
    """Configuration for analysis."""
    analyses_to_run: List[AnalysisType] = field(
        default_factory=lambda: [AnalysisType.ALL]
    )

    # EN 16798-1 settings
    en16798_categories: List[EN16798Category] = field(
        default_factory=lambda: list(EN16798Category)
    )
    season: str = "heating"
    outdoor_co2: float = 400.0

    # TAIL settings
    tail_thresholds: Dict[str, Dict[str, float]] = field(default_factory=dict)

    # RC model settings
    rc_model_type: RCModelType = RCModelType.TWO_R_TWO_C
    setpoint_heating: float = 20.0
    setpoint_cooling: float = 26.0

    # General settings
    aggregate_to_parent: bool = True
    generate_recommendations: bool = True


@dataclass
class SpaceAnalysisResult:
    """Results for a single space."""
    space_id: str
    space_name: str
    space_type: str

    # Analysis results
    en16798_result: Optional[Any] = None
    tail_result: Optional[Any] = None
    ventilation_result: Optional[Any] = None
    occupancy_result: Optional[Any] = None
    rc_model_result: Optional[Any] = None

    # Aggregated results
    summary: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PortfolioAnalysisResult:
    """Results for entire portfolio."""
    portfolio_id: str
    portfolio_name: str

    # Results by space
    space_results: Dict[str, SpaceAnalysisResult]

    # Aggregated portfolio-level results
    portfolio_summary: Dict[str, Any]

    # Hierarchy
    building_summaries: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    floor_summaries: Dict[str, Dict[str, Any]] = field(default_factory=dict)


class AnalysisEngine:
    """
    Unified analysis engine for building portfolio analytics.

    This engine orchestrates all analyses across a portfolio:
    - EN 16798-1 compliance assessment
    - TAIL rating
    - Ventilation rate estimation
    - Occupancy detection
    - RC thermal modeling
    - Portfolio-level aggregation
    """

    def __init__(self, config: Optional[AnalysisConfig] = None):
        """
        Initialize analysis engine.

        Args:
            config: Analysis configuration
        """
        self.config = config or AnalysisConfig()

        # Initialize calculators
        self.en16798_calc = EN16798Calculator()
        self.tail_calc = TAILCalculator()
        self.ventilation_calc = VentilationCalculator(
            outdoor_co2=self.config.outdoor_co2
        )
        self.occupancy_calc = OccupancyCalculator()

    def analyze_space(
        self,
        space: SpaceData,
        config: Optional[AnalysisConfig] = None
    ) -> SpaceAnalysisResult:
        """
        Analyze a single space.

        Args:
            space: Space data
            config: Optional config override

        Returns:
            SpaceAnalysisResult with all analysis results
        """
        cfg = config or self.config
        result = SpaceAnalysisResult(
            space_id=space.id,
            space_name=space.name,
            space_type=space.type,
        )

        analyses_to_run = cfg.analyses_to_run
        if AnalysisType.ALL in analyses_to_run:
            analyses_to_run = [
                AnalysisType.EN16798,
                AnalysisType.TAIL,
                AnalysisType.VENTILATION,
                AnalysisType.OCCUPANCY,
            ]

        # EN 16798-1 analysis
        if AnalysisType.EN16798 in analyses_to_run:
            result.en16798_result = self._analyze_en16798(space, cfg)

        # TAIL analysis
        if AnalysisType.TAIL in analyses_to_run:
            result.tail_result = self._analyze_tail(space, cfg)

        # Ventilation analysis
        if AnalysisType.VENTILATION in analyses_to_run and space.co2 is not None:
            result.ventilation_result = self._analyze_ventilation(space)

        # Occupancy analysis
        if AnalysisType.OCCUPANCY in analyses_to_run and space.co2 is not None:
            result.occupancy_result = self._analyze_occupancy(space)

        # RC model simulation
        if AnalysisType.RC_MODEL in analyses_to_run:
            result.rc_model_result = self._analyze_rc_model(space, cfg)

        # Generate summary
        result.summary = self._generate_space_summary(result)

        return result

    def analyze_portfolio(
        self,
        spaces: List[SpaceData],
        portfolio_id: str = "portfolio",
        portfolio_name: str = "Building Portfolio",
        config: Optional[AnalysisConfig] = None
    ) -> PortfolioAnalysisResult:
        """
        Analyze entire portfolio of spaces.

        Args:
            spaces: List of all spaces in portfolio
            portfolio_id: Portfolio identifier
            portfolio_name: Portfolio name
            config: Optional config override

        Returns:
            PortfolioAnalysisResult with all results
        """
        cfg = config or self.config

        # Analyze each space
        space_results = {}
        for space in spaces:
            result = self.analyze_space(space, cfg)
            space_results[space.id] = result

        # Aggregate by building and floor
        building_summaries = self._aggregate_by_parent(
            spaces, space_results, "building"
        )
        floor_summaries = self._aggregate_by_parent(
            spaces, space_results, "floor"
        )

        # Portfolio-level summary
        portfolio_summary = self._generate_portfolio_summary(
            space_results, building_summaries
        )

        return PortfolioAnalysisResult(
            portfolio_id=portfolio_id,
            portfolio_name=portfolio_name,
            space_results=space_results,
            portfolio_summary=portfolio_summary,
            building_summaries=building_summaries,
            floor_summaries=floor_summaries,
        )

    def _analyze_en16798(
        self,
        space: SpaceData,
        config: AnalysisConfig
    ) -> Dict[str, Any]:
        """Perform EN 16798-1 analysis."""
        if space.temperature is None and space.co2 is None and space.humidity is None:
            return {"error": "No environmental data available"}

        # Time series analysis
        if space.temperature is not None:
            compliance = self.en16798_calc.assess_timeseries_compliance(
                temperature=space.temperature,
                co2=space.co2,
                humidity=space.humidity,
                outdoor_temperature=space.outdoor_temperature,
                season=config.season,
                ventilation_type=space.ventilation_type,
                outdoor_co2=config.outdoor_co2,
                categories_to_check=config.en16798_categories,
            )
        else:
            # Instant values (use mean)
            measured = {}
            if space.temperature is not None:
                measured["temperature"] = float(space.temperature.mean())
            if space.co2 is not None:
                measured["co2"] = float(space.co2.mean())
            if space.humidity is not None:
                measured["humidity"] = float(space.humidity.mean())

            compliance = self.en16798_calc.assess_compliance(
                measured_values=measured,
                season=config.season,
                ventilation_type=space.ventilation_type,
                outdoor_co2=config.outdoor_co2,
                categories_to_check=config.en16798_categories,
            )

        # Calculate ventilation requirements
        if space.area_m2 and space.occupancy_count:
            ventilation_req = {}
            for category in config.en16798_categories:
                vent = self.en16798_calc.calculate_ventilation_requirement(
                    category=category,
                    floor_area_m2=space.area_m2,
                    occupancy_count=space.occupancy_count,
                    pollution_level=space.pollution_level,
                    volume_m3=space.volume_m3,
                )
                ventilation_req[category.value] = {
                    "total_l_s": vent.total_ventilation_l_s,
                    "ach": vent.air_change_rate_ach,
                }
        else:
            ventilation_req = None

        return {
            "compliance": compliance,
            "ventilation_requirements": ventilation_req,
        }

    def _analyze_tail(
        self,
        space: SpaceData,
        config: AnalysisConfig
    ) -> Dict[str, Any]:
        """Perform TAIL analysis."""
        timeseries_data = {}
        if space.temperature is not None:
            timeseries_data["temperature"] = space.temperature
        if space.co2 is not None:
            timeseries_data["co2"] = space.co2
        if space.humidity is not None:
            timeseries_data["humidity"] = space.humidity

        if not timeseries_data:
            return {"error": "No environmental data available"}

        # Use default thresholds if not provided
        thresholds = config.tail_thresholds
        if not thresholds:
            # Default EN 16798 Category II thresholds
            thresholds = {
                "temperature": {"lower": 20.0, "upper": 24.0},
                "co2": {"lower": 0, "upper": 1200},
                "humidity": {"lower": 25, "upper": 60},
            }

        result = self.tail_calc.assess_timeseries(timeseries_data, thresholds)

        return {
            "overall_rating": result.overall_rating.value,
            "overall_rating_label": result.overall_rating_label,
            "overall_compliance_rate": result.overall_compliance_rate,
            "categories": {
                cat.value: {
                    "rating": result.rating.value,
                    "rating_label": result.rating_label,
                    "compliance_rate": result.compliance_rate,
                }
                for cat, result in result.categories.items()
            },
        }

    def _analyze_ventilation(self, space: SpaceData) -> Dict[str, Any]:
        """Perform ventilation rate analysis."""
        result = self.ventilation_calc.estimate_from_co2_decay(
            co2_series=space.co2,
            volume_m3=space.volume_m3,
        )

        if result is None:
            return {"error": "Could not estimate ventilation from CO2 data"}

        return {
            "ach": result.ach,
            "ventilation_l_s": result.ventilation_l_s,
            "category": result.category,
            "r_squared": result.r_squared,
            "quality_score": result.quality_score,
            "description": result.description,
        }

    def _analyze_occupancy(self, space: SpaceData) -> Dict[str, Any]:
        """Perform occupancy analysis."""
        pattern = self.occupancy_calc.detect_occupancy(space.co2)

        return {
            "occupancy_rate": pattern.occupancy_rate,
            "estimated_occupants": pattern.estimated_occupant_count,
            "avg_co2_occupied": pattern.avg_co2_occupied,
            "avg_co2_unoccupied": pattern.avg_co2_unoccupied,
            "typical_hours": pattern.typical_occupancy_hours,
            "description": pattern.description,
        }

    def _analyze_rc_model(
        self,
        space: SpaceData,
        config: AnalysisConfig
    ) -> Dict[str, Any]:
        """Perform RC thermal model simulation."""
        if space.outdoor_temperature is None:
            return {"error": "Outdoor temperature required for RC model"}

        # Estimate RC parameters
        params = RCModelParameters.estimate_from_building_properties(
            volume_m3=space.volume_m3 or (space.area_m2 * 3.0),
            area_m2=space.area_m2,
            window_area_m2=space.window_area_m2 or (space.area_m2 * 0.2),
            construction_type=space.construction_type,
        )

        # Create model
        model = RCThermalModel(params, config.rc_model_type)

        # Solar irradiance (use default if not available)
        solar = space.solar_irradiance
        if solar is None:
            solar = pd.Series(
                0.0,
                index=space.outdoor_temperature.index
            )

        # Simulate
        result = model.simulate(
            outdoor_temperature=space.outdoor_temperature,
            solar_irradiance=solar,
            setpoint_heating=config.setpoint_heating,
            setpoint_cooling=config.setpoint_cooling,
        )

        return {
            "metrics": result.metrics,
            "u_value": model.estimate_u_value(),
            "time_constant_hours": model.estimate_thermal_time_constant(),
        }

    def _generate_space_summary(
        self,
        result: SpaceAnalysisResult
    ) -> Dict[str, Any]:
        """Generate summary for a space."""
        summary = {
            "space_id": result.space_id,
            "space_name": result.space_name,
            "space_type": result.space_type,
        }

        # EN 16798 summary
        if result.en16798_result and "compliance" in result.en16798_result:
            en_data = result.en16798_result["compliance"]
            if isinstance(en_data, dict):
                # Time series result
                best_cat = None
                best_rate = 0
                for cat, data in en_data.items():
                    if data["compliance_rate"] > best_rate:
                        best_rate = data["compliance_rate"]
                        best_cat = cat
                summary["en16798_best_category"] = best_cat
                summary["en16798_compliance_rate"] = best_rate

        # TAIL summary
        if result.tail_result and "overall_rating_label" in result.tail_result:
            summary["tail_rating"] = result.tail_result["overall_rating_label"]
            summary["tail_compliance"] = result.tail_result["overall_compliance_rate"]

        # Ventilation summary
        if result.ventilation_result and "ach" in result.ventilation_result:
            summary["ventilation_ach"] = result.ventilation_result["ach"]
            summary["ventilation_category"] = result.ventilation_result["category"]

        # Occupancy summary
        if result.occupancy_result and "estimated_occupants" in result.occupancy_result:
            summary["estimated_occupants"] = result.occupancy_result["estimated_occupants"]
            summary["occupancy_rate"] = result.occupancy_result["occupancy_rate"]

        return summary

    def _aggregate_by_parent(
        self,
        spaces: List[SpaceData],
        space_results: Dict[str, SpaceAnalysisResult],
        parent_type: str
    ) -> Dict[str, Dict[str, Any]]:
        """Aggregate results by parent (building or floor)."""
        # Group spaces by parent
        parent_groups: Dict[str, List[str]] = {}
        for space in spaces:
            if space.type == "room" and space.parent_id:
                if space.parent_id not in parent_groups:
                    parent_groups[space.parent_id] = []
                parent_groups[space.parent_id].append(space.id)

        # Aggregate for each parent
        summaries = {}
        for parent_id, child_ids in parent_groups.items():
            child_results = [space_results[cid] for cid in child_ids if cid in space_results]

            # Aggregate TAIL ratings
            tail_ratings = [
                r.tail_result
                for r in child_results
                if r.tail_result and "overall_rating" in r.tail_result
            ]

            if tail_ratings:
                avg_tail_compliance = sum(
                    r["overall_compliance_rate"] for r in tail_ratings
                ) / len(tail_ratings)
                worst_tail_rating = max(r["overall_rating"] for r in tail_ratings)
            else:
                avg_tail_compliance = 0
                worst_tail_rating = None

            summaries[parent_id] = {
                "child_count": len(child_ids),
                "avg_tail_compliance": round(avg_tail_compliance, 2),
                "worst_tail_rating": worst_tail_rating,
            }

        return summaries

    def _generate_portfolio_summary(
        self,
        space_results: Dict[str, SpaceAnalysisResult],
        building_summaries: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate portfolio-level summary."""
        total_spaces = len(space_results)

        # Count by type
        type_counts = {}
        for result in space_results.values():
            type_counts[result.space_type] = type_counts.get(result.space_type, 0) + 1

        # Average compliance rates
        tail_compliances = [
            r.tail_result["overall_compliance_rate"]
            for r in space_results.values()
            if r.tail_result and "overall_compliance_rate" in r.tail_result
        ]
        avg_tail_compliance = (
            sum(tail_compliances) / len(tail_compliances)
            if tail_compliances else 0
        )

        return {
            "total_spaces": total_spaces,
            "spaces_by_type": type_counts,
            "total_buildings": len(building_summaries),
            "avg_tail_compliance": round(avg_tail_compliance, 2),
        }
