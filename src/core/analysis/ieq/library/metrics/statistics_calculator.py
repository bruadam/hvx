"""
Statistics Calculator

Single responsibility: Calculate statistical metrics from time series data.
Pure mathematical/statistical computations.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional


def calculate_basic_statistics(data: pd.Series) -> Dict[str, float]:
    """
    Calculate basic statistical metrics.
    
    Args:
        data: Time series data
    
    Returns:
        Dictionary with mean, std, min, max, median, count
    """
    if len(data) == 0:
        return {
            'mean': 0.0,
            'std': 0.0,
            'min': 0.0,
            'max': 0.0,
            'median': 0.0,
            'count': 0
        }
    
    return {
        'mean': float(data.mean()),
        'std': float(data.std()),
        'min': float(data.min()),
        'max': float(data.max()),
        'median': float(data.median()),
        'count': len(data)
    }


def calculate_percentiles(
    data: pd.Series,
    percentiles: Optional[list] = None
) -> Dict[str, float]:
    """
    Calculate percentile values.
    
    Args:
        data: Time series data
        percentiles: List of percentiles to calculate (0-100). Default: [5, 25, 50, 75, 95]
    
    Returns:
        Dictionary with percentile values (e.g., {'p05': 18.5, 'p50': 22.0, ...})
    """
    if percentiles is None:
        percentiles = [5, 25, 50, 75, 95]
    
    if len(data) == 0:
        return {f'p{int(p):02d}': 0.0 for p in percentiles}
    
    result = {}
    for p in percentiles:
        result[f'p{int(p):02d}'] = float(data.quantile(p / 100))
    
    return result


def calculate_extended_statistics(data: pd.Series) -> Dict[str, float]:
    """
    Calculate extended statistical metrics including percentiles.
    
    Args:
        data: Time series data
    
    Returns:
        Dictionary with comprehensive statistics
    """
    if len(data) == 0:
        return {
            'mean': 0.0,
            'std': 0.0,
            'min': 0.0,
            'max': 0.0,
            'median': 0.0,
            'p05': 0.0,
            'p25': 0.0,
            'p75': 0.0,
            'p95': 0.0,
            'count': 0,
            'variance': 0.0,
            'range': 0.0
        }
    
    basic = calculate_basic_statistics(data)
    percentiles = calculate_percentiles(data)
    
    return {
        **basic,
        **percentiles,
        'variance': float(data.var()),
        'range': float(data.max() - data.min())
    }


def calculate_temporal_statistics(data: pd.Series) -> Dict[str, Any]:
    """
    Calculate time-based statistics (hourly, daily, monthly patterns).
    
    Args:
        data: Time series data with DatetimeIndex
    
    Returns:
        Dictionary with temporal statistics
    """
    if not isinstance(data.index, pd.DatetimeIndex) or len(data) == 0:
        return {}
    
    stats = {
        'hourly_mean': data.groupby(data.index.hour).mean().to_dict(),
        'daily_mean': data.groupby(data.index.day_of_week).mean().to_dict(),
        'monthly_mean': data.groupby(data.index.month).mean().to_dict(),
    }
    
    return stats


def calculate_distribution_metrics(data: pd.Series) -> Dict[str, float]:
    """
    Calculate distribution shape metrics (skewness, kurtosis).
    
    Args:
        data: Time series data
    
    Returns:
        Dictionary with skewness and kurtosis
    """
    if len(data) < 3:  # Need at least 3 points for these metrics
        return {
            'skewness': 0.0,
            'kurtosis': 0.0
        }
    
    return {
        'skewness': float(data.skew()),
        'kurtosis': float(data.kurtosis())
    }


def calculate_outlier_metrics(
    data: pd.Series,
    method: str = 'iqr',
    threshold: float = 1.5
) -> Dict[str, Any]:
    """
    Identify and count outliers.
    
    Args:
        data: Time series data
        method: 'iqr' for interquartile range or 'zscore' for standard deviation
        threshold: Multiplier for IQR (default 1.5) or z-score (default 1.5 sigma)
    
    Returns:
        Dictionary with outlier count and percentage
    """
    if len(data) == 0:
        return {
            'outlier_count': 0,
            'outlier_percentage': 0.0,
            'outlier_method': method
        }
    
    if method == 'iqr':
        q1 = data.quantile(0.25)
        q3 = data.quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - threshold * iqr
        upper_bound = q3 + threshold * iqr
        outliers = (data < lower_bound) | (data > upper_bound)
    else:  # zscore
        z_scores = np.abs((data - data.mean()) / data.std())
        outliers = z_scores > threshold
    
    outlier_count = outliers.sum()
    outlier_percentage = (outlier_count / len(data)) * 100
    
    return {
        'outlier_count': int(outlier_count),
        'outlier_percentage': float(outlier_percentage),
        'outlier_method': method,
        'outlier_threshold': threshold
    }
