"""
Weather analyzer for IEQ analysis.

Analyzes weather conditions during violations to provide context
for recommendations.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class WeatherStats:
    """Weather statistics during a specific period."""

    parameter: str
    mean: float
    min: float
    max: float
    std: float
    median: float
    count: int


class WeatherAnalyzer:
    """
    Analyze weather conditions during compliance violations.

    Provides context for understanding when and why violations occur.
    """

    def analyze_during_violations(
        self,
        violation_mask: pd.Series,
        weather_df: pd.DataFrame,
        weather_parameters: list | None = None,
    ) -> dict[str, WeatherStats]:
        """
        Calculate weather statistics during violation periods.

        Args:
            violation_mask: Boolean series (True = violation)
            weather_df: Weather data
            weather_parameters: Parameters to analyze (None = all numeric)

        Returns:
            Dictionary of weather parameter to WeatherStats
        """
        if weather_parameters is None:
            weather_parameters = weather_df.select_dtypes(
                include=[np.number]
            ).columns.tolist()

        # Align weather data with violation mask
        aligned_weather = weather_df.reindex(violation_mask.index)

        # Filter to violation periods only
        violation_weather = aligned_weather[violation_mask]

        stats = {}

        for param in weather_parameters:
            if param not in violation_weather.columns:
                continue

            param_data = violation_weather[param].dropna()

            if len(param_data) == 0:
                continue

            stats[param] = WeatherStats(
                parameter=param,
                mean=round(float(param_data.mean()), 2),
                min=round(float(param_data.min()), 2),
                max=round(float(param_data.max()), 2),
                std=round(float(param_data.std()), 2),
                median=round(float(param_data.median()), 2),
                count=len(param_data),
            )

        return stats

    def compare_violation_vs_compliance(
        self,
        violation_mask: pd.Series,
        weather_df: pd.DataFrame,
        weather_parameter: str,
    ) -> dict[str, WeatherStats]:
        """
        Compare weather conditions during violations vs compliance.

        Args:
            violation_mask: Boolean series
            weather_df: Weather data
            weather_parameter: Parameter to compare

        Returns:
            Dictionary with 'violations' and 'compliance' keys
        """
        if weather_parameter not in weather_df.columns:
            return {}

        aligned_weather = weather_df.reindex(violation_mask.index)

        # Violation period
        violation_data = aligned_weather[violation_mask][weather_parameter].dropna()
        # Compliance period
        compliance_data = aligned_weather[~violation_mask][weather_parameter].dropna()

        results = {}

        if len(violation_data) > 0:
            results["violations"] = WeatherStats(
                parameter=weather_parameter,
                mean=round(float(violation_data.mean()), 2),
                min=round(float(violation_data.min()), 2),
                max=round(float(violation_data.max()), 2),
                std=round(float(violation_data.std()), 2),
                median=round(float(violation_data.median()), 2),
                count=len(violation_data),
            )

        if len(compliance_data) > 0:
            results["compliance"] = WeatherStats(
                parameter=weather_parameter,
                mean=round(float(compliance_data.mean()), 2),
                min=round(float(compliance_data.min()), 2),
                max=round(float(compliance_data.max()), 2),
                std=round(float(compliance_data.std()), 2),
                median=round(float(compliance_data.median()), 2),
                count=len(compliance_data),
            )

        return results


def analyze_weather_during_violations(
    violation_mask: pd.Series,
    weather_df: pd.DataFrame,
    weather_parameters: list | None = None,
) -> dict[str, WeatherStats]:
    """
    Convenience function to analyze weather during violations.

    Args:
        violation_mask: Boolean series
        weather_df: Weather data
        weather_parameters: Parameters to analyze

    Returns:
        Dictionary of weather statistics
    """
    analyzer = WeatherAnalyzer()
    return analyzer.analyze_during_violations(
        violation_mask, weather_df, weather_parameters
    )
