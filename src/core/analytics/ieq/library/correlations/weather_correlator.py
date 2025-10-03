"""
Weather Correlator

Single responsibility: Calculate correlations between indoor parameters and weather data.
Helps identify causes of non-compliance (e.g., overheating correlates with outdoor temperature).
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List, Literal


def calculate_correlation(
    indoor_data: pd.Series,
    weather_data: pd.Series,
    method: Literal['pearson', 'spearman', 'kendall'] = 'pearson'
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


def calculate_boolean_float_correlation(
    boolean_series: pd.Series,
    float_series: pd.Series,
    method: Literal['point_biserial', 'mean_comparison'] = 'point_biserial'
) -> Dict[str, Any]:
    """
    Calculate correlation between boolean timeseries and float timeseries.
    Optimized for non-compliance (boolean) vs weather parameter (float) analysis.

    Args:
        boolean_series: Boolean time series (e.g., True = non-compliant, False = compliant)
        float_series: Float time series (e.g., outdoor temperature, solar radiation)
        method: 'point_biserial' for correlation coefficient,
                'mean_comparison' for statistical comparison

    Returns:
        Dictionary containing:
            - correlation: Point-biserial correlation coefficient (-1 to 1)
            - p_value: Statistical significance p-value
            - mean_when_true: Mean of float values when boolean is True
            - mean_when_false: Mean of float values when boolean is False
            - std_when_true: Std dev of float values when boolean is True
            - std_when_false: Std dev of float values when boolean is False
            - effect_size: Cohen's d effect size
            - n_true: Number of True instances
            - n_false: Number of False instances
            - interpretation: Human-readable interpretation

    Example:
        >>> # Non-compliance vs outdoor temperature
        >>> non_compliance = pd.Series([True, True, False, False, True])
        >>> outdoor_temp = pd.Series([28.5, 30.2, 22.1, 20.5, 29.8])
        >>> result = calculate_boolean_float_correlation(non_compliance, outdoor_temp)
        >>> result['correlation']  # Positive means higher temp = more non-compliance
        0.89
    """
    # Align indices and drop NaN
    combined = pd.DataFrame({
        'boolean': boolean_series,
        'float': float_series
    }).dropna()

    if len(combined) < 3:
        return {
            'correlation': 0.0,
            'p_value': 1.0,
            'mean_when_true': None,
            'mean_when_false': None,
            'std_when_true': None,
            'std_when_false': None,
            'effect_size': 0.0,
            'n_true': 0,
            'n_false': 0,
            'interpretation': 'Insufficient data for correlation analysis'
        }

    # Convert boolean to numeric for correlation (True=1, False=0)
    bool_numeric = combined['boolean'].astype(int)
    float_values = combined['float']

    # Calculate point-biserial correlation
    from scipy import stats

    if method == 'point_biserial':
        # Point-biserial correlation (special case of Pearson for dichotomous variable)
        correlation, p_value = stats.pointbiserialr(bool_numeric, float_values)
    else:
        # Alternative: Pearson correlation
        correlation, p_value = stats.pearsonr(bool_numeric, float_values)

    # Calculate statistics for each group
    true_values = combined[combined['boolean']]['float']
    false_values = combined[~combined['boolean']]['float']

    mean_true = float(true_values.mean()) if len(true_values) > 0 else None
    mean_false = float(false_values.mean()) if len(false_values) > 0 else None
    std_true = float(true_values.std()) if len(true_values) > 0 else None
    std_false = float(false_values.std()) if len(false_values) > 0 else None

    # Calculate Cohen's d effect size
    if mean_true is not None and mean_false is not None and std_true and std_false:
        pooled_std = np.sqrt(((len(true_values) - 1) * std_true**2 +
                              (len(false_values) - 1) * std_false**2) /
                             (len(true_values) + len(false_values) - 2))
        effect_size = (mean_true - mean_false) / pooled_std if pooled_std > 0 else 0.0
    else:
        effect_size = 0.0

    # Interpret results
    interpretation = _interpret_boolean_float_correlation(
        correlation,
        p_value,
        mean_true,
        mean_false,
        effect_size
    )

    return {
        'correlation': round(float(correlation), 3) if not np.isnan(correlation) else 0.0,
        'p_value': float(p_value) if not np.isnan(p_value) else 1.0,
        'mean_when_true': round(mean_true, 2) if mean_true is not None else None,
        'mean_when_false': round(mean_false, 2) if mean_false is not None else None,
        'std_when_true': round(std_true, 2) if std_true is not None else None,
        'std_when_false': round(std_false, 2) if std_false is not None else None,
        'effect_size': round(effect_size, 3),
        'n_true': len(true_values),
        'n_false': len(false_values),
        'interpretation': interpretation
    }


def _interpret_boolean_float_correlation(
    correlation: float,
    p_value: float,
    mean_true: Optional[float],
    mean_false: Optional[float],
    effect_size: float
) -> str:
    """
    Generate human-readable interpretation of boolean-float correlation.

    Args:
        correlation: Correlation coefficient
        p_value: Statistical significance
        mean_true: Mean when boolean is True
        mean_false: Mean when boolean is False
        effect_size: Cohen's d effect size

    Returns:
        Interpretation string
    """
    if mean_true is None or mean_false is None:
        return "Insufficient data for interpretation"

    # Check statistical significance
    is_significant = p_value < 0.05

    # Assess correlation strength
    abs_corr = abs(correlation)
    if abs_corr >= 0.7:
        strength = "very strong"
    elif abs_corr >= 0.5:
        strength = "strong"
    elif abs_corr >= 0.3:
        strength = "moderate"
    elif abs_corr >= 0.1:
        strength = "weak"
    else:
        strength = "negligible"

    # Assess effect size
    abs_effect = abs(effect_size)
    if abs_effect >= 0.8:
        effect_desc = "large practical significance"
    elif abs_effect >= 0.5:
        effect_desc = "medium practical significance"
    elif abs_effect >= 0.2:
        effect_desc = "small practical significance"
    else:
        effect_desc = "negligible practical significance"

    # Build interpretation
    direction = "positive" if correlation > 0 else "negative"
    significance_note = "statistically significant" if is_significant else "not statistically significant"

    diff = mean_true - mean_false

    interpretation = (
        f"{strength.capitalize()} {direction} correlation (r={correlation:.3f}, p={p_value:.4f}). "
        f"Mean difference: {diff:+.2f} ({effect_desc}). "
        f"When True: {mean_true:.2f} ± {mean_false:.2f}. "
        f"Result is {significance_note}."
    )

    return interpretation


def calculate_multiple_boolean_float_correlations(
    boolean_series: pd.Series,
    weather_df: pd.DataFrame,
    weather_parameters: Optional[List[str]] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Calculate correlations between a boolean series and multiple weather parameters.

    Args:
        boolean_series: Boolean time series (e.g., non-compliance mask)
        weather_df: DataFrame with weather data
        weather_parameters: List of weather parameters to correlate with.
                           If None, uses all numeric columns.

    Returns:
        Dictionary mapping weather parameter to correlation results

    Example:
        >>> non_compliance = pd.Series([True, False, True, False])
        >>> weather = pd.DataFrame({
        ...     'outdoor_temp': [28, 22, 30, 20],
        ...     'radiation': [800, 400, 900, 300]
        ... })
        >>> results = calculate_multiple_boolean_float_correlations(
        ...     non_compliance, weather
        ... )
        >>> results['outdoor_temp']['correlation']
        0.95
    """
    if weather_parameters is None:
        weather_parameters = weather_df.select_dtypes(include=[np.number]).columns.tolist()

    correlations = {}

    for param in weather_parameters:
        if param not in weather_df.columns:
            continue

        corr_result = calculate_boolean_float_correlation(
            boolean_series,
            weather_df[param]
        )
        correlations[param] = corr_result

    return correlations
