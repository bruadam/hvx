"""
Recommendations Module - Domain-specific recommendation generators.

Each analyzer focuses on one type of building improvement recommendation.
"""

from .solar_shading_analyzer import (
    analyze_solar_shading_need,
    generate_solar_shading_recommendation,
    get_shading_type_recommendation
)

__all__ = [
    'analyze_solar_shading_need',
    'generate_solar_shading_recommendation',
    'get_shading_type_recommendation',
]
