"""
Time Series Aggregation Utilities

Provides utilities for resampling and aggregating time series data
to ensure minimum resolution requirements are met.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union

import pandas as pd
from pydantic import BaseModel, Field

from .enums.timeseries import TimeResolution, AggregationMethod, DataCategory
from .enums import MetricType


class TimeSeriesAggregator:
    """
    Utility for aggregating time series data to specified resolutions.

    For indoor climate data: ensures minimum hourly resolution.
    For energy data: supports hourly, daily, monthly, and yearly aggregation.
    """

    # Mapping of metric types to data categories
    METRIC_TO_CATEGORY: Dict[MetricType, DataCategory] = {
        MetricType.TEMPERATURE: DataCategory.INDOOR_CLIMATE,
        MetricType.CO2: DataCategory.INDOOR_CLIMATE,
        MetricType.HUMIDITY: DataCategory.INDOOR_CLIMATE,
        MetricType.ILLUMINANCE: DataCategory.INDOOR_CLIMATE,
        MetricType.LUX: DataCategory.INDOOR_CLIMATE,
        MetricType.NOISE: DataCategory.INDOOR_CLIMATE,
        MetricType.VOC: DataCategory.INDOOR_CLIMATE,
        MetricType.PM25: DataCategory.INDOOR_CLIMATE,
        MetricType.PM10: DataCategory.INDOOR_CLIMATE,
        MetricType.OUTDOOR_TEMPERATURE: DataCategory.WEATHER,
        MetricType.OUTDOOR_HUMIDITY: DataCategory.WEATHER,
        MetricType.SOLAR_IRRADIANCE: DataCategory.WEATHER,
        MetricType.WIND_SPEED: DataCategory.WEATHER,
        MetricType.ELECTRICITY: DataCategory.ENERGY_CONSUMPTION,
        MetricType.GAS: DataCategory.ENERGY_CONSUMPTION,
        MetricType.HEAT: DataCategory.ENERGY_CONSUMPTION,
        MetricType.COOLING: DataCategory.ENERGY_CONSUMPTION,
        MetricType.WATER: DataCategory.WATER,
        MetricType.WATER_HOT: DataCategory.WATER,
        MetricType.WATER_COLD: DataCategory.WATER,
        MetricType.POWER: DataCategory.POWER,
        MetricType.APPARENT_POWER: DataCategory.POWER,
        MetricType.REACTIVE_POWER: DataCategory.POWER,
        MetricType.OCCUPANCY: DataCategory.OCCUPANCY,
        MetricType.OCCUPANCY_PERCENT: DataCategory.OCCUPANCY,
    }

    @classmethod
    def get_data_category(cls, metric_type: MetricType) -> DataCategory:
        """Get data category for a metric type."""
        return cls.METRIC_TO_CATEGORY.get(metric_type, DataCategory.INDOOR_CLIMATE)

    @classmethod
    def detect_resolution(
        cls,
        timestamps: Union[List[datetime], pd.DatetimeIndex],
    ) -> Optional[int]:
        """
        Detect the time resolution (in seconds) from timestamps.

        Args:
            timestamps: List of datetime objects or DatetimeIndex

        Returns:
            Detected resolution in seconds or None if cannot be determined
        """
        if isinstance(timestamps, list):
            if len(timestamps) < 2:
                return None
            timestamps = pd.to_datetime(timestamps)

        if len(timestamps) < 2:
            return None

        # Calculate time differences
        diffs = timestamps.to_series().diff().dropna()

        if len(diffs) == 0:
            return None

        # Get the most common interval (mode)
        most_common_diff = diffs.mode()

        if len(most_common_diff) == 0:
            return None

        return int(most_common_diff.iloc[0].total_seconds())

    @classmethod
    def validate_resolution(
        cls,
        timestamps: Union[List[datetime], pd.DatetimeIndex],
        metric_type: MetricType,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate if data resolution meets minimum requirements.

        Args:
            timestamps: List of datetime objects or DatetimeIndex
            metric_type: Type of metric being validated

        Returns:
            Tuple of (is_valid, message)
        """
        detected_seconds = cls.detect_resolution(timestamps)

        if detected_seconds is None:
            return False, "Could not detect time resolution"

        category = cls.get_data_category(metric_type)
        min_resolution = category.minimum_resolution

        if detected_seconds > min_resolution.seconds:
            return False, (
                f"Resolution {detected_seconds}s is coarser than minimum "
                f"required {min_resolution.value} ({min_resolution.seconds}s) "
                f"for {category.value} data"
            )

        return True, None

    @classmethod
    def aggregate_to_resolution(
        cls,
        data: pd.Series,
        target_resolution: TimeResolution,
        method: Optional[AggregationMethod] = None,
        metric_type: Optional[MetricType] = None,
    ) -> pd.Series:
        """
        Aggregate time series data to a target resolution.

        Args:
            data: pandas Series with DatetimeIndex
            target_resolution: Target resolution to aggregate to
            method: Aggregation method (if None, uses default for metric type)
            metric_type: Type of metric (used to determine default method)

        Returns:
            Aggregated pandas Series
        """
        if not isinstance(data.index, pd.DatetimeIndex):
            raise ValueError("Data must have a DatetimeIndex")

        # Determine aggregation method
        if method is None and metric_type is not None:
            category = cls.get_data_category(metric_type)
            method = category.default_aggregation
        elif method is None:
            method = AggregationMethod.MEAN

        # Resample data
        freq = target_resolution.pandas_freq
        resampler = data.resample(freq)

        # Apply aggregation method
        if method == AggregationMethod.MEAN:
            return resampler.mean()
        elif method == AggregationMethod.MEDIAN:
            return resampler.median()
        elif method == AggregationMethod.SUM:
            return resampler.sum()
        elif method == AggregationMethod.MIN:
            return resampler.min()
        elif method == AggregationMethod.MAX:
            return resampler.max()
        elif method == AggregationMethod.FIRST:
            return resampler.first()
        elif method == AggregationMethod.LAST:
            return resampler.last()
        elif method == AggregationMethod.COUNT:
            return resampler.count()
        elif method == AggregationMethod.STD:
            return resampler.std()
        else:
            return resampler.mean()

    @classmethod
    def ensure_minimum_resolution(
        cls,
        data: pd.Series,
        metric_type: MetricType,
        method: Optional[AggregationMethod] = None,
    ) -> pd.Series:
        """
        Ensure data meets minimum resolution requirement for its type.

        For indoor climate data: aggregates to hourly if finer than hourly.
        For energy data: keeps hourly or coarser as-is.

        Args:
            data: pandas Series with DatetimeIndex
            metric_type: Type of metric
            method: Aggregation method (if None, uses default for metric type)

        Returns:
            Aggregated pandas Series meeting minimum resolution
        """
        if not isinstance(data.index, pd.DatetimeIndex):
            raise ValueError("Data must have a DatetimeIndex")

        # Detect current resolution
        detected_seconds = cls.detect_resolution(data.index)

        if detected_seconds is None:
            # Cannot detect resolution, return as-is
            return data

        # Get minimum resolution for this metric type
        category = cls.get_data_category(metric_type)
        min_resolution = category.minimum_resolution

        # If current resolution is finer than minimum, aggregate to minimum
        if detected_seconds < min_resolution.seconds:
            return cls.aggregate_to_resolution(
                data,
                min_resolution,
                method=method,
                metric_type=metric_type,
            )

        # Already meets or exceeds minimum resolution
        return data

    @classmethod
    def aggregate_dict_to_resolution(
        cls,
        timeseries_dict: Dict[str, List[float]],
        timestamps: List[datetime],
        target_resolution: TimeResolution,
        metric_types: Optional[Dict[str, MetricType]] = None,
    ) -> Tuple[Dict[str, List[float]], List[datetime]]:
        """
        Aggregate a dictionary of time series to a target resolution.

        Args:
            timeseries_dict: Dictionary mapping metric names to value lists
            timestamps: List of timestamps
            target_resolution: Target resolution to aggregate to
            metric_types: Optional mapping of metric names to MetricType

        Returns:
            Tuple of (aggregated_dict, aggregated_timestamps)
        """
        if not timeseries_dict:
            return {}, []

        # Convert timestamps to DatetimeIndex
        dt_index = pd.to_datetime(timestamps)

        aggregated_dict: Dict[str, List[float]] = {}
        aggregated_index: Optional[pd.DatetimeIndex] = None

        for metric_name, values in timeseries_dict.items():
            # Create Series
            series = pd.Series(values, index=dt_index)

            # Determine metric type and aggregation method
            metric_type = metric_types.get(metric_name) if metric_types else None

            # Aggregate
            aggregated = cls.aggregate_to_resolution(
                series,
                target_resolution,
                metric_type=metric_type,
            )

            # Store aggregated values
            aggregated_dict[metric_name] = aggregated.tolist()

            # Store index (all should be the same after resampling)
            if aggregated_index is None:
                aggregated_index = pd.DatetimeIndex(aggregated.index)

        # Convert index back to list of datetime objects
        aggregated_timestamps = aggregated_index.to_pydatetime().tolist() if aggregated_index is not None else []

        return aggregated_dict, aggregated_timestamps


class ResamplingConfig(BaseModel):
    """
    Configuration for automatic time series resampling.
    """
    # Resolution settings
    indoor_climate_resolution: TimeResolution = TimeResolution.HOURLY
    energy_hourly_enabled: bool = True
    energy_daily_enabled: bool = True
    energy_monthly_enabled: bool = True
    energy_yearly_enabled: bool = True

    # Aggregation method overrides
    temperature_method: AggregationMethod = AggregationMethod.MEAN
    co2_method: AggregationMethod = AggregationMethod.MEAN
    humidity_method: AggregationMethod = AggregationMethod.MEAN
    energy_method: AggregationMethod = AggregationMethod.SUM
    power_method: AggregationMethod = AggregationMethod.MEAN

    # Quality settings
    minimum_data_quality: float = Field(default=0.7, ge=0, le=1, description="Minimum fraction of valid data points")


__all__ = [
    "TimeSeriesAggregator",
    "ResamplingConfig",
]
