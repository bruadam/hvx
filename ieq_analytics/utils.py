"""
Utility functions for IEQ analytics.
"""

from typing import Any, Dict, Optional
import pandas as pd
import numpy as np


def sanitize_correlation_value(corr_value: Any) -> Optional[float]:
    """
    Sanitize correlation values to handle NaN, complex numbers, and other non-numeric types.
    
    Args:
        corr_value: Raw correlation value from pandas correlation matrix
        
    Returns:
        Sanitized correlation value as float rounded to 3 decimal places, or None if invalid
    """
    # Handle NaN, complex numbers, and other non-numeric types
    if pd.isna(corr_value) or isinstance(corr_value, complex):
        return None
    
    try:
        # Check if corr_value is numeric before converting to float
        if isinstance(corr_value, (int, float, np.number)):
            return round(float(corr_value), 3)
        else:
            return None
    except (ValueError, TypeError):
        return None


def sanitize_correlation_matrix(corr_matrix: pd.DataFrame) -> Dict[str, Dict[str, Optional[float]]]:
    """
    Convert a pandas correlation matrix to a sanitized dictionary format.
    
    Args:
        corr_matrix: Pandas correlation matrix DataFrame
        
    Returns:
        Dictionary with sanitized correlation values
    """
    correlations = {}
    
    for col1 in corr_matrix.columns:
        correlations[col1] = {}
        for col2 in corr_matrix.columns:
            if col1 != col2:
                corr_value = corr_matrix.loc[col1, col2]
                correlations[col1][col2] = sanitize_correlation_value(corr_value)
    
    return correlations


def safe_numeric_operation(value: Any, operation: str = "float", precision: int = 2) -> Optional[float]:
    """
    Safely perform numeric operations with error handling.
    
    Args:
        value: Input value to process
        operation: Type of operation ('float', 'int', 'round')
        precision: Number of decimal places for rounding
        
    Returns:
        Processed numeric value or None if invalid
    """
    try:
        if pd.isna(value):
            return None
            
        if operation == "float":
            return round(float(value), precision)
        elif operation == "int":
            return int(value)
        elif operation == "round":
            return round(value, precision)
        else:
            return float(value)
            
    except (ValueError, TypeError, OverflowError):
        return None


def validate_numeric_series(series: pd.Series) -> bool:
    """
    Validate if a pandas Series contains valid numeric data.
    
    Args:
        series: Pandas Series to validate
        
    Returns:
        True if series contains valid numeric data, False otherwise
    """
    if series.empty:
        return False
        
    # Check if series has numeric dtype
    if not pd.api.types.is_numeric_dtype(series):
        return False
        
    # Check if there are any non-null values
    if series.count() == 0:
        return False
        
    return True


def clean_numeric_data(data: pd.DataFrame, columns: Optional[list] = None) -> pd.DataFrame:
    """
    Clean numeric data by removing infinite values and handling outliers.
    
    Args:
        data: Input DataFrame
        columns: List of columns to clean (default: all numeric columns)
        
    Returns:
        Cleaned DataFrame
    """
    cleaned_data = data.copy()
    
    if columns is None:
        columns = list(cleaned_data.select_dtypes(include=[np.number]).columns)
    
    for col in columns:
        if col in cleaned_data.columns:
            # Replace infinite values with NaN
            cleaned_data[col] = cleaned_data[col].replace([np.inf, -np.inf], np.nan)
            
            # Optionally remove extreme outliers (beyond 5 standard deviations)
            if cleaned_data[col].std() > 0:
                mean_val = cleaned_data[col].mean()
                std_val = cleaned_data[col].std()
                lower_bound = mean_val - 5 * std_val
                upper_bound = mean_val + 5 * std_val
                
                cleaned_data[col] = cleaned_data[col].where(
                    (cleaned_data[col] >= lower_bound) & (cleaned_data[col] <= upper_bound)
                )
    
    return cleaned_data


def format_percentage(value: float, precision: int = 1) -> str:
    """
    Format a decimal value as a percentage string.
    
    Args:
        value: Decimal value (0.0 to 1.0)
        precision: Number of decimal places
        
    Returns:
        Formatted percentage string
    """
    try:
        return f"{value * 100:.{precision}f}%"
    except (ValueError, TypeError):
        return "N/A"


def safe_division(numerator: Any, denominator: Any, default: float = 0.0) -> float:
    """
    Safely perform division with error handling.
    
    Args:
        numerator: Numerator value
        denominator: Denominator value
        default: Default value to return if division fails
        
    Returns:
        Division result or default value
    """
    try:
        if denominator == 0 or pd.isna(denominator) or pd.isna(numerator):
            return default
        return float(numerator) / float(denominator)
    except (ValueError, TypeError, ZeroDivisionError):
        return default


def calculate_data_completeness(data: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate data completeness for each column in a DataFrame.
    
    Args:
        data: Input DataFrame
        
    Returns:
        Dictionary with completeness percentages for each column
    """
    if data.empty:
        return {}
    
    completeness = {}
    total_rows = len(data)
    
    for col in data.columns:
        non_null_count = data[col].count()
        completeness[col] = safe_division(non_null_count, total_rows, 0.0)
    
    return completeness


def detect_time_gaps(timestamps: pd.DatetimeIndex, expected_freq: str = "H") -> list:
    """
    Detect gaps in time series data.
    
    Args:
        timestamps: DatetimeIndex of timestamps
        expected_freq: Expected frequency (pandas frequency string)
        
    Returns:
        List of detected gaps with start time and duration
    """
    if len(timestamps) < 2:
        return []
    
    expected_delta = pd.Timedelta(expected_freq)
    time_diffs = timestamps[1:] - timestamps[:-1]
    
    # Find gaps that are significantly larger than expected
    gaps = time_diffs[time_diffs > expected_delta * 1.5]
    
    gap_info = []
    for i, gap in enumerate(gaps):
        gap_start_indices = (time_diffs == gap).nonzero()[0]
        if len(gap_start_indices) > 0:
            gap_start_idx = int(gap_start_indices[0])
            gap_start = timestamps[gap_start_idx]
            
            gap_info.append({
                "start": gap_start.isoformat(),
                "duration_hours": gap.total_seconds() / 3600
            })
    
    return gap_info
