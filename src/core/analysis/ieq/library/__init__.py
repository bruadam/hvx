"""
IEQ Analysis Library

Pure analytical computation modules organized by concern.
Each module has a single, focused responsibility.

Architecture:
    - evaluators/: Rule evaluation logic (bidirectional, unidirectional, complex)
    - metrics/: Statistical and quality calculations
    - correlations/: Weather and environmental correlation analysis  
    - recommendations/: Domain-specific recommendation generators
    - filters/: Time-based filtering logic

These modules contain ZERO UI code - only pure computational logic.
They are orchestrated by engines (RuleEngine, AnalysisEngine) and services.
"""

# Evaluators
from .evaluators import (
    evaluate_bidirectional,
    evaluate_unidirectional_ascending,
    evaluate_unidirectional_descending,
    parse_bidirectional_config,
    parse_unidirectional_config,
    determine_direction,
)

# Metrics
from .metrics import (
    calculate_compliance_rate,
    calculate_compliance_metrics,
    calculate_basic_statistics,
    calculate_extended_statistics,
    calculate_quality_score,
    calculate_completeness,
    identify_violations,
)

# Correlations
from .correlations import (
    calculate_correlation,
    calculate_weather_correlations,
    calculate_non_compliance_weather_stats,
    identify_weather_driven_issues,
)

# Recommendations
from .recommendations import (
    analyze_solar_shading_need,
    generate_solar_shading_recommendation,
)

__all__ = [
    # Evaluators
    'evaluate_bidirectional',
    'evaluate_unidirectional_ascending',
    'evaluate_unidirectional_descending',
    'parse_bidirectional_config',
    'parse_unidirectional_config',
    'determine_direction',
    
    # Metrics
    'calculate_compliance_rate',
    'calculate_compliance_metrics',
    'calculate_basic_statistics',
    'calculate_extended_statistics',
    'calculate_quality_score',
    'calculate_completeness',
    'identify_violations',
    
    # Correlations
    'calculate_correlation',
    'calculate_weather_correlations',
    'calculate_non_compliance_weather_stats',
    'identify_weather_driven_issues',
    
    # Recommendations
    'analyze_solar_shading_need',
    'generate_solar_shading_recommendation',
]
