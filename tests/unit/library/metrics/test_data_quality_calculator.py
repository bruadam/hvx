"""
Unit tests for data quality calculator module.

Tests pure logic for calculating data completeness and quality scores.
"""

import pytest
import pandas as pd
import numpy as np

from src.core.analysis.ieq.library.metrics.data_quality_calculator import (
    calculate_completeness,
    calculate_quality_score,
    identify_gaps,
    calculate_gap_statistics
)


class TestCalculateCompleteness:
    """Tests for calculate_completeness function."""
    
    def test_complete_data(self):
        """Test with 100% complete data."""
        data = pd.Series([1, 2, 3, 4, 5])
        completeness = calculate_completeness(data)
        
        assert completeness == 100.0
    
    def test_no_data(self):
        """Test with all NaN values."""
        data = pd.Series([np.nan, np.nan, np.nan, np.nan])
        completeness = calculate_completeness(data)
        
        assert completeness == 0.0
    
    def test_partial_data(self):
        """Test with partial data."""
        data = pd.Series([1, np.nan, 3, np.nan, 5])
        completeness = calculate_completeness(data)
        
        assert completeness == 60.0
    
    def test_75_percent_complete(self):
        """Test with 75% complete data."""
        data = pd.Series([1, 2, 3, np.nan])
        completeness = calculate_completeness(data)
        
        assert completeness == 75.0
    
    def test_single_value(self):
        """Test with single value."""
        data = pd.Series([42])
        completeness = calculate_completeness(data)
        
        assert completeness == 100.0
    
    def test_single_nan(self):
        """Test with single NaN."""
        data = pd.Series([np.nan])
        completeness = calculate_completeness(data)
        
        assert completeness == 0.0
    
    def test_empty_series(self):
        """Test with empty series."""
        data = pd.Series([])
        completeness = calculate_completeness(data)
        
        assert completeness == 0.0
    
    def test_mixed_types_with_nan(self):
        """Test with mixed numeric types and NaN."""
        data = pd.Series([1, 2.5, np.nan, 4, 5.5])
        completeness = calculate_completeness(data)
        
        assert completeness == 80.0
    
    def test_large_dataset(self):
        """Test with large dataset."""
        # 900 values, 100 NaN = 90% complete
        data = pd.Series([1] * 900 + [np.nan] * 100)
        completeness = calculate_completeness(data)
        
        assert completeness == 90.0


class TestCalculateQualityScore:
    """Tests for calculate_quality_score function."""
    
    def test_perfect_quality(self):
        """Test with perfect quality data."""
        data = pd.Series([20, 21, 22, 21, 20])
        quality = calculate_quality_score(data)
        
        # Perfect completeness + low variance = high quality
        assert quality > 80
    
    def test_low_quality_many_gaps(self):
        """Test with many gaps."""
        data = pd.Series([20, np.nan, np.nan, np.nan, 21])
        quality = calculate_quality_score(data)
        
        # Low completeness = low quality
        assert quality < 50
    
    def test_quality_with_outliers(self):
        """Test quality affected by outliers."""
        data = pd.Series([20, 21, 20, 100, 21, 20])  # One outlier
        quality = calculate_quality_score(data)
        
        # Outlier affects quality
        assert quality < 100
    
    def test_quality_all_nan(self):
        """Test quality with all NaN."""
        data = pd.Series([np.nan, np.nan, np.nan])
        quality = calculate_quality_score(data)
        
        assert quality == 0.0
    
    def test_quality_stable_data(self):
        """Test quality with stable data."""
        data = pd.Series([22, 22, 22, 22, 22])
        quality = calculate_quality_score(data)
        
        # Perfect stability + completeness = high quality
        assert quality > 90
    
    def test_quality_moderately_variable_data(self):
        """Test quality with moderate variability."""
        data = pd.Series([20, 22, 24, 23, 21, 22, 23])
        quality = calculate_quality_score(data)
        
        # Good completeness, moderate variance
        assert 50 < quality < 100
    
    def test_quality_score_range(self):
        """Test that quality score is always 0-100."""
        test_cases = [
            pd.Series([1, 2, 3, 4, 5]),
            pd.Series([np.nan, 1, np.nan, 2]),
            pd.Series([100, 200, 300]),
            pd.Series([0, 0, 0, 0]),
        ]
        
        for data in test_cases:
            quality = calculate_quality_score(data)
            assert 0 <= quality <= 100


class TestIdentifyGaps:
    """Tests for identify_gaps function."""
    
    def test_no_gaps(self):
        """Test when there are no gaps."""
        data = pd.Series([1, 2, 3, 4, 5], index=[0, 1, 2, 3, 4])
        gaps = identify_gaps(data)
        
        assert len(gaps) == 0
    
    def test_single_gap(self):
        """Test with single gap."""
        data = pd.Series([1, np.nan, 3], index=[0, 1, 2])
        gaps = identify_gaps(data)
        
        assert len(gaps) == 1
        assert gaps[0]['start'] == 1
        assert gaps[0]['end'] == 1
        assert gaps[0]['length'] == 1
    
    def test_multiple_gaps(self):
        """Test with multiple gaps."""
        data = pd.Series([1, np.nan, 3, np.nan, np.nan, 6], index=range(6))
        gaps = identify_gaps(data)
        
        assert len(gaps) == 2
        # First gap at index 1
        assert gaps[0]['start'] == 1
        assert gaps[0]['length'] == 1
        # Second gap at indices 3-4
        assert gaps[1]['start'] == 3
        assert gaps[1]['length'] == 2
    
    def test_consecutive_gaps(self):
        """Test with consecutive gaps."""
        data = pd.Series([1, np.nan, np.nan, np.nan, 5], index=range(5))
        gaps = identify_gaps(data)
        
        assert len(gaps) == 1
        assert gaps[0]['start'] == 1
        assert gaps[0]['end'] == 3
        assert gaps[0]['length'] == 3
    
    def test_gap_at_start(self):
        """Test with gap at start."""
        data = pd.Series([np.nan, np.nan, 3, 4], index=range(4))
        gaps = identify_gaps(data)
        
        assert len(gaps) == 1
        assert gaps[0]['start'] == 0
        assert gaps[0]['length'] == 2
    
    def test_gap_at_end(self):
        """Test with gap at end."""
        data = pd.Series([1, 2, np.nan, np.nan], index=range(4))
        gaps = identify_gaps(data)
        
        assert len(gaps) == 1
        assert gaps[0]['start'] == 2
        assert gaps[0]['length'] == 2
    
    def test_all_gaps(self):
        """Test when all values are NaN."""
        data = pd.Series([np.nan, np.nan, np.nan], index=range(3))
        gaps = identify_gaps(data)
        
        assert len(gaps) == 1
        assert gaps[0]['length'] == 3
    
    def test_gaps_with_datetime_index(self):
        """Test gaps with datetime index."""
        dates = pd.date_range('2024-01-01', periods=5, freq='H')
        data = pd.Series([1, np.nan, np.nan, 4, 5], index=dates)
        gaps = identify_gaps(data)
        
        assert len(gaps) == 1
        assert gaps[0]['length'] == 2
        # Index should be preserved
        assert 'start' in gaps[0]


class TestCalculateGapStatistics:
    """Tests for calculate_gap_statistics function."""
    
    def test_gap_stats_no_gaps(self):
        """Test gap statistics with no gaps."""
        data = pd.Series([1, 2, 3, 4, 5])
        gap_stats = calculate_gap_statistics(data)
        
        assert gap_stats['total_gaps'] == 0
        assert gap_stats['total_missing'] == 0
        assert gap_stats['max_gap_length'] == 0
        assert gap_stats['avg_gap_length'] == 0
    
    def test_gap_stats_single_gap(self):
        """Test gap statistics with single gap."""
        data = pd.Series([1, np.nan, 3, 4, 5])
        gap_stats = calculate_gap_statistics(data)
        
        assert gap_stats['total_gaps'] == 1
        assert gap_stats['total_missing'] == 1
        assert gap_stats['max_gap_length'] == 1
        assert gap_stats['avg_gap_length'] == 1.0
    
    def test_gap_stats_multiple_gaps(self):
        """Test gap statistics with multiple gaps."""
        data = pd.Series([1, np.nan, 3, np.nan, np.nan, 6])
        gap_stats = calculate_gap_statistics(data)
        
        assert gap_stats['total_gaps'] == 2
        assert gap_stats['total_missing'] == 3
        assert gap_stats['max_gap_length'] == 2
        assert gap_stats['avg_gap_length'] == 1.5  # (1 + 2) / 2
    
    def test_gap_stats_long_gap(self):
        """Test gap statistics with long gap."""
        data = pd.Series([1] + [np.nan] * 10 + [12])
        gap_stats = calculate_gap_statistics(data)
        
        assert gap_stats['total_gaps'] == 1
        assert gap_stats['total_missing'] == 10
        assert gap_stats['max_gap_length'] == 10
        assert gap_stats['avg_gap_length'] == 10.0
    
    def test_gap_stats_all_missing(self):
        """Test gap statistics with all missing data."""
        data = pd.Series([np.nan, np.nan, np.nan, np.nan])
        gap_stats = calculate_gap_statistics(data)
        
        assert gap_stats['total_gaps'] == 1
        assert gap_stats['total_missing'] == 4
        assert gap_stats['max_gap_length'] == 4
    
    def test_gap_stats_percentage(self):
        """Test that gap statistics include percentage if needed."""
        data = pd.Series([1, np.nan, np.nan, 4, 5, np.nan, 7, 8, 9, 10])
        gap_stats = calculate_gap_statistics(data)
        
        # 3 missing out of 10 = 30%
        if 'missing_percentage' in gap_stats:
            assert gap_stats['missing_percentage'] == 30.0


class TestDataQualityIntegration:
    """Integration tests for data quality calculations."""
    
    def test_complete_quality_analysis(self):
        """Test complete data quality analysis workflow."""
        # Create realistic data with some gaps
        dates = pd.date_range('2024-01-01', periods=100, freq='H')
        temps = pd.Series([
            20 + np.random.randn() if i % 20 != 0 else np.nan
            for i in range(100)
        ], index=dates)
        
        # Calculate all quality metrics
        completeness = calculate_completeness(temps)
        quality = calculate_quality_score(temps)
        gaps = identify_gaps(temps)
        gap_stats = calculate_gap_statistics(temps)
        
        # Verify consistency
        assert completeness == 100 - gap_stats['total_missing']
        assert len(gaps) == gap_stats['total_gaps']
        assert quality <= completeness  # Quality can't exceed completeness
        
        # Verify reasonable values
        assert 90 <= completeness <= 100
        assert 0 <= quality <= 100
    
    def test_poor_quality_data_analysis(self):
        """Test analysis of poor quality data."""
        # Create data with many gaps
        data = pd.Series([
            1 if i % 2 == 0 else np.nan
            for i in range(20)
        ])
        
        completeness = calculate_completeness(data)
        quality = calculate_quality_score(data)
        gap_stats = calculate_gap_statistics(data)
        
        # Should reflect poor quality
        assert completeness == 50.0
        assert quality < 60
        assert gap_stats['total_gaps'] > 5
    
    def test_high_quality_data_analysis(self):
        """Test analysis of high quality data."""
        # Create stable, complete data
        data = pd.Series([22.0 + np.random.randn() * 0.1 for _ in range(100)])
        
        completeness = calculate_completeness(data)
        quality = calculate_quality_score(data)
        gap_stats = calculate_gap_statistics(data)
        
        # Should reflect high quality
        assert completeness == 100.0
        assert quality > 80
        assert gap_stats['total_gaps'] == 0
    
    def test_realistic_sensor_data(self):
        """Test with realistic sensor data patterns."""
        dates = pd.date_range('2024-01-01', periods=168, freq='H')  # 1 week
        
        # Simulate sensor failure for 6 hours
        temps = []
        for i in range(168):
            if 50 <= i < 56:  # Failure period
                temps.append(np.nan)
            else:
                temps.append(20 + np.sin(i * 2 * np.pi / 24) * 2)
        
        data = pd.Series(temps, index=dates)
        
        completeness = calculate_completeness(data)
        gaps = identify_gaps(data)
        gap_stats = calculate_gap_statistics(data)
        
        # Verify
        assert completeness == pytest.approx(96.4, abs=0.1)  # 162/168
        assert len(gaps) == 1
        assert gap_stats['max_gap_length'] == 6
    
    def test_edge_case_empty_data(self):
        """Test edge case with empty data."""
        data = pd.Series([])
        
        completeness = calculate_completeness(data)
        quality = calculate_quality_score(data)
        gap_stats = calculate_gap_statistics(data)
        
        assert completeness == 0.0
        assert quality == 0.0
        assert gap_stats['total_gaps'] == 0
    
    def test_quality_vs_completeness_relationship(self):
        """Test relationship between quality and completeness."""
        # Same completeness, different quality
        stable_data = pd.Series([20, 20, 20, np.nan, 20])
        variable_data = pd.Series([10, 30, 15, np.nan, 25])
        
        stable_completeness = calculate_completeness(stable_data)
        variable_completeness = calculate_completeness(variable_data)
        
        stable_quality = calculate_quality_score(stable_data)
        variable_quality = calculate_quality_score(variable_data)
        
        # Same completeness
        assert stable_completeness == variable_completeness
        
        # But different quality (stable should be higher)
        assert stable_quality > variable_quality
