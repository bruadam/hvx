"""
Climate correlation analysis module.

Provides tools for correlating indoor environmental quality parameters
with outdoor climate conditions to identify root causes of non-compliance.
"""

from .climate_correlator import (
    ClimateCorrelator,
    CorrelationResult,
    calculate_correlation,
    calculate_multiple_correlations,
)
from .weather_analyzer import (
    WeatherAnalyzer,
    WeatherStats,
    analyze_weather_during_violations,
)

__all__ = [
    "ClimateCorrelator",
    "CorrelationResult",
    "calculate_correlation",
    "calculate_multiple_correlations",
    "WeatherAnalyzer",
    "WeatherStats",
    "analyze_weather_during_violations",
]
