"""
Recommendations Package

Provides pure domain logic for generating building improvement recommendations.

Modules:
- solar_shading_analyzer: Solar shading need analysis
- insulation_analyzer: Building insulation analysis
- ventilation_analyzer: Ventilation system analysis
- hvac_analyzer: HVAC system performance analysis
"""

from .solar_shading_analyzer import (
    analyze_solar_shading_need,
    generate_solar_shading_recommendation,
    get_shading_type_recommendation
)

from .insulation_analyzer import (
    InsulationRecommendation,
    analyze_insulation_need,
    identify_affected_areas,
    generate_insulation_description,
    estimate_improvement
)

from .ventilation_analyzer import (
    VentilationRecommendation,
    analyze_ventilation_need,
    recommend_ventilation_type,
    calculate_recommended_ach,
    generate_ventilation_description,
    estimate_ventilation_improvement
)

from .hvac_analyzer import (
    HVACRecommendation,
    analyze_hvac_performance,
    assess_energy_impact,
    generate_hvac_description,
    estimate_hvac_improvement,
    analyze_maintenance_needs
)

__all__ = [
    # Solar shading
    'analyze_solar_shading_need',
    'generate_solar_shading_recommendation',
    'get_shading_type_recommendation',
    
    # Insulation
    'InsulationRecommendation',
    'analyze_insulation_need',
    'identify_affected_areas',
    'generate_insulation_description',
    'estimate_improvement',
    
    # Ventilation
    'VentilationRecommendation',
    'analyze_ventilation_need',
    'recommend_ventilation_type',
    'calculate_recommended_ach',
    'generate_ventilation_description',
    'estimate_ventilation_improvement',
    
    # HVAC
    'HVACRecommendation',
    'analyze_hvac_performance',
    'assess_energy_impact',
    'generate_hvac_description',
    'estimate_hvac_improvement',
    'analyze_maintenance_needs'
]
