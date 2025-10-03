"""
Unit tests for insulation analyzer module.

Tests pure logic for analyzing insulation needs from temperature patterns.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from src.core.analysis.ieq.library.recommendations.insulation_analyzer import (
    analyze_insulation_need,
    identify_affected_areas,
    estimate_improvement_potential,
    calculate_temperature_variance
)


class TestAnalyzeInsulationNeed:
    """Tests for analyze_insulation_need function."""
    
    def test_no_insulation_issues(self):
        """Test when temperatures are stable (no insulation issues)."""
        dates = pd.date_range('2024-01-01', periods=24, freq='H')
        temps = pd.Series([22.0] * 24, index=dates)
        outdoor = pd.Series([5.0] * 24, index=dates)
        
        result = analyze_insulation_need(temps, outdoor)
        
        assert result['priority'] == 'low'
        assert result['severity_score'] < 0.3
    
    def test_high_insulation_need(self):
        """Test when insulation is clearly needed."""
        dates = pd.date_range('2024-01-01', periods=24, freq='H')
        # Indoor temps vary significantly with outdoor
        temps = pd.Series([15 + i * 0.5 for i in range(24)], index=dates)
        outdoor = pd.Series([0 + i * 0.3 for i in range(24)], index=dates)
        
        result = analyze_insulation_need(temps, outdoor)
        
        assert result['priority'] in ['high', 'medium']
        assert result['severity_score'] > 0.3
    
    def test_medium_insulation_need(self):
        """Test medium insulation need scenario."""
        dates = pd.date_range('2024-01-01', periods=48, freq='H')
        # Moderate temperature variation
        temps = pd.Series([20 + np.sin(i * np.pi / 12) * 2 for i in range(48)], index=dates)
        outdoor = pd.Series([5 + np.sin(i * np.pi / 12) * 3 for i in range(48)], index=dates)
        
        result = analyze_insulation_need(temps, outdoor)
        
        assert result['priority'] in ['medium', 'low', 'high']
        assert 0 <= result['severity_score'] <= 1
    
    def test_result_structure(self):
        """Test that result has correct structure."""
        dates = pd.date_range('2024-01-01', periods=24, freq='H')
        temps = pd.Series(range(24), index=dates)
        outdoor = pd.Series(range(24), index=dates)
        
        result = analyze_insulation_need(temps, outdoor)
        
        assert 'priority' in result
        assert 'affected_areas' in result
        assert 'severity_score' in result
        assert 'estimated_improvement' in result
        assert 'recommendation' in result
    
    def test_with_none_outdoor(self):
        """Test when outdoor temperature is None."""
        dates = pd.date_range('2024-01-01', periods=24, freq='H')
        temps = pd.Series([18, 22, 20, 19, 23, 21] * 4, index=dates)
        
        result = analyze_insulation_need(temps, outdoor=None)
        
        # Should still analyze based on indoor variance
        assert isinstance(result, dict)
        assert 'priority' in result
    
    def test_empty_data(self):
        """Test with empty data."""
        temps = pd.Series([])
        outdoor = pd.Series([])
        
        result = analyze_insulation_need(temps, outdoor)
        
        assert result['priority'] == 'low'
        assert result['severity_score'] == 0


class TestIdentifyAffectedAreas:
    """Tests for identify_affected_areas function."""
    
    def test_no_affected_areas(self):
        """Test when temperatures are uniform (no affected areas)."""
        dates = pd.date_range('2024-01-01', periods=24, freq='H')
        temps = pd.Series([22.0] * 24, index=dates)
        
        areas = identify_affected_areas(temps)
        
        assert len(areas) == 0
    
    def test_morning_cold_spot(self):
        """Test identifying morning cold spots."""
        dates = pd.date_range('2024-01-01', periods=24, freq='H')
        # Morning hours colder
        temps = pd.Series([
            18 if 6 <= i <= 9 else 22
            for i in range(24)
        ], index=dates)
        
        areas = identify_affected_areas(temps)
        
        assert len(areas) > 0
        assert any('morning' in area.lower() or '6' in str(area) for area in areas)
    
    def test_evening_cold_spot(self):
        """Test identifying evening cold spots."""
        dates = pd.date_range('2024-01-01', periods=24, freq='H')
        # Evening hours colder
        temps = pd.Series([
            18 if 18 <= i <= 23 else 22
            for i in range(24)
        ], index=dates)
        
        areas = identify_affected_areas(temps)
        
        assert len(areas) > 0
    
    def test_multiple_affected_areas(self):
        """Test identifying multiple affected areas."""
        dates = pd.date_range('2024-01-01', periods=24, freq='H')
        # Multiple cold periods
        temps = pd.Series([
            18 if i in [6, 7, 8, 18, 19, 20] else 22
            for i in range(24)
        ], index=dates)
        
        areas = identify_affected_areas(temps)
        
        assert len(areas) >= 1
    
    def test_threshold_sensitivity(self):
        """Test that threshold affects area identification."""
        dates = pd.date_range('2024-01-01', periods=24, freq='H')
        temps = pd.Series([20, 19, 20, 20, 19, 20] * 4, index=dates)
        
        areas_strict = identify_affected_areas(temps, threshold=2.0)
        areas_lenient = identify_affected_areas(temps, threshold=0.5)
        
        # Lenient threshold should find more areas
        assert len(areas_lenient) >= len(areas_strict)


class TestEstimateImprovementPotential:
    """Tests for estimate_improvement_potential function."""
    
    def test_high_improvement_potential(self):
        """Test high improvement potential scenario."""
        dates = pd.date_range('2024-01-01', periods=100, freq='H')
        # High variance = high potential
        temps = pd.Series([15 + i % 10 for i in range(100)], index=dates)
        
        improvement = estimate_improvement_potential(temps)
        
        assert improvement > 0.5
    
    def test_low_improvement_potential(self):
        """Test low improvement potential scenario."""
        dates = pd.date_range('2024-01-01', periods=100, freq='H')
        # Low variance = low potential
        temps = pd.Series([22.0 + np.random.randn() * 0.1 for _ in range(100)], index=dates)
        
        improvement = estimate_improvement_potential(temps)
        
        assert improvement < 0.3
    
    def test_medium_improvement_potential(self):
        """Test medium improvement potential scenario."""
        dates = pd.date_range('2024-01-01', periods=48, freq='H')
        # Moderate daily cycle
        temps = pd.Series([20 + np.sin(i * 2 * np.pi / 24) * 1.5 for i in range(48)], index=dates)
        
        improvement = estimate_improvement_potential(temps)
        
        assert 0.2 < improvement < 0.7
    
    def test_improvement_range(self):
        """Test that improvement is always 0-1."""
        test_cases = [
            pd.Series([20] * 50),  # Constant
            pd.Series(range(50)),  # Linear increase
            pd.Series([20 + np.random.randn() * 5 for _ in range(50)]),  # Random
        ]
        
        for temps in test_cases:
            improvement = estimate_improvement_potential(temps)
            assert 0 <= improvement <= 1


class TestCalculateTemperatureVariance:
    """Tests for calculate_temperature_variance function."""
    
    def test_zero_variance(self):
        """Test with constant temperature."""
        temps = pd.Series([22.0] * 100)
        variance = calculate_temperature_variance(temps)
        
        assert variance == 0.0
    
    def test_high_variance(self):
        """Test with high temperature variance."""
        temps = pd.Series([10, 20, 30, 15, 25, 35])
        variance = calculate_temperature_variance(temps)
        
        assert variance > 50  # High std
    
    def test_daily_cycle_variance(self):
        """Test variance with daily temperature cycle."""
        dates = pd.date_range('2024-01-01', periods=72, freq='H')
        temps = pd.Series([20 + np.sin(i * 2 * np.pi / 24) * 3 for i in range(72)], index=dates)
        
        variance = calculate_temperature_variance(temps)
        
        assert variance > 0
    
    def test_variance_with_nan(self):
        """Test variance calculation with NaN values."""
        temps = pd.Series([20, 22, np.nan, 24, 23, np.nan])
        variance = calculate_temperature_variance(temps)
        
        # Should skip NaN
        assert variance > 0


class TestInsulationAnalyzerIntegration:
    """Integration tests for insulation analyzer."""
    
    def test_complete_insulation_analysis(self):
        """Test complete insulation analysis workflow."""
        # Simulate 1 week of data with insulation issues
        dates = pd.date_range('2024-01-01', periods=168, freq='H')
        
        # Indoor temps follow outdoor with lag (poor insulation)
        outdoor = pd.Series([
            5 + np.sin(i * 2 * np.pi / 24) * 5  # -5 to 15°C daily cycle
            for i in range(168)
        ], index=dates)
        
        indoor = pd.Series([
            20 + np.sin((i - 3) * 2 * np.pi / 24) * 2  # Follows outdoor with lag
            for i in range(168)
        ], index=dates)
        
        # Run complete analysis
        result = analyze_insulation_need(indoor, outdoor)
        areas = identify_affected_areas(indoor)
        improvement = estimate_improvement_potential(indoor)
        
        # Verify
        assert result['priority'] in ['low', 'medium', 'high']
        assert 0 <= result['severity_score'] <= 1
        assert isinstance(areas, list)
        assert 0 <= improvement <= 1
        
        # Result should include improvement estimate
        assert 'estimated_improvement' in result
    
    def test_well_insulated_building(self):
        """Test analysis of well-insulated building."""
        dates = pd.date_range('2024-01-01', periods=168, freq='H')
        
        # Stable indoor despite varying outdoor
        outdoor = pd.Series([
            5 + np.sin(i * 2 * np.pi / 24) * 10  # Large outdoor variation
            for i in range(168)
        ], index=dates)
        
        indoor = pd.Series([
            22.0 + np.random.randn() * 0.2  # Very stable indoor
            for _ in range(168)
        ], index=dates)
        
        result = analyze_insulation_need(indoor, outdoor)
        improvement = estimate_improvement_potential(indoor)
        
        # Should indicate low need
        assert result['priority'] == 'low'
        assert improvement < 0.3
    
    def test_seasonal_analysis(self):
        """Test insulation analysis for winter season."""
        # Winter scenario
        dates = pd.date_range('2024-01-01', periods=168, freq='H')
        
        outdoor = pd.Series([0 + np.random.randn() * 3 for _ in range(168)], index=dates)
        indoor = pd.Series([18 + np.random.randn() * 2 for _ in range(168)], index=dates)
        
        result = analyze_insulation_need(indoor, outdoor)
        
        # Should provide meaningful recommendation
        assert 'recommendation' in result
        assert len(result['recommendation']) > 0
    
    def test_edge_case_missing_data(self):
        """Test with missing data."""
        dates = pd.date_range('2024-01-01', periods=50, freq='H')
        indoor = pd.Series([
            20 + np.random.randn() if i % 10 != 0 else np.nan
            for i in range(50)
        ], index=dates)
        outdoor = pd.Series([
            5 + np.random.randn() if i % 10 != 0 else np.nan
            for i in range(50)
        ], index=dates)
        
        result = analyze_insulation_need(indoor, outdoor)
        
        # Should handle missing data gracefully
        assert isinstance(result, dict)
        assert 'priority' in result
    
    def test_recommendation_text_quality(self):
        """Test that recommendations are meaningful."""
        dates = pd.date_range('2024-01-01', periods=100, freq='H')
        temps = pd.Series([15 + i % 10 for i in range(100)], index=dates)
        outdoor = pd.Series([5 + i % 8 for i in range(100)], index=dates)
        
        result = analyze_insulation_need(temps, outdoor)
        
        # Recommendation should be non-empty string
        assert isinstance(result['recommendation'], str)
        assert len(result['recommendation']) > 10
        
        # Should mention insulation
        assert any(word in result['recommendation'].lower() 
                   for word in ['insulation', 'thermal', 'heat', 'cold'])
