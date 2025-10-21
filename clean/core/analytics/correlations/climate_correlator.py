"""
Climate correlator for IEQ analysis.

Calculates correlations between indoor parameters and outdoor climate conditions
to identify weather-driven issues.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Literal
import pandas as pd
import numpy as np
from scipy import stats


@dataclass
class CorrelationResult:
    """Result of a correlation analysis."""

    parameter: str
    correlation: float
    p_value: float
    strength: str  # "negligible", "weak", "moderate", "strong", "very_strong"
    direction: str  # "positive", "negative"
    interpretation: str
    mean_during_violations: Optional[float] = None
    mean_during_compliance: Optional[float] = None
    effect_size: Optional[float] = None


class ClimateCorrelator:
    """
    Correlate indoor parameters with outdoor climate.

    Helps identify:
    - Solar heat gain issues (temp correlates with radiation)
    - Poor insulation (temp correlates negatively with outdoor temp)
    - Natural ventilation issues (CO2 correlates negatively with outdoor temp)
    """

    def __init__(self):
        """Initialize climate correlator."""
        pass

    def correlate_with_climate(
        self,
        indoor_data: pd.Series,
        climate_df: pd.DataFrame,
        climate_parameters: Optional[List[str]] = None,
        method: Literal["pearson", "spearman"] = "pearson",
    ) -> Dict[str, CorrelationResult]:
        """
        Correlate indoor parameter with multiple climate parameters.

        Args:
            indoor_data: Indoor parameter time series
            climate_df: DataFrame with climate data (outdoor_temp, radiation, etc.)
            climate_parameters: Climate parameters to correlate with (None = all)
            method: Correlation method

        Returns:
            Dictionary mapping climate parameter to CorrelationResult
        """
        if climate_parameters is None:
            climate_parameters = climate_df.select_dtypes(
                include=[np.number]
            ).columns.tolist()

        results = {}

        for param in climate_parameters:
            if param not in climate_df.columns:
                continue

            result = calculate_correlation(
                indoor_data, climate_df[param], param, method
            )
            results[param] = result

        return results

    def correlate_violations_with_climate(
        self,
        violation_mask: pd.Series,
        climate_df: pd.DataFrame,
        climate_parameters: Optional[List[str]] = None,
    ) -> Dict[str, CorrelationResult]:
        """
        Correlate violations (boolean) with climate parameters (float).

        Uses point-biserial correlation to identify climate conditions
        during violations vs compliance.

        Args:
            violation_mask: Boolean series (True = violation, False = compliant)
            climate_df: Climate data
            climate_parameters: Parameters to analyze

        Returns:
            Dictionary of climate parameter to correlation results
        """
        if climate_parameters is None:
            climate_parameters = climate_df.select_dtypes(
                include=[np.number]
            ).columns.tolist()

        results = {}

        for param in climate_parameters:
            if param not in climate_df.columns:
                continue

            # Align data
            combined = pd.DataFrame(
                {"violations": violation_mask, "climate": climate_df[param]}
            ).dropna()

            if len(combined) < 3:
                continue

            # Convert boolean to numeric
            violations_numeric = combined["violations"].astype(int)
            climate_values = combined["climate"]

            # Point-biserial correlation
            try:
                correlation, p_value = stats.pointbiserialr(
                    violations_numeric, climate_values
                )
            except Exception:
                continue

            # Calculate means for each group
            mean_violations = float(
                combined[combined["violations"]]["climate"].mean()
            )
            mean_compliance = float(
                combined[~combined["violations"]]["climate"].mean()
            )

            # Effect size (Cohen's d)
            std_violations = combined[combined["violations"]]["climate"].std()
            std_compliance = combined[~combined["violations"]]["climate"].std()

            n_violations = combined["violations"].sum()
            n_compliance = (~combined["violations"]).sum()

            if n_violations > 0 and n_compliance > 0:
                pooled_std = np.sqrt(
                    (
                        (n_violations - 1) * std_violations**2
                        + (n_compliance - 1) * std_compliance**2
                    )
                    / (n_violations + n_compliance - 2)
                )
                effect_size = (
                    (mean_violations - mean_compliance) / pooled_std
                    if pooled_std > 0
                    else 0.0
                )
            else:
                effect_size = 0.0

            # Interpret
            strength = _assess_correlation_strength(abs(correlation))
            direction = "positive" if correlation > 0 else "negative"
            interpretation = _interpret_climate_correlation(
                param, correlation, p_value, mean_violations, mean_compliance
            )

            results[param] = CorrelationResult(
                parameter=param,
                correlation=round(correlation, 3),
                p_value=p_value,
                strength=strength,
                direction=direction,
                interpretation=interpretation,
                mean_during_violations=round(mean_violations, 2),
                mean_during_compliance=round(mean_compliance, 2),
                effect_size=round(effect_size, 3),
            )

        return results

    def identify_climate_drivers(
        self,
        correlations: Dict[str, CorrelationResult],
        threshold: float = 0.5,
    ) -> List[CorrelationResult]:
        """
        Identify significant climate drivers from correlations.

        Args:
            correlations: Dictionary of correlation results
            threshold: Minimum absolute correlation to consider significant

        Returns:
            List of significant correlations, sorted by strength
        """
        significant = [
            result
            for result in correlations.values()
            if abs(result.correlation) >= threshold
        ]

        # Sort by absolute correlation
        significant.sort(key=lambda r: abs(r.correlation), reverse=True)

        return significant


def calculate_correlation(
    indoor_data: pd.Series,
    climate_data: pd.Series,
    parameter_name: str,
    method: Literal["pearson", "spearman"] = "pearson",
) -> CorrelationResult:
    """
    Calculate correlation between indoor and climate parameter.

    Args:
        indoor_data: Indoor parameter time series
        climate_data: Climate parameter time series
        parameter_name: Name of climate parameter
        method: Correlation method

    Returns:
        CorrelationResult
    """
    # Align and drop NaN
    combined = pd.DataFrame({"indoor": indoor_data, "climate": climate_data}).dropna()

    if len(combined) < 3:
        return CorrelationResult(
            parameter=parameter_name,
            correlation=0.0,
            p_value=1.0,
            strength="negligible",
            direction="positive",
            interpretation="Insufficient data for correlation",
        )

    # Calculate correlation
    if method == "pearson":
        correlation, p_value = stats.pearsonr(combined["indoor"], combined["climate"])
    else:
        correlation, p_value = stats.spearmanr(combined["indoor"], combined["climate"])

    # Assess strength and direction
    strength = _assess_correlation_strength(abs(correlation))
    direction = "positive" if correlation > 0 else "negative"
    interpretation = _interpret_climate_correlation(
        parameter_name, correlation, p_value
    )

    return CorrelationResult(
        parameter=parameter_name,
        correlation=round(correlation, 3),
        p_value=p_value,
        strength=strength,
        direction=direction,
        interpretation=interpretation,
    )


def calculate_multiple_correlations(
    indoor_data: pd.Series,
    climate_df: pd.DataFrame,
    climate_parameters: Optional[List[str]] = None,
) -> Dict[str, CorrelationResult]:
    """
    Calculate correlations with multiple climate parameters.

    Args:
        indoor_data: Indoor parameter time series
        climate_df: Climate data
        climate_parameters: Parameters to correlate (None = all numeric)

    Returns:
        Dictionary of parameter to CorrelationResult
    """
    correlator = ClimateCorrelator()
    return correlator.correlate_with_climate(indoor_data, climate_df, climate_parameters)


def _assess_correlation_strength(abs_correlation: float) -> str:
    """Assess correlation strength."""
    if abs_correlation >= 0.8:
        return "very_strong"
    elif abs_correlation >= 0.6:
        return "strong"
    elif abs_correlation >= 0.4:
        return "moderate"
    elif abs_correlation >= 0.2:
        return "weak"
    else:
        return "negligible"


def _interpret_climate_correlation(
    parameter: str,
    correlation: float,
    p_value: float,
    mean_violations: Optional[float] = None,
    mean_compliance: Optional[float] = None,
) -> str:
    """Generate human-readable interpretation."""
    param_lower = parameter.lower()
    is_significant = p_value < 0.05
    abs_corr = abs(correlation)

    if abs_corr < 0.2:
        return f"Negligible correlation with {parameter}"

    # Build interpretation
    strength_desc = _assess_correlation_strength(abs_corr)
    direction = "increases" if correlation > 0 else "decreases"

    interpretation = f"{strength_desc.replace('_', ' ').capitalize()} "

    # Parameter-specific interpretation
    if "temp" in param_lower:
        if correlation > 0:
            interpretation += f"positive correlation with outdoor temperature (r={correlation:.2f}). "
            interpretation += "Indoor issues worsen when outdoor temperature increases. "
        else:
            interpretation += f"negative correlation with outdoor temperature (r={correlation:.2f}). "
            interpretation += "Indoor issues worsen when outdoor temperature decreases (poor insulation likely). "

    elif "radiation" in param_lower or "solar" in param_lower:
        if correlation > 0:
            interpretation += f"positive correlation with solar radiation (r={correlation:.2f}). "
            interpretation += "Solar heat gain is a significant factor (consider shading). "
        else:
            interpretation += f"negative correlation with solar radiation (r={correlation:.2f}). "

    else:
        interpretation += f"{direction} with {parameter} (r={correlation:.2f}). "

    # Add statistical significance
    if is_significant:
        interpretation += "Statistically significant (p<0.05)."
    else:
        interpretation += "Not statistically significant (p≥0.05)."

    # Add mean comparison if available
    if mean_violations is not None and mean_compliance is not None:
        diff = mean_violations - mean_compliance
        interpretation += (
            f" During violations: {mean_violations:.1f}, "
            f"during compliance: {mean_compliance:.1f} (Δ={diff:+.1f})."
        )

    return interpretation
