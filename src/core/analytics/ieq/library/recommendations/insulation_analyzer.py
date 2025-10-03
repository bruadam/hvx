"""
Insulation Analysis Module

Pure domain logic for analyzing building insulation needs based on 
temperature patterns and heat loss/gain indicators.

Design Principles:
- Single responsibility: Only insulation need analysis
- Pure functions: No side effects, no UI dependencies
- Type-safe: Full type hints and validation
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class InsulationRecommendation:
    """Recommendation for insulation improvements."""
    
    needed: bool
    priority: str  # "high", "medium", "low"
    affected_areas: List[str]  # e.g., ["walls", "roof", "windows"]
    issue_type: str  # "heat_loss", "heat_gain", "both"
    severity_score: float  # 0.0 to 1.0
    description: str
    estimated_improvement: Optional[float] = None  # Expected % improvement


def analyze_insulation_need(
    heating_season_data: Dict[str, Any],
    cooling_season_data: Dict[str, Any],
    compliance_issues: Dict[str, Any],
    weather_correlation: Optional[Dict[str, Any]] = None
) -> InsulationRecommendation:
    """
    Analyze if insulation improvements are needed based on temperature patterns.
    
    Args:
        heating_season_data: Statistics for heating season
            - avg_indoor_temp: Average indoor temperature
            - temp_drop_rate: Rate of temperature drop
            - heating_load_hours: Hours with high heating demand
        cooling_season_data: Statistics for cooling season
            - avg_indoor_temp: Average indoor temperature
            - temp_rise_rate: Rate of temperature rise
            - cooling_load_hours: Hours with high cooling demand
        compliance_issues: Non-compliance patterns
            - cold_violations: Number of too-cold violations
            - hot_violations: Number of too-hot violations
            - seasonal_pattern: "winter", "summer", or "both"
        weather_correlation: Optional weather correlation data
            - outdoor_temp_correlation: Correlation coefficient
            - thermal_lag: Time lag in temperature response
    
    Returns:
        InsulationRecommendation with analysis results
    
    Example:
        >>> heating = {
        ...     'avg_indoor_temp': 18.5,
        ...     'temp_drop_rate': 0.8,  # °C per hour
        ...     'heating_load_hours': 1200
        ... }
        >>> cooling = {
        ...     'avg_indoor_temp': 27.5,
        ...     'temp_rise_rate': 1.2,
        ...     'cooling_load_hours': 800
        ... }
        >>> issues = {
        ...     'cold_violations': 450,
        ...     'hot_violations': 320,
        ...     'seasonal_pattern': 'both'
        ... }
        >>> result = analyze_insulation_need(heating, cooling, issues)
        >>> result.needed
        True
        >>> result.issue_type
        'both'
    """
    # Extract key metrics
    temp_drop_rate = heating_season_data.get('temp_drop_rate', 0.0)
    temp_rise_rate = cooling_season_data.get('temp_rise_rate', 0.0)
    cold_violations = compliance_issues.get('cold_violations', 0)
    hot_violations = compliance_issues.get('hot_violations', 0)
    
    # Determine issue type
    has_heat_loss = temp_drop_rate > 0.5 or cold_violations > 100
    has_heat_gain = temp_rise_rate > 0.7 or hot_violations > 100
    
    if has_heat_loss and has_heat_gain:
        issue_type = "both"
    elif has_heat_loss:
        issue_type = "heat_loss"
    elif has_heat_gain:
        issue_type = "heat_gain"
    else:
        issue_type = "none"
    
    # Calculate severity score (0.0 to 1.0)
    severity_components = []
    
    # Temperature change rate severity
    if temp_drop_rate > 0:
        severity_components.append(min(temp_drop_rate / 2.0, 1.0))
    if temp_rise_rate > 0:
        severity_components.append(min(temp_rise_rate / 2.5, 1.0))
    
    # Violation severity
    total_violations = cold_violations + hot_violations
    violation_severity = min(total_violations / 1000, 1.0)
    severity_components.append(violation_severity)
    
    # Weather correlation severity (if available)
    if weather_correlation:
        correlation = abs(weather_correlation.get('outdoor_temp_correlation', 0.0))
        if correlation > 0.7:  # High correlation indicates poor insulation
            severity_components.append(correlation)
    
    severity_score = sum(severity_components) / len(severity_components) if severity_components else 0.0
    
    # Determine priority
    if severity_score >= 0.7:
        priority = "high"
    elif severity_score >= 0.4:
        priority = "medium"
    else:
        priority = "low"
    
    # Identify affected areas
    affected_areas = identify_affected_areas(
        heating_season_data,
        cooling_season_data,
        weather_correlation
    )
    
    # Generate description
    description = generate_insulation_description(
        issue_type,
        priority,
        affected_areas,
        temp_drop_rate,
        temp_rise_rate
    )
    
    # Estimate improvement
    estimated_improvement = estimate_improvement(severity_score, issue_type)
    
    # Determine if recommendation is needed
    needed = severity_score >= 0.3 and issue_type != "none"
    
    return InsulationRecommendation(
        needed=needed,
        priority=priority,
        affected_areas=affected_areas,
        issue_type=issue_type,
        severity_score=severity_score,
        description=description,
        estimated_improvement=estimated_improvement
    )


def identify_affected_areas(
    heating_data: Dict[str, Any],
    cooling_data: Dict[str, Any],
    weather_correlation: Optional[Dict[str, Any]]
) -> List[str]:
    """
    Identify which building areas likely need insulation improvements.
    
    Args:
        heating_data: Heating season statistics
        cooling_data: Cooling season statistics
        weather_correlation: Weather correlation data
    
    Returns:
        List of affected area names
    
    Example:
        >>> heating = {'temp_drop_rate': 0.9}
        >>> cooling = {'temp_rise_rate': 1.3}
        >>> areas = identify_affected_areas(heating, cooling, None)
        >>> 'roof' in areas
        True
    """
    affected = []
    
    temp_drop = heating_data.get('temp_drop_rate', 0.0)
    temp_rise = cooling_data.get('temp_rise_rate', 0.0)
    
    # High temperature rise suggests roof/ceiling issues
    if temp_rise > 1.0:
        affected.append("roof")
    
    # Significant heat loss/gain suggests wall issues
    if temp_drop > 0.6 or temp_rise > 0.8:
        affected.append("walls")
    
    # Fast temperature changes suggest window issues
    if temp_drop > 0.7 or temp_rise > 0.9:
        affected.append("windows")
    
    # Very high correlation with outdoor temp suggests envelope issues
    if weather_correlation:
        correlation = abs(weather_correlation.get('outdoor_temp_correlation', 0.0))
        if correlation > 0.8:
            if "walls" not in affected:
                affected.append("walls")
            affected.append("envelope")
    
    return affected if affected else ["general"]


def generate_insulation_description(
    issue_type: str,
    priority: str,
    affected_areas: List[str],
    temp_drop_rate: float,
    temp_rise_rate: float
) -> str:
    """
    Generate human-readable description of insulation issues.
    
    Args:
        issue_type: Type of issue ("heat_loss", "heat_gain", "both")
        priority: Priority level
        affected_areas: List of affected areas
        temp_drop_rate: Temperature drop rate (°C/hour)
        temp_rise_rate: Temperature rise rate (°C/hour)
    
    Returns:
        Descriptive string
    
    Example:
        >>> desc = generate_insulation_description(
        ...     "both", "high", ["roof", "walls"], 0.9, 1.2
        ... )
        >>> "insulation improvements" in desc.lower()
        True
    """
    areas_str = ", ".join(affected_areas)
    
    if issue_type == "heat_loss":
        issue_desc = f"significant heat loss (temperature drops at {temp_drop_rate:.1f}°C/hour)"
    elif issue_type == "heat_gain":
        issue_desc = f"significant heat gain (temperature rises at {temp_rise_rate:.1f}°C/hour)"
    else:  # both
        issue_desc = f"both heat loss ({temp_drop_rate:.1f}°C/hour) and heat gain ({temp_rise_rate:.1f}°C/hour)"
    
    description = (
        f"{priority.capitalize()} priority insulation improvements needed. "
        f"Building shows {issue_desc}. "
        f"Focus on: {areas_str}."
    )
    
    return description


def estimate_improvement(severity_score: float, issue_type: str) -> float:
    """
    Estimate potential improvement from insulation upgrades.
    
    Args:
        severity_score: Severity score (0.0 to 1.0)
        issue_type: Type of thermal issue
    
    Returns:
        Expected improvement percentage (0-100)
    
    Example:
        >>> estimate_improvement(0.8, "both")
        45.0
    """
    # Base improvement potential
    base_improvement = severity_score * 50  # Up to 50% improvement
    
    # Bonus for addressing multiple issues
    if issue_type == "both":
        multiplier = 1.2
    else:
        multiplier = 1.0
    
    estimated = min(base_improvement * multiplier, 60)  # Cap at 60%
    
    return round(estimated, 1)


__all__ = [
    'InsulationRecommendation',
    'analyze_insulation_need',
    'identify_affected_areas',
    'generate_insulation_description',
    'estimate_improvement'
]
