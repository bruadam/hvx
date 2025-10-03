"""
Unit tests for unidirectional evaluator module.

Tests the pure logic for evaluating single threshold compliance.
"""

import pytest
import pandas as pd
import numpy as np

from src.core.analytics.ieq.library.evaluators.unidirectional_evaluator import (
    evaluate_unidirectional_ascending,
    evaluate_unidirectional_descending,
    parse_unidirectional_config,
    determine_direction
)


class TestEvaluateUnidirectionalAscending:
    """Tests for evaluate_unidirectional_ascending (values >= threshold)."""
    
    def test_all_values_above_threshold(self):
        """Test when all values are above threshold."""
        data = pd.Series([20, 22, 24, 26, 28])
        result = evaluate_unidirectional_ascending(data, 18)
        
        assert result.all(), "All values should be compliant"
        assert len(result) == len(data)
    
    def test_all_values_below_threshold(self):
        """Test when all values are below threshold."""
        data = pd.Series([10, 12, 14, 16])
        result = evaluate_unidirectional_ascending(data, 18)
        
        assert not result.any(), "No values should be compliant"
    
    def test_mixed_values(self):
        """Test with mixed values above and below threshold."""
        data = pd.Series([16, 18, 20, 22])
        result = evaluate_unidirectional_ascending(data, 18)
        
        expected = pd.Series([False, True, True, True])
        pd.testing.assert_series_equal(result, expected, check_names=False)
    
    def test_threshold_value_inclusive(self):
        """Test that threshold value is compliant (inclusive)."""
        data = pd.Series([18.0])
        result = evaluate_unidirectional_ascending(data, 18)
        
        assert result.iloc[0] == True, "Threshold value should be compliant"
    
    def test_with_negative_threshold(self):
        """Test with negative threshold."""
        data = pd.Series([-10, -5, 0, 5])
        result = evaluate_unidirectional_ascending(data, -3)
        
        expected = pd.Series([False, False, True, True])
        pd.testing.assert_series_equal(result, expected, check_names=False)
    
    def test_empty_series(self):
        """Test with empty series."""
        data = pd.Series([], dtype=float)
        result = evaluate_unidirectional_ascending(data, 18)
        
        assert len(result) == 0
        assert result.dtype == bool


class TestEvaluateUnidirectionalDescending:
    """Tests for evaluate_unidirectional_descending (values <= threshold)."""
    
    def test_all_values_below_threshold(self):
        """Test when all values are below threshold."""
        data = pd.Series([600, 700, 800, 900])
        result = evaluate_unidirectional_descending(data, 1000)
        
        assert result.all(), "All values should be compliant"
    
    def test_all_values_above_threshold(self):
        """Test when all values are above threshold."""
        data = pd.Series([1100, 1200, 1300])
        result = evaluate_unidirectional_descending(data, 1000)
        
        assert not result.any(), "No values should be compliant"
    
    def test_mixed_values(self):
        """Test with mixed values."""
        data = pd.Series([800, 1000, 1200, 1400])
        result = evaluate_unidirectional_descending(data, 1000)
        
        expected = pd.Series([True, True, False, False])
        pd.testing.assert_series_equal(result, expected, check_names=False)
    
    def test_threshold_value_inclusive(self):
        """Test that threshold value is compliant (inclusive)."""
        data = pd.Series([1000.0])
        result = evaluate_unidirectional_descending(data, 1000)
        
        assert result.iloc[0] == True, "Threshold value should be compliant"
    
    def test_co2_use_case(self):
        """Test realistic CO2 use case."""
        # CO2 should be <= 1000 ppm
        co2_data = pd.Series([600, 800, 950, 1000, 1050, 1200])
        result = evaluate_unidirectional_descending(co2_data, 1000)
        
        expected = pd.Series([True, True, True, True, False, False])
        pd.testing.assert_series_equal(result, expected, check_names=False)


class TestParseUnidirectionalConfig:
    """Tests for parse_unidirectional_config function."""
    
    def test_parse_limit_as_number(self):
        """Test parsing with 'limit' as direct number."""
        config = {'limit': 1000}
        result = parse_unidirectional_config(config)
        
        assert result == 1000.0
        assert isinstance(result, float)
    
    def test_parse_limit_as_float(self):
        """Test parsing with 'limit' as float."""
        config = {'limit': 26.5}
        result = parse_unidirectional_config(config)
        
        assert result == 26.5
    
    def test_parse_limit_dict_with_value(self):
        """Test parsing with 'limit' as dict containing 'value'."""
        config = {
            'limit': {
                'value': 1000,
                'unit': 'ppm'
            }
        }
        result = parse_unidirectional_config(config)
        
        assert result == 1000.0
    
    def test_parse_threshold(self):
        """Test parsing with 'threshold' key."""
        config = {'threshold': 18.0}
        result = parse_unidirectional_config(config)
        
        assert result == 18.0
    
    def test_parse_value(self):
        """Test parsing with 'value' key."""
        config = {'value': 25.0}
        result = parse_unidirectional_config(config)
        
        assert result == 25.0
    
    def test_parse_negative_value(self):
        """Test parsing with negative value."""
        config = {'limit': -5.5}
        result = parse_unidirectional_config(config)
        
        assert result == -5.5
    
    def test_parse_zero(self):
        """Test parsing with zero value."""
        config = {'limit': 0}
        result = parse_unidirectional_config(config)
        
        assert result == 0.0
    
    def test_missing_threshold_raises_error(self):
        """Test that missing threshold raises ValueError."""
        config = {'description': 'Test rule'}
        
        with pytest.raises(ValueError, match="must include"):
            parse_unidirectional_config(config)
    
    def test_empty_config_raises_error(self):
        """Test that empty config raises ValueError."""
        config = {}
        
        with pytest.raises(ValueError):
            parse_unidirectional_config(config)
    
    def test_parse_priority_order(self):
        """Test that 'limit' takes priority over other keys."""
        config = {
            'limit': 1000,
            'threshold': 800,
            'value': 1200
        }
        result = parse_unidirectional_config(config)
        
        assert result == 1000.0, "'limit' should take priority"


class TestDetermineDirection:
    """Tests for determine_direction function."""
    
    def test_explicit_ascending(self):
        """Test with explicit ascending mode."""
        config = {'mode': 'unidirectional_ascending'}
        result = determine_direction(config)
        
        assert result == 'ascending'
    
    def test_explicit_descending(self):
        """Test with explicit descending mode."""
        config = {'mode': 'unidirectional_descending'}
        result = determine_direction(config)
        
        assert result == 'descending'
    
    def test_temperature_feature_defaults_ascending(self):
        """Test that temperature defaults to ascending (>= threshold)."""
        config = {'feature': 'temperature'}
        result = determine_direction(config)
        
        assert result == 'ascending'
    
    def test_co2_feature_defaults_descending(self):
        """Test that CO2 defaults to descending (<= threshold)."""
        config = {'feature': 'co2'}
        result = determine_direction(config)
        
        assert result == 'descending'
    
    def test_co2_ppm_feature_defaults_descending(self):
        """Test that co2_ppm defaults to descending."""
        config = {'feature': 'co2_ppm'}
        result = determine_direction(config)
        
        assert result == 'descending'
    
    def test_parameter_instead_of_feature(self):
        """Test using 'parameter' key instead of 'feature'."""
        config = {'parameter': 'co2'}
        result = determine_direction(config)
        
        assert result == 'descending'
    
    def test_case_insensitive_feature(self):
        """Test case-insensitive feature matching."""
        config = {'feature': 'CO2'}
        result = determine_direction(config)
        
        assert result == 'descending'
    
    def test_no_hints_defaults_ascending(self):
        """Test default when no hints are present."""
        config = {'description': 'Some rule'}
        result = determine_direction(config)
        
        assert result == 'ascending'


class TestUnidirectionalIntegration:
    """Integration tests for unidirectional evaluation."""
    
    def test_co2_workflow(self):
        """Test complete CO2 evaluation workflow."""
        config = {
            'description': 'CO2 limit compliance',
            'feature': 'co2',
            'limit': 1000,
            'mode': 'unidirectional_descending'
        }
        
        # Parse
        threshold = parse_unidirectional_config(config)
        direction = determine_direction(config)
        
        # Sample CO2 data
        co2_data = pd.Series([
            600, 750, 850, 950, 1000,   # Compliant
            1050, 1100, 1200, 1350       # Non-compliant
        ])
        
        # Evaluate
        if direction == 'descending':
            result = evaluate_unidirectional_descending(co2_data, threshold)
        else:
            result = evaluate_unidirectional_ascending(co2_data, threshold)
        
        # Verify
        assert result[:5].all(), "First 5 should be compliant"
        assert not result[5:].any(), "Last 4 should be non-compliant"
    
    def test_temperature_workflow(self):
        """Test complete temperature evaluation workflow."""
        config = {
            'description': 'Minimum temperature',
            'feature': 'temperature',
            'limit': 18,
            'mode': 'unidirectional_ascending'
        }
        
        threshold = parse_unidirectional_config(config)
        direction = determine_direction(config)
        
        temp_data = pd.Series([16, 17, 18, 19, 20, 21])
        
        if direction == 'ascending':
            result = evaluate_unidirectional_ascending(temp_data, threshold)
        else:
            result = evaluate_unidirectional_descending(temp_data, threshold)
        
        expected = pd.Series([False, False, True, True, True, True])
        pd.testing.assert_series_equal(result, expected, check_names=False)
    
    def test_with_real_timeseries(self):
        """Test with realistic time series."""
        dates = pd.date_range('2024-01-01 08:00', periods=12, freq='H')
        co2_values = pd.Series([
            650, 750, 850, 950, 1050, 1150,
            1200, 1100, 1000, 900, 800, 700
        ], index=dates)
        
        config = {'limit': 1000, 'feature': 'co2'}
        
        threshold = parse_unidirectional_config(config)
        result = evaluate_unidirectional_descending(co2_values, threshold)
        
        # First 4 compliant, next 3 not, last 5 compliant
        assert result[:4].all()
        assert not result[4:7].any()
        assert result[7:].all()
        assert result.index.equals(dates)
