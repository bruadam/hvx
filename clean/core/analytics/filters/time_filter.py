"""Time-based data filter."""

import pandas as pd
from datetime import time, datetime
from typing import Optional, List, Tuple

from core.domain.value_objects.time_range import TimeRange


class TimeFilter:
    """Filter data based on time criteria."""

    @staticmethod
    def filter_by_time_range(df: pd.DataFrame, time_range: TimeRange) -> pd.DataFrame:
        """
        Filter DataFrame to specific time range.

        Args:
            df: DataFrame with DatetimeIndex
            time_range: Time range to filter to

        Returns:
            Filtered DataFrame
        """
        if df.empty or not isinstance(df.index, pd.DatetimeIndex):
            return df

        mask = (df.index >= time_range.start) & (df.index <= time_range.end)
        return df[mask].copy()

    @staticmethod
    def filter_by_hour_range(
        df: pd.DataFrame, start_hour: int, end_hour: int
    ) -> pd.DataFrame:
        """
        Filter DataFrame to specific hours of day.

        Args:
            df: DataFrame with DatetimeIndex
            start_hour: Start hour (0-23)
            end_hour: End hour (0-23)

        Returns:
            Filtered DataFrame
        """
        if df.empty or not isinstance(df.index, pd.DatetimeIndex):
            return df

        if start_hour <= end_hour:
            mask = (df.index.hour >= start_hour) & (df.index.hour <= end_hour)
        else:
            # Handle wrap-around (e.g., 22:00 to 02:00)
            mask = (df.index.hour >= start_hour) | (df.index.hour <= end_hour)

        return df[mask].copy()

    @staticmethod
    def filter_by_weekdays(
        df: pd.DataFrame, include_weekdays: bool = True
    ) -> pd.DataFrame:
        """
        Filter DataFrame to weekdays or weekends.

        Args:
            df: DataFrame with DatetimeIndex
            include_weekdays: True for weekdays (Mon-Fri), False for weekends (Sat-Sun)

        Returns:
            Filtered DataFrame
        """
        if df.empty or not isinstance(df.index, pd.DatetimeIndex):
            return df

        if include_weekdays:
            mask = df.index.weekday < 5  # Monday=0, Friday=4
        else:
            mask = df.index.weekday >= 5  # Saturday=5, Sunday=6

        return df[mask].copy()

    @staticmethod
    def filter_by_months(df: pd.DataFrame, months: List[int]) -> pd.DataFrame:
        """
        Filter DataFrame to specific months.

        Args:
            df: DataFrame with DatetimeIndex
            months: List of month numbers (1-12)

        Returns:
            Filtered DataFrame
        """
        if df.empty or not isinstance(df.index, pd.DatetimeIndex):
            return df

        mask = df.index.month.isin(months)
        return df[mask].copy()

    @staticmethod
    def filter_by_season(df: pd.DataFrame, season: str) -> pd.DataFrame:
        """
        Filter DataFrame to specific season.

        Args:
            df: DataFrame with DatetimeIndex
            season: Season name ('winter', 'spring', 'summer', 'autumn')

        Returns:
            Filtered DataFrame
        """
        season_months = {
            "winter": [12, 1, 2],
            "spring": [3, 4, 5],
            "summer": [6, 7, 8],
            "autumn": [9, 10, 11],
        }

        if season.lower() not in season_months:
            return df

        return TimeFilter.filter_by_months(df, season_months[season.lower()])

    @staticmethod
    def filter_by_date_list(df: pd.DataFrame, dates: List[datetime]) -> pd.DataFrame:
        """
        Filter DataFrame to specific dates.

        Args:
            df: DataFrame with DatetimeIndex
            dates: List of datetime objects

        Returns:
            Filtered DataFrame
        """
        if df.empty or not isinstance(df.index, pd.DatetimeIndex):
            return df

        # Extract dates only (ignore time)
        date_set = {d.date() for d in dates}
        mask = df.index.date.isin(date_set)

        return df[mask].copy()

    @staticmethod
    def exclude_holidays(
        df: pd.DataFrame, holidays: List[datetime]
    ) -> pd.DataFrame:
        """
        Exclude specific holiday dates.

        Args:
            df: DataFrame with DatetimeIndex
            holidays: List of holiday datetime objects

        Returns:
            Filtered DataFrame (holidays excluded)
        """
        if df.empty or not isinstance(df.index, pd.DatetimeIndex):
            return df

        # Extract dates only
        holiday_dates = {h.date() for h in holidays}
        mask = ~df.index.date.isin(holiday_dates)

        return df[mask].copy()

    @staticmethod
    def get_operating_hours(
        df: pd.DataFrame,
        start_hour: int = 8,
        end_hour: int = 18,
        exclude_weekends: bool = True,
        holidays: Optional[List[datetime]] = None,
    ) -> pd.DataFrame:
        """
        Filter to operating/business hours.

        Args:
            df: DataFrame with DatetimeIndex
            start_hour: Start of operating hours (default 8 AM)
            end_hour: End of operating hours (default 6 PM)
            exclude_weekends: Whether to exclude weekends
            holidays: Optional list of holidays to exclude

        Returns:
            Filtered DataFrame
        """
        if df.empty:
            return df

        # Apply filters in sequence
        filtered = TimeFilter.filter_by_hour_range(df, start_hour, end_hour)

        if exclude_weekends:
            filtered = TimeFilter.filter_by_weekdays(filtered, include_weekdays=True)

        if holidays:
            filtered = TimeFilter.exclude_holidays(filtered, holidays)

        return filtered
