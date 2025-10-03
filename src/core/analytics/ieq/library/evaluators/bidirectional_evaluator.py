"""
Bidirectional Rule Evaluator

Single responsibility: Evaluate whether values fall within a min/max range.
Used for comfort ranges (e.g., temperature 20-26°C, humidity 30-70%).
"""

import pandas as pd
from typing import Dict, Any, Union


def evaluate_bidirectional(
    data: pd.Series,
    min_value: float,
    max_value: float
) -> pd.Series:
    """
    Evaluate bidirectional compliance (values must be within range).
    
    Args:
        data: Time series data to evaluate
        min_value: Minimum acceptable value (inclusive)
        max_value: Maximum acceptable value (inclusive)
    
    Returns:
        Boolean series where True = compliant (within range)
    
    Example:
        >>> data = pd.Series([18, 22, 24, 28])
        >>> evaluate_bidirectional(data, 20, 26)
        0    False  # 18 < 20
        1     True  # 22 in range
        2     True  # 24 in range
        3    False  # 28 > 26
    """
    return (data >= min_value) & (data <= max_value)


def parse_bidirectional_config(rule_config: Dict[str, Any]) -> Dict[str, float]:
    """
    Parse bidirectional rule configuration to extract min/max values.
    
    Args:
        rule_config: Rule configuration dictionary
    
    Returns:
        Dictionary with 'min' and 'max' keys
    
    Raises:
        ValueError: If configuration is invalid
    """
    # Try 'limits' dictionary first (new format)
    if 'limits' in rule_config:
        limits = rule_config['limits']
        if isinstance(limits, dict):
            if 'lower' in limits and 'upper' in limits:
                return {
                    'min': float(limits['lower']),
                    'max': float(limits['upper'])
                }
            elif 'min' in limits and 'max' in limits:
                return {
                    'min': float(limits['min']),
                    'max': float(limits['max'])
                }
    
    # Try direct min/max (legacy format)
    if 'min' in rule_config and 'max' in rule_config:
        return {
            'min': float(rule_config['min']),
            'max': float(rule_config['max'])
        }
    
    # Try limit as range string or dict
    if 'limit' in rule_config:
        limit = rule_config['limit']
        if isinstance(limit, dict):
            if 'min' in limit and 'max' in limit:
                return {
                    'min': float(limit['min']),
                    'max': float(limit['max'])
                }
    
    raise ValueError(
        "Bidirectional rule configuration must include 'limits' with 'lower'/'upper' "
        "or 'min'/'max' values"
    )
