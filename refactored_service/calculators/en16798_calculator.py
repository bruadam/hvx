"""
EN 16798-1 standard calculator for the refactored service.

Implements full EN 16798-1 calculations including:
- Fixed temperature thresholds for heating/cooling seasons
- Adaptive comfort model for naturally ventilated buildings
- CO2 concentration limits
- Humidity thresholds
- Required ventilation rates
- Category determination based on compliance
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, Dict, List
import numpy as np
import pandas as pd

try:
    from pythermalcomfort.models import adaptive_en
    from pythermalcomfort.utilities import running_mean_outdoor_temperature
    PYTHERMALCOMFORT_AVAILABLE = True
except ImportError:
    PYTHERMALCOMFORT_AVAILABLE = False
    adaptive_en = None
    running_mean_outdoor_temperature = None


class EN16798Category(str, Enum):
    """EN 16798-1 indoor environment categories."""
    CATEGORY_I = "I"      # High level of expectation
    CATEGORY_II = "II"    # Normal level of expectation
    CATEGORY_III = "III"  # Moderate level of expectation
    CATEGORY_IV = "IV"    # Low level of expectation


class VentilationType(str, Enum):
    """Building ventilation types."""
    MECHANICAL = "mechanical"
    NATURAL = "natural"
    MIXED_MODE = "mixed_mode"


class PollutionLevel(str, Enum):
    """Building pollution level for ventilation calculations."""
    VERY_LOW = "very_low"      # 0.0 L/(s·m²)
    LOW = "low"                # 0.5 L/(s·m²)
    NON_LOW = "non_low"        # 1.0 L/(s·m²)

    @property
    def emission_factor(self) -> float:
        """Get building emission factor in L/(s·m²)."""
        factors = {
            "very_low": 0.0,
            "low": 0.5,
            "non_low": 1.0,
        }
        return factors[self.value]


@dataclass
class EN16798Thresholds:
    """Complete thresholds for a specific EN 16798-1 category."""
    category: EN16798Category
    temperature_heating: Dict[str, float]
    temperature_cooling: Dict[str, float]
    co2_ppm: float
    humidity_lower: float
    humidity_upper: float
    ventilation_per_person_l_s: float
    ventilation_per_area_l_s_m2: float


@dataclass
class EN16798ComplianceResult:
    """Results of EN 16798-1 compliance assessment."""
    achieved_category: Optional[EN16798Category]
    all_compliant_categories: List[EN16798Category]
    compliance_by_category: Dict[EN16798Category, Dict[str, Any]]
    thresholds_used: Dict[EN16798Category, EN16798Thresholds]
    season: str
    adaptive_model_used: bool


@dataclass
class VentilationRequirement:
    """Calculated ventilation requirements."""
    total_ventilation_l_s: float
    ventilation_per_person_l_s: float
    ventilation_per_area_l_s_m2: float
    occupant_contribution_l_s: float
    building_contribution_l_s: float
    air_change_rate_ach: Optional[float]
    category: EN16798Category


class EN16798Calculator:
    """
    Complete EN 16798-1 calculator for indoor environmental assessment.

    This calculator provides:
    1. Temperature thresholds (fixed and adaptive comfort)
    2. CO2 concentration limits
    3. Humidity thresholds
    4. Required ventilation rates
    5. Category determination from measurements
    """

    # Temperature thresholds for heating season (°C)
    TEMP_HEATING = {
        EN16798Category.CATEGORY_I: {"lower": 21.0, "upper": 23.0, "design": 22.0},
        EN16798Category.CATEGORY_II: {"lower": 20.0, "upper": 24.0, "design": 22.0},
        EN16798Category.CATEGORY_III: {"lower": 19.0, "upper": 25.0, "design": 22.0},
        EN16798Category.CATEGORY_IV: {"lower": 17.0, "upper": 27.0, "design": 22.0},
    }

    # Temperature thresholds for cooling season (°C)
    TEMP_COOLING = {
        EN16798Category.CATEGORY_I: {"lower": 23.5, "upper": 25.5, "design": 24.5},
        EN16798Category.CATEGORY_II: {"lower": 23.0, "upper": 26.0, "design": 24.5},
        EN16798Category.CATEGORY_III: {"lower": 22.0, "upper": 27.0, "design": 24.5},
        EN16798Category.CATEGORY_IV: {"lower": 20.0, "upper": 29.0, "design": 24.5},
    }

    # Adaptive comfort deviations (°C)
    ADAPTIVE_TEMP_DEVIATION = {
        EN16798Category.CATEGORY_I: 2.0,
        EN16798Category.CATEGORY_II: 3.0,
        EN16798Category.CATEGORY_III: 4.0,
        EN16798Category.CATEGORY_IV: 5.0,
    }

    # CO2 above outdoor (ppm)
    CO2_ABOVE_OUTDOOR = {
        EN16798Category.CATEGORY_I: 550,
        EN16798Category.CATEGORY_II: 800,
        EN16798Category.CATEGORY_III: 1350,
        EN16798Category.CATEGORY_IV: 1350,
    }

    # Relative humidity (%)
    HUMIDITY = {
        EN16798Category.CATEGORY_I: {"lower": 30, "upper": 50},
        EN16798Category.CATEGORY_II: {"lower": 25, "upper": 60},
        EN16798Category.CATEGORY_III: {"lower": 20, "upper": 70},
        EN16798Category.CATEGORY_IV: {"lower": 15, "upper": 80},
    }

    # Ventilation per person (L/(s·person))
    VENTILATION_PER_PERSON = {
        EN16798Category.CATEGORY_I: 10,
        EN16798Category.CATEGORY_II: 7,
        EN16798Category.CATEGORY_III: 4,
        EN16798Category.CATEGORY_IV: 4,
    }

    OUTDOOR_CO2 = 400.0  # Default outdoor CO2 (ppm)

    @classmethod
    def get_temperature_thresholds(
        cls,
        category: EN16798Category,
        season: str = "heating",
        outdoor_running_mean_temp: Optional[float] = None,
        ventilation_type: VentilationType = VentilationType.MECHANICAL
    ) -> Dict[str, float]:
        """Get temperature thresholds for a category."""
        # Use adaptive comfort for natural/mixed-mode ventilation
        if (ventilation_type in [VentilationType.NATURAL, VentilationType.MIXED_MODE]
            and outdoor_running_mean_temp is not None
            and 10.0 <= outdoor_running_mean_temp <= 30.0):
            return cls._get_adaptive_temperature_thresholds(category, outdoor_running_mean_temp)

        # Use fixed thresholds
        if season.lower() == "cooling":
            return cls.TEMP_COOLING[category].copy()
        else:
            return cls.TEMP_HEATING[category].copy()

    @classmethod
    def _get_adaptive_temperature_thresholds(
        cls,
        category: EN16798Category,
        outdoor_running_mean_temp: float
    ) -> Dict[str, Any]:
        """Calculate adaptive comfort thresholds."""
        # Comfort temperature: T_comf = 0.33 × T_rm + 18.8
        t_comf = 0.33 * outdoor_running_mean_temp + 18.8

        if PYTHERMALCOMFORT_AVAILABLE and adaptive_en is not None:
            try:
                result = adaptive_en(
                    tdb=t_comf,
                    tr=t_comf,
                    t_running_mean=outdoor_running_mean_temp,
                    v=0.1
                )

                def to_scalar(val: Any) -> float:
                    if isinstance(val, (list, np.ndarray)):
                        return float(val[0]) if len(val) > 0 else 0.0
                    return float(val)

                if category == EN16798Category.CATEGORY_I:
                    lower = to_scalar(result.tmp_cmf_cat_i_low)
                    upper = to_scalar(result.tmp_cmf_cat_i_up)
                elif category == EN16798Category.CATEGORY_II:
                    lower = to_scalar(result.tmp_cmf_cat_ii_low)
                    upper = to_scalar(result.tmp_cmf_cat_ii_up)
                elif category == EN16798Category.CATEGORY_III:
                    lower = to_scalar(result.tmp_cmf_cat_iii_low)
                    upper = to_scalar(result.tmp_cmf_cat_iii_up)
                else:  # Category IV
                    deviation = cls.ADAPTIVE_TEMP_DEVIATION[category]
                    lower = t_comf - deviation
                    upper = t_comf + deviation

                return {
                    "lower": round(lower, 1),
                    "upper": round(upper, 1),
                    "design": round(to_scalar(result.tmp_cmf), 1),
                    "outdoor_running_mean": round(outdoor_running_mean_temp, 1),
                    "adaptive_model": True,
                }
            except Exception:
                pass

        # Fallback: manual calculation
        deviation = cls.ADAPTIVE_TEMP_DEVIATION[category]
        return {
            "lower": round(t_comf - deviation, 1),
            "upper": round(t_comf + deviation, 1),
            "design": round(t_comf, 1),
            "outdoor_running_mean": round(outdoor_running_mean_temp, 1),
            "adaptive_model": True,
        }

    @classmethod
    def calculate_running_mean_outdoor_temp(
        cls,
        daily_outdoor_temps: List[float],
        alpha: float = 0.8
    ) -> Optional[float]:
        """Calculate exponentially-weighted running mean outdoor temperature."""
        if not daily_outdoor_temps or len(daily_outdoor_temps) < 7:
            return sum(daily_outdoor_temps) / len(daily_outdoor_temps) if daily_outdoor_temps else None

        t_rm = 0.0
        weight_sum = 0.0

        for i, temp in enumerate(daily_outdoor_temps[:30]):
            weight = alpha ** i
            t_rm += (1 - alpha) * weight * temp
            weight_sum += (1 - alpha) * weight

        return t_rm / weight_sum if weight_sum > 0 else None

    @classmethod
    def get_thresholds(
        cls,
        category: EN16798Category,
        season: str = "heating",
        outdoor_running_mean_temp: Optional[float] = None,
        ventilation_type: VentilationType = VentilationType.MECHANICAL,
        outdoor_co2: float = OUTDOOR_CO2,
        pollution_level: PollutionLevel = PollutionLevel.NON_LOW
    ) -> EN16798Thresholds:
        """Get complete thresholds for a category."""
        return EN16798Thresholds(
            category=category,
            temperature_heating=cls.get_temperature_thresholds(
                category, "heating", outdoor_running_mean_temp, ventilation_type
            ),
            temperature_cooling=cls.get_temperature_thresholds(
                category, "cooling", outdoor_running_mean_temp, ventilation_type
            ),
            co2_ppm=outdoor_co2 + cls.CO2_ABOVE_OUTDOOR[category],
            humidity_lower=cls.HUMIDITY[category]["lower"],
            humidity_upper=cls.HUMIDITY[category]["upper"],
            ventilation_per_person_l_s=cls.VENTILATION_PER_PERSON[category],
            ventilation_per_area_l_s_m2=pollution_level.emission_factor,
        )

    @classmethod
    def calculate_ventilation_requirement(
        cls,
        category: EN16798Category,
        floor_area_m2: float,
        occupancy_count: int,
        pollution_level: PollutionLevel = PollutionLevel.NON_LOW,
        volume_m3: Optional[float] = None
    ) -> VentilationRequirement:
        """Calculate required ventilation rate."""
        q_p = cls.VENTILATION_PER_PERSON[category]
        q_B = pollution_level.emission_factor

        occupant_contribution = occupancy_count * q_p
        building_contribution = floor_area_m2 * q_B
        total_ventilation = occupant_contribution + building_contribution

        ach = None
        if volume_m3 and volume_m3 > 0:
            q_tot_m3_h = total_ventilation * 3.6
            ach = q_tot_m3_h / volume_m3

        return VentilationRequirement(
            total_ventilation_l_s=round(total_ventilation, 2),
            ventilation_per_person_l_s=q_p,
            ventilation_per_area_l_s_m2=q_B,
            occupant_contribution_l_s=round(occupant_contribution, 2),
            building_contribution_l_s=round(building_contribution, 2),
            air_change_rate_ach=round(ach, 2) if ach else None,
            category=category,
        )

    @classmethod
    def assess_compliance(
        cls,
        measured_values: Dict[str, float],
        season: str = "heating",
        outdoor_running_mean_temp: Optional[float] = None,
        ventilation_type: VentilationType = VentilationType.MECHANICAL,
        outdoor_co2: float = OUTDOOR_CO2,
        categories_to_check: Optional[List[EN16798Category]] = None
    ) -> EN16798ComplianceResult:
        """
        Assess which EN 16798-1 category is achieved based on measurements.

        Args:
            measured_values: Dict with keys "temperature", "co2", "humidity"
            season: "heating" or "cooling"
            outdoor_running_mean_temp: For adaptive comfort
            ventilation_type: Type of ventilation
            outdoor_co2: Outdoor CO2 concentration
            categories_to_check: Categories to evaluate (default: all)

        Returns:
            EN16798ComplianceResult with achieved category and details
        """
        if categories_to_check is None:
            categories_to_check = list(EN16798Category)

        achieved_categories = []
        compliance_details = {}
        thresholds_used = {}
        adaptive_used = False

        for category in categories_to_check:
            compliant = True
            details = {}

            # Get thresholds
            thresholds = cls.get_thresholds(
                category, season, outdoor_running_mean_temp, ventilation_type, outdoor_co2
            )
            thresholds_used[category] = thresholds

            # Check temperature
            if "temperature" in measured_values:
                temp = measured_values["temperature"]
                temp_thresholds = thresholds.temperature_heating if season.lower() == "heating" else thresholds.temperature_cooling
                temp_ok = temp_thresholds["lower"] <= temp <= temp_thresholds["upper"]
                details["temperature"] = {
                    "value": temp,
                    "thresholds": temp_thresholds,
                    "compliant": temp_ok,
                }
                compliant = compliant and temp_ok
                adaptive_used = bool(temp_thresholds.get("adaptive_model", False))

            # Check CO2
            if "co2" in measured_values:
                co2 = measured_values["co2"]
                co2_ok = co2 <= thresholds.co2_ppm
                details["co2"] = {
                    "value": co2,
                    "threshold": thresholds.co2_ppm,
                    "compliant": co2_ok,
                }
                compliant = compliant and co2_ok

            # Check humidity
            if "humidity" in measured_values:
                rh = measured_values["humidity"]
                rh_ok = thresholds.humidity_lower <= rh <= thresholds.humidity_upper
                details["humidity"] = {
                    "value": rh,
                    "lower": thresholds.humidity_lower,
                    "upper": thresholds.humidity_upper,
                    "compliant": rh_ok,
                }
                compliant = compliant and rh_ok

            compliance_details[category] = {
                "compliant": compliant,
                "details": details,
            }

            if compliant:
                achieved_categories.append(category)

        # Best achieved category
        best_category = achieved_categories[0] if achieved_categories else None

        return EN16798ComplianceResult(
            achieved_category=best_category,
            all_compliant_categories=achieved_categories,
            compliance_by_category=compliance_details,
            thresholds_used=thresholds_used,
            season=season,
            adaptive_model_used=bool(adaptive_used),
        )

    @classmethod
    def assess_timeseries_compliance(
        cls,
        temperature: Optional[pd.Series] = None,
        co2: Optional[pd.Series] = None,
        humidity: Optional[pd.Series] = None,
        outdoor_temperature: Optional[pd.Series] = None,
        season: str = "heating",
        ventilation_type: VentilationType = VentilationType.MECHANICAL,
        outdoor_co2: float = OUTDOOR_CO2,
        categories_to_check: Optional[List[EN16798Category]] = None
    ) -> Dict[str, Any]:
        """
        Assess compliance over time series data.

        Returns compliance rates for each category.
        """
        if categories_to_check is None:
            categories_to_check = list(EN16798Category)

        # Calculate running mean outdoor temp if available
        outdoor_running_mean = None
        if outdoor_temperature is not None and len(outdoor_temperature) > 0:
            daily_temps = outdoor_temperature.resample('D').mean().dropna().tolist()
            outdoor_running_mean = cls.calculate_running_mean_outdoor_temp(daily_temps)

        results = {}
        for category in categories_to_check:
            thresholds = cls.get_thresholds(
                category, season, outdoor_running_mean, ventilation_type, outdoor_co2
            )

            compliances = []

            # Temperature compliance
            if temperature is not None:
                temp_thresh = thresholds.temperature_heating if season.lower() == "heating" else thresholds.temperature_cooling
                temp_compliant = (temperature >= temp_thresh["lower"]) & (temperature <= temp_thresh["upper"])
                compliances.append(temp_compliant)

            # CO2 compliance
            if co2 is not None:
                co2_compliant = co2 <= thresholds.co2_ppm
                compliances.append(co2_compliant)

            # Humidity compliance
            if humidity is not None:
                rh_compliant = (humidity >= thresholds.humidity_lower) & (humidity <= thresholds.humidity_upper)
                compliances.append(rh_compliant)

            # Overall compliance (all must pass)
            if compliances:
                overall_compliant = pd.concat(compliances, axis=1).all(axis=1)
                compliance_rate = (overall_compliant.sum() / len(overall_compliant)) * 100
            else:
                compliance_rate = 0.0

            results[category.value] = {
                "compliance_rate": round(compliance_rate, 2),
                "thresholds": thresholds,
            }

        return results
