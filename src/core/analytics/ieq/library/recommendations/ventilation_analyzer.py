"""
Ventilation Analysis Module

Pure domain logic for analyzing ventilation needs based on 
CO2 levels, humidity patterns, and air quality indicators.

Design Principles:
- Single responsibility: Only ventilation need analysis
- Pure functions: No side effects, no UI dependencies
- Type-safe: Full type hints and validation
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class VentilationRecommendation:
    """Recommendation for ventilation improvements."""
    
    needed: bool
    priority: str  # "high", "medium", "low"
    ventilation_type: str  # "natural", "mechanical", "hybrid"
    issue_indicators: List[str]  # e.g., ["high_co2", "high_humidity"]
    severity_score: float  # 0.0 to 1.0
    description: str
    recommended_rate: Optional[float] = None  # Recommended ACH (air changes per hour)
    estimated_improvement: Optional[float] = None  # Expected % improvement


def analyze_ventilation_need(
    co2_data: Dict[str, Any],
    humidity_data: Optional[Dict[str, Any]] = None,
    occupancy_data: Optional[Dict[str, Any]] = None,
    compliance_issues: Optional[Dict[str, Any]] = None
) -> VentilationRecommendation:
    """
    Analyze if ventilation improvements are needed based on air quality patterns.
    
    Args:
        co2_data: CO2 level statistics
            - avg_co2: Average CO2 level (ppm)
            - max_co2: Maximum CO2 level (ppm)
            - high_co2_hours: Hours above threshold
            - co2_rise_rate: Rate of CO2 increase (ppm/hour)
        humidity_data: Optional humidity statistics
            - avg_humidity: Average relative humidity (%)
            - high_humidity_hours: Hours above threshold
        occupancy_data: Optional occupancy information
            - avg_occupancy: Average number of occupants
            - peak_occupancy: Peak occupancy
        compliance_issues: Optional compliance violation data
            - co2_violations: Number of CO2 violations
            - humidity_violations: Number of humidity violations
    
    Returns:
        VentilationRecommendation with analysis results
    
    Example:
        >>> co2 = {
        ...     'avg_co2': 1200,
        ...     'max_co2': 1800,
        ...     'high_co2_hours': 450,
        ...     'co2_rise_rate': 150
        ... }
        >>> humidity = {
        ...     'avg_humidity': 68,
        ...     'high_humidity_hours': 200
        ... }
        >>> result = analyze_ventilation_need(co2, humidity)
        >>> result.needed
        True
        >>> "high_co2" in result.issue_indicators
        True
    """
    # Extract CO2 metrics
    avg_co2 = co2_data.get('avg_co2', 400)
    max_co2 = co2_data.get('max_co2', 400)
    high_co2_hours = co2_data.get('high_co2_hours', 0)
    co2_rise_rate = co2_data.get('co2_rise_rate', 0)
    
    # Identify issues
    issue_indicators = []
    severity_components = []
    
    # CO2 analysis
    if avg_co2 > 1000:
        issue_indicators.append("high_co2")
        co2_severity = min((avg_co2 - 400) / 1600, 1.0)  # Normalize to 0-1
        severity_components.append(co2_severity)
    
    if co2_rise_rate > 100:
        issue_indicators.append("rapid_co2_buildup")
        rate_severity = min(co2_rise_rate / 300, 1.0)
        severity_components.append(rate_severity)
    
    # Humidity analysis (if available)
    if humidity_data:
        avg_humidity = humidity_data.get('avg_humidity', 50)
        high_humidity_hours = humidity_data.get('high_humidity_hours', 0)
        
        if avg_humidity > 65:
            issue_indicators.append("high_humidity")
            humidity_severity = min((avg_humidity - 40) / 40, 1.0)
            severity_components.append(humidity_severity)
        
        if avg_humidity < 30:
            issue_indicators.append("low_humidity")
            severity_components.append(0.4)  # Moderate severity for low humidity
    
    # Compliance violations (if available)
    if compliance_issues:
        co2_violations = compliance_issues.get('co2_violations', 0)
        if co2_violations > 50:
            issue_indicators.append("frequent_violations")
            violation_severity = min(co2_violations / 500, 1.0)
            severity_components.append(violation_severity)
    
    # Calculate overall severity
    severity_score = sum(severity_components) / len(severity_components) if severity_components else 0.0
    
    # Determine priority
    if severity_score >= 0.7 or max_co2 > 1500:
        priority = "high"
    elif severity_score >= 0.4:
        priority = "medium"
    else:
        priority = "low"
    
    # Recommend ventilation type
    ventilation_type = recommend_ventilation_type(
        avg_co2,
        co2_rise_rate,
        occupancy_data,
        humidity_data
    )
    
    # Calculate recommended air change rate
    recommended_rate = calculate_recommended_ach(
        avg_co2,
        co2_rise_rate,
        occupancy_data
    )
    
    # Generate description
    description = generate_ventilation_description(
        issue_indicators,
        priority,
        ventilation_type,
        avg_co2,
        humidity_data.get('avg_humidity') if humidity_data else None
    )
    
    # Estimate improvement
    estimated_improvement = estimate_ventilation_improvement(severity_score)
    
    # Determine if recommendation is needed
    needed = severity_score >= 0.3 or avg_co2 > 1000
    
    return VentilationRecommendation(
        needed=needed,
        priority=priority,
        ventilation_type=ventilation_type,
        issue_indicators=issue_indicators,
        severity_score=severity_score,
        description=description,
        recommended_rate=recommended_rate,
        estimated_improvement=estimated_improvement
    )


def recommend_ventilation_type(
    avg_co2: float,
    co2_rise_rate: float,
    occupancy_data: Optional[Dict[str, Any]],
    humidity_data: Optional[Dict[str, Any]]
) -> str:
    """
    Recommend appropriate ventilation type based on conditions.
    
    Args:
        avg_co2: Average CO2 level (ppm)
        co2_rise_rate: Rate of CO2 increase
        occupancy_data: Occupancy information
        humidity_data: Humidity statistics
    
    Returns:
        Ventilation type: "natural", "mechanical", or "hybrid"
    
    Example:
        >>> recommend_ventilation_type(1400, 200, {'avg_occupancy': 30}, None)
        'mechanical'
    """
    # High CO2 or rapid buildup needs mechanical ventilation
    if avg_co2 > 1300 or co2_rise_rate > 150:
        return "mechanical"
    
    # High occupancy needs mechanical or hybrid
    if occupancy_data:
        avg_occupancy = occupancy_data.get('avg_occupancy', 0)
        if avg_occupancy > 20:
            return "mechanical"
        elif avg_occupancy > 10:
            return "hybrid"
    
    # Humidity issues may benefit from mechanical control
    if humidity_data:
        avg_humidity = humidity_data.get('avg_humidity', 50)
        if avg_humidity > 70 or avg_humidity < 25:
            return "hybrid"
    
    # Moderate issues can use natural ventilation
    return "natural"


def calculate_recommended_ach(
    avg_co2: float,
    co2_rise_rate: float,
    occupancy_data: Optional[Dict[str, Any]]
) -> float:
    """
    Calculate recommended air changes per hour (ACH).
    
    Args:
        avg_co2: Average CO2 level (ppm)
        co2_rise_rate: Rate of CO2 increase
        occupancy_data: Occupancy information
    
    Returns:
        Recommended ACH value
    
    Example:
        >>> calculate_recommended_ach(1200, 120, {'avg_occupancy': 15})
        6.0
    """
    # Base ACH on CO2 levels
    if avg_co2 > 1400:
        base_ach = 8.0
    elif avg_co2 > 1200:
        base_ach = 6.0
    elif avg_co2 > 1000:
        base_ach = 4.0
    else:
        base_ach = 2.0
    
    # Adjust for rapid CO2 buildup
    if co2_rise_rate > 150:
        base_ach += 2.0
    elif co2_rise_rate > 100:
        base_ach += 1.0
    
    # Adjust for occupancy
    if occupancy_data:
        avg_occupancy = occupancy_data.get('avg_occupancy', 0)
        occupancy_factor = avg_occupancy / 10  # 1 ACH per 10 people
        base_ach = max(base_ach, occupancy_factor)
    
    return round(min(base_ach, 12.0), 1)  # Cap at 12 ACH


def generate_ventilation_description(
    issue_indicators: List[str],
    priority: str,
    ventilation_type: str,
    avg_co2: float,
    avg_humidity: Optional[float]
) -> str:
    """
    Generate human-readable description of ventilation issues.
    
    Args:
        issue_indicators: List of identified issues
        priority: Priority level
        ventilation_type: Recommended ventilation type
        avg_co2: Average CO2 level
        avg_humidity: Average humidity (if available)
    
    Returns:
        Descriptive string
    
    Example:
        >>> desc = generate_ventilation_description(
        ...     ["high_co2", "rapid_co2_buildup"],
        ...     "high",
        ...     "mechanical",
        ...     1300,
        ...     None
        ... )
        >>> "mechanical ventilation" in desc.lower()
        True
    """
    issues_str = ", ".join(issue_indicators)
    
    description = (
        f"{priority.capitalize()} priority ventilation improvements needed. "
        f"Issues detected: {issues_str}. "
        f"Average CO2 level: {avg_co2:.0f} ppm. "
    )
    
    if avg_humidity is not None:
        description += f"Average humidity: {avg_humidity:.1f}%. "
    
    description += f"Recommend {ventilation_type} ventilation system."
    
    return description


def estimate_ventilation_improvement(severity_score: float) -> float:
    """
    Estimate potential air quality improvement from ventilation upgrades.
    
    Args:
        severity_score: Severity score (0.0 to 1.0)
    
    Returns:
        Expected improvement percentage (0-100)
    
    Example:
        >>> estimate_ventilation_improvement(0.75)
        52.5
    """
    # Ventilation improvements typically highly effective
    base_improvement = severity_score * 70  # Up to 70% improvement
    
    return round(min(base_improvement, 75), 1)  # Cap at 75%


__all__ = [
    'VentilationRecommendation',
    'analyze_ventilation_need',
    'recommend_ventilation_type',
    'calculate_recommended_ach',
    'generate_ventilation_description',
    'estimate_ventilation_improvement'
]
