"""
Compliance Calculator

Single responsibility: Calculate compliance rates and metrics from boolean compliance series.
Pure mathematical computation without any domain logic.
"""

import pandas as pd
from typing import Dict, Any, Tuple


def calculate_compliance_rate(compliance_series: pd.Series) -> float:
    """
    Calculate compliance rate as percentage.
    
    Args:
        compliance_series: Boolean series where True = compliant
    
    Returns:
        Compliance rate as percentage (0-100)
    
    Example:
        >>> compliance = pd.Series([True, True, False, True])
        >>> calculate_compliance_rate(compliance)
        75.0
    """
    if len(compliance_series) == 0:
        return 0.0
    
    compliant_count = compliance_series.sum()
    total_count = len(compliance_series)
    
    return (compliant_count / total_count) * 100


def calculate_compliance_metrics(compliance_series: pd.Series) -> Dict[str, Any]:
    """
    Calculate comprehensive compliance metrics.
    
    Args:
        compliance_series: Boolean series where True = compliant
    
    Returns:
        Dictionary with:
            - compliance_rate: Percentage (0-100)
            - total_points: Total number of data points
            - compliant_points: Number of compliant points
            - non_compliant_points: Number of non-compliant points
            - compliance_ratio: Ratio (0-1)
    """
    total_points = len(compliance_series)
    
    if total_points == 0:
        return {
            'compliance_rate': 0.0,
            'total_points': 0,
            'compliant_points': 0,
            'non_compliant_points': 0,
            'compliance_ratio': 0.0
        }
    
    compliant_points = int(compliance_series.sum())
    non_compliant_points = total_points - compliant_points
    compliance_ratio = compliant_points / total_points
    
    return {
        'compliance_rate': compliance_ratio * 100,
        'total_points': total_points,
        'compliant_points': compliant_points,
        'non_compliant_points': non_compliant_points,
        'compliance_ratio': compliance_ratio
    }


def identify_violations(
    data: pd.Series,
    compliance_series: pd.Series,
    max_violations: int = 100
) -> pd.DataFrame:
    """
    Identify timestamp and values of non-compliant points.
    
    Args:
        data: Original time series data
        compliance_series: Boolean compliance series
        max_violations: Maximum number of violations to return
    
    Returns:
        DataFrame with columns: timestamp, value, compliant
    """
    # Combine data and compliance
    violations_df = pd.DataFrame({
        'timestamp': data.index,
        'value': data.values,
        'compliant': compliance_series.values
    })
    
    # Filter to non-compliant only
    violations_df = violations_df[~violations_df['compliant']]
    
    # Limit number of violations
    if len(violations_df) > max_violations:
        violations_df = violations_df.head(max_violations)
    
    return violations_df


def calculate_hour_based_compliance(
    compliance_series: pd.Series,
    max_exceedance_hours: int
) -> Tuple[bool, int, float]:
    """
    Calculate compliance based on maximum allowed exceedance hours (e.g., BR18 regulations).
    
    Args:
        compliance_series: Boolean series where True = compliant
        max_exceedance_hours: Maximum allowed non-compliant hours
    
    Returns:
        Tuple of (passes_hour_test, total_exceedance_hours, hour_compliance_rate)
    
    Example:
        >>> compliance = pd.Series([True] * 95 + [False] * 5)  # 5% non-compliant
        >>> calculate_hour_based_compliance(compliance, max_exceedance_hours=10)
        (True, 5, 100.0)  # Passes because 5 < 10
    """
    total_exceedance_hours = (~compliance_series).sum()
    passes_hour_test = total_exceedance_hours <= max_exceedance_hours
    
    if max_exceedance_hours > 0:
        hour_compliance_rate = (1 - (total_exceedance_hours / max_exceedance_hours)) * 100
        hour_compliance_rate = max(0.0, min(100.0, hour_compliance_rate))
    else:
        hour_compliance_rate = 100.0 if total_exceedance_hours == 0 else 0.0
    
    return passes_hour_test, int(total_exceedance_hours), hour_compliance_rate
