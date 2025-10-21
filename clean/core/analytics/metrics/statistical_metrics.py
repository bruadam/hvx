"""Statistical metrics calculator."""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional


class StatisticalMetrics:
    """Calculate statistical metrics for time series data."""

    @staticmethod
    def calculate_basic_statistics(series: pd.Series) -> Dict[str, float]:
        """
        Calculate basic statistical metrics.

        Args:
            series: Pandas Series with numerical data

        Returns:
            Dictionary with statistical metrics
        """
        clean_data = series.dropna()

        if len(clean_data) == 0:
            return {
                "count": 0,
                "mean": 0.0,
                "std": 0.0,
                "min": 0.0,
                "max": 0.0,
                "median": 0.0,
                "q25": 0.0,
                "q75": 0.0,
            }

        return {
            "count": len(clean_data),
            "mean": float(clean_data.mean()),
            "std": float(clean_data.std()),
            "min": float(clean_data.min()),
            "max": float(clean_data.max()),
            "median": float(clean_data.median()),
            "q25": float(clean_data.quantile(0.25)),
            "q75": float(clean_data.quantile(0.75)),
        }

    @staticmethod
    def calculate_extended_statistics(series: pd.Series) -> Dict[str, float]:
        """
        Calculate extended statistical metrics.

        Args:
            series: Pandas Series with numerical data

        Returns:
            Dictionary with extended statistical metrics
        """
        clean_data = series.dropna()

        if len(clean_data) == 0:
            return {}

        basic = StatisticalMetrics.calculate_basic_statistics(series)

        # Add extended metrics
        extended = {
            **basic,
            "variance": float(clean_data.var()),
            "skewness": float(clean_data.skew()),
            "kurtosis": float(clean_data.kurtosis()),
            "range": float(clean_data.max() - clean_data.min()),
            "iqr": float(clean_data.quantile(0.75) - clean_data.quantile(0.25)),
            "cv": (
                float(clean_data.std() / clean_data.mean())
                if clean_data.mean() != 0
                else 0.0
            ),
        }

        return extended

    @staticmethod
    def calculate_percentiles(series: pd.Series, percentiles: list[float]) -> Dict[str, float]:
        """
        Calculate specific percentiles.

        Args:
            series: Pandas Series with numerical data
            percentiles: List of percentiles to calculate (0-100)

        Returns:
            Dictionary mapping percentile to value
        """
        clean_data = series.dropna()

        if len(clean_data) == 0:
            return {f"p{p}": 0.0 for p in percentiles}

        return {
            f"p{int(p)}": float(clean_data.quantile(p / 100)) for p in percentiles
        }

    @staticmethod
    def calculate_temporal_statistics(
        df: pd.DataFrame, column: str, freq: str = "D"
    ) -> Dict[str, Any]:
        """
        Calculate statistics over time periods.

        Args:
            df: DataFrame with DatetimeIndex
            column: Column name to analyze
            freq: Frequency for grouping ('H'=hourly, 'D'=daily, 'W'=weekly, 'M'=monthly)

        Returns:
            Dictionary with temporal statistics
        """
        if column not in df.columns or df.empty:
            return {}

        resampled = df[column].resample(freq).agg(
            ["mean", "std", "min", "max", "count"]
        )

        return {
            "temporal_mean": float(resampled["mean"].mean()),
            "temporal_std": float(resampled["std"].mean()),
            "temporal_min": float(resampled["min"].min()),
            "temporal_max": float(resampled["max"].max()),
            "periods_analyzed": len(resampled),
        }

    @staticmethod
    def detect_outliers(series: pd.Series, method: str = "iqr") -> Dict[str, Any]:
        """
        Detect outliers in data.

        Args:
            series: Pandas Series with numerical data
            method: Method to use ('iqr' or 'zscore')

        Returns:
            Dictionary with outlier information
        """
        clean_data = series.dropna()

        if len(clean_data) == 0:
            return {"outlier_count": 0, "outlier_percentage": 0.0}

        if method == "iqr":
            q1 = clean_data.quantile(0.25)
            q3 = clean_data.quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            outliers = (clean_data < lower_bound) | (clean_data > upper_bound)
        else:  # zscore
            z_scores = np.abs((clean_data - clean_data.mean()) / clean_data.std())
            outliers = z_scores > 3

        outlier_count = outliers.sum()

        return {
            "outlier_count": int(outlier_count),
            "outlier_percentage": float((outlier_count / len(clean_data)) * 100),
            "method": method,
        }
