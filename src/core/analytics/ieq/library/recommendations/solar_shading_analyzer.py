"""
Solar Shading Analyzer

Single responsibility: Analyze if a room needs solar shading based on overheating
patterns and weather correlations.
"""

from typing import Dict, Any, Optional, List, Tuple


def analyze_solar_shading_need(
    summer_compliance_rate: float,
    outdoor_temp_correlation: float,
    solar_radiation_correlation: float,
    avg_outdoor_temp_during_issues: Optional[float] = None,
    avg_radiation_during_issues: Optional[float] = None
) -> Tuple[bool, str, List[str]]:
    """
    Determine if solar shading is needed based on overheating patterns.
    
    Args:
        summer_compliance_rate: Compliance rate during summer (0-100)
        outdoor_temp_correlation: Correlation between outdoor temp and overheating
        solar_radiation_correlation: Correlation between solar radiation and overheating
        avg_outdoor_temp_during_issues: Average outdoor temp when overheating occurs
        avg_radiation_during_issues: Average solar radiation when overheating occurs
    
    Returns:
        Tuple of (needs_shading, priority_level, rationale_list)
        priority_level: 'critical', 'high', 'medium', 'low', or 'none'
    
    Logic:
        - Strong positive correlation with temp/radiation indicates solar gain
        - Poor compliance + moderate correlation suggests shading would help
    """
    rationale = []
    
    # Strong evidence: positive correlations indicate solar gain is the driver
    strong_temp_correlation = outdoor_temp_correlation > 0.5
    strong_radiation_correlation = solar_radiation_correlation > 0.5
    
    # Moderate evidence
    moderate_temp_correlation = outdoor_temp_correlation > 0.3
    moderate_radiation_correlation = solar_radiation_correlation > 0.3
    
    # Poor compliance threshold
    poor_compliance = summer_compliance_rate < 70
    very_poor_compliance = summer_compliance_rate < 50
    
    # Decision logic
    needs_shading = False
    priority = 'none'
    
    # Critical need: Very poor compliance + strong correlations
    if very_poor_compliance and (strong_temp_correlation or strong_radiation_correlation):
        needs_shading = True
        priority = 'critical'
        
        if strong_radiation_correlation:
            rationale.append(
                f"Very strong solar radiation correlation ({solar_radiation_correlation:+.2f}) "
                f"with severe overheating ({summer_compliance_rate:.1f}% compliance). "
                f"Direct solar gain through windows is primary driver."
            )
        if strong_temp_correlation:
            rationale.append(
                f"Strong outdoor temperature correlation ({outdoor_temp_correlation:+.2f}) "
                f"indicates heat gain from environment worsens overheating."
            )
    
    # High need: Poor compliance + strong correlation
    elif poor_compliance and (strong_temp_correlation or strong_radiation_correlation):
        needs_shading = True
        priority = 'high'
        
        rationale.append(
            f"Strong weather correlation combined with poor compliance ({summer_compliance_rate:.1f}%) "
            f"indicates solar heat gain is a major factor."
        )
        
        if strong_radiation_correlation:
            rationale.append(
                f"Solar radiation correlation of {solar_radiation_correlation:+.2f} confirms "
                f"direct solar gain through glazing."
            )
    
    # Medium need: Moderate correlation with poor compliance
    elif poor_compliance and (moderate_temp_correlation or moderate_radiation_correlation):
        needs_shading = True
        priority = 'medium'
        
        rationale.append(
            f"Moderate weather correlation with poor compliance ({summer_compliance_rate:.1f}%) "
            f"suggests solar gain contributes to overheating issues."
        )
    
    # Low need: Good compliance but strong correlation (preventive)
    elif summer_compliance_rate >= 70 and (strong_temp_correlation or strong_radiation_correlation):
        needs_shading = True
        priority = 'low'
        
        rationale.append(
            f"While current compliance is acceptable ({summer_compliance_rate:.1f}%), "
            f"strong weather correlations suggest vulnerability to warmer conditions."
        )
    
    # Add context about weather conditions during issues
    if needs_shading and avg_outdoor_temp_during_issues:
        rationale.append(
            f"During overheating events, outdoor temperature averages {avg_outdoor_temp_during_issues:.1f}°C"
            + (f" with solar radiation of {avg_radiation_during_issues:.0f} W/m²" 
               if avg_radiation_during_issues else "")
            + "."
        )
    
    return needs_shading, priority, rationale


def generate_solar_shading_recommendation(
    needs_shading: bool,
    priority: str,
    rationale: List[str],
    compliance_rate: float
) -> Optional[Dict[str, Any]]:
    """
    Generate structured solar shading recommendation.
    
    Args:
        needs_shading: Whether shading is needed
        priority: Priority level
        rationale: List of rationale strings
        compliance_rate: Current summer compliance rate
    
    Returns:
        Recommendation dictionary or None if not needed
    """
    if not needs_shading or priority == 'none':
        return None
    
    # Calculate potential impact
    if priority == 'critical':
        impact = "Could improve summer compliance by 30-50 percentage points"
    elif priority == 'high':
        impact = "Could improve summer compliance by 20-40 percentage points"
    elif priority == 'medium':
        impact = "Could improve summer compliance by 10-25 percentage points"
    else:  # low
        impact = "Preventive measure to maintain comfort in future warmer conditions"
    
    # Determine cost based on solution
    if priority in ['critical', 'high']:
        cost = "Medium to High (€200-400 per window for external automated blinds)"
        solution = (
            "Install external solar shading (motorized external blinds, awnings, or brise-soleil). "
            "External shading is 3-4x more effective than internal blinds as it blocks heat "
            "before it enters the building. Motorization enables automatic control based on "
            "solar radiation levels."
        )
    else:
        cost = "Low to Medium (€100-200 per window for manual external blinds)"
        solution = (
            "Consider external solar shading (external blinds or awnings). "
            "Manual blinds are more cost-effective for lower priority issues."
        )
    
    return {
        'type': 'solar_shading',
        'priority': priority,
        'title': 'Install External Solar Shading',
        'description': (
            f"Room experiences significant summer overheating ({compliance_rate:.1f}% compliant). "
            f"Analysis shows solar heat gain is a major contributing factor. {solution}"
        ),
        'rationale': rationale,
        'estimated_impact': impact,
        'implementation_cost': cost,
        'evidence': {
            'summer_compliance': compliance_rate
        }
    }


def get_shading_type_recommendation(
    window_orientation: Optional[str] = None,
    building_type: Optional[str] = None
) -> str:
    """
    Recommend specific shading type based on building characteristics.
    
    Args:
        window_orientation: 'south', 'east', 'west', 'north'
        building_type: 'office', 'residential', 'commercial'
    
    Returns:
        Recommendation text for shading type
    """
    recommendations = []
    
    if window_orientation:
        orientation = window_orientation.lower()
        
        if orientation == 'south':
            recommendations.append(
                "South-facing windows: Horizontal overhangs or brise-soleil work well "
                "as they block high summer sun while allowing lower winter sun"
            )
        elif orientation in ['east', 'west']:
            recommendations.append(
                f"{orientation.capitalize()}-facing windows: Vertical fins or adjustable louvers "
                f"recommended to block low-angle sun"
            )
        elif orientation == 'north':
            recommendations.append(
                "North-facing windows: Minimal shading needed unless excessive glazing"
            )
    
    if building_type:
        b_type = building_type.lower()
        
        if b_type == 'office':
            recommendations.append(
                "Office buildings: Automated blinds with light sensors maintain daylight "
                "while preventing glare and overheating"
            )
        elif b_type == 'residential':
            recommendations.append(
                "Residential: Manual external roller shutters provide good balance of "
                "cost, effectiveness, and security"
            )
    
    return " ".join(recommendations) if recommendations else "Consult with building envelope specialist for optimal solution"
