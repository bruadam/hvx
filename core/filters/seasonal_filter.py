"""Seasonal filter."""

from datetime import datetime

import pandas as pd

from core.enums.country import CountryCode
from core.filters.time_filter import TimeFilter


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
        "all_year": list(range(1, 13)),  # All months
    }

    DEFAULT_COUNTRY = CountryCode.DK

    REGION_PERIODS = {
        "subarctic": {"heating": [9, 10, 11, 12, 1, 2, 3, 4, 5], "cooling": [6, 7, 8]},
        "baltic": {"heating": [9, 10, 11, 12, 1, 2, 3, 4, 5], "cooling": [6, 7, 8]},
        "north_sea": {"heating": [10, 11, 12, 1, 2, 3, 4], "cooling": [5, 6, 7, 8, 9]},
        "atlantic": {"heating": [10, 11, 12, 1, 2, 3, 4, 5], "cooling": [6, 7, 8, 9]},
        "central": {"heating": [10, 11, 12, 1, 2, 3, 4], "cooling": [5, 6, 7, 8]},
        "alpine": {"heating": [9, 10, 11, 12, 1, 2, 3, 4, 5], "cooling": [6, 7, 8]},
        "continental_east": {"heating": [9, 10, 11, 12, 1, 2, 3, 4], "cooling": [5, 6, 7, 8]},
        "balkan": {"heating": [10, 11, 12, 1, 2, 3, 4], "cooling": [5, 6, 7, 8, 9]},
        "mediterranean": {"heating": [11, 12, 1, 2, 3], "cooling": [6, 7, 8, 9]},
        "south_mediterranean": {
            "heating": [12, 1, 2],
            "cooling": [5, 6, 7, 8, 9, 10],
        },
        "caucasus": {"heating": [10, 11, 12, 1, 2, 3, 4], "cooling": [5, 6, 7, 8, 9]},
    }

    COUNTRY_REGION_MAP = {
        CountryCode.AD: "alpine",
        CountryCode.AL: "balkan",
        CountryCode.AM: "caucasus",
        CountryCode.AT: "alpine",
        CountryCode.AZ: "caucasus",
        CountryCode.BA: "balkan",
        CountryCode.BE: "north_sea",
        CountryCode.BG: "balkan",
        CountryCode.BY: "continental_east",
        CountryCode.CH: "alpine",
        CountryCode.CY: "south_mediterranean",
        CountryCode.CZ: "central",
        CountryCode.DE: "central",
        CountryCode.DK: "north_sea",
        CountryCode.EE: "baltic",
        CountryCode.ES: "mediterranean",
        CountryCode.FI: "subarctic",
        CountryCode.FR: "central",
        CountryCode.GB: "atlantic",
        CountryCode.GE: "caucasus",
        CountryCode.GR: "mediterranean",
        CountryCode.HR: "balkan",
        CountryCode.HU: "central",
        CountryCode.IE: "atlantic",
        CountryCode.IS: "subarctic",
        CountryCode.IT: "mediterranean",
        CountryCode.XK: "balkan",
        CountryCode.LI: "alpine",
        CountryCode.LT: "baltic",
        CountryCode.LU: "central",
        CountryCode.LV: "baltic",
        CountryCode.MC: "mediterranean",
        CountryCode.MD: "continental_east",
        CountryCode.ME: "balkan",
        CountryCode.MK: "balkan",
        CountryCode.MT: "south_mediterranean",
        CountryCode.NL: "north_sea",
        CountryCode.NO: "subarctic",
        CountryCode.PL: "central",
        CountryCode.PT: "mediterranean",
        CountryCode.RO: "balkan",
        CountryCode.RS: "balkan",
        CountryCode.RU: "continental_east",
        CountryCode.SE: "subarctic",
        CountryCode.SI: "balkan",
        CountryCode.SK: "central",
        CountryCode.SM: "mediterranean",
        CountryCode.TR: "south_mediterranean",
        CountryCode.UA: "continental_east",
        CountryCode.VA: "mediterranean",
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

    def _get_months_for_period(self, period: str) -> list[int]:
        """Get month numbers for a period type."""
        base_period, country = self._split_period_spec(period)
        normalized_period = self._normalize_period_key(base_period)
        country_code = CountryCode.from_value(country)

        months = self._get_months_for_country_period(normalized_period, country_code)
        if months is None and normalized_period in {"heating", "cooling", "non_heating"}:
            months = self._get_months_for_country_period(
                normalized_period, self.DEFAULT_COUNTRY
            )

        if months is not None:
            return months

        if normalized_period in self.SEASONS:
            return self.SEASONS[normalized_period]

        if normalized_period in self.PERIODS:
            return self.PERIODS[normalized_period]

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
    ) -> list[tuple[datetime, datetime, str]]:
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

    @staticmethod
    def _split_period_spec(period: str) -> tuple[str, str | None]:
        """Split period and country specifier (period:country)."""
        if ":" not in period:
            return period, None
        base, _, country = period.partition(":")
        return base, country

    @classmethod
    def _normalize_period_key(cls, period: str) -> str:
        mapping = {
            "heating_season": "heating",
            "cooling_season": "cooling",
            "non_heating_season": "non_heating",
            "non_heating": "non_heating",
        }
        return mapping.get(period, period)

    @classmethod
    def _get_country_profile(
        cls, country: str | CountryCode | None
    ) -> dict[str, list[int]] | None:
        normalized_country = CountryCode.from_value(country)
        if not normalized_country:
            return None
        region = cls.COUNTRY_REGION_MAP.get(normalized_country)
        if not region:
            return None
        return cls.REGION_PERIODS[region]

    @classmethod
    def _get_months_for_country_period(
        cls, period: str, country: str | CountryCode | None
    ) -> list[int] | None:
        profile = cls._get_country_profile(country)
        if not profile:
            return None

        if period == "heating":
            return profile["heating"]
        if period == "cooling":
            return profile["cooling"]
        if period == "non_heating":
            return cls._invert_months(profile["heating"])
        return None

    @staticmethod
    def _invert_months(months: list[int]) -> list[int]:
        heating_set = {m for m in months if 1 <= m <= 12}
        return [month for month in range(1, 13) if month not in heating_set]
