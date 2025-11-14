"""
TAIL (Thermal, Acoustic, Indoor Air Quality, Luminous) rating calculator.

Implements the TAIL rating scheme for comprehensive indoor environmental quality assessment.

Reference: https://www.sciencedirect.com/science/article/pii/S0378778821003133
ALDREN project - https://github.com/asitkm76/TAILRatingScheme
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional
import pandas as pd


class TAILRating(int, Enum):
    """TAIL rating levels."""
    EXCELLENT = 1  # Green - ≥95% compliant
    GOOD = 2       # Yellow - 70-95% compliant
    FAIR = 3       # Orange - 50-70% compliant
    POOR = 4       # Red - <50% compliant

    def to_label(self) -> str:
        """Convert to roman numeral label."""
        labels = {1: "I", 2: "II", 3: "III", 4: "IV"}
        return labels[self.value]

    def to_color(self) -> str:
        """Get color name for rating."""
        colors = {1: "Green", 2: "Yellow", 3: "Orange", 4: "Red"}
        return colors[self.value]


class TAILCategory(str, Enum):
    """TAIL assessment categories."""
    THERMAL = "thermal"
    ACOUSTIC = "acoustic"
    IAQ = "iaq"              # Indoor Air Quality
    LUMINOUS = "luminous"


@dataclass
class TAILParameterResult:
    """Result for a single parameter."""
    parameter: str
    value: float
    threshold_lower: Optional[float]
    threshold_upper: Optional[float]
    compliant: bool
    category: TAILCategory


@dataclass
class TAILCategoryResult:
    """Result for a TAIL category."""
    category: TAILCategory
    rating: TAILRating
    rating_label: str
    compliance_rate: float
    parameter_count: int
    parameters: List[TAILParameterResult]


@dataclass
class TAILOverallResult:
    """Overall TAIL assessment result."""
    overall_rating: TAILRating
    overall_rating_label: str
    overall_compliance_rate: float
    categories: Dict[TAILCategory, TAILCategoryResult]
    total_parameters: int


class TAILCalculator:
    """
    Calculator for TAIL rating scheme.

    TAIL provides comprehensive indoor environmental quality assessment across:
    - T: Thermal comfort (temperature, humidity)
    - A: Acoustic comfort (noise levels)
    - I: Indoor Air Quality (CO2, PM2.5, VOCs, etc.)
    - L: Luminous comfort (illuminance, daylight)

    Rating Scale:
    - I (1): Green - Excellent (≥95% compliant)
    - II (2): Yellow - Good (70-95% compliant)
    - III (3): Orange - Fair (50-70% compliant)
    - IV (4): Red - Poor (<50% compliant)
    """

    # Rating thresholds (compliance percentage)
    RATING_THRESHOLDS = {
        TAILRating.EXCELLENT: 95.0,
        TAILRating.GOOD: 70.0,
        TAILRating.FAIR: 50.0,
        TAILRating.POOR: 0.0,
    }

    # Parameter to category mapping
    PARAMETER_CATEGORIES = {
        # Thermal
        "temperature": TAILCategory.THERMAL,
        "temp": TAILCategory.THERMAL,
        "humidity": TAILCategory.THERMAL,
        "rh": TAILCategory.THERMAL,
        "relative_humidity": TAILCategory.THERMAL,
        "pmv": TAILCategory.THERMAL,
        "ppd": TAILCategory.THERMAL,

        # Acoustic
        "noise": TAILCategory.ACOUSTIC,
        "sound": TAILCategory.ACOUSTIC,
        "acoustic": TAILCategory.ACOUSTIC,
        "sound_level": TAILCategory.ACOUSTIC,
        "noise_level": TAILCategory.ACOUSTIC,
        "decibel": TAILCategory.ACOUSTIC,
        "db": TAILCategory.ACOUSTIC,

        # IAQ
        "co2": TAILCategory.IAQ,
        "pm25": TAILCategory.IAQ,
        "pm2.5": TAILCategory.IAQ,
        "pm10": TAILCategory.IAQ,
        "voc": TAILCategory.IAQ,
        "tvoc": TAILCategory.IAQ,
        "formaldehyde": TAILCategory.IAQ,
        "radon": TAILCategory.IAQ,
        "ventilation": TAILCategory.IAQ,
        "air_quality": TAILCategory.IAQ,

        # Luminous
        "illuminance": TAILCategory.LUMINOUS,
        "light": TAILCategory.LUMINOUS,
        "daylight": TAILCategory.LUMINOUS,
        "lux": TAILCategory.LUMINOUS,
        "daylight_factor": TAILCategory.LUMINOUS,
        "luminance": TAILCategory.LUMINOUS,
    }

    @classmethod
    def compliance_to_rating(cls, compliance_rate: float) -> TAILRating:
        """Convert compliance percentage to TAIL rating."""
        if compliance_rate >= cls.RATING_THRESHOLDS[TAILRating.EXCELLENT]:
            return TAILRating.EXCELLENT
        elif compliance_rate >= cls.RATING_THRESHOLDS[TAILRating.GOOD]:
            return TAILRating.GOOD
        elif compliance_rate >= cls.RATING_THRESHOLDS[TAILRating.FAIR]:
            return TAILRating.FAIR
        else:
            return TAILRating.POOR

    @classmethod
    def get_parameter_category(cls, parameter: str) -> Optional[TAILCategory]:
        """Determine which TAIL category a parameter belongs to."""
        param_lower = parameter.lower().replace("_", "").replace(" ", "")
        for param_key, category in cls.PARAMETER_CATEGORIES.items():
            if param_key.replace("_", "").replace(" ", "") in param_lower:
                return category
        return None

    @classmethod
    def assess_instant_values(
        cls,
        measured_values: Dict[str, float],
        thresholds: Dict[str, Dict[str, float]]
    ) -> TAILOverallResult:
        """
        Assess TAIL rating from instant measured values and thresholds.

        Args:
            measured_values: Dict of parameter -> measured value
            thresholds: Dict of parameter -> {lower, upper} thresholds

        Returns:
            TAILOverallResult with ratings and details
        """
        # Group parameters by category
        parameter_results: Dict[TAILCategory, List[TAILParameterResult]] = {
            cat: [] for cat in TAILCategory
        }

        for param, value in measured_values.items():
            category = cls.get_parameter_category(param)
            if category is None:
                continue

            threshold = thresholds.get(param, {})
            lower = threshold.get("lower", float("-inf"))
            upper = threshold.get("upper", float("inf"))

            compliant = lower <= value <= upper

            param_result = TAILParameterResult(
                parameter=param,
                value=value,
                threshold_lower=lower if lower != float("-inf") else None,
                threshold_upper=upper if upper != float("inf") else None,
                compliant=compliant,
                category=category,
            )
            parameter_results[category].append(param_result)

        # Calculate category ratings
        category_results = {}
        for category in TAILCategory:
            params = parameter_results[category]
            if not params:
                continue

            compliant_count = sum(1 for p in params if p.compliant)
            compliance_rate = (compliant_count / len(params)) * 100
            rating = cls.compliance_to_rating(compliance_rate)

            category_results[category] = TAILCategoryResult(
                category=category,
                rating=rating,
                rating_label=rating.to_label(),
                compliance_rate=round(compliance_rate, 2),
                parameter_count=len(params),
                parameters=params,
            )

        # Overall rating (worst category)
        if category_results:
            worst_rating = max(cat.rating for cat in category_results.values())
            total_params = sum(len(params) for params in parameter_results.values() if params)
            total_compliant = sum(
                sum(1 for p in cat.parameters if p.compliant)
                for cat in category_results.values()
            )
            overall_compliance = (total_compliant / total_params * 100) if total_params > 0 else 0.0
        else:
            worst_rating = TAILRating.POOR
            overall_compliance = 0.0
            total_params = 0

        return TAILOverallResult(
            overall_rating=worst_rating,
            overall_rating_label=worst_rating.to_label(),
            overall_compliance_rate=round(overall_compliance, 2),
            categories=category_results,
            total_parameters=total_params,
        )

    @classmethod
    def assess_timeseries(
        cls,
        timeseries_data: Dict[str, pd.Series],
        thresholds: Dict[str, Dict[str, float]]
    ) -> TAILOverallResult:
        """
        Assess TAIL rating from time series data.

        Args:
            timeseries_data: Dict of parameter -> pd.Series
            thresholds: Dict of parameter -> {lower, upper} thresholds

        Returns:
            TAILOverallResult with ratings based on compliance over time
        """
        # Group parameters by category
        category_compliance: Dict[TAILCategory, List[float]] = {
            cat: [] for cat in TAILCategory
        }
        category_params: Dict[TAILCategory, List[TAILParameterResult]] = {
            cat: [] for cat in TAILCategory
        }

        for param, series in timeseries_data.items():
            category = cls.get_parameter_category(param)
            if category is None or series.empty:
                continue

            threshold = thresholds.get(param, {})
            lower = threshold.get("lower", float("-inf"))
            upper = threshold.get("upper", float("inf"))

            # Calculate compliance for each timestep
            compliant_series = (series >= lower) & (series <= upper)
            compliance_rate = (compliant_series.sum() / len(compliant_series)) * 100

            category_compliance[category].append(compliance_rate)

            # Create parameter result with mean value
            param_result = TAILParameterResult(
                parameter=param,
                value=round(float(series.mean()), 2),
                threshold_lower=lower if lower != float("-inf") else None,
                threshold_upper=upper if upper != float("inf") else None,
                compliant=compliance_rate >= 50.0,  # Consider compliant if >50% of time
                category=category,
            )
            category_params[category].append(param_result)

        # Calculate category ratings
        category_results = {}
        for category in TAILCategory:
            compliances = category_compliance[category]
            params = category_params[category]
            if not compliances:
                continue

            # Category compliance is average of all parameter compliances
            avg_compliance = sum(compliances) / len(compliances)
            rating = cls.compliance_to_rating(avg_compliance)

            category_results[category] = TAILCategoryResult(
                category=category,
                rating=rating,
                rating_label=rating.to_label(),
                compliance_rate=round(avg_compliance, 2),
                parameter_count=len(params),
                parameters=params,
            )

        # Overall rating (worst category)
        if category_results:
            worst_rating = max(cat.rating for cat in category_results.values())
            all_compliances = [comp for comps in category_compliance.values() for comp in comps]
            overall_compliance = sum(all_compliances) / len(all_compliances) if all_compliances else 0.0
            total_params = sum(len(params) for params in category_params.values() if params)
        else:
            worst_rating = TAILRating.POOR
            overall_compliance = 0.0
            total_params = 0

        return TAILOverallResult(
            overall_rating=worst_rating,
            overall_rating_label=worst_rating.to_label(),
            overall_compliance_rate=round(overall_compliance, 2),
            categories=category_results,
            total_parameters=total_params,
        )

    @classmethod
    def aggregate_ratings(
        cls,
        child_results: List[TAILOverallResult],
        aggregation_method: str = "worst"
    ) -> TAILOverallResult:
        """
        Aggregate TAIL ratings from multiple child entities (rooms/buildings).

        Args:
            child_results: List of TAIL results from child entities
            aggregation_method: 'worst' or 'average'

        Returns:
            Aggregated TAIL result
        """
        if not child_results:
            return TAILOverallResult(
                overall_rating=TAILRating.POOR,
                overall_rating_label="IV",
                overall_compliance_rate=0.0,
                categories={},
                total_parameters=0,
            )

        # Aggregate by category
        category_results = {}
        for category in TAILCategory:
            category_data = [
                r.categories[category]
                for r in child_results
                if category in r.categories
            ]

            if not category_data:
                continue

            if aggregation_method == "worst":
                worst_rating = max(cat.rating for cat in category_data)
                avg_compliance = sum(cat.compliance_rate for cat in category_data) / len(category_data)
            else:  # average
                avg_compliance = sum(cat.compliance_rate for cat in category_data) / len(category_data)
                worst_rating = cls.compliance_to_rating(avg_compliance)

            total_params = sum(cat.parameter_count for cat in category_data)

            category_results[category] = TAILCategoryResult(
                category=category,
                rating=worst_rating,
                rating_label=worst_rating.to_label(),
                compliance_rate=round(avg_compliance, 2),
                parameter_count=total_params,
                parameters=[],  # Not preserving individual parameters in aggregation
            )

        # Overall
        if category_results:
            worst_rating = max(cat.rating for cat in category_results.values())
            avg_compliance = sum(cat.compliance_rate for cat in category_results.values()) / len(category_results)
            total_params = sum(cat.parameter_count for cat in category_results.values())
        else:
            worst_rating = TAILRating.POOR
            avg_compliance = 0.0
            total_params = 0

        return TAILOverallResult(
            overall_rating=worst_rating,
            overall_rating_label=worst_rating.to_label(),
            overall_compliance_rate=round(avg_compliance, 2),
            categories=category_results,
            total_parameters=total_params,
        )
