"""
Ventilation rate estimation from CO2 decay analysis.

Estimates air change rate (ACH) by analyzing exponential CO2 decay
when room becomes unoccupied.

Based on: CO2(t) = CO2_outdoor + (CO2_initial - CO2_outdoor) * exp(-ACH * t)
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit


@dataclass
class VentilationRateResult:
    """Result of ventilation rate analysis."""
    ach: float  # Air changes per hour
    ventilation_l_s: Optional[float]  # Ventilation rate in L/s
    r_squared: float  # Goodness of fit
    initial_co2: float  # CO2 when decay started (ppm)
    final_co2: float  # CO2 at end of decay (ppm)
    outdoor_co2: float  # Estimated outdoor CO2 (ppm)
    confidence_interval: Tuple[float, float]  # 95% CI for ACH
    quality_score: float  # 0-1, based on R² and data quality
    category: str  # "poor", "fair", "good", "excellent"
    description: str


class VentilationCalculator:
    """
    Estimate ventilation rate from CO2 decay.

    Analyzes periods when room becomes unoccupied and CO2 decays
    back to outdoor levels to estimate air change rate.
    """

    # Ventilation quality categories (based on ACH)
    ACH_CATEGORIES = {
        "excellent": 6.0,
        "good": 4.0,
        "fair": 2.0,
        "poor": 0.0,
    }

    def __init__(self, outdoor_co2: float = 400.0):
        """
        Initialize calculator.

        Args:
            outdoor_co2: Outdoor CO2 concentration (ppm), default 400
        """
        self.outdoor_co2 = outdoor_co2

    def estimate_from_co2_decay(
        self,
        co2_series: pd.Series,
        volume_m3: Optional[float] = None,
        min_decay_threshold: float = 100.0
    ) -> Optional[VentilationRateResult]:
        """
        Estimate ventilation rate from CO2 decay.

        Args:
            co2_series: Time series of CO2 measurements
            volume_m3: Room volume for L/s calculation
            min_decay_threshold: Minimum CO2 drop to consider (ppm)

        Returns:
            VentilationRateResult if decay found, None otherwise
        """
        # Identify decay periods
        decay_segments = self._identify_decay_periods(co2_series, min_decay_threshold)

        if not decay_segments:
            return None

        # Analyze all segments and average
        results = []
        for segment in decay_segments:
            result = self._analyze_decay_segment(segment, volume_m3)
            if result and result.r_squared > 0.7:  # Only good fits
                results.append(result)

        if not results:
            return None

        # Weight by R²
        total_weight = sum(r.r_squared for r in results)
        if total_weight == 0:
            return None

        weighted_ach = sum(r.ach * r.r_squared for r in results) / total_weight
        avg_r_squared = sum(r.r_squared for r in results) / len(results)

        # Calculate pooled confidence interval
        ach_values = [r.ach for r in results]
        ci_lower = float(np.percentile(ach_values, 2.5))
        ci_upper = float(np.percentile(ach_values, 97.5))

        # Ventilation in L/s
        ventilation_l_s = None
        if volume_m3:
            ventilation_l_s = (weighted_ach * volume_m3 * 1000) / 3600

        category = self._categorize_ach(weighted_ach)
        quality_score = avg_r_squared

        description = (
            f"Estimated {weighted_ach:.2f} ACH ({category}) from {len(results)} decay periods. "
            f"Average R²={avg_r_squared:.3f}."
        )

        return VentilationRateResult(
            ach=round(weighted_ach, 2),
            ventilation_l_s=round(ventilation_l_s, 1) if ventilation_l_s else None,
            r_squared=round(avg_r_squared, 3),
            initial_co2=round(float(np.mean([r.initial_co2 for r in results])), 1),
            final_co2=self.outdoor_co2,
            outdoor_co2=self.outdoor_co2,
            confidence_interval=(round(ci_lower, 2), round(ci_upper, 2)),
            quality_score=round(quality_score, 3),
            category=category,
            description=description,
        )

    def _identify_decay_periods(
        self,
        co2_series: pd.Series,
        min_decay: float
    ) -> List[pd.Series]:
        """Identify periods where CO2 is decaying."""
        segments = []
        co2_diff = co2_series.diff()

        in_decay = False
        decay_start = None

        for i in range(1, len(co2_series)):
            if not in_decay:
                # Look for start of decay (2 consecutive decreases)
                if i >= 2 and co2_diff.iloc[i] < 0 and co2_diff.iloc[i - 1] < 0:
                    if co2_series.iloc[i - 2] > co2_series.iloc[i] + min_decay:
                        in_decay = True
                        decay_start = i - 2
            else:
                # Look for end of decay (increase or plateau)
                if co2_diff.iloc[i] > 5:
                    segment = co2_series.iloc[decay_start:i]
                    if len(segment) >= 5:
                        segments.append(segment)
                    in_decay = False
                    decay_start = None

        # Handle decay extending to end
        if in_decay and decay_start is not None:
            segment = co2_series.iloc[decay_start:]
            if len(segment) >= 5:
                segments.append(segment)

        return segments

    def _analyze_decay_segment(
        self,
        co2_segment: pd.Series,
        volume_m3: Optional[float]
    ) -> Optional[VentilationRateResult]:
        """Analyze a single decay segment to estimate ACH."""
        if len(co2_segment) < 5:
            return None

        # Time in hours from start
        if isinstance(co2_segment.index, pd.DatetimeIndex):
            time_hours = (co2_segment.index - co2_segment.index[0]).total_seconds() / 3600
            time_hours = np.array(time_hours)
        else:
            time_hours = np.arange(len(co2_segment), dtype=float)

        co2_values = co2_segment.values.astype(float)

        # Initial values
        C0 = float(co2_values[0])
        C_outdoor = self.outdoor_co2

        # Exponential decay function
        def decay_func(t, ach):
            return C_outdoor + (C0 - C_outdoor) * np.exp(-ach * t)

        try:
            # Fit curve
            popt, pcov = curve_fit(
                decay_func,
                time_hours,
                co2_values,
                p0=[1.0],
                bounds=([0.1], [20.0]),
            )

            ach = float(popt[0])

            # Calculate R²
            y_pred = decay_func(time_hours, ach)
            ss_res = np.sum((co2_values - y_pred) ** 2)
            ss_tot = np.sum((co2_values - np.mean(co2_values)) ** 2)
            r_squared = float(1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0)

            # Confidence interval
            perr = np.sqrt(np.diag(pcov))
            ci_lower = ach - 1.96 * perr[0]
            ci_upper = ach + 1.96 * perr[0]

            # Ventilation in L/s
            ventilation_l_s = None
            if volume_m3:
                ventilation_l_s = (ach * volume_m3 * 1000) / 3600

            category = self._categorize_ach(ach)
            quality_score = min(r_squared * (len(co2_segment) / 20), 1.0)

            description = (
                f"Estimated {ach:.2f} ACH ({category}). "
                f"R²={r_squared:.3f}. "
                f"CO2 decayed from {C0:.0f} to ~{C_outdoor:.0f} ppm."
            )

            return VentilationRateResult(
                ach=round(ach, 2),
                ventilation_l_s=round(ventilation_l_s, 1) if ventilation_l_s else None,
                r_squared=round(r_squared, 3),
                initial_co2=round(C0, 1),
                final_co2=C_outdoor,
                outdoor_co2=C_outdoor,
                confidence_interval=(round(float(ci_lower), 2), round(float(ci_upper), 2)),
                quality_score=round(quality_score, 3),
                category=category,
                description=description,
            )

        except Exception:
            return None

    def _categorize_ach(self, ach: float) -> str:
        """Categorize ventilation based on ACH."""
        if ach >= self.ACH_CATEGORIES["excellent"]:
            return "excellent"
        elif ach >= self.ACH_CATEGORIES["good"]:
            return "good"
        elif ach >= self.ACH_CATEGORIES["fair"]:
            return "fair"
        else:
            return "poor"

    def calculate_required_ach(
        self,
        volume_m3: float,
        required_ventilation_l_s: float
    ) -> float:
        """
        Calculate required ACH from ventilation rate.

        Args:
            volume_m3: Room volume (m³)
            required_ventilation_l_s: Required ventilation (L/s)

        Returns:
            Required air change rate (ACH)
        """
        if volume_m3 <= 0:
            return 0.0

        # Convert L/s to m³/h: L/s * 3.6 = m³/h
        ventilation_m3_h = required_ventilation_l_s * 3.6

        # ACH = m³/h / volume
        return ventilation_m3_h / volume_m3
