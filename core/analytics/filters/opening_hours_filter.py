"""Opening hours filter."""

from datetime import datetime

import pandas as pd

from core.analytics.filters.time_filter import TimeFilter
from core.domain.enums.building_type import BuildingType


class OpeningHoursFilter:
    """Filter data based on building opening hours."""

    def __init__(
        self,
        opening_hours: tuple[int, int] | None = None,
        building_type: BuildingType | None = None,
        holidays: list[datetime] | None = None,
    ):
        """
        Initialize opening hours filter.

        Args:
            opening_hours: Tuple of (start_hour, end_hour), e.g., (8, 18) for 8 AM to 6 PM
            building_type: Building type (used if opening_hours not provided)
            holidays: List of holiday dates to exclude
        """
        if opening_hours:
            self.start_hour, self.end_hour = opening_hours
        elif building_type:
            self.start_hour, self.end_hour = building_type.typical_occupancy_hours
        else:
            # Default to standard office hours
            self.start_hour, self.end_hour = 8, 18

        self.holidays = holidays or []

    def apply(self, df: pd.DataFrame, exclude_weekends: bool = True) -> pd.DataFrame:
        """
        Apply opening hours filter to DataFrame.

        Args:
            df: DataFrame with DatetimeIndex
            exclude_weekends: Whether to exclude weekend days

        Returns:
            Filtered DataFrame containing only opening hours data
        """
        return TimeFilter.get_operating_hours(
            df,
            start_hour=self.start_hour,
            end_hour=self.end_hour,
            exclude_weekends=exclude_weekends,
            holidays=self.holidays,
        )

    def apply_inverse(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply inverse filter (non-opening hours).

        Args:
            df: DataFrame with DatetimeIndex

        Returns:
            Filtered DataFrame containing only non-opening hours data
        """
        if df.empty:
            return df

        opening_hours_df = self.apply(df)

        # Return complement - data not in opening hours
        mask = ~df.index.isin(opening_hours_df.index)
        return df[mask].copy()

    def get_operating_periods(self, df: pd.DataFrame) -> list[tuple[datetime, datetime]]:
        """
        Get list of operating periods in the data.

        Args:
            df: DataFrame with DatetimeIndex

        Returns:
            List of (start, end) datetime tuples representing operating periods
        """
        opening_df = self.apply(df)

        if opening_df.empty:
            return []

        periods = []
        period_start = opening_df.index[0]
        prev_timestamp = opening_df.index[0]

        for timestamp in opening_df.index[1:]:
            gap = (timestamp - prev_timestamp).total_seconds() / 3600  # hours

            # If gap is more than 2 hours, consider it a new period
            if gap > 2:
                periods.append((period_start.to_pydatetime(), prev_timestamp.to_pydatetime()))
                period_start = timestamp

            prev_timestamp = timestamp

        # Add final period
        periods.append((period_start.to_pydatetime(), prev_timestamp.to_pydatetime()))

        return periods
