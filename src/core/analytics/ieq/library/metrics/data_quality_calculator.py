"""
Data Quality Calculator

Single responsibility: Calculate data quality metrics (completeness, missing data, etc.).
"""

import pandas as pd
from typing import Dict, Any


def calculate_completeness(data: pd.Series) -> float:
    """
    Calculate data completeness as percentage of non-null values.
    
    Args:
        data: Time series data (may contain NaN)
    
    Returns:
        Completeness percentage (0-100)
    
    Example:
        >>> data = pd.Series([1, 2, None, 4, 5])
        >>> calculate_completeness(data)
        80.0  # 4 out of 5 values are present
    """
    if len(data) == 0:
        return 0.0
    
    non_null_count = data.notna().sum()
    total_count = len(data)
    
    return (non_null_count / total_count) * 100


def calculate_missing_data_metrics(data: pd.Series) -> Dict[str, Any]:
    """
    Calculate comprehensive missing data metrics.
    
    Args:
        data: Time series data
    
    Returns:
        Dictionary with missing data statistics
    """
    total_points = len(data)
    missing_points = data.isna().sum()
    valid_points = total_points - missing_points
    
    return {
        'total_points': total_points,
        'valid_points': int(valid_points),
        'missing_points': int(missing_points),
        'completeness': calculate_completeness(data),
        'missing_percentage': (missing_points / total_points * 100) if total_points > 0 else 0.0
    }


def calculate_quality_score(data: pd.Series) -> float:
    """
    Calculate overall data quality score (0-100).
    
    Factors:
        - Completeness (70% weight)
        - Consistency - no excessive outliers (30% weight)
    
    Args:
        data: Time series data
    
    Returns:
        Quality score (0-100)
    """
    if len(data) == 0:
        return 0.0
    
    # Completeness component (70% weight)
    completeness = calculate_completeness(data)
    
    # Consistency component (30% weight)
    # Check for outliers using IQR method
    valid_data = data.dropna()
    if len(valid_data) < 4:
        consistency_score = 100.0  # Too few points to judge
    else:
        q1 = valid_data.quantile(0.25)
        q3 = valid_data.quantile(0.75)
        iqr = q3 - q1
        
        if iqr == 0:
            consistency_score = 100.0  # No variation
        else:
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            outliers = ((valid_data < lower_bound) | (valid_data > upper_bound)).sum()
            outlier_percentage = (outliers / len(valid_data)) * 100
            
            # Penalize high outlier rates
            consistency_score = max(0, 100 - outlier_percentage * 2)
    
    # Weighted average
    quality_score = (completeness * 0.7) + (consistency_score * 0.3)
    
    return round(quality_score, 2)


def identify_data_gaps(data: pd.Series, max_gap_hours: int = 24) -> Dict[str, Any]:
    """
    Identify gaps in time series data.
    
    Args:
        data: Time series data with DatetimeIndex
        max_gap_hours: Maximum acceptable gap in hours
    
    Returns:
        Dictionary with gap information
    """
    if not isinstance(data.index, pd.DatetimeIndex) or len(data) < 2:
        return {
            'has_gaps': False,
            'gap_count': 0,
            'max_gap_hours': 0.0
        }
    
    # Calculate time differences
    time_diffs = data.index.to_series().diff()
    
    # Convert to hours
    gap_hours = time_diffs.dt.total_seconds() / 3600
    
    # Find gaps exceeding threshold
    significant_gaps = gap_hours[gap_hours > max_gap_hours]
    
    return {
        'has_gaps': len(significant_gaps) > 0,
        'gap_count': len(significant_gaps),
        'max_gap_hours': float(gap_hours.max()) if len(gap_hours) > 0 else 0.0,
        'total_gap_hours': float(significant_gaps.sum()) if len(significant_gaps) > 0 else 0.0
    }


def calculate_sampling_rate(data: pd.Series) -> Dict[str, Any]:
    """
    Calculate the sampling rate/frequency of the data.
    
    Args:
        data: Time series data with DatetimeIndex
    
    Returns:
        Dictionary with sampling information
    """
    if not isinstance(data.index, pd.DatetimeIndex) or len(data) < 2:
        return {
            'median_interval_minutes': 0.0,
            'is_regular': False,
            'inferred_frequency': None
        }
    
    # Calculate intervals between consecutive timestamps
    intervals = data.index.to_series().diff().dt.total_seconds() / 60  # Convert to minutes
    
    median_interval = intervals.median()
    std_interval = intervals.std()
    
    # Consider regular if std is less than 10% of median
    is_regular = (std_interval / median_interval) < 0.1 if median_interval > 0 else False
    
    # Try to infer pandas frequency
    try:
        inferred_freq = pd.infer_freq(data.index)
    except:
        inferred_freq = None
    
    return {
        'median_interval_minutes': float(median_interval),
        'std_interval_minutes': float(std_interval),
        'is_regular': is_regular,
        'inferred_frequency': inferred_freq
    }
