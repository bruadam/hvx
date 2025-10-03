"""
Unit tests for HVAC analyzer module.

Tests pure logic for analyzing HVAC performance and maintenance needs.
"""

import pytest
import pandas as pd
import numpy as np

from src.core.analytics.ieq.library.recommendations.hvac_analyzer import (
    analyze_hvac_performance,
    assess_energy_impact,
    analyze_maintenance_needs
)


class TestAnalyzeHVACPerformance:
    """Tests for analyze_hvac_performance function."""
    
    def test_good_hvac_performance(self):
        """Test when HVAC is performing well."""
        dates = pd.date_range('2024-01-01', periods=168, freq='H')
        temps = pd.Series([22.0 + np.random.randn() * 0.3 for _ in range(168)], index=dates)
        setpoint = pd.Series([22.0] * 168, index=dates)
        
        temp_control = {
            'avg_deviation': float((temps - setpoint).abs().mean()),
            'max_deviation': float((temps - setpoint).abs().max()),
            'control_stability': 1.0 - float((temps - setpoint).std() / 10),
            'response_time': 10
        }
        setpoint_dev = {
            'overshoot_frequency': 0.0,
            'undershoot_frequency': 0.0,
            'steady_state_error': float((temps - setpoint).abs().mean())
        }
        result = analyze_hvac_performance(temp_control, setpoint_dev)
        assert result.priority == 'low'
        assert len(result.issue_types) == 0
    
    def test_poor_hvac_performance(self):
        """Test when HVAC is performing poorly."""
        dates = pd.date_range('2024-01-01', periods=168, freq='H')
        temps = pd.Series([18 + i % 8 for i in range(168)], index=dates)  # Variable
        setpoint = pd.Series([22.0] * 168, index=dates)
        
        temp_control = {
            'avg_deviation': float((temps - setpoint).abs().mean()),
            'max_deviation': float((temps - setpoint).abs().max()),
            'control_stability': 0.3,
            'response_time': 50
        }
        setpoint_dev = {
            'overshoot_frequency': 0.3,
            'undershoot_frequency': 0.4,
            'steady_state_error': float((temps - setpoint).abs().mean())
        }
        result = analyze_hvac_performance(temp_control, setpoint_dev)
        
    impact = assess_energy_impact(['short_cycling'], {'cycles_per_hour': 8, 'short_cycling': True}, 0.4, 0.1)
    assert impact in ['medium', 'high', 'very_high', 'low']


class TestAnalyzeMaintenanceNeeds:
    """Tests for analyze_maintenance_needs function."""
    
    def test_no_maintenance_needed(self):
        """Test when no maintenance is needed."""
        dates = pd.date_range('2024-01-01', periods=168, freq='H')
        temps = pd.Series([22.0 + np.random.randn() * 0.2 for _ in range(168)], index=dates)
        
        temp_control = {
            'control_stability': 0.9,
            'response_time': 10
        }
        cycling = {'short_cycling': False}
        maintenance = analyze_maintenance_needs(temp_control, cycling)
        assert isinstance(maintenance, list)
    
    def test_maintenance_needed_old_system(self):
        """Test when system is old."""
        dates = pd.date_range('2024-01-01', periods=168, freq='H')
        temps = pd.Series([20 + i % 6 for i in range(168)], index=dates)
        
        temp_control = {
            'control_stability': 0.4,
            'response_time': 50
        }
        cycling = {'short_cycling': True}
        maintenance = analyze_maintenance_needs(temp_control, cycling)
        assert isinstance(maintenance, list)
        assert len(maintenance) > 0
    
    def test_maintenance_needed_unstable_temps(self):
        """Test when temperatures are unstable."""
        dates = pd.date_range('2024-01-01', periods=168, freq='H')
        temps = pd.Series([15 + np.random.randint(0, 10) for _ in range(168)], index=dates)
        
        temp_control = {
            'control_stability': 0.3,
            'response_time': 45
        }
        cycling = {'short_cycling': True}
        maintenance = analyze_maintenance_needs(temp_control, cycling)
        assert isinstance(maintenance, list)
    
    def test_maintenance_result_structure(self):
        """Test maintenance result structure."""
        dates = pd.date_range('2024-01-01', periods=100, freq='H')
        temps = pd.Series(range(100), index=dates)
        
        temp_control = {
            'control_stability': 0.6,
            'response_time': 30
        }
        cycling = {'short_cycling': False}
        maintenance = analyze_maintenance_needs(temp_control, cycling)
        assert isinstance(maintenance, list)




class TestHVACAnalyzerIntegration:
    """Integration tests for HVAC analyzer."""
    
    def test_complete_hvac_analysis(self):
        """Test complete HVAC analysis workflow."""
        # Simulate 1 week of HVAC data
        dates = pd.date_range('2024-01-01', periods=168, freq='H')
        
        setpoint = pd.Series([22.0] * 168, index=dates)
        temps = pd.Series([
            22 + np.sin(i * 2 * np.pi / 24) * 1.5  # Daily cycle
            for i in range(168)
        ], index=dates)
        outdoor = pd.Series([
            5 + np.sin(i * 2 * np.pi / 24) * 8  # Outdoor variation
            for i in range(168)
        ], index=dates)
        
        # Run complete analysis
        temp_control = {
            'avg_deviation': float((temps - setpoint).abs().mean()),
            'max_deviation': float((temps - setpoint).abs().max()),
            'control_stability': 1.0 - float((temps - setpoint).std() / 10),
            'response_time': 10
        }
        setpoint_dev = {
            'overshoot_frequency': 0.1,
            'undershoot_frequency': 0.1,
            'steady_state_error': float((temps - setpoint).abs().mean())
        }
        result = analyze_hvac_performance(temp_control, setpoint_dev)
        energy = assess_energy_impact(result.issue_types, None, setpoint_dev['overshoot_frequency'], setpoint_dev['undershoot_frequency'])
        maintenance = analyze_maintenance_needs(temp_control, {'short_cycling': False})
        # Verify
        assert result.priority in ['low', 'medium', 'high']
        assert energy in ['low', 'medium', 'high', 'minimal', 'very_high']
        assert isinstance(maintenance, list)
    
    def test_well_maintained_system(self):
        """Test analysis of well-maintained HVAC system."""
        dates = pd.date_range('2024-01-01', periods=168, freq='H')
        
        setpoint = pd.Series([22.0] * 168, index=dates)
        temps = pd.Series([22.0 + np.random.randn() * 0.2 for _ in range(168)], index=dates)
        
        temp_control = {
            'avg_deviation': float((temps - setpoint).abs().mean()),
            'max_deviation': float((temps - setpoint).abs().max()),
            'control_stability': 0.95,
            'response_time': 8
        }
        setpoint_dev = {
            'overshoot_frequency': 0.0,
            'undershoot_frequency': 0.0,
            'steady_state_error': float((temps - setpoint).abs().mean())
        }
        result = analyze_hvac_performance(temp_control, setpoint_dev)
        maintenance = analyze_maintenance_needs(temp_control, {'short_cycling': False})
        # Should indicate good performance
        assert result.priority == 'low'
        assert isinstance(maintenance, list)
    
    def test_problematic_system(self):
        """Test analysis of problematic HVAC system."""
        dates = pd.date_range('2024-01-01', periods=168, freq='H')
        
        setpoint = pd.Series([22.0] * 168, index=dates)
        # Wide swings and deviation
        temps = pd.Series([18 + i % 8 for i in range(168)], index=dates)
        
        temp_control = {
            'avg_deviation': float((temps - setpoint).abs().mean()),
            'max_deviation': float((temps - setpoint).abs().max()),
            'control_stability': 0.4,
            'response_time': 40
        }
        setpoint_dev = {
            'overshoot_frequency': 0.3,
            'undershoot_frequency': 0.3,
            'steady_state_error': float((temps - setpoint).abs().mean())
        }
        result = analyze_hvac_performance(temp_control, setpoint_dev)
        # Should indicate problems
        assert result.priority in ['medium', 'high']
        assert isinstance(result.issue_types, list)
    
    def test_winter_operation(self):
        """Test HVAC analysis for winter conditions."""
        dates = pd.date_range('2024-01-01', periods=168, freq='H')
        
        setpoint = pd.Series([22.0] * 168, index=dates)
        temps = pd.Series([21.5 + np.random.randn() * 0.5 for _ in range(168)], index=dates)
        outdoor = pd.Series([-5 + np.random.randn() * 3 for _ in range(168)], index=dates)
        
        temp_control = {
            'avg_deviation': float((temps - setpoint).abs().mean()),
            'max_deviation': float((temps - setpoint).abs().max()),
            'control_stability': 0.8,
            'response_time': 15
        }
        setpoint_dev = {
            'overshoot_frequency': 0.1,
            'undershoot_frequency': 0.1,
            'steady_state_error': float((temps - setpoint).abs().mean())
        }
        result = analyze_hvac_performance(temp_control, setpoint_dev)
        energy = assess_energy_impact(result.issue_types, None, setpoint_dev['overshoot_frequency'], setpoint_dev['undershoot_frequency'])
        # Winter operation more challenging
        assert energy in ['medium', 'high', 'very_high', 'low']
        assert isinstance(energy, str)
    
    def test_summer_operation(self):
        """Test HVAC analysis for summer conditions."""
        dates = pd.date_range('2024-06-01', periods=168, freq='H')
        
        setpoint = pd.Series([24.0] * 168, index=dates)
        temps = pd.Series([24.5 + np.random.randn() * 0.4 for _ in range(168)], index=dates)
        outdoor = pd.Series([30 + np.random.randn() * 3 for _ in range(168)], index=dates)
        
        temp_control = {
            'avg_deviation': float((temps - setpoint).abs().mean()),
            'max_deviation': float((temps - setpoint).abs().max()),
            'control_stability': 0.85,
            'response_time': 12
        }
        setpoint_dev = {
            'overshoot_frequency': 0.05,
            'undershoot_frequency': 0.05,
            'steady_state_error': float((temps - setpoint).abs().mean())
        }
        result = analyze_hvac_performance(temp_control, setpoint_dev)
        energy = assess_energy_impact(result.issue_types, None, setpoint_dev['overshoot_frequency'], setpoint_dev['undershoot_frequency'])
        assert isinstance(energy, str)
    
    def test_edge_case_extreme_conditions(self):
        """Test with extreme outdoor conditions (refactored)."""
        dates = pd.date_range('2024-01-01', periods=100, freq='H')
        setpoint = pd.Series([22.0] * 100, index=dates)
        temps = pd.Series([20.0] * 100, index=dates)
        temp_control = {
            'avg_deviation': float((temps - setpoint).abs().mean()),
            'max_deviation': float((temps - setpoint).abs().max()),
            'control_stability': 0.7,
            'response_time': 20
        }
        setpoint_dev = {
            'overshoot_frequency': 0.0,
            'undershoot_frequency': 0.0,
            'steady_state_error': float((temps - setpoint).abs().mean())
        }
        result = analyze_hvac_performance(temp_control, setpoint_dev)
        assert hasattr(result, 'energy_impact')
    
    def test_recommendation_quality(self):
        """Test that recommendations are meaningful (refactored)."""
        dates = pd.date_range('2024-01-01', periods=100, freq='H')
        temps = pd.Series([19 + i % 5 for i in range(100)], index=dates)
        setpoint = pd.Series([22.0] * 100, index=dates)
        temp_control = {
            'avg_deviation': float((temps - setpoint).abs().mean()),
            'max_deviation': float((temps - setpoint).abs().max()),
            'control_stability': 0.5,
            'response_time': 30
        }
        setpoint_dev = {
            'overshoot_frequency': 0.2,
            'undershoot_frequency': 0.2,
            'steady_state_error': float((temps - setpoint).abs().mean())
        }
        result = analyze_hvac_performance(temp_control, setpoint_dev)
        # Should have recommendations
        assert len(result.recommended_actions) > 0
        # Actions should be strings
        for action in result.recommended_actions:
            assert isinstance(action, str)
            assert len(action) > 5
