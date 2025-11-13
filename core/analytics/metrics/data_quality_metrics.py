"""Data quality metrics calculator."""

from typing import Any

import pandas as pd


class DataQualityMetrics:
    """Calculate data quality metrics."""

    @staticmethod
    def calculate_completeness(series: pd.Series) -> float:
        """
        Calculate data completeness percentage.

        Args:
            series: Pandas Series

        Returns:
            Completeness as percentage (0-100)
        """
        if len(series) == 0:
            return 0.0

        non_null_count = series.notna().sum()
        return (non_null_count / len(series)) * 100

    @staticmethod
    def calculate_quality_score(series: pd.Series) -> float:
        """
        Calculate overall quality score.

        Considers completeness, outliers, and data consistency.

        Args:
            series: Pandas Series

        Returns:
            Quality score (0-100)
        """
        if len(series) == 0:
            return 0.0

        # Component 1: Completeness (40% weight)
        completeness = DataQualityMetrics.calculate_completeness(series)
        completeness_score = completeness * 0.4

        # Component 2: Outlier ratio (30% weight)
        clean_data = series.dropna()
        if len(clean_data) > 0:
            q1 = clean_data.quantile(0.25)
            q3 = clean_data.quantile(0.75)
            iqr = q3 - q1
            outliers = ((clean_data < (q1 - 3 * iqr)) | (clean_data > (q3 + 3 * iqr))).sum()
            outlier_ratio = outliers / len(clean_data)
            outlier_score = (1 - outlier_ratio) * 30
        else:
            outlier_score = 0.0

        # Component 3: Data consistency (30% weight)
        # Based on std/mean ratio (coefficient of variation)
        if len(clean_data) > 1 and clean_data.mean() != 0:
            cv = clean_data.std() / abs(clean_data.mean())
            # Lower CV is better, normalize to 0-1 range
            consistency_score = max(0, 1 - min(cv, 1)) * 30
        else:
            consistency_score = 30.0 if len(clean_data) > 0 else 0.0

        total_score = completeness_score + outlier_score + consistency_score
        return min(100.0, max(0.0, total_score))

    @staticmethod
    def identify_missing_periods(df: pd.DataFrame, expected_freq: str = "H") -> dict[str, Any]:
        """
        Identify periods with missing data.

        Args:
            df: DataFrame with DatetimeIndex
            expected_freq: Expected frequency ('H'=hourly, 'D'=daily, etc.)

        Returns:
            Dictionary with missing period information
        """
        if df.empty or not isinstance(df.index, pd.DatetimeIndex):
            return {"missing_periods": 0, "gaps": []}

        # Create expected index
        expected_index = pd.date_range(
            start=df.index.min(), end=df.index.max(), freq=expected_freq
        )

        # Find missing timestamps
        missing = expected_index.difference(df.index)

        # Group consecutive missing periods
        gaps = []
        if len(missing) > 0:
            gap_start = missing[0]
            gap_end = missing[0]

            for i in range(1, len(missing)):
                if (missing[i] - gap_end).total_seconds() <= pd.Timedelta(expected_freq).total_seconds() * 1.5:
                    gap_end = missing[i]
                else:
                    gaps.append({"start": gap_start.isoformat(), "end": gap_end.isoformat()})
                    gap_start = missing[i]
                    gap_end = missing[i]

            gaps.append({"start": gap_start.isoformat(), "end": gap_end.isoformat()})

        return {
            "missing_periods": len(missing),
            "missing_percentage": (len(missing) / len(expected_index)) * 100,
            "gaps": gaps[:10],  # Return max 10 largest gaps
            "total_gaps": len(gaps),
        }

    @staticmethod
    def calculate_temporal_coverage(df: pd.DataFrame) -> dict[str, Any]:
        """
        Calculate temporal coverage statistics.

        Args:
            df: DataFrame with DatetimeIndex

        Returns:
            Dictionary with temporal coverage metrics
        """
        if df.empty or not isinstance(df.index, pd.DatetimeIndex):
            return {
                "start_date": None,
                "end_date": None,
                "duration_days": 0,
                "data_points": 0,
            }

        duration = df.index.max() - df.index.min()

        return {
            "start_date": df.index.min().isoformat(),
            "end_date": df.index.max().isoformat(),
            "duration_days": duration.total_seconds() / 86400,
            "data_points": len(df),
            "avg_frequency_hours": (
                duration.total_seconds() / 3600 / len(df) if len(df) > 1 else 0
            ),
        }

    @staticmethod
    def detect_duplicate_timestamps(df: pd.DataFrame) -> dict[str, Any]:
        """
        Detect duplicate timestamps in data.

        Args:
            df: DataFrame with DatetimeIndex

        Returns:
            Dictionary with duplicate information
        """
        if df.empty or not isinstance(df.index, pd.DatetimeIndex):
            return {"duplicate_count": 0, "duplicate_percentage": 0.0}

        duplicates = df.index.duplicated().sum()

        return {
            "duplicate_count": int(duplicates),
            "duplicate_percentage": (duplicates / len(df)) * 100 if len(df) > 0 else 0.0,
        }

    @staticmethod
    def calculate_comprehensive_quality(df: pd.DataFrame, column: str) -> dict[str, Any]:
        """
        Calculate comprehensive quality assessment for a column.

        Args:
            df: DataFrame with DatetimeIndex
            column: Column name to assess

        Returns:
            Dictionary with comprehensive quality metrics
        """
        if column not in df.columns:
            return {"error": f"Column {column} not found"}

        series = df[column]

        return {
            "completeness": DataQualityMetrics.calculate_completeness(series),
            "quality_score": DataQualityMetrics.calculate_quality_score(series),
            "missing_periods": DataQualityMetrics.identify_missing_periods(
                df[[column]].dropna()
            ),
            "temporal_coverage": DataQualityMetrics.calculate_temporal_coverage(df),
            "duplicates": DataQualityMetrics.detect_duplicate_timestamps(df),
        }
