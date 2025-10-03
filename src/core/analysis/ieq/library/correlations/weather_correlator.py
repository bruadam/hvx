"""
Weather Correlator

Single responsibility: Calculate correlations between indoor parameters and weather data.
Helps identify causes of non-compliance (e.g., overheating correlates with outdoor temperature).
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List


def calculate_correlation(
    indoor_data: pd.Series,
    weather_data: pd.Series,
    method: str = 'pearson'
) -> float:
    """
    Calculate correlation coefficient between two time series.
    
    Args:
        indoor_data: Indoor parameter time series
        weather_data: Weather parameter time series
        method: 'pearson', 'spearman', or 'kendall'
    
    Returns:
        Correlation coefficient (-1 to 1)
    """
    # Align indices and drop NaN
    combined = pd.DataFrame({
        'indoor': indoor_data,
        'weather': weather_data
    }).dropna()
    
    if len(combined) < 3:  # Need minimum points for correlation
        return 0.0
    
    corr = combined['indoor'].corr(combined['weather'], method=method)
    
    return float(corr) if not np.isnan(corr) else 0.0


def calculate_weather_correlations(
    indoor_data: pd.Series,
    weather_df: pd.DataFrame,
    weather_parameters: Optional[List[str]] = None
) -> Dict[str, float]:
    """
    Calculate correlations with multiple weather parameters.
    
    Args:
        indoor_data: Indoor parameter time series
        weather_df: DataFrame with weather data (outdoor_temp, radiation, etc.)
        weather_parameters: List of weather parameters to correlate with.
                           If None, uses all numeric columns.
    
    Returns:
        Dictionary mapping weather parameter to correlation coefficient
    
    Example:
        >>> indoor_temp = pd.Series([20, 22, 25, 28])
        >>> weather = pd.DataFrame({
        ...     'outdoor_temp': [15, 18, 22, 26],
        ...     'radiation': [200, 400, 800, 1000]
        ... })
        >>> calculate_weather_correlations(indoor_temp, weather)
        {'outdoor_temp': 0.98, 'radiation': 0.95}
    """
    if weather_parameters is None:
        weather_parameters = weather_df.select_dtypes(include=[np.number]).columns.tolist()
    
    correlations = {}
    
    for param in weather_parameters:
        if param not in weather_df.columns:
            continue
        
        corr = calculate_correlation(indoor_data, weather_df[param])
        correlations[param] = round(corr, 3)
    
    return correlations


def calculate_non_compliance_weather_stats(
    weather_df: pd.DataFrame,
    non_compliance_mask: pd.Series,
    weather_parameters: Optional[List[str]] = None
) -> Dict[str, Dict[str, float]]:
    """
    Calculate weather statistics during non-compliance periods.
    
    Args:
        weather_df: DataFrame with weather data
        non_compliance_mask: Boolean series where True = non-compliant
        weather_parameters: Weather parameters to analyze
    
    Returns:
        Dictionary of weather parameter -> {mean, min, max, std}
    
    Example:
        Useful to answer: "What was the outdoor temperature when indoor temp exceeded limits?"
    """
    if weather_parameters is None:
        weather_parameters = weather_df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Align weather data with non-compliance mask
    aligned_weather = weather_df.reindex(non_compliance_mask.index)
    
    # Filter to non-compliance periods only
    non_compliance_weather = aligned_weather[non_compliance_mask]
    
    stats = {}
    
    for param in weather_parameters:
        if param not in non_compliance_weather.columns:
            continue
        
        param_data = non_compliance_weather[param].dropna()
        
        if len(param_data) == 0:
            continue
        
        stats[param] = {
            'mean': round(float(param_data.mean()), 2),
            'min': round(float(param_data.min()), 2),
            'max': round(float(param_data.max()), 2),
            'std': round(float(param_data.std()), 2),
            'median': round(float(param_data.median()), 2)
        }
    
    return stats


def identify_weather_driven_issues(
    correlations: Dict[str, float],
    correlation_threshold: float = 0.5
) -> List[Dict[str, Any]]:
    """
    Identify which weather factors are driving non-compliance.
    
    Args:
        correlations: Dictionary of weather parameter -> correlation coefficient
        correlation_threshold: Minimum absolute correlation to consider significant
    
    Returns:
        List of weather factors with significant correlations
    """
    issues = []
    
    for param, corr in correlations.items():
        if abs(corr) >= correlation_threshold:
            direction = 'positive' if corr > 0 else 'negative'
            strength = 'strong' if abs(corr) >= 0.7 else 'moderate'
            
            issues.append({
                'weather_parameter': param,
                'correlation': corr,
                'direction': direction,
                'strength': strength,
                'interpretation': _interpret_correlation(param, corr)
            })
    
    # Sort by absolute correlation (strongest first)
    issues.sort(key=lambda x: abs(x['correlation']), reverse=True)
    
    return issues


def _interpret_correlation(weather_param: str, correlation: float) -> str:
    """
    Generate human-readable interpretation of weather correlation.
    
    Args:
        weather_param: Name of weather parameter
        correlation: Correlation coefficient
    
    Returns:
        Interpretation string
    """
    param_lower = weather_param.lower()
    
    if abs(correlation) < 0.3:
        return f"{weather_param} has weak influence"
    
    # Positive correlation
    if correlation > 0:
        if 'temp' in param_lower or 'temperature' in param_lower:
            return f"Indoor issues worsen when outdoor temperature increases (r={correlation:.2f})"
        elif 'radiation' in param_lower or 'solar' in param_lower:
            return f"Indoor issues worsen with increased solar radiation (r={correlation:.2f})"
        else:
            return f"Indoor issues increase with higher {weather_param} (r={correlation:.2f})"
    
    # Negative correlation
    else:
        if 'temp' in param_lower or 'temperature' in param_lower:
            return f"Indoor issues worsen when outdoor temperature decreases (r={correlation:.2f})"
        elif 'wind' in param_lower:
            return f"Higher wind speeds reduce indoor issues (r={correlation:.2f})"
        else:
            return f"Indoor issues increase with lower {weather_param} (r={correlation:.2f})"


def calculate_seasonal_correlations(
    indoor_data: pd.Series,
    weather_df: pd.DataFrame,
    weather_param: str
) -> Dict[str, float]:
    """
    Calculate correlations by season.
    
    Args:
        indoor_data: Indoor parameter time series
        weather_df: Weather data
        weather_param: Weather parameter to correlate
    
    Returns:
        Dictionary of season -> correlation
    """
    if not isinstance(indoor_data.index, pd.DatetimeIndex):
        return {}
    
    # Define seasons (Northern Hemisphere)
    def get_season(month):
        if month in [12, 1, 2]:
            return 'winter'
        elif month in [3, 4, 5]:
            return 'spring'
        elif month in [6, 7, 8]:
            return 'summer'
        else:
            return 'autumn'
    
    indoor_data_with_season = indoor_data.to_frame('value')
    indoor_data_with_season['season'] = indoor_data.index.month.map(get_season)
    
    seasonal_corrs = {}
    
    for season in ['winter', 'spring', 'summer', 'autumn']:
        season_data = indoor_data_with_season[indoor_data_with_season['season'] == season]['value']
        
        if len(season_data) < 3:
            continue
        
        corr = calculate_correlation(season_data, weather_df[weather_param])
        seasonal_corrs[season] = corr
    
    return seasonal_corrs
