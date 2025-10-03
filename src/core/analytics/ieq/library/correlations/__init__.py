"""
Correlations Module - Weather and environmental correlation analysis.

Single responsibility: Calculate and interpret correlations between indoor and outdoor conditions.
"""

from .weather_correlator import (
    calculate_correlation,
    calculate_weather_correlations,
    calculate_non_compliance_weather_stats,
    identify_weather_driven_issues,
    calculate_seasonal_correlations,
    calculate_boolean_float_correlation,
    calculate_multiple_boolean_float_correlations
)

__all__ = [
    'calculate_correlation',
    'calculate_weather_correlations',
    'calculate_non_compliance_weather_stats',
    'identify_weather_driven_issues',
    'calculate_seasonal_correlations',
    'calculate_boolean_float_correlation',
    'calculate_multiple_boolean_float_correlations',
]
