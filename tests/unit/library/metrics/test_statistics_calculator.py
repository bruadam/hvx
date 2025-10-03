"""
Unit tests for statistics calculator module.

Tests pure logic for calculating basic and extended statistics.
"""

import pytest
import pandas as pd
import numpy as np

from src.core.analysis.ieq.library.metrics.statistics_calculator import (
    calculate_basic_statistics,
    calculate_extended_statistics,
    calculate_percentiles,
    calculate_temporal_statistics
)


class TestCalculateBasicStatistics:
    """Tests for calculate_basic_statistics function."""
    
    def test_basic_stats_simple_data(self):
        """Test basic statistics with simple data."""
        data = pd.Series([1, 2, 3, 4, 5])
        stats = calculate_basic_statistics(data)
        
        assert stats['mean'] == 3.0
        assert stats['median'] == 3.0
        assert stats['std'] == pytest.approx(1.58, abs=0.01)
        assert stats['min'] == 1
        assert stats['max'] == 5
    
    def test_basic_stats_all_same_values(self):
        """Test with all identical values."""
        data = pd.Series([5, 5, 5, 5, 5])
        stats = calculate_basic_statistics(data)
        
        assert stats['mean'] == 5.0
        assert stats['median'] == 5.0
        assert stats['std'] == 0.0
        assert stats['min'] == 5
        assert stats['max'] == 5
    
    def test_basic_stats_single_value(self):
        """Test with single value."""
        data = pd.Series([42])
        stats = calculate_basic_statistics(data)
        
        assert stats['mean'] == 42
        assert stats['median'] == 42
        assert stats['min'] == 42
        assert stats['max'] == 42
        assert np.isnan(stats['std'])  # std of single value is NaN
    
    def test_basic_stats_negative_values(self):
        """Test with negative values."""
        data = pd.Series([-5, -3, 0, 3, 5])
        stats = calculate_basic_statistics(data)
        
        assert stats['mean'] == 0.0
        assert stats['median'] == 0.0
        assert stats['min'] == -5
        assert stats['max'] == 5
    
    def test_basic_stats_with_nan(self):
        """Test handling of NaN values."""
        data = pd.Series([1, 2, np.nan, 4, 5])
        stats = calculate_basic_statistics(data)
        
        # Should skip NaN values
        assert stats['mean'] == 3.0
        assert stats['median'] == 3.0
        assert stats['min'] == 1
        assert stats['max'] == 5
    
    def test_basic_stats_all_nan(self):
        """Test with all NaN values."""
        data = pd.Series([np.nan, np.nan, np.nan])
        stats = calculate_basic_statistics(data)
        
        # All stats should be NaN
        assert np.isnan(stats['mean'])
        assert np.isnan(stats['median'])
        assert np.isnan(stats['min'])
        assert np.isnan(stats['max'])
    
    def test_basic_stats_empty_series(self):
        """Test with empty series."""
        data = pd.Series([])
        stats = calculate_basic_statistics(data)
        
        # Should return NaN for all stats
        assert np.isnan(stats['mean'])
        assert np.isnan(stats['median'])
    
    def test_basic_stats_float_precision(self):
        """Test floating point precision."""
        data = pd.Series([1.1, 2.2, 3.3, 4.4, 5.5])
        stats = calculate_basic_statistics(data)
        
        assert abs(stats['mean'] - 3.3) < 0.01
        assert abs(stats['median'] - 3.3) < 0.01
    
    def test_basic_stats_large_range(self):
        """Test with large value range."""
        data = pd.Series([1, 1000000])
        stats = calculate_basic_statistics(data)
        
        assert stats['min'] == 1
        assert stats['max'] == 1000000
        assert stats['mean'] == 500000.5


class TestCalculateExtendedStatistics:
    """Tests for calculate_extended_statistics function."""
    
    def test_extended_stats_includes_basic(self):
        """Test that extended stats include basic stats."""
        data = pd.Series([1, 2, 3, 4, 5])
        stats = calculate_extended_statistics(data)
        
        # Should include basic stats
        assert 'mean' in stats
        assert 'median' in stats
        assert 'std' in stats
        assert 'min' in stats
        assert 'max' in stats
    
    def test_extended_stats_includes_percentiles(self):
        """Test that extended stats include percentiles."""
        data = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        stats = calculate_extended_statistics(data)
        
        # Should include percentiles
        assert 'p25' in stats
        assert 'p75' in stats
        assert 'p95' in stats
        
        assert stats['p25'] == 3.25
        assert stats['p75'] == 7.75
        assert stats['p95'] == 9.55
    
    def test_extended_stats_includes_count(self):
        """Test that extended stats include count."""
        data = pd.Series([1, 2, 3, 4, 5])
        stats = calculate_extended_statistics(data)
        
        assert 'count' in stats
        assert stats['count'] == 5
    
    def test_extended_stats_with_nan(self):
        """Test extended stats with NaN values."""
        data = pd.Series([1, 2, np.nan, 4, 5, np.nan])
        stats = calculate_extended_statistics(data)
        
        # Count should be non-NaN values
        assert stats['count'] == 4
        assert stats['mean'] == 3.0
    
    def test_extended_stats_variance(self):
        """Test that variance is calculated if included."""
        data = pd.Series([1, 2, 3, 4, 5])
        stats = calculate_extended_statistics(data)
        
        if 'variance' in stats:
            assert stats['variance'] == pytest.approx(2.5, abs=0.01)
    
    def test_extended_stats_range(self):
        """Test that range is calculated if included."""
        data = pd.Series([10, 20, 30, 40, 50])
        stats = calculate_extended_statistics(data)
        
        if 'range' in stats:
            assert stats['range'] == 40


class TestCalculatePercentiles:
    """Tests for calculate_percentiles function."""
    
    def test_standard_percentiles(self):
        """Test standard percentile calculation."""
        data = pd.Series(range(1, 101))  # 1 to 100
        percentiles = calculate_percentiles(data, [25, 50, 75])
        
        assert percentiles[25] == 25.75
        assert percentiles[50] == 50.5
        assert percentiles[75] == 75.25
    
    def test_single_percentile(self):
        """Test calculating single percentile."""
        data = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        percentiles = calculate_percentiles(data, [50])
        
        assert 50 in percentiles
        assert percentiles[50] == 5.5
    
    def test_extreme_percentiles(self):
        """Test extreme percentiles (0 and 100)."""
        data = pd.Series([10, 20, 30, 40, 50])
        percentiles = calculate_percentiles(data, [0, 100])
        
        assert percentiles[0] == 10
        assert percentiles[100] == 50
    
    def test_percentiles_with_duplicates(self):
        """Test percentiles with duplicate values."""
        data = pd.Series([5, 5, 5, 5, 5])
        percentiles = calculate_percentiles(data, [25, 50, 75])
        
        assert percentiles[25] == 5
        assert percentiles[50] == 5
        assert percentiles[75] == 5
    
    def test_percentiles_with_nan(self):
        """Test percentiles with NaN values."""
        data = pd.Series([1, 2, np.nan, 4, 5])
        percentiles = calculate_percentiles(data, [50])
        
        # Should skip NaN
        assert percentiles[50] == 3.0
    
    def test_custom_percentile_list(self):
        """Test with custom percentile list."""
        data = pd.Series(range(1, 11))
        percentiles = calculate_percentiles(data, [10, 90, 95, 99])
        
        assert 10 in percentiles
        assert 90 in percentiles
        assert 95 in percentiles
        assert 99 in percentiles


class TestCalculateTemporalStatistics:
    """Tests for calculate_temporal_statistics function."""
    
    def test_hourly_statistics(self):
        """Test hourly statistics calculation."""
        dates = pd.date_range('2024-01-01', periods=48, freq='H')
        data = pd.Series([20 + i % 24 for i in range(48)], index=dates)
        
        temporal_stats = calculate_temporal_statistics(data, freq='H')
        
        # Should group by hour and calculate stats
        assert 'by_hour' in temporal_stats
        assert len(temporal_stats['by_hour']) > 0
    
    def test_daily_statistics(self):
        """Test daily statistics calculation."""
        dates = pd.date_range('2024-01-01', periods=72, freq='H')
        data = pd.Series(range(72), index=dates)
        
        temporal_stats = calculate_temporal_statistics(data, freq='D')
        
        # Should group by day
        assert 'by_day' in temporal_stats
        assert len(temporal_stats['by_day']) == 3  # 3 days
    
    def test_weekly_statistics(self):
        """Test weekly statistics calculation."""
        dates = pd.date_range('2024-01-01', periods=14*24, freq='H')
        data = pd.Series(range(14*24), index=dates)
        
        temporal_stats = calculate_temporal_statistics(data, freq='W')
        
        # Should group by week
        assert 'by_week' in temporal_stats
    
    def test_non_datetime_index(self):
        """Test with non-datetime index."""
        data = pd.Series([1, 2, 3, 4, 5], index=[0, 1, 2, 3, 4])
        
        # Should handle gracefully or return None
        temporal_stats = calculate_temporal_statistics(data, freq='H')
        
        assert temporal_stats is None or isinstance(temporal_stats, dict)
    
    def test_temporal_stats_include_mean_std(self):
        """Test that temporal stats include mean and std."""
        dates = pd.date_range('2024-01-01', periods=48, freq='H')
        data = pd.Series([20, 22] * 24, index=dates)
        
        temporal_stats = calculate_temporal_statistics(data, freq='H')
        
        if temporal_stats and 'by_hour' in temporal_stats:
            for hour_stats in temporal_stats['by_hour'].values():
                assert 'mean' in hour_stats or isinstance(hour_stats, (int, float))


class TestStatisticsIntegration:
    """Integration tests for statistics calculations."""
    
    def test_complete_statistical_analysis(self):
        """Test complete statistical analysis workflow."""
        # Create realistic temperature data
        dates = pd.date_range('2024-01-01', periods=168, freq='H')  # 1 week
        temps = pd.Series([
            20 + np.sin(i * 2 * np.pi / 24) * 3  # Daily cycle ±3°C
            for i in range(168)
        ], index=dates)
        
        # Calculate all statistics
        basic = calculate_basic_statistics(temps)
        extended = calculate_extended_statistics(temps)
        percentiles = calculate_percentiles(temps, [25, 50, 75, 95])
        
        # Verify consistency
        assert basic['mean'] == extended['mean']
        assert basic['median'] == extended['median']
        assert percentiles[50] == pytest.approx(basic['median'], abs=0.1)
        
        # Verify reasonable values
        assert 17 < basic['mean'] < 23
        assert basic['std'] > 0
        assert basic['min'] < basic['mean'] < basic['max']
    
    def test_co2_statistics_realistic(self):
        """Test with realistic CO2 data."""
        dates = pd.date_range('2024-01-01 08:00', periods=50, freq='H')
        # Simulate office hours with higher CO2
        co2 = pd.Series([
            400 if i % 24 < 8 or i % 24 > 18 else 800 + np.random.randint(-100, 100)
            for i in range(50)
        ], index=dates)
        
        stats = calculate_extended_statistics(co2)
        percentiles = calculate_percentiles(co2, [50, 95])
        
        # Verify
        assert stats['min'] >= 300  # Outdoor minimum
        assert stats['max'] < 2000  # Reasonable maximum
        assert percentiles[95] > percentiles[50]
    
    def test_humidity_statistics_realistic(self):
        """Test with realistic humidity data."""
        data = pd.Series([45, 50, 55, 48, 52, 47, 53, 49, 51, 46])
        
        stats = calculate_basic_statistics(data)
        extended = calculate_extended_statistics(data)
        
        # Verify humidity in reasonable range
        assert 30 < stats['mean'] < 70
        assert stats['min'] >= 0
        assert stats['max'] <= 100
        
        # Extended should have more info
        assert len(extended) > len(stats)
    
    def test_statistics_with_missing_data(self):
        """Test statistics calculation with missing data."""
        dates = pd.date_range('2024-01-01', periods=100, freq='H')
        # Add missing data
        temps = pd.Series(
            [20 + np.random.randn() if i % 10 != 0 else np.nan for i in range(100)],
            index=dates
        )
        
        basic = calculate_basic_statistics(temps)
        extended = calculate_extended_statistics(temps)
        
        # Should handle NaN values
        assert not np.isnan(basic['mean'])
        assert extended['count'] < 100  # Some NaN values excluded
        assert extended['count'] >= 90  # 10% missing
    
    def test_edge_case_all_zero(self):
        """Test edge case with all zero values."""
        data = pd.Series([0, 0, 0, 0, 0])
        stats = calculate_basic_statistics(data)
        
        assert stats['mean'] == 0
        assert stats['median'] == 0
        assert stats['std'] == 0
        assert stats['min'] == 0
        assert stats['max'] == 0
    
    def test_statistics_preserve_precision(self):
        """Test that statistics preserve float precision."""
        data = pd.Series([20.123, 20.456, 20.789])
        stats = calculate_basic_statistics(data)
        
        # Should not lose precision
        assert isinstance(stats['mean'], float)
        assert abs(stats['mean'] - 20.456) < 0.001
