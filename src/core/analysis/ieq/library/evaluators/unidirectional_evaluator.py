"""
Unidirectional Rule Evaluator

Single responsibility: Evaluate whether values are above/below a single threshold.
Used for limit-based rules (e.g., CO2 < 1000 ppm, temp > 18°C).
"""

import pandas as pd
from typing import Dict, Any


def evaluate_unidirectional_ascending(
    data: pd.Series,
    threshold: float
) -> pd.Series:
    """
    Evaluate ascending unidirectional compliance (values must be >= threshold).
    
    Args:
        data: Time series data to evaluate
        threshold: Minimum acceptable value
    
    Returns:
        Boolean series where True = compliant (>= threshold)
    
    Example:
        >>> data = pd.Series([16, 18, 20, 22])
        >>> evaluate_unidirectional_ascending(data, 18)
        0    False  # 16 < 18
        1     True  # 18 >= 18
        2     True  # 20 >= 18
        3     True  # 22 >= 18
    """
    return data >= threshold


def evaluate_unidirectional_descending(
    data: pd.Series,
    threshold: float
) -> pd.Series:
    """
    Evaluate descending unidirectional compliance (values must be <= threshold).
    
    Args:
        data: Time series data to evaluate
        threshold: Maximum acceptable value
    
    Returns:
        Boolean series where True = compliant (<= threshold)
    
    Example:
        >>> data = pd.Series([800, 1000, 1200, 1400])
        >>> evaluate_unidirectional_descending(data, 1000)
        0     True  # 800 <= 1000
        1     True  # 1000 <= 1000
        2    False  # 1200 > 1000
        3    False  # 1400 > 1000
    """
    return data <= threshold


def parse_unidirectional_config(rule_config: Dict[str, Any]) -> float:
    """
    Parse unidirectional rule configuration to extract threshold.
    
    Args:
        rule_config: Rule configuration dictionary
    
    Returns:
        Threshold value as float
    
    Raises:
        ValueError: If threshold not found in configuration
    """
    # Try 'limit' first (most common)
    if 'limit' in rule_config:
        limit = rule_config['limit']
        if isinstance(limit, (int, float)):
            return float(limit)
        elif isinstance(limit, dict) and 'value' in limit:
            return float(limit['value'])
    
    # Try 'threshold'
    if 'threshold' in rule_config:
        return float(rule_config['threshold'])
    
    # Try 'value'
    if 'value' in rule_config:
        return float(rule_config['value'])
    
    raise ValueError(
        "Unidirectional rule configuration must include 'limit', 'threshold', or 'value'"
    )


def determine_direction(rule_config: Dict[str, Any]) -> str:
    """
    Determine if rule is ascending (>=) or descending (<=).
    
    Args:
        rule_config: Rule configuration dictionary
    
    Returns:
        'ascending' or 'descending'
    """
    mode = rule_config.get('mode', '').lower()
    
    if 'ascending' in mode or 'above' in mode or 'greater' in mode:
        return 'ascending'
    elif 'descending' in mode or 'below' in mode or 'less' in mode:
        return 'descending'
    
    # Infer from parameter type if not specified
    parameter = rule_config.get('parameter', '').lower()
    feature = rule_config.get('feature', '').lower()
    param_str = parameter or feature
    
    # CO2, VOC, noise = descending (lower is better)
    if any(x in param_str for x in ['co2', 'voc', 'noise', 'pm']):
        return 'descending'
    
    # Temperature minimum = ascending (higher than min)
    if 'temp' in param_str and 'min' in mode:
        return 'ascending'
    
    # Default to descending (most common: limits are upper bounds)
    return 'descending'
