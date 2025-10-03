"""
Test boolean-float correlation functionality for non-compliance vs weather analysis.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.core.analytics.ieq.library.correlations import (
    calculate_boolean_float_correlation,
    calculate_multiple_boolean_float_correlations
)


class TestBooleanFloatCorrelation:
    """Test suite for boolean-float correlation calculations."""

    def test_perfect_positive_correlation(self):
        """Test perfect positive correlation between non-compliance and temperature."""
        # Non-compliance increases with temperature
        timestamps = pd.date_range('2024-01-01', periods=10, freq='H')
        non_compliance = pd.Series([False, False, False, False, False, True, True, True, True, True], index=timestamps)
        temperature = pd.Series([20, 21, 22, 23, 24, 25, 26, 27, 28, 29], index=timestamps)

        result = calculate_boolean_float_correlation(non_compliance, temperature)

        assert result['correlation'] > 0.9, "Should have strong positive correlation"
        assert result['mean_when_true'] > result['mean_when_false'], "Temperature should be higher when non-compliant"
        assert result['n_true'] == 5
        assert result['n_false'] == 5

    def test_negative_correlation(self):
        """Test negative correlation (non-compliance decreases with temperature)."""
        timestamps = pd.date_range('2024-01-01', periods=10, freq='H')
        non_compliance = pd.Series([True, True, True, True, True, False, False, False, False, False], index=timestamps)
        temperature = pd.Series([15, 16, 17, 18, 19, 25, 26, 27, 28, 29], index=timestamps)

        result = calculate_boolean_float_correlation(non_compliance, temperature)

        assert result['correlation'] < -0.9, "Should have strong negative correlation"
        assert result['mean_when_true'] < result['mean_when_false'], "Temperature should be lower when non-compliant"

    def test_no_correlation(self):
        """Test case with no correlation."""
        timestamps = pd.date_range('2024-01-01', periods=10, freq='H')
        non_compliance = pd.Series([True, False, True, False, True, False, True, False, True, False], index=timestamps)
        temperature = pd.Series([20, 25, 21, 26, 22, 27, 23, 28, 24, 29], index=timestamps)

        result = calculate_boolean_float_correlation(non_compliance, temperature)

        assert abs(result['correlation']) < 0.3, "Should have weak correlation"

    def test_realistic_overheating_scenario(self):
        """Test realistic scenario: overheating correlates with outdoor temperature."""
        # Generate realistic data: overheating more likely at high outdoor temps
        np.random.seed(42)
        timestamps = pd.date_range('2024-06-01', periods=100, freq='H')

        # Outdoor temperature varies between 15-35°C
        outdoor_temp = pd.Series(
            20 + 10 * np.sin(np.linspace(0, 2*np.pi, 100)) + np.random.normal(0, 2, 100),
            index=timestamps
        )

        # Non-compliance more likely when temp > 28°C
        non_compliance = pd.Series(
            (outdoor_temp > 28) & (np.random.random(100) > 0.3),  # 70% probability when hot
            index=timestamps
        )

        result = calculate_boolean_float_correlation(non_compliance, outdoor_temp)

        assert result['correlation'] > 0.3, "Should show positive correlation with outdoor temp"
        assert result['mean_when_true'] > 28, "Average temp during non-compliance should be high"
        assert result['p_value'] < 0.05, "Result should be statistically significant"

    def test_solar_radiation_correlation(self):
        """Test correlation between non-compliance and solar radiation."""
        np.random.seed(42)
        timestamps = pd.date_range('2024-06-01', periods=100, freq='H')

        # Solar radiation varies 0-1000 W/m²
        solar_radiation = pd.Series(
            500 + 400 * np.sin(np.linspace(0, 4*np.pi, 100)) + np.random.normal(0, 50, 100),
            index=timestamps
        )
        solar_radiation = solar_radiation.clip(0, 1000)

        # Non-compliance more likely with high solar radiation
        non_compliance = pd.Series(
            (solar_radiation > 700) & (np.random.random(100) > 0.4),
            index=timestamps
        )

        result = calculate_boolean_float_correlation(non_compliance, solar_radiation)

        assert result['correlation'] > 0.2, "Should show positive correlation with solar radiation"
        assert result['mean_when_true'] > result['mean_when_false']

    def test_multiple_weather_parameters(self):
        """Test correlation with multiple weather parameters simultaneously."""
        timestamps = pd.date_range('2024-06-01', periods=50, freq='H')

        # Create weather dataframe
        weather_df = pd.DataFrame({
            'outdoor_temp': 20 + 10 * np.sin(np.linspace(0, np.pi, 50)),
            'solar_radiation': 500 + 300 * np.sin(np.linspace(0, np.pi, 50)),
            'wind_speed': 2 + 3 * np.random.random(50),
            'humidity': 50 + 20 * np.random.random(50)
        }, index=timestamps)

        # Non-compliance correlated with temp and radiation
        non_compliance = pd.Series(
            (weather_df['outdoor_temp'] > 27) | (weather_df['solar_radiation'] > 700),
            index=timestamps
        )

        results = calculate_multiple_boolean_float_correlations(
            non_compliance,
            weather_df
        )

        assert 'outdoor_temp' in results
        assert 'solar_radiation' in results
        assert results['outdoor_temp']['correlation'] > 0
        assert results['solar_radiation']['correlation'] > 0

    def test_insufficient_data(self):
        """Test handling of insufficient data."""
        timestamps = pd.date_range('2024-01-01', periods=2, freq='H')
        non_compliance = pd.Series([True, False], index=timestamps)
        temperature = pd.Series([20, 25], index=timestamps)

        result = calculate_boolean_float_correlation(non_compliance, temperature)

        assert result['correlation'] == 0.0
        assert result['interpretation'] == 'Insufficient data for correlation analysis'

    def test_all_true_or_all_false(self):
        """Test case where boolean series is all True or all False."""
        timestamps = pd.date_range('2024-01-01', periods=10, freq='H')
        non_compliance = pd.Series([True] * 10, index=timestamps)
        temperature = pd.Series(range(20, 30), index=timestamps)

        result = calculate_boolean_float_correlation(non_compliance, temperature)

        # Should handle gracefully (no variance in boolean)
        assert result is not None

    def test_nan_handling(self):
        """Test handling of NaN values in data."""
        timestamps = pd.date_range('2024-01-01', periods=10, freq='H')
        non_compliance = pd.Series([True, False, True, np.nan, True, False, True, False, True, False], index=timestamps)
        temperature = pd.Series([20, 25, 30, 35, np.nan, 22, 27, 32, 29, 24], index=timestamps)

        result = calculate_boolean_float_correlation(non_compliance, temperature)

        # Should drop NaN and calculate on remaining data
        assert result['n_true'] + result['n_false'] <= 8  # Some data dropped

    def test_effect_size_calculation(self):
        """Test Cohen's d effect size calculation."""
        timestamps = pd.date_range('2024-01-01', periods=20, freq='H')

        # Clear difference in means
        non_compliance = pd.Series([True]*10 + [False]*10, index=timestamps)
        temperature = pd.Series([30]*10 + [20]*10, index=timestamps)

        result = calculate_boolean_float_correlation(non_compliance, temperature)

        assert abs(result['effect_size']) > 2, "Should show large effect size"
        assert 'large practical significance' in result['interpretation'].lower()

    def test_statistical_significance(self):
        """Test p-value and statistical significance."""
        np.random.seed(42)
        timestamps = pd.date_range('2024-01-01', periods=100, freq='H')

        # Strong correlation should be significant
        temperature = pd.Series(20 + 10 * np.linspace(0, 1, 100), index=timestamps)
        non_compliance = pd.Series(temperature > 25, index=timestamps)

        result = calculate_boolean_float_correlation(non_compliance, temperature)

        assert result['p_value'] < 0.05, "Strong correlation should be statistically significant"
        assert 'statistically significant' in result['interpretation']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
