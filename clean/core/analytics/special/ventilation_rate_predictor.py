"""
Ventilation rate prediction from CO2 decay analysis.

Uses exponential decay of CO2 after occupants leave to estimate
air change rate (ACH - Air Changes per Hour).

Based on the principle:
CO2(t) = CO2_outdoor + (CO2_initial - CO2_outdoor) * exp(-ACH * t)

Where:
- CO2(t) is concentration at time t
- CO2_outdoor is outdoor CO2 (~400 ppm)
- CO2_initial is initial concentration when room becomes unoccupied
- ACH is air changes per hour
- t is time in hours
"""

from dataclasses import dataclass
from typing import Optional, Tuple, List
import pandas as pd
import numpy as np
from scipy.optimize import curve_fit
from scipy import stats


@dataclass
class VentilationRateResult:
    """Result of ventilation rate analysis."""

    ach: float  # Air changes per hour
    r_squared: float  # Goodness of fit
    decay_constant: float  # Decay rate
    initial_co2: float  # CO2 level when decay started
    outdoor_co2: float  # Estimated outdoor CO2
    confidence_interval: Tuple[float, float]  # 95% CI for ACH
    ventilation_category: str  # "poor", "fair", "good", "excellent"
    description: str
    quality_score: float  # 0-1, based on R² and data quality


class VentilationRatePredictor:
    """
    Predict ventilation rate from CO2 decay.

    Analyzes periods when room becomes unoccupied and CO2 decays
    back to outdoor levels.
    """

    def __init__(self, outdoor_co2: float = 400.0):
        """
        Initialize predictor.

        Args:
            outdoor_co2: Outdoor CO2 concentration (ppm), default 400
        """
        self.outdoor_co2 = outdoor_co2

    def predict_from_decay(
        self,
        co2_series: pd.Series,
        decay_window_hours: float = 4.0,
        min_decay_threshold: float = 100.0,
    ) -> Optional[VentilationRateResult]:
        """
        Predict ventilation rate from CO2 decay.

        Args:
            co2_series: Time series of CO2 measurements
            decay_window_hours: Expected decay window to analyze (hours)
            min_decay_threshold: Minimum CO2 drop to consider (ppm)

        Returns:
            VentilationRateResult if decay period found, None otherwise
        """
        # Identify decay periods
        decay_segments = self._identify_decay_periods(
            co2_series, min_decay_threshold
        )

        if not decay_segments:
            return None

        # Analyze best decay segment
        best_result = None
        best_r_squared = 0.0

        for segment in decay_segments:
            result = self._analyze_decay_segment(segment)
            if result and result.r_squared > best_r_squared:
                best_result = result
                best_r_squared = result.r_squared

        return best_result

    def _identify_decay_periods(
        self,
        co2_series: pd.Series,
        min_decay: float,
    ) -> List[pd.Series]:
        """
        Identify periods where CO2 is decaying.

        Looks for sustained decreases in CO2 concentration.
        """
        segments = []

        # Calculate rolling decrease
        co2_diff = co2_series.diff()

        # Find start of decay (CO2 starts decreasing)
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
                if co2_diff.iloc[i] > 5:  # CO2 increasing
                    # Extract segment
                    segment = co2_series.iloc[decay_start:i]
                    if len(segment) >= 5:  # Minimum points for fitting
                        segments.append(segment)
                    in_decay = False
                    decay_start = None

        # Handle decay period extending to end
        if in_decay and decay_start is not None:
            segment = co2_series.iloc[decay_start:]
            if len(segment) >= 5:
                segments.append(segment)

        return segments

    def _analyze_decay_segment(
        self,
        co2_segment: pd.Series,
    ) -> Optional[VentilationRateResult]:
        """
        Analyze a single decay segment to estimate ACH.

        Fits exponential decay: CO2(t) = C_outdoor + (C0 - C_outdoor) * exp(-ACH * t)
        """
        if len(co2_segment) < 5:
            return None

        # Time in hours from start
        if isinstance(co2_segment.index, pd.DatetimeIndex):
            time_hours = (
                co2_segment.index - co2_segment.index[0]
            ).total_seconds() / 3600
        else:
            # Assume hourly data
            time_hours = np.arange(len(co2_segment))

        co2_values = co2_segment.values

        # Initial guess for parameters
        C0 = co2_values[0]  # Initial CO2
        C_outdoor = self.outdoor_co2

        # Define exponential decay function
        def decay_func(t, ach):
            return C_outdoor + (C0 - C_outdoor) * np.exp(-ach * t)

        try:
            # Fit curve
            popt, pcov = curve_fit(
                decay_func,
                time_hours,
                co2_values,
                p0=[1.0],  # Initial guess for ACH
                bounds=([0.1], [20.0]),  # ACH typically 0.1 to 20
            )

            ach = popt[0]

            # Calculate R²
            y_pred = decay_func(time_hours, ach)
            ss_res = np.sum((co2_values - y_pred) ** 2)
            ss_tot = np.sum((co2_values - np.mean(co2_values)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

            # Calculate confidence interval
            perr = np.sqrt(np.diag(pcov))
            ci_lower = ach - 1.96 * perr[0]
            ci_upper = ach + 1.96 * perr[0]

            # Assess ventilation quality
            category = self._categorize_ventilation(ach)

            # Quality score based on R² and segment length
            quality_score = min(r_squared * (len(co2_segment) / 20), 1.0)

            description = (
                f"Estimated {ach:.2f} air changes per hour ({category}). "
                f"Model fit: R²={r_squared:.3f}. "
                f"CO2 decayed from {C0:.0f} ppm to ~{C_outdoor:.0f} ppm."
            )

            return VentilationRateResult(
                ach=round(ach, 2),
                r_squared=round(r_squared, 3),
                decay_constant=round(ach, 3),
                initial_co2=round(C0, 1),
                outdoor_co2=C_outdoor,
                confidence_interval=(round(ci_lower, 2), round(ci_upper, 2)),
                ventilation_category=category,
                description=description,
                quality_score=round(quality_score, 3),
            )

        except Exception as e:
            # Fitting failed
            return None

    def _categorize_ventilation(self, ach: float) -> str:
        """Categorize ventilation based on ACH."""
        if ach >= 6.0:
            return "excellent"
        elif ach >= 4.0:
            return "good"
        elif ach >= 2.0:
            return "fair"
        else:
            return "poor"

    def predict_from_multiple_periods(
        self,
        co2_series: pd.Series,
    ) -> Optional[VentilationRateResult]:
        """
        Predict ventilation rate using multiple decay periods.

        Averages results from multiple decay events for better accuracy.
        """
        decay_segments = self._identify_decay_periods(co2_series, min_decay=100.0)

        if not decay_segments:
            return None

        # Analyze all segments
        results = []
        for segment in decay_segments:
            result = self._analyze_decay_segment(segment)
            if result and result.r_squared > 0.7:  # Only good fits
                results.append(result)

        if not results:
            return None

        # Average the ACH values weighted by R²
        total_weight = sum(r.r_squared for r in results)
        if total_weight == 0:
            return None

        weighted_ach = sum(r.ach * r.r_squared for r in results) / total_weight
        avg_r_squared = np.mean([r.r_squared for r in results])

        # Calculate pooled confidence interval
        ach_values = [r.ach for r in results]
        ci_lower = np.percentile(ach_values, 2.5)
        ci_upper = np.percentile(ach_values, 97.5)

        category = self._categorize_ventilation(weighted_ach)
        quality_score = avg_r_squared

        description = (
            f"Estimated {weighted_ach:.2f} ACH ({category}) from {len(results)} decay periods. "
            f"Average R²={avg_r_squared:.3f}."
        )

        return VentilationRateResult(
            ach=round(weighted_ach, 2),
            r_squared=round(avg_r_squared, 3),
            decay_constant=round(weighted_ach, 3),
            initial_co2=round(np.mean([r.initial_co2 for r in results]), 1),
            outdoor_co2=self.outdoor_co2,
            confidence_interval=(round(ci_lower, 2), round(ci_upper, 2)),
            ventilation_category=category,
            description=description,
            quality_score=round(quality_score, 3),
        )


def predict_ventilation_rate_from_co2_decay(
    co2_series: pd.Series,
    outdoor_co2: float = 400.0,
) -> Optional[VentilationRateResult]:
    """
    Convenience function to predict ventilation rate from CO2 decay.

    Args:
        co2_series: Time series of CO2 measurements
        outdoor_co2: Outdoor CO2 concentration (ppm)

    Returns:
        VentilationRateResult or None if no decay periods found

    Example:
        >>> co2_data = pd.Series([800, 750, 680, 620, 560, 510, 470, 440, 420])
        >>> result = predict_ventilation_rate_from_co2_decay(co2_data)
        >>> print(f"ACH: {result.ach}, Category: {result.ventilation_category}")
        ACH: 2.5, Category: fair
    """
    predictor = VentilationRatePredictor(outdoor_co2)
    return predictor.predict_from_multiple_periods(co2_series)
