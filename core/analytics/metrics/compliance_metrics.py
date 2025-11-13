"""Compliance metrics calculator."""

from typing import Any

import numpy as np
import pandas as pd

from core.domain.models.violation import Violation
from core.domain.value_objects.compliance_threshold import ComplianceThreshold


class ComplianceMetrics:
    """Calculate compliance metrics for threshold-based evaluation."""

    @staticmethod
    def calculate_compliance_rate(
        series: pd.Series, threshold: ComplianceThreshold
    ) -> float:
        """
        Calculate compliance rate for a threshold.

        Args:
            series: Pandas Series with measurement values
            threshold: Compliance threshold to evaluate against

        Returns:
            Compliance rate as percentage (0-100)
        """
        clean_data = series.dropna()

        if len(clean_data) == 0:
            return 0.0

        compliant = sum(threshold.is_compliant(val) for val in clean_data)
        return (compliant / len(clean_data)) * 100

    @staticmethod
    def identify_violations(
        series: pd.Series, threshold: ComplianceThreshold, max_violations: int = 1000
    ) -> list[Violation]:
        """
        Identify all violations in the data.

        Args:
            series: Pandas Series with DatetimeIndex and measurement values
            threshold: Compliance threshold
            max_violations: Maximum number of violations to return

        Returns:
            List of Violation objects
        """
        clean_data = series.dropna()
        violations = []

        for timestamp, value in clean_data.items():
            if not threshold.is_compliant(value):
                deviation = abs(threshold.distance_from_compliance(value))

                # Determine severity based on deviation
                if threshold.threshold_type == "bidirectional":
                    range_size = threshold.upper_limit - threshold.lower_limit
                    severity_ratio = deviation / range_size if range_size > 0 else 0
                else:
                    severity_ratio = deviation / abs(value) if value != 0 else 0

                if severity_ratio > 0.5:
                    severity = "critical"
                elif severity_ratio > 0.3:
                    severity = "major"
                elif severity_ratio > 0.1:
                    severity = "moderate"
                else:
                    severity = "minor"

                violation = Violation(
                    timestamp=timestamp.to_pydatetime() if hasattr(timestamp, 'to_pydatetime') else timestamp,
                    measured_value=float(value),
                    expected_min=threshold.lower_limit,
                    expected_max=threshold.upper_limit,
                    deviation=deviation,
                    severity=severity,
                )

                violations.append(violation)

                if len(violations) >= max_violations:
                    break

        return violations

    @staticmethod
    def calculate_exceedance_hours(
        series: pd.Series, threshold: ComplianceThreshold
    ) -> dict[str, float]:
        """
        Calculate hours of exceedance.

        Args:
            series: Pandas Series with DatetimeIndex
            threshold: Compliance threshold

        Returns:
            Dictionary with exceedance hours metrics
        """
        clean_data = series.dropna()

        if len(clean_data) == 0:
            return {"total_hours": 0.0, "exceedance_hours": 0.0, "exceedance_percentage": 0.0}

        # Assume hourly data or interpolate
        non_compliant = sum(not threshold.is_compliant(val) for val in clean_data)

        # Calculate hours (assuming data is roughly hourly)
        total_hours = len(clean_data)
        exceedance_hours = non_compliant

        return {
            "total_hours": float(total_hours),
            "exceedance_hours": float(exceedance_hours),
            "exceedance_percentage": (exceedance_hours / total_hours * 100) if total_hours > 0 else 0.0,
        }

    @staticmethod
    def calculate_consecutive_violations(
        series: pd.Series, threshold: ComplianceThreshold
    ) -> dict[str, Any]:
        """
        Calculate statistics about consecutive violations.

        Args:
            series: Pandas Series with DatetimeIndex
            threshold: Compliance threshold

        Returns:
            Dictionary with consecutive violation metrics
        """
        clean_data = series.dropna()

        if len(clean_data) == 0:
            return {
                "max_consecutive": 0,
                "avg_consecutive": 0.0,
                "violation_periods": 0,
            }

        # Create boolean array of non-compliance
        non_compliant = np.array([not threshold.is_compliant(val) for val in clean_data])

        # Find consecutive sequences
        consecutive_lengths = []
        current_length = 0

        for is_violation in non_compliant:
            if is_violation:
                current_length += 1
            else:
                if current_length > 0:
                    consecutive_lengths.append(current_length)
                    current_length = 0

        if current_length > 0:
            consecutive_lengths.append(current_length)

        if not consecutive_lengths:
            return {
                "max_consecutive": 0,
                "avg_consecutive": 0.0,
                "violation_periods": 0,
            }

        return {
            "max_consecutive": int(max(consecutive_lengths)),
            "avg_consecutive": float(np.mean(consecutive_lengths)),
            "violation_periods": len(consecutive_lengths),
        }

    @staticmethod
    def calculate_temporal_compliance(
        series: pd.Series, threshold: ComplianceThreshold, freq: str = "D"
    ) -> pd.Series:
        """
        Calculate compliance rate over time periods.

        Args:
            series: Pandas Series with DatetimeIndex
            threshold: Compliance threshold
            freq: Frequency for grouping

        Returns:
            Series with compliance rates per period
        """
        clean_data = series.dropna()

        if len(clean_data) == 0:
            return pd.Series()

        # Group by frequency and calculate compliance for each period
        def calc_compliance(group):
            if len(group) == 0:
                return 0.0
            compliant = sum(threshold.is_compliant(val) for val in group)
            return (compliant / len(group)) * 100

        return clean_data.resample(freq).apply(calc_compliance)
