"""
Unit tests for bidirectional evaluator module.

Tests the pure logic for evaluating min/max range compliance.
"""

import pytest
import pandas as pd
import numpy as np

from src.core.analytics.ieq.library.evaluators.bidirectional_evaluator import (
    evaluate_bidirectional,
    parse_bidirectional_config
)


class TestEvaluateBidirectional:
    """Tests for evaluate_bidirectional function."""
    
    def test_all_values_within_range(self):
        """Test when all values are within acceptable range."""
        data = pd.Series([20, 21, 22, 23, 24, 25])
        result = evaluate_bidirectional(data, 20, 26)
        
        assert result.all(), "All values should be compliant"
        assert len(result) == len(data)
        assert result.dtype == bool
    
    def test_all_values_outside_range(self):
        """Test when all values are outside acceptable range."""
        data = pd.Series([10, 12, 14, 30, 32, 35])
        result = evaluate_bidirectional(data, 20, 26)
        
        assert not result.any(), "No values should be compliant"
        assert len(result) == len(data)
    
    def test_mixed_compliance(self):
        """Test with mix of compliant and non-compliant values."""
        data = pd.Series([18, 20, 22, 24, 26, 28])
        result = evaluate_bidirectional(data, 20, 26)
        
        expected = pd.Series([False, True, True, True, True, False])
        pd.testing.assert_series_equal(result, expected, check_names=False)
    
    def test_boundary_values_inclusive(self):
        """Test that boundary values are inclusive."""
        data = pd.Series([20, 26])
        result = evaluate_bidirectional(data, 20, 26)
        
        assert result.all(), "Boundary values should be compliant (inclusive)"
    
    def test_values_just_outside_boundaries(self):
        """Test values just outside boundaries."""
        data = pd.Series([19.9, 26.1])
        result = evaluate_bidirectional(data, 20, 26)
        
        assert not result.any(), "Values just outside should be non-compliant"
    
    def test_empty_series(self):
        """Test with empty series."""
        data = pd.Series([], dtype=float)
        result = evaluate_bidirectional(data, 20, 26)
        
        assert len(result) == 0
        assert result.dtype == bool
    
    def test_single_value(self):
        """Test with single value."""
        data = pd.Series([23.0])
        result = evaluate_bidirectional(data, 20, 26)
        
        assert result.iloc[0] == True
        assert len(result) == 1
    
    def test_with_datetime_index(self):
        """Test with datetime index."""
        dates = pd.date_range('2024-01-01', periods=5, freq='H')
        data = pd.Series([21, 22, 23, 24, 25], index=dates)
        result = evaluate_bidirectional(data, 20, 26)
        
        assert result.all()
        assert (result.index == dates).all()
    
    def test_negative_range(self):
        """Test with negative value range."""
        data = pd.Series([-5, -3, -1, 1, 3])
        result = evaluate_bidirectional(data, -4, 2)
        
        expected = pd.Series([False, True, True, True, False])
        pd.testing.assert_series_equal(result, expected, check_names=False)
    
    def test_float_precision(self):
        """Test with floating point precision edge cases."""
        data = pd.Series([19.999999, 20.000001, 25.999999, 26.000001])
        result = evaluate_bidirectional(data, 20.0, 26.0)
        
        # First and last should be non-compliant, middle two compliant
        expected = pd.Series([False, True, True, False])
        pd.testing.assert_series_equal(result, expected, check_names=False)
    
    def test_equal_min_max(self):
        """Test when min equals max (single acceptable value)."""
        data = pd.Series([22, 23, 24])
        result = evaluate_bidirectional(data, 23, 23)
        
        expected = pd.Series([False, True, False])
        pd.testing.assert_series_equal(result, expected, check_names=False)
    
    def test_with_nan_values(self):
        """Test behavior with NaN values."""
        data = pd.Series([20, np.nan, 22, np.nan, 24])
        result = evaluate_bidirectional(data, 20, 26)
        
        # NaN comparisons return False
        assert result.iloc[0] == True
        assert result.iloc[1] == False  # NaN
        assert result.iloc[2] == True
        assert result.iloc[3] == False  # NaN
        assert result.iloc[4] == True


class TestParseBidirectionalConfig:
    """Tests for parse_bidirectional_config function."""
    
    def test_parse_limits_lower_upper(self):
        """Test parsing with 'limits' dict containing 'lower' and 'upper'."""
        config = {
            'limits': {
                'lower': 20.0,
                'upper': 26.0
            }
        }
        result = parse_bidirectional_config(config)
        
        assert result == {'min': 20.0, 'max': 26.0}
    
    def test_parse_limits_min_max(self):
        """Test parsing with 'limits' dict containing 'min' and 'max'."""
        config = {
            'limits': {
                'min': 18.5,
                'max': 25.5
            }
        }
        result = parse_bidirectional_config(config)
        
        assert result == {'min': 18.5, 'max': 25.5}
    
    def test_parse_direct_min_max(self):
        """Test parsing with direct 'min' and 'max' keys."""
        config = {
            'min': 15.0,
            'max': 30.0
        }
        result = parse_bidirectional_config(config)
        
        assert result == {'min': 15.0, 'max': 30.0}
    
    def test_parse_limit_dict(self):
        """Test parsing with 'limit' as dict."""
        config = {
            'limit': {
                'min': 19.0,
                'max': 27.0
            }
        }
        result = parse_bidirectional_config(config)
        
        assert result == {'min': 19.0, 'max': 27.0}
    
    def test_parse_integer_values(self):
        """Test that integer values are converted to float."""
        config = {
            'limits': {
                'lower': 20,
                'upper': 26
            }
        }
        result = parse_bidirectional_config(config)
        
        assert result == {'min': 20.0, 'max': 26.0}
        assert isinstance(result['min'], float)
        assert isinstance(result['max'], float)
    
    def test_parse_negative_values(self):
        """Test parsing with negative values."""
        config = {
            'limits': {
                'lower': -10.5,
                'upper': -2.3
            }
        }
        result = parse_bidirectional_config(config)
        
        assert result == {'min': -10.5, 'max': -2.3}
    
    def test_parse_missing_limits_raises_error(self):
        """Test that missing limits raises ValueError."""
        config = {'description': 'Test rule'}
        
        with pytest.raises(ValueError, match="must include.*limits"):
            parse_bidirectional_config(config)
    
    def test_parse_incomplete_limits_raises_error(self):
        """Test that incomplete limits raise ValueError."""
        config = {
            'limits': {
                'lower': 20.0
                # Missing 'upper'
            }
        }
        
        with pytest.raises(ValueError, match="must include both"):
            parse_bidirectional_config(config)
    
    def test_parse_empty_config_raises_error(self):
        """Test that empty config raises ValueError."""
        config = {}
        
        with pytest.raises(ValueError):
            parse_bidirectional_config(config)
    
    def test_parse_with_extra_fields(self):
        """Test that extra fields are ignored."""
        config = {
            'limits': {
                'lower': 20.0,
                'upper': 26.0
            },
            'description': 'Temperature comfort',
            'feature': 'temperature',
            'period': 'heating_season'
        }
        result = parse_bidirectional_config(config)
        
        # Only min/max should be in result
        assert result == {'min': 20.0, 'max': 26.0}
        assert len(result) == 2


class TestBidirectionalIntegration:
    """Integration tests combining parsing and evaluation."""
    
    def test_full_workflow_en16798_style(self):
        """Test complete workflow with EN16798-style config."""
        # Simulate EN16798 Category I heating season config
        config = {
            'description': 'Temperature Category I heating season',
            'feature': 'temperature',
            'filter': 'opening_hours',
            'period': 'heating_season',
            'mode': 'bidirectional',
            'limits': {
                'lower': 21,
                'upper': 23
            }
        }
        
        # Parse config
        parsed = parse_bidirectional_config(config)
        
        # Sample data
        data = pd.Series([19, 20, 21, 22, 23, 24, 25])
        
        # Evaluate
        result = evaluate_bidirectional(data, parsed['min'], parsed['max'])
        
        # Check results
        expected = pd.Series([False, False, True, True, True, False, False])
        pd.testing.assert_series_equal(result, expected, check_names=False)
    
    def test_full_workflow_with_real_timeseries(self):
        """Test with realistic time series data."""
        # Create realistic temperature data
        dates = pd.date_range('2024-01-01 08:00', periods=24, freq='H')
        temperatures = pd.Series([
            19.5, 20.2, 21.0, 21.8, 22.5, 23.0,  # Morning rise
            23.2, 23.5, 23.8, 24.0, 24.2, 24.5,  # Midday
            24.8, 25.0, 25.2, 24.8, 24.5, 24.0,  # Afternoon
            23.5, 23.0, 22.5, 22.0, 21.5, 21.0   # Evening
        ], index=dates)
        
        config = {
            'limits': {'lower': 21.0, 'upper': 24.0}
        }
        
        parsed = parse_bidirectional_config(config)
        result = evaluate_bidirectional(temperatures, parsed['min'], parsed['max'])
        
        # Count compliance
        compliance_rate = (result.sum() / len(result)) * 100
        
        assert 50 < compliance_rate < 100  # Should have partial compliance
        assert len(result) == 24
        assert result.index.equals(dates)
