"""
HVAC System Analysis Module

Pure domain logic for analyzing HVAC system performance and 
recommending improvements based on temperature control patterns.

Design Principles:
- Single responsibility: Only HVAC performance analysis
- Pure functions: No side effects, no UI dependencies
- Type-safe: Full type hints and validation
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class HVACRecommendation:
    """Recommendation for HVAC system improvements."""
    
    needed: bool
    priority: str  # "high", "medium", "low"
    issue_types: List[str]  # e.g., ["poor_control", "oversized", "undersized"]
    severity_score: float  # 0.0 to 1.0
    description: str
    recommended_actions: List[str]  # Specific improvement actions
    estimated_improvement: Optional[float] = None  # Expected % improvement
    energy_impact: Optional[str] = None  # "high", "medium", "low"


def analyze_hvac_performance(
    temperature_control: Dict[str, Any],
    setpoint_deviation: Dict[str, Any],
    cycling_behavior: Optional[Dict[str, Any]] = None,
    compliance_issues: Optional[Dict[str, Any]] = None
) -> HVACRecommendation:
    """
    Analyze HVAC system performance and recommend improvements.
    
    Args:
        temperature_control: Temperature control statistics
            - avg_deviation: Average deviation from setpoint (°C)
            - max_deviation: Maximum deviation from setpoint (°C)
            - control_stability: Stability score (0-1)
            - response_time: Time to reach setpoint (minutes)
        setpoint_deviation: Setpoint deviation patterns
            - overshoot_frequency: How often temperature overshoots
            - undershoot_frequency: How often temperature undershoots
            - steady_state_error: Average steady-state error
        cycling_behavior: Optional cycling analysis
            - cycles_per_hour: Number of on/off cycles per hour
            - short_cycling: Boolean indicating short cycling
            - runtime_ratio: Percentage of time system is on
        compliance_issues: Optional compliance violation data
            - temperature_violations: Number of violations
            - violation_duration: Average duration of violations
    
    Returns:
        HVACRecommendation with analysis results
    
    Example:
        >>> temp_control = {
        ...     'avg_deviation': 2.5,
        ...     'max_deviation': 5.0,
        ...     'control_stability': 0.4,
        ...     'response_time': 45
        ... }
        >>> setpoint_dev = {
        ...     'overshoot_frequency': 0.3,
        ...     'undershoot_frequency': 0.4,
        ...     'steady_state_error': 1.8
        ... }
        >>> result = analyze_hvac_performance(temp_control, setpoint_dev)
        >>> result.needed
        True
        >>> "poor_control" in result.issue_types
        True
    """
    # Extract key metrics
    avg_deviation = temperature_control.get('avg_deviation', 0.0)
    max_deviation = temperature_control.get('max_deviation', 0.0)
    control_stability = temperature_control.get('control_stability', 1.0)
    response_time = temperature_control.get('response_time', 0)
    
    overshoot_freq = setpoint_deviation.get('overshoot_frequency', 0.0)
    undershoot_freq = setpoint_deviation.get('undershoot_frequency', 0.0)
    steady_state_error = setpoint_deviation.get('steady_state_error', 0.0)
    
    # Identify issues
    issue_types = []
    severity_components = []
    recommended_actions = []
    
    # Poor temperature control
    if avg_deviation > 1.5 or control_stability < 0.6:
        issue_types.append("poor_control")
        control_severity = min(avg_deviation / 3.0, 1.0)
        severity_components.append(control_severity)
        recommended_actions.append("Calibrate or upgrade thermostat")
        recommended_actions.append("Review and optimize control logic")
    
    # Slow response time
    if response_time > 30:
        issue_types.append("slow_response")
        response_severity = min(response_time / 60, 1.0)
        severity_components.append(response_severity)
        recommended_actions.append("Check system capacity and sizing")
    
    # Overshooting issues (oversized system)
    if overshoot_freq > 0.2:
        issue_types.append("oversized")
        severity_components.append(overshoot_freq)
        recommended_actions.append("Consider variable speed drives")
        recommended_actions.append("Implement staged heating/cooling")
    
    # Undershooting issues (undersized system)
    if undershoot_freq > 0.3:
        issue_types.append("undersized")
        severity_components.append(undershoot_freq)
        recommended_actions.append("Evaluate system capacity")
        recommended_actions.append("Check for maintenance issues")
    
    # Cycling behavior analysis
    if cycling_behavior:
        cycles_per_hour = cycling_behavior.get('cycles_per_hour', 0)
        short_cycling = cycling_behavior.get('short_cycling', False)
        
        if short_cycling or cycles_per_hour > 6:
            issue_types.append("short_cycling")
            severity_components.append(0.7)
            recommended_actions.append("Investigate and fix short cycling")
            recommended_actions.append("Check refrigerant levels and filters")
    
    # Compliance violations
    if compliance_issues:
        temp_violations = compliance_issues.get('temperature_violations', 0)
        if temp_violations > 100:
            issue_types.append("frequent_violations")
            violation_severity = min(temp_violations / 500, 1.0)
            severity_components.append(violation_severity)
    
    # Calculate overall severity
    severity_score = sum(severity_components) / len(severity_components) if severity_components else 0.0
    
    # Determine priority
    if severity_score >= 0.7:
        priority = "high"
    elif severity_score >= 0.4:
        priority = "medium"
    else:
        priority = "low"
    
    # Assess energy impact
    energy_impact = assess_energy_impact(
        issue_types,
        cycling_behavior,
        overshoot_freq,
        undershoot_freq
    )
    
    # Generate description
    description = generate_hvac_description(
        issue_types,
        priority,
        avg_deviation,
        control_stability
    )
    
    # Estimate improvement potential
    estimated_improvement = estimate_hvac_improvement(severity_score, issue_types)
    
    # Remove duplicate recommendations
    recommended_actions = list(dict.fromkeys(recommended_actions))
    
    # Determine if recommendation is needed
    needed = severity_score >= 0.3 or len(issue_types) > 0
    
    return HVACRecommendation(
        needed=needed,
        priority=priority,
        issue_types=issue_types,
        severity_score=severity_score,
        description=description,
        recommended_actions=recommended_actions,
        estimated_improvement=estimated_improvement,
        energy_impact=energy_impact
    )


def assess_energy_impact(
    issue_types: List[str],
    cycling_behavior: Optional[Dict[str, Any]],
    overshoot_freq: float,
    undershoot_freq: float
) -> str:
    """
    Assess the energy impact of identified HVAC issues.
    
    Args:
        issue_types: List of identified issues
        cycling_behavior: Cycling behavior data
        overshoot_freq: Frequency of temperature overshoot
        undershoot_freq: Frequency of temperature undershoot
    
    Returns:
        Energy impact level: "high", "medium", or "low"
    
    Example:
        >>> assess_energy_impact(
        ...     ["short_cycling", "oversized"],
        ...     {'cycles_per_hour': 8},
        ...     0.4,
        ...     0.1
        ... )
        'high'
    """
    high_impact_issues = {"short_cycling", "oversized", "poor_control"}
    
    # Check for high-impact issues
    if any(issue in high_impact_issues for issue in issue_types):
        return "high"
    
    # Check cycling behavior
    if cycling_behavior:
        cycles_per_hour = cycling_behavior.get('cycles_per_hour', 0)
        if cycles_per_hour > 6:
            return "high"
    
    # Check for significant overshoot (wastes energy)
    if overshoot_freq > 0.3:
        return "high"
    
    # Moderate issues
    if len(issue_types) >= 2:
        return "medium"
    
    return "low"


def generate_hvac_description(
    issue_types: List[str],
    priority: str,
    avg_deviation: float,
    control_stability: float
) -> str:
    """
    Generate human-readable description of HVAC issues.
    
    Args:
        issue_types: List of identified issues
        priority: Priority level
        avg_deviation: Average temperature deviation
        control_stability: Control stability score
    
    Returns:
        Descriptive string
    
    Example:
        >>> desc = generate_hvac_description(
        ...     ["poor_control", "slow_response"],
        ...     "high",
        ...     2.8,
        ...     0.45
        ... )
        >>> "hvac system improvements" in desc.lower()
        True
    """
    issues_str = ", ".join(issue_types)
    
    description = (
        f"{priority.capitalize()} priority HVAC system improvements needed. "
        f"Issues detected: {issues_str}. "
        f"Average temperature deviation: {avg_deviation:.1f}°C. "
        f"Control stability: {control_stability:.1%}."
    )
    
    return description


def estimate_hvac_improvement(severity_score: float, issue_types: List[str]) -> float:
    """
    Estimate potential improvement from HVAC upgrades.
    
    Args:
        severity_score: Severity score (0.0 to 1.0)
        issue_types: List of identified issues
    
    Returns:
        Expected improvement percentage (0-100)
    
    Example:
        >>> estimate_hvac_improvement(0.7, ["poor_control", "short_cycling"])
        56.0
    """
    # Base improvement on severity
    base_improvement = severity_score * 60  # Up to 60% improvement
    
    # Bonus for addressing multiple issues
    if len(issue_types) >= 3:
        multiplier = 1.3
    elif len(issue_types) >= 2:
        multiplier = 1.15
    else:
        multiplier = 1.0
    
    estimated = min(base_improvement * multiplier, 70)  # Cap at 70%
    
    return round(estimated, 1)


def analyze_maintenance_needs(
    temperature_control: Dict[str, Any],
    cycling_behavior: Optional[Dict[str, Any]] = None
) -> List[str]:
    """
    Identify specific maintenance needs based on performance patterns.
    
    Args:
        temperature_control: Temperature control statistics
        cycling_behavior: Optional cycling behavior data
    
    Returns:
        List of recommended maintenance actions
    
    Example:
        >>> temp_control = {'control_stability': 0.3, 'response_time': 50}
        >>> cycling = {'short_cycling': True}
        >>> maintenance = analyze_maintenance_needs(temp_control, cycling)
        >>> len(maintenance) > 0
        True
    """
    maintenance_actions = []
    
    # Poor stability suggests filter or sensor issues
    stability = temperature_control.get('control_stability', 1.0)
    if stability < 0.5:
        maintenance_actions.append("Replace air filters")
        maintenance_actions.append("Calibrate temperature sensors")
    
    # Slow response suggests maintenance issues
    response_time = temperature_control.get('response_time', 0)
    if response_time > 40:
        maintenance_actions.append("Clean coils and heat exchangers")
        maintenance_actions.append("Check refrigerant charge")
    
    # Short cycling suggests specific issues
    if cycling_behavior and cycling_behavior.get('short_cycling', False):
        maintenance_actions.append("Check thermostat location and calibration")
        maintenance_actions.append("Inspect compressor and controls")
        maintenance_actions.append("Verify proper airflow")
    
    return maintenance_actions


__all__ = [
    'HVACRecommendation',
    'analyze_hvac_performance',
    'assess_energy_impact',
    'generate_hvac_description',
    'estimate_hvac_improvement',
    'analyze_maintenance_needs'
]
