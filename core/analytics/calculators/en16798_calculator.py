"""EN 16798-1 standard calculator for ventilation rates and thresholds."""

from dataclasses import dataclass
from typing import Any

import numpy as np

from core.domain.enums.en16798_category import EN16798Category
from core.domain.enums.occupancy import ActivityLevel, OccupancyDensity
from core.domain.enums.pollution_level import PollutionLevel
from core.domain.enums.ventilation import VentilationType

try:
    from pythermalcomfort.models import adaptive_en
    from pythermalcomfort.utilities import running_mean_outdoor_temperature
    PYTHERMALCOMFORT_AVAILABLE = True
except ImportError:
    PYTHERMALCOMFORT_AVAILABLE = False
    adaptive_en = None
    running_mean_outdoor_temperature = None


@dataclass
class EN16798RoomMetadata:
    """Metadata required for EN 16798-1 calculations."""

    room_type: str
    floor_area: float  # m²
    volume: float | None = None  # m³
    occupancy_count: int | None = None  # Number of occupants
    ventilation_type: VentilationType = VentilationType.NATURAL
    pollution_level: PollutionLevel = PollutionLevel.NON_LOW
    activity_level: ActivityLevel | None = None
    occupancy_density: OccupancyDensity | None = None
    target_category: EN16798Category = EN16798Category.CATEGORY_II

    def __post_init__(self):
        """Initialize derived properties."""
        # Auto-determine activity level if not provided
        if self.activity_level is None:
            self.activity_level = ActivityLevel.get_for_room_type(self.room_type)

        # Auto-determine occupancy density if not provided
        if self.occupancy_density is None:
            if self.occupancy_count and self.floor_area > 0:
                area_per_person = self.floor_area / self.occupancy_count
                self.occupancy_density = OccupancyDensity.from_area_per_person(area_per_person)
            else:
                self.occupancy_density = OccupancyDensity.get_for_room_type(self.room_type)

        # Estimate occupancy if not provided
        if self.occupancy_count is None:
            self.occupancy_count = int(self.floor_area * self.occupancy_density.typical_occupancy_per_m2)


class EN16798StandardCalculator:
    """
    Calculator for EN 16798-1 thresholds and ventilation requirements.

    This calculator determines:
    - Temperature thresholds for each category (fixed and adaptive)
    - CO2 concentration limits for each category
    - Required ventilation rates based on occupancy and pollution
    - Humidity thresholds

    Temperature Assessment Methods:
    1. Fixed thresholds: For mechanically conditioned buildings (heating/cooling seasons)
    2. Adaptive comfort: For naturally ventilated/mixed-mode buildings based on outdoor temperature
    """

    # Temperature thresholds for heating season (°C) - MECHANICALLY CONDITIONED
    # Table B.1 - Design indoor temperatures for heating
    TEMP_HEATING = {
        EN16798Category.CATEGORY_I: {"lower": 21.0, "upper": 23.0, "design": 22.0},
        EN16798Category.CATEGORY_II: {"lower": 20.0, "upper": 24.0, "design": 22.0},
        EN16798Category.CATEGORY_III: {"lower": 19.0, "upper": 25.0, "design": 22.0},
        EN16798Category.CATEGORY_IV: {"lower": 17.0, "upper": 27.0, "design": 22.0},
    }

    # Temperature thresholds for cooling season (°C) - MECHANICALLY CONDITIONED
    # Table B.2 - Design indoor temperatures for cooling
    TEMP_COOLING = {
        EN16798Category.CATEGORY_I: {"lower": 23.5, "upper": 25.5, "design": 24.5},
        EN16798Category.CATEGORY_II: {"lower": 23.0, "upper": 26.0, "design": 24.5},
        EN16798Category.CATEGORY_III: {"lower": 22.0, "upper": 27.0, "design": 24.5},
        EN16798Category.CATEGORY_IV: {"lower": 20.0, "upper": 29.0, "design": 24.5},
    }

    # Adaptive comfort temperature deviations (°C) - NATURALLY VENTILATED
    # EN 16798-1 Table B.8 - Acceptable temperature ranges for adaptive approach
    # Values represent acceptable deviation from comfort temperature
    ADAPTIVE_TEMP_DEVIATION = {
        EN16798Category.CATEGORY_I: 2.0,   # ±2°C from comfort temp
        EN16798Category.CATEGORY_II: 3.0,  # ±3°C from comfort temp
        EN16798Category.CATEGORY_III: 4.0, # ±4°C from comfort temp
        EN16798Category.CATEGORY_IV: 5.0,  # ±5°C from comfort temp
    }

    # CO2 concentration above outdoor (ppm)
    # Table B.3 - Indoor air quality categories
    CO2_ABOVE_OUTDOOR = {
        EN16798Category.CATEGORY_I: 550,  # High expectation
        EN16798Category.CATEGORY_II: 800,  # Normal expectation
        EN16798Category.CATEGORY_III: 1350,  # Moderate expectation
        EN16798Category.CATEGORY_IV: 1350,  # Above Category III
    }

    # Assumed outdoor CO2 concentration (ppm)
    OUTDOOR_CO2 = 400 # TODO: make it configurable

    # Relative humidity thresholds (%)
    # Section 6.2.1.5 - Humidity criteria
    HUMIDITY = {
        EN16798Category.CATEGORY_I: {"lower": 30, "upper": 50},
        EN16798Category.CATEGORY_II: {"lower": 25, "upper": 60},
        EN16798Category.CATEGORY_III: {"lower": 20, "upper": 70},
        EN16798Category.CATEGORY_IV: {"lower": 15, "upper": 80},
    }

    # Ventilation rate per person (L/(s·person))
    # Table B.5 - Ventilation rates for dilution of human bioeffluents
    VENTILATION_PER_PERSON = {
        EN16798Category.CATEGORY_I: 10,  # L/(s·person)
        EN16798Category.CATEGORY_II: 7,
        EN16798Category.CATEGORY_III: 4,
        EN16798Category.CATEGORY_IV: 4,
    }

    @classmethod
    def get_temperature_thresholds(
        cls,
        category: EN16798Category,
        season: str = "heating",
        outdoor_running_mean_temp: float | None = None,
        ventilation_type: VentilationType = VentilationType.MECHANICAL
    ) -> dict[str, float]:
        """
        Get temperature thresholds for a category and season.

        For naturally ventilated or mixed-mode buildings with outdoor_running_mean_temp provided,
        uses adaptive comfort model. Otherwise uses fixed thresholds for mechanically conditioned.

        Args:
            category: EN 16798-1 category
            season: "heating" or "cooling"
            outdoor_running_mean_temp: Running mean outdoor temperature (°C) for adaptive model
            ventilation_type: Type of ventilation system

        Returns:
            Dictionary with lower, upper, and design temperatures
        """
        # Use adaptive comfort for naturally ventilated buildings when outdoor temp is available
        if (ventilation_type in [VentilationType.NATURAL, VentilationType.MIXED_MODE]
            and outdoor_running_mean_temp is not None
            and PYTHERMALCOMFORT_AVAILABLE):
            return cls._get_adaptive_temperature_thresholds(
                category, outdoor_running_mean_temp
            )

        # Otherwise use fixed thresholds
        if season.lower() == "cooling":
            return cls.TEMP_COOLING[category].copy()
        else:
            return cls.TEMP_HEATING[category].copy()

    @classmethod
    def _get_adaptive_temperature_thresholds(
        cls,
        category: EN16798Category,
        outdoor_running_mean_temp: float
    ) -> dict[str, Any]:
        """
        Calculate adaptive thermal comfort thresholds based on outdoor running mean temperature.

        Uses pythermalcomfort's adaptive_en function which implements EN 16798-1/EN 15251
        adaptive comfort model.

        Args:
            category: EN 16798-1 category
            outdoor_running_mean_temp: Running mean outdoor temperature (°C)

        Returns:
            Dictionary with lower, upper, and design (comfort) temperatures
        """
        # EN 16798-1 limits adaptive model application:
        # - Valid for 10°C ≤ T_rm ≤ 30°C
        if outdoor_running_mean_temp < 10.0 or outdoor_running_mean_temp > 30.0:
            # Outside valid range, fall back to fixed thresholds
            if outdoor_running_mean_temp < 15.0:
                return {**cls.TEMP_HEATING[category], "model": "fixed_heating"}
            else:
                return {**cls.TEMP_COOLING[category], "model": "fixed_cooling"}

        if PYTHERMALCOMFORT_AVAILABLE and adaptive_en is not None:
            try:
                # Use pythermalcomfort's adaptive_en model
                # The model uses operative temperature, so we use comfort temp for both tdb and tr
                # to get the neutral comfort point
                t_comf = 0.33 * outdoor_running_mean_temp + 18.8

                result = adaptive_en(
                    tdb=t_comf,
                    tr=t_comf,
                    t_running_mean=outdoor_running_mean_temp,
                    v=0.1  # Assume low air speed
                )

                # Helper function to extract scalar from potential list/array
                def to_scalar(val: Any) -> float:
                    if isinstance(val, (list, np.ndarray)):
                        return float(val[0]) if len(val) > 0 else 0.0
                    return float(val)

                # pythermalcomfort returns a named tuple with attributes
                # Map EN 16798 categories to the result attributes
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
                    # Use manual calculation for Category IV (±5°C)
                    deviation = cls.ADAPTIVE_TEMP_DEVIATION[category]
                    lower = t_comf - deviation
                    upper = t_comf + deviation

                return {
                    "lower": round(lower, 1),
                    "upper": round(upper, 1),
                    "design": round(to_scalar(result.tmp_cmf), 1),
                    "outdoor_running_mean": round(outdoor_running_mean_temp, 1),
                    "adaptive_model": True,
                    "model": "adaptive_en",
                }

            except Exception:
                # Fall back to manual calculation if pythermalcomfort fails
                pass

        # Manual calculation (fallback or when pythermalcomfort not available)
        # Comfort temperature calculation (EN 16798-1 adaptive model)
        # T_comf = 0.33 × T_rm + 18.8
        t_comf = 0.33 * outdoor_running_mean_temp + 18.8

        # Get acceptable deviation for this category
        deviation = cls.ADAPTIVE_TEMP_DEVIATION[category]

        # Calculate acceptable range
        lower = t_comf - deviation
        upper = t_comf + deviation

        return {
            "lower": round(lower, 1),
            "upper": round(upper, 1),
            "design": round(t_comf, 1),
            "outdoor_running_mean": round(outdoor_running_mean_temp, 1),
            "adaptive_model": True,
            "model": "manual",
        }

    @classmethod
    def calculate_running_mean_outdoor_temp(
        cls,
        daily_outdoor_temps: list[float],
        alpha: float = 0.8
    ) -> float | None:
        """
        Calculate exponentially-weighted running mean outdoor temperature.

        T_rm = (1-α) × [T_ed-1 + α×T_ed-2 + α²×T_ed-3 + ...]

        Where:
        - T_rm = running mean outdoor temperature
        - T_ed-i = daily mean outdoor temperature for i days ago
        - α = constant (0.8 recommended for EN 16798-1)

        Args:
            daily_outdoor_temps: List of daily mean outdoor temperatures,
                                most recent first [today, yesterday, 2 days ago, ...]
            alpha: Weighting constant (default 0.8 per EN 16798-1)

        Returns:
            Running mean outdoor temperature in °C
        """
        if not daily_outdoor_temps:
            return None

        # Ensure we have at least 7 days of data (recommended minimum)
        if len(daily_outdoor_temps) < 7:
            # If less than 7 days, use simple average
            return sum(daily_outdoor_temps) / len(daily_outdoor_temps)

        # Calculate exponentially weighted running mean
        t_rm = 0.0
        weight_sum = 0.0

        for i, temp in enumerate(daily_outdoor_temps[:30]):  # Use up to 30 days
            weight = alpha ** i
            t_rm += (1 - alpha) * weight * temp
            weight_sum += (1 - alpha) * weight

        if weight_sum > 0:
            return t_rm / weight_sum
        else:
            return sum(daily_outdoor_temps[:7]) / min(7, len(daily_outdoor_temps))

    @classmethod
    def get_co2_threshold(
        cls,
        category: EN16798Category,
        outdoor_co2: float = OUTDOOR_CO2
    ) -> float:
        """
        Get absolute CO2 concentration threshold for a category.

        Args:
            category: EN 16798-1 category
            outdoor_co2: Outdoor CO2 concentration in ppm

        Returns:
            Maximum indoor CO2 concentration in ppm
        """
        return outdoor_co2 + cls.CO2_ABOVE_OUTDOOR[category]

    @classmethod
    def get_humidity_thresholds(
        cls,
        category: EN16798Category
    ) -> dict[str, int]:
        """
        Get relative humidity thresholds for a category.

        Args:
            category: EN 16798-1 category

        Returns:
            Dictionary with lower and upper RH limits (%)
        """
        return cls.HUMIDITY[category].copy()

    @classmethod
    def calculate_required_ventilation_rate(
        cls,
        room_metadata: EN16798RoomMetadata,
        category: EN16798Category
    ) -> dict[str, Any]:
        """
        Calculate required ventilation rate for a room.

        EN 16798-1 equation: q_tot = n × q_p + A × q_B

        Where:
        - q_tot = total ventilation rate [L/s]
        - n = number of persons
        - q_p = ventilation rate per person [L/(s·person)]
        - A = floor area [m²]
        - q_B = ventilation rate per floor area for building emissions [L/(s·m²)]

        Args:
            room_metadata: Room metadata
            category: Target EN 16798-1 category

        Returns:
            Dictionary with ventilation calculations
        """
        # Ventilation per person
        q_p = cls.VENTILATION_PER_PERSON[category]

        # Ventilation per floor area (building emissions)
        q_B = room_metadata.pollution_level.building_emission_factor

        # Number of occupants
        n = room_metadata.occupancy_count or 0

        # Total ventilation rate
        q_tot = n * q_p + room_metadata.floor_area * q_B

        # Air change rate (if volume known)
        ach = None
        if room_metadata.volume and room_metadata.volume > 0:
            # Convert L/s to m³/h and divide by volume
            q_tot_m3_h = q_tot * 3.6  # L/s to m³/h
            ach = q_tot_m3_h / room_metadata.volume

        # Ventilation rate per floor area
        q_per_m2 = q_tot / room_metadata.floor_area if room_metadata.floor_area > 0 else 0

        return {
            "total_ventilation_l_s": round(q_tot, 2),
            "ventilation_per_person_l_s": q_p,
            "ventilation_per_area_l_s_m2": q_B,
            "occupant_contribution_l_s": round(n * q_p, 2),
            "building_contribution_l_s": round(room_metadata.floor_area * q_B, 2),
            "ventilation_per_floor_area_l_s_m2": round(q_per_m2, 2),
            "air_change_rate_ach": round(ach, 2) if ach else None,
            "occupancy_count": n,
            "floor_area_m2": room_metadata.floor_area,
            "category": category.value,
        }

    @classmethod
    def get_all_thresholds_for_room(
        cls,
        room_metadata: EN16798RoomMetadata,
        categories: list[EN16798Category] | None = None,
        outdoor_running_mean_temp: float | None = None
    ) -> dict[EN16798Category, dict[str, Any]]:
        """
        Get all thresholds for all categories for a specific room.

        Args:
            room_metadata: Room metadata
            categories: List of categories to evaluate (default: all)
            outdoor_running_mean_temp: Running mean outdoor temperature for adaptive comfort

        Returns:
            Dictionary mapping category to all thresholds
        """
        if categories is None:
            categories = list(EN16798Category)

        result = {}

        for category in categories:
            result[category] = {
                "category": category.value,
                "category_name": category.display_name,
                "temperature_heating": cls.get_temperature_thresholds(
                    category, "heating", outdoor_running_mean_temp, room_metadata.ventilation_type
                ),
                "temperature_cooling": cls.get_temperature_thresholds(
                    category, "cooling", outdoor_running_mean_temp, room_metadata.ventilation_type
                ),
                "co2_threshold_ppm": cls.get_co2_threshold(category),
                "humidity_thresholds": cls.get_humidity_thresholds(category),
                "ventilation": cls.calculate_required_ventilation_rate(
                    room_metadata, category
                ),
            }

        return result

    @classmethod
    def determine_achieved_category(
        cls,
        room_metadata: EN16798RoomMetadata,
        measured_values: dict[str, float],
        season: str = "heating",
        outdoor_running_mean_temp: float | None = None
    ) -> dict[str, Any]:
        """
        Determine which EN 16798-1 category is achieved based on measurements.

        Args:
            room_metadata: Room metadata
            measured_values: Dict with keys like "temperature", "co2", "humidity"
            season: "heating" or "cooling"
            outdoor_running_mean_temp: Running mean outdoor temperature for adaptive comfort

        Returns:
            Dictionary with achieved category and details
        """
        achieved_categories = []
        compliance_details = {}

        # Check each category from best to worst
        for category in [
            EN16798Category.CATEGORY_I,
            EN16798Category.CATEGORY_II,
            EN16798Category.CATEGORY_III,
            EN16798Category.CATEGORY_IV,
        ]:
            compliant = True
            details = {}

            # Check temperature
            if "temperature" in measured_values:
                temp = measured_values["temperature"]
                temp_thresholds = cls.get_temperature_thresholds(
                    category, season, outdoor_running_mean_temp, room_metadata.ventilation_type
                )
                temp_ok = temp_thresholds["lower"] <= temp <= temp_thresholds["upper"]
                details["temperature"] = {
                    "value": temp,
                    "thresholds": temp_thresholds,
                    "compliant": temp_ok,
                }
                compliant = compliant and temp_ok

            # Check CO2
            if "co2" in measured_values:
                co2 = measured_values["co2"]
                co2_threshold = cls.get_co2_threshold(category)
                co2_ok = co2 <= co2_threshold
                details["co2"] = {
                    "value": co2,
                    "threshold": co2_threshold,
                    "compliant": co2_ok,
                }
                compliant = compliant and co2_ok

            # Check humidity
            if "humidity" in measured_values:
                rh = measured_values["humidity"]
                rh_thresholds = cls.get_humidity_thresholds(category)
                rh_ok = rh_thresholds["lower"] <= rh <= rh_thresholds["upper"]
                details["humidity"] = {
                    "value": rh,
                    "thresholds": rh_thresholds,
                    "compliant": rh_ok,
                }
                compliant = compliant and rh_ok

            compliance_details[category] = {
                "compliant": compliant,
                "details": details,
            }

            if compliant:
                achieved_categories.append(category)

        # Highest achieved category
        highest = achieved_categories[0] if achieved_categories else None

        return {
            "achieved_category": highest.value if highest else None,
            "achieved_category_name": highest.display_name if highest else "None",
            "all_compliant_categories": [c.value for c in achieved_categories],
            "compliance_details": compliance_details,
        }
