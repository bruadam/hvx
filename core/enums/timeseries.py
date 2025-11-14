"""
Time series resolution and aggregation enums.
"""

from enum import Enum


class TimeResolution(str, Enum):
    """
    Standard time resolutions for data aggregation.

    For indoor climate data: minimum hourly, with sub-hourly averaging.
    For energy data: supports hourly to yearly aggregation.
    """
    MINUTE = "1min"
    FIVE_MINUTES = "5min"
    FIFTEEN_MINUTES = "15min"
    THIRTY_MINUTES = "30min"
    HOURLY = "1h"
    DAILY = "1d"
    WEEKLY = "1w"
    MONTHLY = "1M"
    YEARLY = "1Y"

    @property
    def seconds(self) -> int:
        """Get resolution in seconds."""
        mapping = {
            self.MINUTE: 60,
            self.FIVE_MINUTES: 300,
            self.FIFTEEN_MINUTES: 900,
            self.THIRTY_MINUTES: 1800,
            self.HOURLY: 3600,
            self.DAILY: 86400,
            self.WEEKLY: 604800,
            self.MONTHLY: 2592000,  # Approximate: 30 days
            self.YEARLY: 31536000,  # Approximate: 365 days
        }
        return mapping.get(self, 3600)

    @property
    def pandas_freq(self) -> str:
        """Get pandas-compatible frequency string."""
        mapping = {
            self.MINUTE: "1min",
            self.FIVE_MINUTES: "5min",
            self.FIFTEEN_MINUTES: "15min",
            self.THIRTY_MINUTES: "30min",
            self.HOURLY: "1h",
            self.DAILY: "1D",
            self.WEEKLY: "1W",
            self.MONTHLY: "1MS",  # Month start
            self.YEARLY: "1YS",   # Year start
        }
        return mapping.get(self, "1h")


class AggregationMethod(str, Enum):
    """
    Methods for aggregating time series data to coarser resolutions.
    """
    MEAN = "mean"
    MEDIAN = "median"
    SUM = "sum"
    MIN = "min"
    MAX = "max"
    FIRST = "first"
    LAST = "last"
    COUNT = "count"
    STD = "std"


class DataCategory(str, Enum):
    """
    Categories of data with different resolution requirements.
    """
    INDOOR_CLIMATE = "indoor_climate"
    ENERGY_CONSUMPTION = "energy_consumption"
    OCCUPANCY = "occupancy"
    WEATHER = "weather"
    POWER = "power"
    WATER = "water"

    @property
    def minimum_resolution(self) -> TimeResolution:
        """Get minimum required resolution for this data category."""
        mapping = {
            self.INDOOR_CLIMATE: TimeResolution.HOURLY,
            self.ENERGY_CONSUMPTION: TimeResolution.HOURLY,
            self.OCCUPANCY: TimeResolution.FIFTEEN_MINUTES,
            self.WEATHER: TimeResolution.HOURLY,
            self.POWER: TimeResolution.FIFTEEN_MINUTES,
            self.WATER: TimeResolution.HOURLY,
        }
        return mapping.get(self, TimeResolution.HOURLY)

    @property
    def default_aggregation(self) -> AggregationMethod:
        """Get default aggregation method for this data category."""
        mapping = {
            self.INDOOR_CLIMATE: AggregationMethod.MEAN,
            self.ENERGY_CONSUMPTION: AggregationMethod.SUM,
            self.OCCUPANCY: AggregationMethod.MEAN,
            self.WEATHER: AggregationMethod.MEAN,
            self.POWER: AggregationMethod.MEAN,
            self.WATER: AggregationMethod.SUM,
        }
        return mapping.get(self, AggregationMethod.MEAN)


__all__ = [
    "TimeResolution",
    "AggregationMethod",
    "DataCategory",
]
