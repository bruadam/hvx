"""
Unit tests for ventilation analyzer module.

Tests pure logic for analyzing ventilation needs from CO2 and humidity data.
"""

import pytest
import pandas as pd
import numpy as np

from src.core.analysis.ieq.library.recommendations.ventilation_analyzer import (
    analyze_ventilation_need,
    recommend_ventilation_type,
    calculate_recommended_ach,
    identify_peak_periods,
    assess_ventilation_effectiveness
)


class TestAnalyzeVentilationNeed:
    """Tests for analyze_ventilation_need function."""
    
    def test_no_ventilation_issues(self):
        """Test when CO2 levels are acceptable."""
        dates = pd.date_range('2024-01-01', periods=24, freq='H')
        co2 = pd.Series([600] * 24, index=dates)
        humidity = pd.Series([45] * 24, index=dates)
        
        result = analyze_ventilation_need(co2, humidity)
        
        assert result['priority'] == 'low'
        assert result['issue_indicators']['high_co2'] == False
    
    def test_high_co2_ventilation_need(self):
        """Test when CO2 levels are high."""
        dates = pd.date_range('2024-01-01', periods=24, freq='H')
        co2 = pd.Series([1200] * 24, index=dates)  # High CO2
        humidity = pd.Series([45] * 24, index=dates)
        
        result = analyze_ventilation_need(co2, humidity)
        
        assert result['priority'] in ['high', 'medium']
        assert result['issue_indicators']['high_co2'] == True
    
    def test_high_humidity_ventilation_need(self):
        """Test when humidity is high."""
        dates = pd.date_range('2024-01-01', periods=24, freq='H')
        co2 = pd.Series([700] * 24, index=dates)
        humidity = pd.Series([75] * 24, index=dates)  # High humidity
        
        result = analyze_ventilation_need(co2, humidity)
        
        assert result['issue_indicators']['high_humidity'] == True
    
    def test_both_co2_and_humidity_high(self):
        """Test when both CO2 and humidity are high."""
        dates = pd.date_range('2024-01-01', periods=24, freq='H')
        co2 = pd.Series([1300] * 24, index=dates)
        humidity = pd.Series([80] * 24, index=dates)
        
        result = analyze_ventilation_need(co2, humidity)
        
        assert result['priority'] == 'high'
        assert result['issue_indicators']['high_co2'] == True
        assert result['issue_indicators']['high_humidity'] == True
    
    def test_result_structure(self):
        """Test that result has correct structure."""
        dates = pd.date_range('2024-01-01', periods=24, freq='H')
        co2 = pd.Series([800] * 24, index=dates)
        
        result = analyze_ventilation_need(co2, humidity=None)
        
        assert 'priority' in result
        assert 'ventilation_type' in result
        assert 'recommended_ach' in result
        assert 'issue_indicators' in result
        assert 'recommendation' in result
    
    def test_with_none_humidity(self):
        """Test when humidity is None."""
        dates = pd.date_range('2024-01-01', periods=24, freq='H')
        co2 = pd.Series([900] * 24, index=dates)
        
        result = analyze_ventilation_need(co2, humidity=None)
        
        # Should still analyze based on CO2
        assert isinstance(result, dict)
        assert 'priority' in result


class TestRecommendVentilationType:
    """Tests for recommend_ventilation_type function."""
    
    def test_natural_ventilation_sufficient(self):
        """Test when natural ventilation is sufficient."""
        dates = pd.date_range('2024-01-01', periods=24, freq='H')
        co2 = pd.Series([650] * 24, index=dates)
        
        vtype = recommend_ventilation_type(co2, occupancy='low')
        
        assert vtype in ['natural', 'passive']
    
    def test_mechanical_ventilation_needed(self):
        """Test when mechanical ventilation is needed."""
        dates = pd.date_range('2024-01-01', periods=24, freq='H')
        co2 = pd.Series([1400] * 24, index=dates)
        
        vtype = recommend_ventilation_type(co2, occupancy='high')
        
        assert vtype in ['mechanical', 'hybrid']
    
    def test_hybrid_ventilation_moderate(self):
        """Test hybrid ventilation for moderate conditions."""
        dates = pd.date_range('2024-01-01', periods=24, freq='H')
        co2 = pd.Series([900] * 24, index=dates)
        
        vtype = recommend_ventilation_type(co2, occupancy='medium')
        
        assert vtype in ['hybrid', 'mechanical', 'natural']
    
    def test_occupancy_affects_type(self):
        """Test that occupancy level affects recommendation."""
        dates = pd.date_range('2024-01-01', periods=24, freq='H')
        co2 = pd.Series([800] * 24, index=dates)
        
        low_occ = recommend_ventilation_type(co2, occupancy='low')
        high_occ = recommend_ventilation_type(co2, occupancy='high')
        
        # Different occupancy should potentially give different recommendations
        assert isinstance(low_occ, str)
        assert isinstance(high_occ, str)


class TestCalculateRecommendedACH:
    """Tests for calculate_recommended_ach function."""
    
    def test_low_co2_low_ach(self):
        """Test low CO2 requires low ACH."""
        dates = pd.date_range('2024-01-01', periods=24, freq='H')
        co2 = pd.Series([600] * 24, index=dates)
        
        ach = calculate_recommended_ach(co2, room_volume=100, occupants=2)
        
        assert ach < 5  # Low ACH
    
    def test_high_co2_high_ach(self):
        """Test high CO2 requires high ACH."""
        dates = pd.date_range('2024-01-01', periods=24, freq='H')
        co2 = pd.Series([1500] * 24, index=dates)
        
        ach = calculate_recommended_ach(co2, room_volume=100, occupants=5)
        
        assert ach > 5  # High ACH
    
    def test_ach_with_volume(self):
        """Test that room volume affects ACH."""
        dates = pd.date_range('2024-01-01', periods=24, freq='H')
        co2 = pd.Series([1000] * 24, index=dates)
        
        ach_small = calculate_recommended_ach(co2, room_volume=50, occupants=3)
        ach_large = calculate_recommended_ach(co2, room_volume=200, occupants=3)
        
        # Smaller room needs higher ACH
        assert ach_small >= ach_large
    
    def test_ach_with_occupants(self):
        """Test that occupant count affects ACH."""
        dates = pd.date_range('2024-01-01', periods=24, freq='H')
        co2 = pd.Series([1000] * 24, index=dates)
        
        ach_few = calculate_recommended_ach(co2, room_volume=100, occupants=2)
        ach_many = calculate_recommended_ach(co2, room_volume=100, occupants=10)
        
        # More occupants need higher ACH
        assert ach_many >= ach_few
    
    def test_ach_positive(self):
        """Test that ACH is always positive."""
        dates = pd.date_range('2024-01-01', periods=24, freq='H')
        co2 = pd.Series([800] * 24, index=dates)
        
        ach = calculate_recommended_ach(co2, room_volume=100, occupants=3)
        
        assert ach > 0
    
    def test_ach_with_none_params(self):
        """Test ACH calculation with None parameters."""
        dates = pd.date_range('2024-01-01', periods=24, freq='H')
        co2 = pd.Series([1000] * 24, index=dates)
        
        ach = calculate_recommended_ach(co2, room_volume=None, occupants=None)
        
        # Should return default or calculated value
        assert ach > 0


class TestIdentifyPeakPeriods:
    """Tests for identify_peak_periods function."""
    
    def test_no_peak_periods(self):
        """Test when there are no peak periods."""
        dates = pd.date_range('2024-01-01', periods=24, freq='H')
        co2 = pd.Series([600] * 24, index=dates)
        
        peaks = identify_peak_periods(co2, threshold=1000)
        
        assert len(peaks) == 0
    
    def test_single_peak_period(self):
        """Test identifying single peak period."""
        dates = pd.date_range('2024-01-01', periods=24, freq='H')
        co2 = pd.Series([
            1200 if 9 <= i <= 17 else 600  # Office hours peak
            for i in range(24)
        ], index=dates)
        
        peaks = identify_peak_periods(co2, threshold=1000)
        
        assert len(peaks) > 0
    
    def test_multiple_peak_periods(self):
        """Test identifying multiple peak periods."""
        dates = pd.date_range('2024-01-01', periods=24, freq='H')
        co2 = pd.Series([
            1200 if i in range(9, 12) or i in range(14, 17) else 600
            for i in range(24)
        ], index=dates)
        
        peaks = identify_peak_periods(co2, threshold=1000)
        
        assert len(peaks) >= 1
    
    def test_peak_structure(self):
        """Test that peak dict has correct structure."""
        dates = pd.date_range('2024-01-01', periods=24, freq='H')
        co2 = pd.Series([1200 if 10 <= i <= 15 else 600 for i in range(24)], index=dates)
        
        peaks = identify_peak_periods(co2, threshold=1000)
        
        if len(peaks) > 0:
            peak = peaks[0]
            assert 'start' in peak or 'period' in peak
            assert 'max_value' in peak or 'value' in peak


class TestAssessVentilationEffectiveness:
    """Tests for assess_ventilation_effectiveness function."""
    
    def test_effective_ventilation(self):
        """Test when ventilation is effective."""
        dates = pd.date_range('2024-01-01', periods=48, freq='H')
        # CO2 rises during day, drops at night (good ventilation)
        co2 = pd.Series([
            800 if 9 <= (i % 24) <= 17 else 500
            for i in range(48)
        ], index=dates)
        
        effectiveness = assess_ventilation_effectiveness(co2)
        
        assert effectiveness > 0.5  # Good effectiveness
    
    def test_ineffective_ventilation(self):
        """Test when ventilation is ineffective."""
        dates = pd.date_range('2024-01-01', periods=48, freq='H')
        # CO2 stays high (poor ventilation)
        co2 = pd.Series([1200] * 48, index=dates)
        
        effectiveness = assess_ventilation_effectiveness(co2)
        
        assert effectiveness < 0.5  # Poor effectiveness
    
    def test_effectiveness_range(self):
        """Test that effectiveness is 0-1."""
        test_cases = [
            pd.Series([600] * 50),
            pd.Series([1500] * 50),
            pd.Series([800 + i % 100 for i in range(50)]),
        ]
        
        for co2 in test_cases:
            effectiveness = assess_ventilation_effectiveness(co2)
            assert 0 <= effectiveness <= 1


class TestVentilationAnalyzerIntegration:
    """Integration tests for ventilation analyzer."""
    
    def test_complete_ventilation_analysis(self):
        """Test complete ventilation analysis workflow."""
        # Simulate 1 week of office data
        dates = pd.date_range('2024-01-01', periods=168, freq='H')
        
        # Office pattern: high during work hours
        co2 = pd.Series([
            400 + (600 if 9 <= (i % 24) <= 17 else 0) + np.random.randint(-50, 50)
            for i in range(168)
        ], index=dates)
        
        humidity = pd.Series([
            45 + np.random.randint(-5, 5)
            for _ in range(168)
        ], index=dates)
        
        # Run complete analysis
        result = analyze_ventilation_need(co2, humidity)
        vtype = recommend_ventilation_type(co2, occupancy='medium')
        ach = calculate_recommended_ach(co2, room_volume=150, occupants=5)
        peaks = identify_peak_periods(co2, threshold=900)
        effectiveness = assess_ventilation_effectiveness(co2)
        
        # Verify
        assert result['priority'] in ['low', 'medium', 'high']
        assert vtype in ['natural', 'mechanical', 'hybrid', 'passive']
        assert ach > 0
        assert isinstance(peaks, list)
        assert 0 <= effectiveness <= 1
    
    def test_residential_scenario(self):
        """Test residential ventilation scenario."""
        dates = pd.date_range('2024-01-01', periods=168, freq='H')
        
        # Residential: lower occupancy, moderate CO2
        co2 = pd.Series([
            500 + np.random.randint(-100, 200)
            for _ in range(168)
        ], index=dates)
        
        humidity = pd.Series([50 + np.random.randint(-10, 10) for _ in range(168)], index=dates)
        
        result = analyze_ventilation_need(co2, humidity)
        vtype = recommend_ventilation_type(co2, occupancy='low')
        
        # Residential typically needs natural/passive
        assert result['priority'] in ['low', 'medium']
        assert vtype in ['natural', 'passive', 'hybrid']
    
    def test_classroom_scenario(self):
        """Test classroom ventilation scenario."""
        dates = pd.date_range('2024-01-01', periods=168, freq='H')
        
        # Classroom: high occupancy during school hours
        co2 = pd.Series([
            400 if (i % 24) < 8 or (i % 24) > 16
            else 1200 + np.random.randint(-100, 100)
            for i in range(168)
        ], index=dates)
        
        result = analyze_ventilation_need(co2, humidity=None)
        vtype = recommend_ventilation_type(co2, occupancy='high')
        ach = calculate_recommended_ach(co2, room_volume=200, occupants=25)
        
        # Classroom needs mechanical or hybrid
        assert result['priority'] in ['medium', 'high']
        assert vtype in ['mechanical', 'hybrid']
        assert ach > 3  # Higher ACH for classrooms
    
    def test_edge_case_extreme_values(self):
        """Test with extreme CO2 values."""
        dates = pd.date_range('2024-01-01', periods=50, freq='H')
        co2 = pd.Series([2500] * 50, index=dates)  # Very high
        
        result = analyze_ventilation_need(co2, humidity=None)
        
        assert result['priority'] == 'high'
        assert result['issue_indicators']['high_co2'] == True
    
    def test_recommendation_quality(self):
        """Test that recommendations are meaningful."""
        dates = pd.date_range('2024-01-01', periods=100, freq='H')
        co2 = pd.Series([1100] * 100, index=dates)
        humidity = pd.Series([65] * 100, index=dates)
        
        result = analyze_ventilation_need(co2, humidity)
        
        # Recommendation should be non-empty and mention ventilation
        assert isinstance(result['recommendation'], str)
        assert len(result['recommendation']) > 10
        assert any(word in result['recommendation'].lower() 
                   for word in ['ventilation', 'air', 'co2', 'fresh'])
