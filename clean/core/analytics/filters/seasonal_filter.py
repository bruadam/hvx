"""Seasonal filter."""

import pandas as pd
from typing import List, Optional
from datetime import datetime

from core.analytics.filters.time_filter import TimeFilter


class SeasonalFilter:
    """Filter data based on seasons or custom periods."""

    # Standard season definitions (Northern Hemisphere)
    SEASONS = {
        "winter": [12, 1, 2],
        "spring": [3, 4, 5],
        "summer": [6, 7, 8],
        "autumn": [9, 10, 11],
        "fall": [9, 10, 11],  # Alias for autumn
    }

    # Common period definitions
    PERIODS = {
        "heating_season": [10, 11, 12, 1, 2, 3, 4],  # October to April
        "non_heating_season": [5, 6, 7, 8, 9],  # May to September
        "cooling_season": [5, 6, 7, 8, 9],  # May to September
        "all_year": list(range(1, 13)),  # All months
    }

    def __init__(self, period_type: str = "all_year"):
        """
        Initialize seasonal filter.

        Args:
            period_type: Type of period to filter
                       ('winter', 'spring', 'summer', 'autumn',
                        'heating_season', 'non_heating_season', 'all_year')
        """
        self.period_type = period_type.lower()
        self.months = self._get_months_for_period(self.period_type)

    def _get_months_for_period(self, period: str) -> List[int]:
        """Get month numbers for a period type."""
        if period in self.SEASONS:
            return self.SEASONS[period]
        elif period in self.PERIODS:
            return self.PERIODS[period]
        else:
            # Default to all year
            return self.PERIODS["all_year"]

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply seasonal filter to DataFrame.

        Args:
            df: DataFrame with DatetimeIndex

        Returns:
            Filtered DataFrame
        """
        if self.period_type == "all_year":
            return df

        return TimeFilter.filter_by_months(df, self.months)

    @staticmethod
    def filter_by_season(df: pd.DataFrame, season: str) -> pd.DataFrame:
        """
        Filter DataFrame to specific season.

        Args:
            df: DataFrame with DatetimeIndex
            season: Season name

        Returns:
            Filtered DataFrame
        """
        sf = SeasonalFilter(season)
        return sf.apply(df)

    @staticmethod
    def filter_by_custom_period(
        df: pd.DataFrame, start_month: int, end_month: int
    ) -> pd.DataFrame:
        """
        Filter DataFrame to custom month range.

        Args:
            df: DataFrame with DatetimeIndex
            start_month: Start month (1-12)
            end_month: End month (1-12)

        Returns:
            Filtered DataFrame
        """
        if start_month <= end_month:
            months = list(range(start_month, end_month + 1))
        else:
            # Handle wrap-around (e.g., November to February)
            months = list(range(start_month, 13)) + list(range(1, end_month + 1))

        return TimeFilter.filter_by_months(df, months)

    def get_season_boundaries(
        self, df: pd.DataFrame
    ) -> List[tuple[datetime, datetime, str]]:
        """
        Get season boundaries within the data range.

        Args:
            df: DataFrame with DatetimeIndex

        Returns:
            List of (start, end, season_name) tuples
        """
        if df.empty or not isinstance(df.index, pd.DatetimeIndex):
            return []

        data_start = df.index.min()
        data_end = df.index.max()

        boundaries = []
        current_date = data_start

        while current_date <= data_end:
            month = current_date.month
            season = self._get_season_for_month(month)

            # Find season end
            season_months = self.SEASONS.get(season, [month])
            last_month = season_months[-1]

            # Calculate season end date
            if month <= last_month:
                season_end = current_date.replace(month=last_month, day=28)
            else:
                # Handle year boundary
                season_end = current_date.replace(
                    year=current_date.year + 1, month=last_month, day=28
                )

            season_end = min(season_end, data_end)

            boundaries.append((current_date.to_pydatetime(), season_end.to_pydatetime(), season))

            # Move to next season
            current_date = season_end + pd.Timedelta(days=1)

        return boundaries

    @staticmethod
    def _get_season_for_month(month: int) -> str:
        """Get season name for a month."""
        for season, months in SeasonalFilter.SEASONS.items():
            if month in months:
                return season
        return "unknown"
