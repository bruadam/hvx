"""
TAIL (Thermal, Acoustic, Indoor Air Quality, Luminous) rating calculator.

Implements the algorithm described in standards/tail/docs/TAIL_algorithm.txt.
Processes parameter time series, applies schedule filtering, categorises
measurements per parameter-specific logic, and returns graph-ready data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from core.schedules import (
    generate_occupancy_mask,
    get_opening_profile_for_building_type,
)


class TAILRating(int, Enum):
    """TAIL rating levels."""

    EXCELLENT = 1  # Green - ≥95% compliant
    GOOD = 2  # Yellow - 70-95% compliant
    FAIR = 3  # Orange - 50-70% compliant
    POOR = 4  # Red - <50% compliant

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
    IAQ = "iaq"  # Indoor Air Quality
    LUMINOUS = "luminous"


@dataclass
class TAILParameterResult:
    """Result for a single parameter."""

    parameter: str
    category: TAILCategory
    rating: TAILRating
    rating_label: str
    dominant_color: str
    distribution: Dict[str, float]
    sample_count: int
    summary_value: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TAILCategoryResult:
    """Result for a TAIL category."""

    category: TAILCategory
    rating: TAILRating
    rating_label: str
    compliance_rate: float
    parameter_count: int
    parameters: List[TAILParameterResult]
    dominant_color: str


@dataclass
class TAILOverallResult:
    """Overall TAIL assessment result."""

    overall_rating: TAILRating
    overall_rating_label: str
    overall_compliance_rate: float
    categories: Dict[TAILCategory, TAILCategoryResult]
    total_parameters: int
    visualization: Dict[str, Any]
    parameter_results: List[TAILParameterResult]


class TAILCalculator:
    """
    Calculator for the TAIL rating scheme.

    Implements the perform_TAILanalysis workflow:
    - Filter measurements to working hours based on building type
    - Categorise each parameter following ALDREN/TAIL guidance
    - Compute domain ratings using worst-case logic
    - Provide nested JSON payload that downstream graph renderers can use
    """

    COLOR_ORDER = ["green", "yellow", "orange", "red"]
    COLOR_TO_RATING = {
        "green": TAILRating.EXCELLENT,
        "yellow": TAILRating.GOOD,
        "orange": TAILRating.FAIR,
        "red": TAILRating.POOR,
    }

    # Parameter aliases used when reading sensor names
    PARAMETER_ALIASES = {
        "temp": "temperature",
        "temperature": "temperature",
        "operative_temperature": "temperature",
        "rh": "relative_humidity",
        "relativehumidity": "relative_humidity",
        "humidity": "relative_humidity",
        "co2": "co2",
        "co₂": "co2",
        "pm25": "pm25",
        "pm2.5": "pm25",
        "pm_2_5": "pm25",
        "pm10": "pm10",
        "voc": "voc",
        "tvoc": "voc",
        "formaldehyde": "formaldehyde",
        "benzene": "benzene",
        "radon": "radon",
        "ventilation": "ventilation",
        "vent": "ventilation",
        "mold": "mold",
        "mould": "mold",
        "noise": "noise",
        "noise_level": "noise",
        "sound": "noise",
        "sound_level": "noise",
        "illuminance": "illuminance",
        "lux": "illuminance",
        "light": "illuminance",
        "daylightfactor": "daylight_factor",
        "daylight_factor": "daylight_factor",
    }

    PARAMETER_CATEGORIES = {
        "temperature": TAILCategory.THERMAL,
        "relative_humidity": TAILCategory.IAQ,
        "humidity": TAILCategory.IAQ,
        "co2": TAILCategory.IAQ,
        "pm25": TAILCategory.IAQ,
        "pm10": TAILCategory.IAQ,
        "voc": TAILCategory.IAQ,
        "formaldehyde": TAILCategory.IAQ,
        "benzene": TAILCategory.IAQ,
        "radon": TAILCategory.IAQ,
        "ventilation": TAILCategory.IAQ,
        "mold": TAILCategory.IAQ,
        "noise": TAILCategory.ACOUSTIC,
        "illuminance": TAILCategory.LUMINOUS,
        "daylight_factor": TAILCategory.LUMINOUS,
    }

    TEMPERATURE_THRESHOLDS: Dict[str, List[Tuple[str, float, float]]] = {
        "heating": [
            ("green", 21.0, 24.0),
            ("yellow", 20.0, 25.0),
            ("orange", 18.0, 26.0),
        ],
        "non_heating": [
            ("green", 23.0, 26.0),
            ("yellow", 22.0, 27.0),
            ("orange", 21.0, 28.0),
        ],
    }

    RH_THRESHOLDS: Dict[str, List[Tuple[str, float, float]]] = {
        "office": [
            ("green", 30.0, 60.0),
            ("yellow", 25.0, 65.0),
            ("orange", 20.0, 70.0),
        ],
        "hotel": [
            ("green", 30.0, 60.0),
            ("yellow", 28.0, 65.0),
            ("orange", 25.0, 70.0),
        ],
        "default": [
            ("green", 30.0, 60.0),
            ("yellow", 25.0, 65.0),
            ("orange", 20.0, 70.0),
        ],
    }

    POLLUTANT_THRESHOLDS: Dict[str, List[Tuple[str, Optional[float], Optional[float]]]] = {
        "pm25": [("green", None, 15.0), ("yellow", 15.0, 35.0), ("orange", 35.0, 55.0)],
        "pm10": [("green", None, 30.0), ("yellow", 30.0, 50.0), ("orange", 50.0, 75.0)],
        "voc": [("green", None, 300.0), ("yellow", 300.0, 600.0), ("orange", 600.0, 1000.0)],
        "formaldehyde": [("green", None, 60.0), ("yellow", 60.0, 100.0), ("orange", 100.0, 150.0)],
        "benzene": [("green", None, 5.0), ("yellow", 5.0, 10.0), ("orange", 10.0, 20.0)],
        "radon": [("green", None, 100.0), ("yellow", 100.0, 200.0), ("orange", 200.0, 300.0)],
    }

    NOISE_THRESHOLDS: Dict[str, Dict[str, float]] = {
        "small_office": {"green": 38.0, "yellow": 42.0, "orange": 48.0},
        "open_office": {"green": 45.0, "yellow": 50.0, "orange": 55.0},
        "hotel": {"green": 35.0, "yellow": 40.0, "orange": 45.0},
        "default": {"green": 40.0, "yellow": 45.0, "orange": 55.0},
    }

    ILLUMINANCE_TARGETS = {
        "office": 500.0,
        "school": 300.0,
        "hotel": 200.0,
        "default": 300.0,
    }

    DAYLIGHT_THRESHOLDS = [
        ("green", 2.0, None),
        ("yellow", 1.5, 2.0),
        ("orange", 1.0, 1.5),
    ]

    VENTILATION_PER_PERSON_LPS = 10.0  # l/s per occupant per ALDREN guidance

    @classmethod
    def assess_instant_values(
        cls,
        measured_values: Dict[str, float],
        thresholds: Dict[str, Dict[str, float]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TAILOverallResult:
        """
        Convenience wrapper to score a snapshot of measurements.
        """

        series_data = {
            param: pd.Series([value]) for param, value in measured_values.items()
        }
        return cls.assess_timeseries(series_data, thresholds, metadata=metadata)

    @classmethod
    def assess_timeseries(
        cls,
        timeseries_data: Dict[str, pd.Series],
        thresholds: Dict[str, Dict[str, float]],
        metadata: Optional[Dict[str, Any]] = None,
        building_name: Optional[str] = None,
    ) -> TAILOverallResult:
        """
        Assess TAIL rating from time series data following the TAIL algorithm.
        """

        metadata = metadata or {}
        filtered_series = cls._prepare_series(timeseries_data, metadata.get("building_type"))

        parameter_results: List[TAILParameterResult] = []

        for param_name, series in filtered_series.items():
            normalized = cls._normalize_parameter_name(param_name)
            category = cls.PARAMETER_CATEGORIES.get(normalized)
            if category is None:
                continue

            evaluator = cls._get_parameter_evaluator(normalized)
            if evaluator:
                result = evaluator(series, metadata)
            else:
                threshold = thresholds.get(param_name) or thresholds.get(normalized)
                result = cls._evaluate_generic(normalized, series, category, threshold or {})

            if result:
                parameter_results.append(result)

        category_results = cls._build_category_results(parameter_results)
        overall_rating, overall_compliance = cls._summarize_overall(category_results)
        visualization = cls._build_visualization(
            parameter_results=parameter_results,
            category_results=category_results,
            overall_rating=overall_rating,
            overall_compliance=overall_compliance,
            metadata=metadata,
            building_name=building_name,
        )

        return TAILOverallResult(
            overall_rating=overall_rating,
            overall_rating_label=overall_rating.to_label(),
            overall_compliance_rate=round(overall_compliance, 2),
            categories=category_results,
            total_parameters=len(parameter_results),
            visualization=visualization,
            parameter_results=parameter_results,
        )

    # ------------------------------------------------------------------ helpers
    @classmethod
    def _prepare_series(
        cls,
        timeseries_data: Dict[str, pd.Series],
        building_type: Optional[str],
    ) -> Dict[str, pd.Series]:
        """Filter data by weekdays/working hours."""

        filtered: Dict[str, pd.Series] = {}
        mask = cls._build_schedule_mask(timeseries_data, building_type)

        for param, series in timeseries_data.items():
            if not isinstance(series, pd.Series) or series.empty:
                continue

            aligned_series = series.copy()
            if mask is not None and isinstance(aligned_series.index, pd.DatetimeIndex):
                aligned_mask = mask.reindex(aligned_series.index)
                aligned_mask = aligned_mask.fillna(False)
                aligned_series = aligned_series[aligned_mask]

            filtered[param] = aligned_series.dropna()

        return filtered

    @classmethod
    def _build_schedule_mask(
        cls, series_dict: Dict[str, pd.Series], building_type: Optional[str]
    ) -> Optional[pd.Series]:
        """Create occupancy mask for weekdays + working hours."""

        for series in series_dict.values():
            if isinstance(series, pd.Series) and isinstance(series.index, pd.DatetimeIndex):
                if not series.index.empty:
                    profile = get_opening_profile_for_building_type(building_type)
                    return generate_occupancy_mask(series.index, profile)
        return None

    @classmethod
    def _normalize_parameter_name(cls, parameter: str) -> str:
        token = parameter.lower().replace(" ", "").replace("_", "")
        return cls.PARAMETER_ALIASES.get(token, parameter.lower())

    # ---------------------------------------------------------------- parameter dispatch
    @classmethod
    def _get_parameter_evaluator(cls, parameter: str):
        evaluators = {
            "temperature": cls._evaluate_temperature,
            "relative_humidity": cls._evaluate_humidity,
            "co2": cls._evaluate_co2,
            "pm25": cls._evaluate_pm25,
            "pm10": cls._evaluate_pm10,
            "voc": cls._evaluate_voc,
            "formaldehyde": cls._evaluate_formaldehyde,
            "benzene": cls._evaluate_benzene,
            "radon": cls._evaluate_radon,
            "ventilation": cls._evaluate_ventilation,
            "mold": cls._evaluate_mold,
            "noise": cls._evaluate_noise,
            "illuminance": cls._evaluate_illuminance,
            "daylight_factor": cls._evaluate_daylight_factor,
        }
        return evaluators.get(parameter)

    @classmethod
    def _evaluate_temperature(cls, series: pd.Series, metadata: Dict[str, Any]) -> Optional[TAILParameterResult]:
        series = cls._numeric_series(series)
        if series.empty:
            return None

        season_hint = metadata.get("season_hint")
        season = cls._determine_season(series.index, season_hint)
        thresholds = cls.TEMPERATURE_THRESHOLDS[season]
        counts = cls._count_by_thresholds(series, thresholds)
        summary = float(series.mean())

        return cls._build_parameter_result(
            parameter="temperature",
            category=TAILCategory.THERMAL,
            counts=counts,
            sample_count=int(series.size),
            summary_value=round(summary, 2),
            metadata={"season": season, "thresholds": thresholds},
        )

    @classmethod
    def _evaluate_humidity(cls, series: pd.Series, metadata: Dict[str, Any]) -> Optional[TAILParameterResult]:
        series = cls._numeric_series(series)
        if series.empty:
            return None
        series = series[(series >= 1.0) & (series <= 100.0)].round()
        if series.empty:
            return None

        building_type = (metadata.get("building_type") or "default").lower()
        if building_type not in cls.RH_THRESHOLDS:
            building_type = "default"

        thresholds = cls.RH_THRESHOLDS[building_type]
        counts = cls._count_by_thresholds(series, thresholds)

        return cls._build_parameter_result(
            parameter="relative_humidity",
            category=TAILCategory.IAQ,
            counts=counts,
            sample_count=int(series.size),
            summary_value=round(float(series.mean()), 2),
            metadata={"building_type": building_type, "thresholds": thresholds},
        )

    # Pollutants ---------------------------------------------------------------------------
    @classmethod
    def _evaluate_pm25(cls, series: pd.Series, metadata: Dict[str, Any]) -> Optional[TAILParameterResult]:
        return cls._evaluate_pollutant_series("pm25", series, metadata)

    @classmethod
    def _evaluate_pm10(cls, series: pd.Series, metadata: Dict[str, Any]) -> Optional[TAILParameterResult]:
        return cls._evaluate_pollutant_series("pm10", series, metadata)

    @classmethod
    def _evaluate_voc(cls, series: pd.Series, metadata: Dict[str, Any]) -> Optional[TAILParameterResult]:
        return cls._evaluate_pollutant_series("voc", series, metadata)

    @classmethod
    def _evaluate_formaldehyde(cls, series: pd.Series, metadata: Dict[str, Any]) -> Optional[TAILParameterResult]:
        return cls._evaluate_pollutant_series("formaldehyde", series, metadata)

    @classmethod
    def _evaluate_benzene(cls, series: pd.Series, metadata: Dict[str, Any]) -> Optional[TAILParameterResult]:
        return cls._evaluate_pollutant_series("benzene", series, metadata)

    @classmethod
    def _evaluate_radon(cls, series: pd.Series, metadata: Dict[str, Any]) -> Optional[TAILParameterResult]:
        return cls._evaluate_pollutant_series("radon", series, metadata)

    @classmethod
    def _evaluate_pollutant_series(
        cls, parameter: str, series: pd.Series, metadata: Dict[str, Any]
    ) -> Optional[TAILParameterResult]:
        series = cls._numeric_series(series)
        if series.empty:
            return None

        thresholds = cls.POLLUTANT_THRESHOLDS[parameter]
        counts = cls._count_by_thresholds(series, thresholds)

        return cls._build_parameter_result(
            parameter=parameter,
            category=TAILCategory.IAQ,
            counts=counts,
            sample_count=int(series.size),
            summary_value=round(float(series.mean()), 2),
            metadata={"thresholds": thresholds},
        )

    # IAQ specific calculations -------------------------------------------------------------
    @classmethod
    def _evaluate_co2(cls, series: pd.Series, metadata: Dict[str, Any]) -> Optional[TAILParameterResult]:
        series = cls._numeric_series(series)
        if series.empty:
            return None

        p95 = float(series.quantile(0.95))
        thresholds = [("green", None, 800.0), ("yellow", 800.0, 1000.0), ("orange", 1000.0, 1400.0)]
        label_counts = cls._counts_from_single_value(p95, thresholds)

        return cls._build_parameter_result(
            parameter="co2",
            category=TAILCategory.IAQ,
            counts=label_counts,
            sample_count=1,
            summary_value=round(p95, 2),
            metadata={"percentile": 95, "thresholds": thresholds},
        )

    @classmethod
    def _evaluate_ventilation(
        cls, series: pd.Series, metadata: Dict[str, Any]
    ) -> Optional[TAILParameterResult]:
        series = cls._numeric_series(series)
        if series.empty:
            return None

        required = cls._ventilation_requirement(metadata)
        ratio_series = series / required["per_person_rate_lps"]
        thresholds = [
            ("green", 1.0, None),
            ("yellow", 0.8, 1.0),
            ("orange", 0.6, 0.8),
        ]
        counts = cls._count_by_thresholds(ratio_series, thresholds)

        return cls._build_parameter_result(
            parameter="ventilation",
            category=TAILCategory.IAQ,
            counts=counts,
            sample_count=int(series.size),
            summary_value=round(float(series.mean()), 2),
            metadata={"requirement": required, "thresholds": thresholds},
        )

    @classmethod
    def _evaluate_mold(cls, series: pd.Series, metadata: Dict[str, Any]) -> Optional[TAILParameterResult]:
        if not isinstance(series, pd.Series) or series.empty:
            return None

        counts = {color: 0 for color in cls.COLOR_ORDER}
        normalized_entries = series.astype(str).str.lower()

        for entry in normalized_entries:
            if any(term in entry for term in ["no visible", "none detected", "absent"]):
                color = "green"
            elif any(term in entry for term in ["trace", "isolated", "minor"]):
                color = "yellow"
            elif any(term in entry for term in ["localized", "surface", "moderate"]):
                color = "orange"
            else:
                color = "red"
            counts[color] += 1

        return cls._build_parameter_result(
            parameter="mold",
            category=TAILCategory.IAQ,
            counts=counts,
            sample_count=len(normalized_entries),
            summary_value=None,
            metadata={},
        )

    # Acoustic ------------------------------------------------------------------------------
    @classmethod
    def _evaluate_noise(cls, series: pd.Series, metadata: Dict[str, Any]) -> Optional[TAILParameterResult]:
        series = cls._numeric_series(series)
        if series.empty:
            return None

        noise_p5 = float(np.percentile(series, 5))
        room_type = (metadata.get("room_type") or metadata.get("building_type") or "default").lower()
        if room_type not in cls.NOISE_THRESHOLDS:
            room_type = "default"

        threshold = cls.NOISE_THRESHOLDS[room_type]
        counts = cls._counts_from_single_value(noise_p5, [
            ("green", None, threshold["green"]),
            ("yellow", threshold["green"], threshold["yellow"]),
            ("orange", threshold["yellow"], threshold["orange"]),
        ])

        return cls._build_parameter_result(
            parameter="noise",
            category=TAILCategory.ACOUSTIC,
            counts=counts,
            sample_count=1,
            summary_value=round(noise_p5, 2),
            metadata={"room_type": room_type, "thresholds": threshold},
        )

    # Luminous -----------------------------------------------------------------------------
    @classmethod
    def _evaluate_illuminance(cls, series: pd.Series, metadata: Dict[str, Any]) -> Optional[TAILParameterResult]:
        series = cls._numeric_series(series)
        if series.empty:
            return None

        building_type = (metadata.get("building_type") or "default").lower()
        target = cls.ILLUMINANCE_TARGETS.get(building_type, cls.ILLUMINANCE_TARGETS["default"])
        compliance_pct = float((series >= target).sum() / len(series) * 100.0)

        counts = cls._counts_from_single_value(
            compliance_pct,
            [
                ("green", 95.0, None),
                ("yellow", 70.0, 95.0),
                ("orange", 50.0, 70.0),
            ],
            red_if_below=True,
        )

        return cls._build_parameter_result(
            parameter="illuminance",
            category=TAILCategory.LUMINOUS,
            counts=counts,
            sample_count=1,
            summary_value=round(compliance_pct, 2),
            metadata={"target_lux": target, "percentage_compliant": compliance_pct},
        )

    @classmethod
    def _evaluate_daylight_factor(cls, series: pd.Series, metadata: Dict[str, Any]) -> Optional[TAILParameterResult]:
        series = cls._numeric_series(series)
        if series.empty:
            return None

        thresholds = cls.DAYLIGHT_THRESHOLDS
        counts = cls._count_by_thresholds(series, thresholds)

        return cls._build_parameter_result(
            parameter="daylight_factor",
            category=TAILCategory.LUMINOUS,
            counts=counts,
            sample_count=int(series.size),
            summary_value=round(float(series.mean()), 2),
            metadata={"thresholds": thresholds},
        )

    # Generic ------------------------------------------------------------------------------
    @classmethod
    def _evaluate_generic(
        cls,
        parameter: str,
        series: pd.Series,
        category: TAILCategory,
        thresholds: Dict[str, float],
    ) -> Optional[TAILParameterResult]:
        series = cls._numeric_series(series)
        if series.empty or not thresholds:
            return None

        lower = thresholds.get("lower", float("-inf"))
        upper = thresholds.get("upper", float("inf"))
        span = upper - lower if np.isfinite(lower) and np.isfinite(upper) else None

        counts = {color: 0 for color in cls.COLOR_ORDER}
        for value in series:
            if lower <= value <= upper:
                counts["green"] += 1
            elif span is not None:
                delta = min(abs(value - upper), abs(value - lower))
                if delta <= 0.05 * span:
                    counts["yellow"] += 1
                elif delta <= 0.15 * span:
                    counts["orange"] += 1
                else:
                    counts["red"] += 1
            else:
                counts["red"] += 1

        return cls._build_parameter_result(
            parameter=parameter,
            category=category,
            counts=counts,
            sample_count=int(series.size),
            summary_value=round(float(series.mean()), 2),
            metadata={"thresholds": thresholds},
        )

    # ---------------------------------------------------------------- aggregation helpers
    @classmethod
    def _build_category_results(
        cls, parameter_results: List[TAILParameterResult]
    ) -> Dict[TAILCategory, TAILCategoryResult]:
        grouped: Dict[TAILCategory, List[TAILParameterResult]] = {
            cat: [] for cat in TAILCategory
        }
        for result in parameter_results:
            grouped[result.category].append(result)

        category_results: Dict[TAILCategory, TAILCategoryResult] = {}
        for category, params in grouped.items():
            if not params:
                continue

            worst_rating = max(param.rating for param in params)
            compliance = sum(
                param.metadata.get("compliance_rate", 0.0) for param in params
            ) / len(params)

            dominant_color = cls._worst_color_from_params(params)

            category_results[category] = TAILCategoryResult(
                category=category,
                rating=worst_rating,
                rating_label=worst_rating.to_label(),
                compliance_rate=round(compliance, 2),
                parameter_count=len(params),
                parameters=params,
                dominant_color=dominant_color,
            )

        return category_results

    @classmethod
    def _summarize_overall(
        cls, category_results: Dict[TAILCategory, TAILCategoryResult]
    ) -> Tuple[TAILRating, float]:
        if not category_results:
            return TAILRating.POOR, 0.0

        worst_rating = max(category.rating for category in category_results.values())
        compliance = sum(cat.compliance_rate for cat in category_results.values()) / len(
            category_results
        )
        return worst_rating, compliance

    @classmethod
    def _build_visualization(
        cls,
        parameter_results: List[TAILParameterResult],
        category_results: Dict[TAILCategory, TAILCategoryResult],
        overall_rating: TAILRating,
        overall_compliance: float,
        metadata: Dict[str, Any],
        building_name: Optional[str],
    ) -> Dict[str, Any]:
        visualization: Dict[str, Any] = {
            "entity": building_name or metadata.get("entity_name"),
            "overall": {
                "rating": overall_rating.to_label(),
                "rating_color": overall_rating.to_color(),
                "compliance": round(overall_compliance, 2),
            },
            "domains": {},
            "metadata": {
                "building_type": metadata.get("building_type"),
                "room_type": metadata.get("room_type"),
                "area_m2": metadata.get("area_m2"),
                "design_occupancy": metadata.get("design_occupancy"),
            },
        }

        for category, result in category_results.items():
            domain_payload = {
                "rating": result.rating_label,
                "rating_color": result.rating.to_color(),
                "compliance": result.compliance_rate,
                "dominant_color": result.dominant_color,
                "parameters": {},
            }
            for param in result.parameters:
                domain_payload["parameters"][param.parameter] = {
                    "rating": param.rating_label,
                    "rating_color": param.rating.to_color(),
                    "dominant_color": param.dominant_color,
                    "distribution": param.distribution,
                    "samples": param.sample_count,
                    "summary_value": param.summary_value,
                    "metadata": param.metadata,
                }
            visualization["domains"][category.value] = domain_payload

        return visualization

    # ---------------------------------------------------------------- utility helpers
    @classmethod
    def _numeric_series(cls, series: pd.Series) -> pd.Series:
        if not isinstance(series, pd.Series):
            return pd.Series(dtype=float)
        numeric = pd.to_numeric(series, errors="coerce")
        return numeric.dropna()

    @classmethod
    def _count_by_thresholds(
        cls,
        series: pd.Series,
        thresholds: List[Tuple[str, Optional[float], Optional[float]]],
    ) -> Dict[str, int]:
        counts = {color: 0 for color in cls.COLOR_ORDER}
        for value in series:
            color = cls._color_from_thresholds(value, thresholds)
            counts[color] += 1
        return counts

    @classmethod
    def _color_from_thresholds(
        cls,
        value: float,
        thresholds: List[Tuple[str, Optional[float], Optional[float]]],
        red_if_below: bool = False,
    ) -> str:
        for color, lower, upper in thresholds:
            lower_check = lower if lower is not None else float("-inf")
            upper_check = upper if upper is not None else float("inf")
            if lower_check <= value <= upper_check:
                return color
        if red_if_below:
            return "red"
        return "red"

    @classmethod
    def _counts_from_single_value(
        cls,
        value: float,
        thresholds: List[Tuple[str, Optional[float], Optional[float]]],
        red_if_below: bool = False,
    ) -> Dict[str, int]:
        color = cls._color_from_thresholds(value, thresholds, red_if_below)
        counts = {key: 0 for key in cls.COLOR_ORDER}
        counts[color] = 1
        return counts

    @classmethod
    def _build_parameter_result(
        cls,
        parameter: str,
        category: TAILCategory,
        counts: Dict[str, int],
        sample_count: int,
        summary_value: Optional[float],
        metadata: Dict[str, Any],
    ) -> TAILParameterResult:
        distribution = cls._distribution(counts)
        dominant_color = cls._worst_color(counts)
        rating = cls.COLOR_TO_RATING[dominant_color]
        metadata = dict(metadata)
        metadata["compliance_rate"] = cls._compliance_from_distribution(distribution)

        return TAILParameterResult(
            parameter=parameter,
            category=category,
            rating=rating,
            rating_label=rating.to_label(),
            dominant_color=dominant_color.title(),
            distribution=distribution,
            sample_count=sample_count,
            summary_value=summary_value,
            metadata=metadata,
        )

    @classmethod
    def _distribution(cls, counts: Dict[str, int]) -> Dict[str, float]:
        total = sum(counts.values())
        if total == 0:
            return {color: 0.0 for color in cls.COLOR_ORDER}
        return {
            color: round(count / total * 100.0, 2) for color, count in counts.items()
        }

    @classmethod
    def _worst_color(cls, counts: Dict[str, int]) -> str:
        for color in reversed(cls.COLOR_ORDER):
            if counts.get(color, 0) > 0:
                return color
        return "green"

    @classmethod
    def _worst_color_from_params(cls, params: List[TAILParameterResult]) -> str:
        color_counts = {color: 0 for color in cls.COLOR_ORDER}
        for param in params:
            for color, pct in param.distribution.items():
                if pct > 0:
                    color_counts[color] += 1
        return cls._worst_color(color_counts).title()

    @classmethod
    def _compliance_from_distribution(cls, distribution: Dict[str, float]) -> float:
        return round(distribution.get("green", 0.0) + 0.5 * distribution.get("yellow", 0.0), 2)

    @classmethod
    def _determine_season(
        cls, index: pd.Index, season_hint: Optional[str] = None
    ) -> str:
        if season_hint in ("heating", "non_heating"):
            return "heating" if season_hint == "heating" else "non_heating"

        if isinstance(index, pd.DatetimeIndex) and not index.empty:
            heating_months = {10, 11, 12, 1, 2, 3}
            heating_count = sum(1 for month in index.month if month in heating_months)
            return "heating" if heating_count >= len(index) / 2 else "non_heating"

        return "heating"

    @classmethod
    def _ventilation_requirement(cls, metadata: Dict[str, Any]) -> Dict[str, Any]:
        area = metadata.get("area_m2") or 0.0
        occupancy = metadata.get("design_occupancy") or metadata.get("design_occupants")
        if occupancy is None and area:
            occupancy = max(1, round(area / 10.0))
        occupancy = occupancy or 1
        per_person = cls.VENTILATION_PER_PERSON_LPS
        total = per_person * occupancy
        return {
            "per_person_rate_lps": per_person,
            "total_lps": total,
            "assumed_occupancy": occupancy,
            "area_m2": area,
        }
