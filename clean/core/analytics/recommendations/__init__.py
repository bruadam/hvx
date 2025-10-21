"""
Smart recommendations engine.

Generates evidence-based recommendations using:
- Sensitivity analysis
- Climate correlations
- Compliance patterns
- Standard violations
"""

from .recommendation_engine import (
    RecommendationEngine,
    SmartRecommendation,
    generate_recommendations_for_room,
)
from .solar_shading_analyzer import (
    SolarShadingAnalyzer,
    analyze_solar_shading_need,
)
from .insulation_analyzer import (
    InsulationAnalyzer,
    analyze_insulation_need,
)
from .ventilation_optimizer import (
    VentilationOptimizer,
    analyze_ventilation_needs,
)

__all__ = [
    "RecommendationEngine",
    "SmartRecommendation",
    "generate_recommendations_for_room",
    "SolarShadingAnalyzer",
    "analyze_solar_shading_need",
    "InsulationAnalyzer",
    "analyze_insulation_need",
    "VentilationOptimizer",
    "analyze_ventilation_needs",
]
