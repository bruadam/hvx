"""ASHRAE 55 Adaptive Thermal Comfort Calculator.

This calculator implements the ASHRAE 55 adaptive comfort model for naturally
conditioned spaces, using the pythermalcomfort library.
"""

from dataclasses import dataclass
from typing import Any

import numpy as np

try:
    from pythermalcomfort.models import adaptive_ashrae
    from pythermalcomfort.utilities import running_mean_outdoor_temperature
    PYTHERMALCOMFORT_AVAILABLE = True
except ImportError:
    PYTHERMALCOMFORT_AVAILABLE = False
    adaptive_ashrae = None
    running_mean_outdoor_temperature = None


@dataclass
class ASHRAEAdaptiveResult:
    """Result from ASHRAE adaptive comfort calculation."""

    tmp_cmf: float  # Comfort temperature (°C)
    tmp_cmf_80_low: float  # 80% acceptability lower limit (°C)
    tmp_cmf_80_up: float  # 80% acceptability upper limit (°C)
    tmp_cmf_90_low: float  # 90% acceptability lower limit (°C)
    tmp_cmf_90_up: float  # 90% acceptability upper limit (°C)
    acceptability_80: bool  # Within 80% acceptability limits
    acceptability_90: bool  # Within 90% acceptability limits
    outdoor_running_mean: float  # Running mean outdoor temperature (°C)


class ASHRAEAdaptiveCalculator:
    """
    Calculator for ASHRAE 55 adaptive thermal comfort model.

    The ASHRAE 55 adaptive model applies to:
    - Naturally conditioned spaces (no mechanical cooling/heating)
    - Occupants with metabolic rates between 1.0 and 1.3 met
    - Occupants free to adapt clothing (0.5 to 1.0 clo)
    - Running mean outdoor temperature between 10°C and 33.5°C

    Reference: ASHRAE Standard 55-2020
    """

    # Valid range for running mean outdoor temperature
    T_RM_MIN = 10.0  # °C
    T_RM_MAX = 33.5  # °C

    @classmethod
    def calculate_adaptive_comfort(
        cls,
        tdb: float,
        tr: float,
        t_running_mean: float,
        v: float = 0.1,
        units: str = "SI"
    ) -> ASHRAEAdaptiveResult | None:
        """
        Calculate ASHRAE 55 adaptive thermal comfort.

        Args:
            tdb: Dry bulb air temperature (°C or °F)
            tr: Mean radiant temperature (°C or °F)
            t_running_mean: Running mean outdoor temperature (°C or °F)
            v: Air speed (m/s or fps), default 0.1 m/s
            units: "SI" or "IP" (Imperial)

        Returns:
            ASHRAEAdaptiveResult with comfort temperature and acceptability limits,
            or None if pythermalcomfort not available or inputs invalid
        """
        if not PYTHERMALCOMFORT_AVAILABLE:
            return None

        # Validate running mean temperature range
        if units == "SI":
            if not (cls.T_RM_MIN <= t_running_mean <= cls.T_RM_MAX):
                return None
        else:
            # Convert to Celsius for range check
            t_rm_c = (t_running_mean - 32) * 5/9
            if not (cls.T_RM_MIN <= t_rm_c <= cls.T_RM_MAX):
                return None

        try:
            # Call pythermalcomfort adaptive_ashrae model
            result = adaptive_ashrae(
                tdb=tdb,
                tr=tr,
                t_running_mean=t_running_mean,
                v=v,
                units=units
            )

            return ASHRAEAdaptiveResult(
                tmp_cmf=result['tmp_cmf'],
                tmp_cmf_80_low=result['tmp_cmf_80_low'],
                tmp_cmf_80_up=result['tmp_cmf_80_up'],
                tmp_cmf_90_low=result['tmp_cmf_90_low'],
                tmp_cmf_90_up=result['tmp_cmf_90_up'],
                acceptability_80=result['acceptability_80'],
                acceptability_90=result['acceptability_90'],
                outdoor_running_mean=t_running_mean
            )
        except Exception:
            # Handle any calculation errors
            return None

    @classmethod
    def calculate_running_mean_outdoor_temp(
        cls,
        daily_outdoor_temps: list[float],
        alpha: float = 0.9,
        units: str = "SI"
    ) -> float | None:
        """
        Calculate running mean outdoor temperature using pythermalcomfort.

        For ASHRAE 55, the running mean is calculated as:
        T_rm(i) = (1-α) × [T_ed(i-1) + α×T_ed(i-2) + α²×T_ed(i-3) + ...]

        Where α = 0.9 for ASHRAE (different from EN 16798-1 which uses 0.8)

        Args:
            daily_outdoor_temps: List of daily mean outdoor temperatures,
                                most recent first [today, yesterday, 2 days ago, ...]
            alpha: Weighting constant (default 0.9 for ASHRAE)
            units: "SI" (Celsius) or "IP" (Fahrenheit)

        Returns:
            Running mean outdoor temperature in specified units, or None if error
        """
        if not PYTHERMALCOMFORT_AVAILABLE:
            return None

        if not daily_outdoor_temps:
            return None

        # Ensure we have at least 7 days of data (recommended)
        if len(daily_outdoor_temps) < 7:
            # If less than 7 days, use simple average
            return sum(daily_outdoor_temps) / len(daily_outdoor_temps)

        try:
            # Use pythermalcomfort's running_mean_outdoor_temperature
            # Note: This function expects temps in reverse order (oldest first)
            temps_reversed = list(reversed(daily_outdoor_temps))

            # Calculate for each day and return the most recent (last one)
            t_rm = running_mean_outdoor_temperature(
                temp_array=temps_reversed,
                alpha=alpha,
                units=units
            )

            # Return the most recent running mean (last value)
            return t_rm[-1] if isinstance(t_rm, (list, np.ndarray)) else t_rm

        except Exception:
            # Fallback to manual calculation
            return cls._calculate_running_mean_manual(daily_outdoor_temps, alpha)

    @classmethod
    def _calculate_running_mean_manual(
        cls,
        daily_outdoor_temps: list[float],
        alpha: float = 0.9
    ) -> float | None:
        """
        Manual calculation of running mean outdoor temperature.

        Fallback method when pythermalcomfort is not available or fails.

        Args:
            daily_outdoor_temps: List of daily mean outdoor temperatures,
                                most recent first
            alpha: Weighting constant (default 0.9 for ASHRAE)

        Returns:
            Running mean outdoor temperature
        """
        if not daily_outdoor_temps:
            return None

        t_rm = 0.0
        weight_sum = 0.0

        # Use up to 30 days of data
        for i, temp in enumerate(daily_outdoor_temps[:30]):
            weight = alpha ** i
            t_rm += (1 - alpha) * weight * temp
            weight_sum += (1 - alpha) * weight

        if weight_sum > 0:
            return t_rm / weight_sum
        else:
            return sum(daily_outdoor_temps[:7]) / min(7, len(daily_outdoor_temps))

    @classmethod
    def get_comfort_range(
        cls,
        t_running_mean: float,
        acceptability: int = 80,
        units: str = "SI"
    ) -> dict[str, float] | None:
        """
        Get the acceptable temperature range for a given running mean outdoor temperature.

        Args:
            t_running_mean: Running mean outdoor temperature (°C or °F)
            acceptability: 80 or 90 (percent acceptability)
            units: "SI" or "IP"

        Returns:
            Dictionary with lower, upper, and comfort temperatures
        """
        # Use comfort temperature as both tdb and tr for range calculation
        # This gives us the neutral comfort point
        if units == "SI":
            t_cmf = 0.31 * t_running_mean + 17.8
        else:
            # Convert formula for Fahrenheit
            t_rm_c = (t_running_mean - 32) * 5/9
            t_cmf_c = 0.31 * t_rm_c + 17.8
            t_cmf = t_cmf_c * 9/5 + 32

        result = cls.calculate_adaptive_comfort(
            tdb=t_cmf,
            tr=t_cmf,
            t_running_mean=t_running_mean,
            units=units
        )

        if not result:
            return None

        if acceptability == 90:
            return {
                "lower": result.tmp_cmf_90_low,
                "upper": result.tmp_cmf_90_up,
                "comfort": result.tmp_cmf,
                "acceptability": "90%",
            }
        else:  # 80%
            return {
                "lower": result.tmp_cmf_80_low,
                "upper": result.tmp_cmf_80_up,
                "comfort": result.tmp_cmf,
                "acceptability": "80%",
            }

    @classmethod
    def assess_thermal_comfort(
        cls,
        indoor_temp: float,
        mean_radiant_temp: float,
        outdoor_running_mean: float,
        air_speed: float = 0.1,
        units: str = "SI"
    ) -> dict[str, Any]:
        """
        Comprehensive thermal comfort assessment using ASHRAE adaptive model.

        Args:
            indoor_temp: Indoor air temperature (°C or °F)
            mean_radiant_temp: Mean radiant temperature (°C or °F)
            outdoor_running_mean: Running mean outdoor temperature (°C or °F)
            air_speed: Air speed (m/s or fps), default 0.1 m/s
            units: "SI" or "IP"

        Returns:
            Dictionary with comfort assessment results
        """
        result = cls.calculate_adaptive_comfort(
            tdb=indoor_temp,
            tr=mean_radiant_temp,
            t_running_mean=outdoor_running_mean,
            v=air_speed,
            units=units
        )

        if not result:
            return {
                "valid": False,
                "error": "Calculation failed or inputs out of valid range",
                "t_running_mean_min": cls.T_RM_MIN,
                "t_running_mean_max": cls.T_RM_MAX,
            }

        # Calculate operative temperature
        t_op = (indoor_temp + mean_radiant_temp) / 2

        # Determine comfort level
        if result.acceptability_90:
            comfort_level = "Comfortable (90% acceptability)"
        elif result.acceptability_80:
            comfort_level = "Acceptable (80% acceptability)"
        else:
            comfort_level = "Outside comfort range"

        # Calculate deviation from comfort temperature
        deviation = t_op - result.tmp_cmf

        return {
            "valid": True,
            "comfort_level": comfort_level,
            "acceptability_80": result.acceptability_80,
            "acceptability_90": result.acceptability_90,
            "operative_temperature": round(t_op, 1),
            "comfort_temperature": round(result.tmp_cmf, 1),
            "deviation_from_comfort": round(deviation, 1),
            "range_80_acceptability": {
                "lower": round(result.tmp_cmf_80_low, 1),
                "upper": round(result.tmp_cmf_80_up, 1),
            },
            "range_90_acceptability": {
                "lower": round(result.tmp_cmf_90_low, 1),
                "upper": round(result.tmp_cmf_90_up, 1),
            },
            "outdoor_running_mean": round(outdoor_running_mean, 1),
            "units": units,
        }

    @classmethod
    def batch_assessment(
        cls,
        indoor_temps: list[float],
        mean_radiant_temps: list[float],
        outdoor_running_mean: float,
        air_speeds: list[float] | None = None,
        units: str = "SI"
    ) -> dict[str, Any]:
        """
        Assess thermal comfort for multiple time points.

        Args:
            indoor_temps: List of indoor air temperatures
            mean_radiant_temps: List of mean radiant temperatures
            outdoor_running_mean: Running mean outdoor temperature (constant)
            air_speeds: List of air speeds (optional, defaults to 0.1 for all)
            units: "SI" or "IP"

        Returns:
            Dictionary with batch assessment results and statistics
        """
        if not indoor_temps or not mean_radiant_temps:
            return {"valid": False, "error": "Empty input lists"}

        if len(indoor_temps) != len(mean_radiant_temps):
            return {"valid": False, "error": "Input lists must have same length"}

        if air_speeds is None:
            air_speeds = [0.1] * len(indoor_temps)
        elif len(air_speeds) != len(indoor_temps):
            return {"valid": False, "error": "Air speeds list must match length"}

        results = []
        acceptable_80_count = 0
        acceptable_90_count = 0

        for tdb, tr, v in zip(indoor_temps, mean_radiant_temps, air_speeds, strict=False):
            assessment = cls.assess_thermal_comfort(
                indoor_temp=tdb,
                mean_radiant_temp=tr,
                outdoor_running_mean=outdoor_running_mean,
                air_speed=v,
                units=units
            )

            if assessment.get("valid"):
                results.append(assessment)
                if assessment["acceptability_80"]:
                    acceptable_80_count += 1
                if assessment["acceptability_90"]:
                    acceptable_90_count += 1

        total_valid = len(results)

        if total_valid == 0:
            return {"valid": False, "error": "No valid assessments"}

        return {
            "valid": True,
            "total_points": len(indoor_temps),
            "valid_points": total_valid,
            "acceptability_80_percent": round(100 * acceptable_80_count / total_valid, 1),
            "acceptability_90_percent": round(100 * acceptable_90_count / total_valid, 1),
            "outdoor_running_mean": outdoor_running_mean,
            "detailed_results": results if total_valid <= 100 else results[:100],  # Limit output
            "units": units,
        }
