"""
Unit tests for compliance calculator module.

Tests pure logic for calculating compliance rates and identifying violations.
"""

import pytest
import pandas as pd
import numpy as np

from src.core.analytics.ieq.library.metrics.compliance_calculator import (
    calculate_compliance_rate,
    calculate_compliance_metrics,
    identify_violations,
    calculate_hour_based_compliance
)


class TestCalculateComplianceRate:
    """Tests for calculate_compliance_rate function."""
    
    def test_full_compliance(self):
        """Test with 100% compliance."""
        compliance = pd.Series([True, True, True, True])
        rate = calculate_compliance_rate(compliance)
        
        assert rate == 100.0
    
    def test_no_compliance(self):
        """Test with 0% compliance."""
        compliance = pd.Series([False, False, False, False])
        rate = calculate_compliance_rate(compliance)
        
        assert rate == 0.0
    
    def test_partial_compliance(self):
        """Test with partial compliance."""
        compliance = pd.Series([True, True, False, False])
        rate = calculate_compliance_rate(compliance)
        
        assert rate == 50.0
    
    def test_75_percent_compliance(self):
        """Test with 75% compliance."""
        compliance = pd.Series([True, True, True, False])
        rate = calculate_compliance_rate(compliance)
        
        assert rate == 75.0
    
    def test_single_compliant(self):
        """Test with single compliant value."""
        compliance = pd.Series([True])
        rate = calculate_compliance_rate(compliance)
        
        assert rate == 100.0
    
    def test_single_non_compliant(self):
        """Test with single non-compliant value."""
        compliance = pd.Series([False])
        rate = calculate_compliance_rate(compliance)
        
        assert rate == 0.0
    
    def test_empty_series_returns_zero(self):
        """Test that empty series returns 0."""
        compliance = pd.Series([], dtype=bool)
        rate = calculate_compliance_rate(compliance)
        
        assert rate == 0.0
    
    def test_large_dataset(self):
        """Test with large dataset."""
        # 850 True, 150 False = 85%
        compliance = pd.Series([True] * 850 + [False] * 150)
        rate = calculate_compliance_rate(compliance)
        
        assert rate == 85.0
    
    def test_floating_point_precision(self):
        """Test floating point precision in calculation."""
        # 2 out of 3 = 66.666...%
        compliance = pd.Series([True, True, False])
        rate = calculate_compliance_rate(compliance)
        
        assert 66.6 < rate < 66.7


class TestCalculateComplianceMetrics:
    """Tests for calculate_compliance_metrics function."""
    
    def test_full_metrics_all_compliant(self):
        """Test full metrics with all compliant data."""
        compliance = pd.Series([True] * 10)
        metrics = calculate_compliance_metrics(compliance)
        
        assert metrics['total_points'] == 10
        assert metrics['compliant_points'] == 10
        assert metrics['non_compliant_points'] == 0
        assert metrics['compliance_rate'] == 100.0
    
    def test_full_metrics_no_compliance(self):
        """Test full metrics with no compliant data."""
        compliance = pd.Series([False] * 10)
        metrics = calculate_compliance_metrics(compliance)
        
        assert metrics['total_points'] == 10
        assert metrics['compliant_points'] == 0
        assert metrics['non_compliant_points'] == 10
        assert metrics['compliance_rate'] == 0.0
    
    def test_full_metrics_mixed(self):
        """Test full metrics with mixed compliance."""
        compliance = pd.Series([True, True, True, False, False])
        metrics = calculate_compliance_metrics(compliance)
        
        assert metrics['total_points'] == 5
        assert metrics['compliant_points'] == 3
        assert metrics['non_compliant_points'] == 2
        assert metrics['compliance_rate'] == 60.0
    
    def test_empty_series_metrics(self):
        """Test metrics with empty series."""
        compliance = pd.Series([], dtype=bool)
        metrics = calculate_compliance_metrics(compliance)
        
        assert metrics['total_points'] == 0
        assert metrics['compliant_points'] == 0
        assert metrics['non_compliant_points'] == 0
        assert metrics['compliance_rate'] == 0.0


class TestIdentifyViolations:
    """Tests for identify_violations function."""
    
    def test_no_violations(self):
        """Test when there are no violations."""
        data = pd.Series([22, 23, 24], index=[0, 1, 2])
        compliance = pd.Series([True, True, True], index=[0, 1, 2])
        
        violations = identify_violations(data, compliance, 'temperature')
        
        assert len(violations) == 0
    
    def test_all_violations(self):
        """Test when all values are violations."""
        data = pd.Series([28, 29, 30], index=[0, 1, 2])
        compliance = pd.Series([False, False, False], index=[0, 1, 2])
        
        violations = identify_violations(data, compliance, 'temperature')
        
        assert len(violations) == 3
        assert all(v['parameter'] == 'temperature' for v in violations)
    
    def test_mixed_violations(self):
        """Test with some violations."""
        data = pd.Series([22, 28, 23, 29], index=[0, 1, 2, 3])
        compliance = pd.Series([True, False, True, False], index=[0, 1, 2, 3])
        
        violations = identify_violations(data, compliance, 'temperature')
        
        assert len(violations) == 2
        assert violations[0]['value'] == 28
        assert violations[1]['value'] == 29
    
    def test_violation_structure(self):
        """Test that violation dict has correct structure."""
        data = pd.Series([1200], index=[0])
        compliance = pd.Series([False], index=[0])
        
        violations = identify_violations(data, compliance, 'co2')
        
        assert len(violations) == 1
        v = violations[0]
        
        assert 'index' in v
        assert 'value' in v
        assert 'parameter' in v
        assert v['parameter'] == 'co2'
        assert v['value'] == 1200
    
    def test_with_datetime_index(self):
        """Test with datetime index."""
        dates = pd.date_range('2024-01-01', periods=3, freq='H')
        data = pd.Series([28, 29, 30], index=dates)
        compliance = pd.Series([False, False, False], index=dates)
        
        violations = identify_violations(data, compliance, 'temperature')
        
        assert len(violations) == 3
        # Index should be preserved (as string if datetime)
        assert all('index' in v for v in violations)
    
    def test_preserves_index_order(self):
        """Test that violations preserve index order."""
        data = pd.Series([28, 23, 29, 24], index=[10, 20, 30, 40])
        compliance = pd.Series([False, True, False, True], index=[10, 20, 30, 40])
        
        violations = identify_violations(data, compliance, 'temperature')
        
        assert len(violations) == 2
        assert violations[0]['index'] == 10
        assert violations[1]['index'] == 30
    
    def test_float_values_in_violations(self):
        """Test that float values are preserved."""
        data = pd.Series([28.5, 29.7], index=[0, 1])
        compliance = pd.Series([False, False], index=[0, 1])
        
        violations = identify_violations(data, compliance, 'temperature')
        
        assert violations[0]['value'] == 28.5
        assert violations[1]['value'] == 29.7


class TestCalculateHourBasedCompliance:
    """Tests for calculate_hour_based_compliance function."""
    
    def test_all_hours_compliant(self):
        """Test when all hours are compliant."""
        dates = pd.date_range('2024-01-01', periods=24, freq='H')
        compliance = pd.Series([True] * 24, index=dates)
        
        result = calculate_hour_based_compliance(compliance)
        
        assert result['total_hours'] == 24
        assert result['compliant_hours'] == 24
        assert result['compliance_rate'] == 100.0
    
    def test_no_hours_compliant(self):
        """Test when no hours are compliant."""
        dates = pd.date_range('2024-01-01', periods=24, freq='H')
        compliance = pd.Series([False] * 24, index=dates)
        
        result = calculate_hour_based_compliance(compliance)
        
        assert result['total_hours'] == 24
        assert result['compliant_hours'] == 0
        assert result['compliance_rate'] == 0.0
    
    def test_partial_compliance(self):
        """Test with partial compliance."""
        dates = pd.date_range('2024-01-01', periods=100, freq='H')
        compliance = pd.Series([True] * 75 + [False] * 25, index=dates)
        
        result = calculate_hour_based_compliance(compliance)
        
        assert result['total_hours'] == 100
        assert result['compliant_hours'] == 75
        assert result['compliance_rate'] == 75.0
    
    def test_non_datetime_index_returns_none(self):
        """Test that non-datetime index returns None or handles gracefully."""
        compliance = pd.Series([True, False, True, False], index=[0, 1, 2, 3])
        
        # Should handle non-datetime index
        result = calculate_hour_based_compliance(compliance)
        
        # Might return None or basic metrics
        assert isinstance(result, dict)
    
    def test_multi_day_period(self):
        """Test with multi-day period."""
        # 3 days = 72 hours
        dates = pd.date_range('2024-01-01', periods=72, freq='H')
        # 60 compliant, 12 non-compliant
        compliance = pd.Series([True] * 60 + [False] * 12, index=dates)
        
        result = calculate_hour_based_compliance(compliance)
        
        assert result['total_hours'] == 72
        assert result['compliant_hours'] == 60
        assert abs(result['compliance_rate'] - 83.333) < 0.01


class TestComplianceIntegration:
    """Integration tests for compliance calculations."""
    
    def test_complete_workflow(self):
        """Test complete compliance analysis workflow."""
        # Create test data
        dates = pd.date_range('2024-01-01', periods=100, freq='H')
        temperatures = pd.Series([20 + i % 10 for i in range(100)], index=dates)
        
        # Evaluate compliance (20-26°C)
        compliance = (temperatures >= 20) & (temperatures <= 26)
        
        # Calculate metrics
        metrics = calculate_compliance_metrics(compliance)
        violations = identify_violations(temperatures, compliance, 'temperature')
        hour_metrics = calculate_hour_based_compliance(compliance)
        
        # Verify
        assert metrics['compliance_rate'] == hour_metrics['compliance_rate']
        assert len(violations) == metrics['non_compliant_points']
        assert metrics['total_points'] == 100
    
    def test_en16798_category_i_simulation(self):
        """Simulate EN16798 Category I compliance check."""
        # Simulate 1 week of data
        dates = pd.date_range('2024-01-01', periods=168, freq='H')  # 1 week
        
        # Simulate temperature with some violations
        temps = pd.Series([
            21 + np.sin(i * 2 * np.pi / 24) * 1.5  # Daily cycle
            for i in range(168)
        ], index=dates)
        
        # EN16798 Cat I: 21-23°C
        compliance = (temps >= 21) & (temps <= 23)
        
        # Calculate all metrics
        rate = calculate_compliance_rate(compliance)
        metrics = calculate_compliance_metrics(compliance)
        violations = identify_violations(temps, compliance, 'temperature')
        hour_metrics = calculate_hour_based_compliance(compliance)
        
        # Assertions
        assert 0 <= rate <= 100
        assert metrics['total_points'] == 168
        assert len(violations) <= 168
        assert hour_metrics['total_hours'] == 168
        assert metrics['compliance_rate'] == rate
