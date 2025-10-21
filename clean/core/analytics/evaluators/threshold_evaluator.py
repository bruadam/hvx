"""Threshold-based evaluator."""

import pandas as pd
from typing import Dict, Any, Optional

from core.analytics.evaluators.base_evaluator import BaseEvaluator
from core.analytics.metrics.statistical_metrics import StatisticalMetrics
from core.analytics.metrics.compliance_metrics import ComplianceMetrics
from core.domain.models.compliance_result import ComplianceResult
from core.domain.value_objects.compliance_threshold import ComplianceThreshold
from core.domain.enums.parameter_type import ParameterType
from core.domain.enums.standard_type import StandardType


class ThresholdEvaluator(BaseEvaluator):
    """
    General-purpose threshold-based evaluator.

    Evaluates compliance against bidirectional or unidirectional thresholds.
    """

    def __init__(
        self,
        standard: StandardType,
        threshold: ComplianceThreshold,
        compliance_level: float = 95.0,
    ):
        """
        Initialize threshold evaluator.

        Args:
            standard: Standard being evaluated
            threshold: Compliance threshold to evaluate against
            compliance_level: Minimum compliance rate to be considered compliant (default 95%)
        """
        super().__init__(standard)
        self.threshold = threshold
        self.compliance_level = compliance_level

    def evaluate(
        self,
        data: pd.Series,
        parameter: ParameterType,
        test_id: str,
        **kwargs: Any
    ) -> ComplianceResult:
        """
        Evaluate compliance against threshold.

        Args:
            data: Time series data with DatetimeIndex
            parameter: Parameter being evaluated
            test_id: Unique test identifier
            **kwargs: Additional parameters (not used)

        Returns:
            ComplianceResult with detailed evaluation
        """
        # Clean data
        clean_data = data.dropna()

        if len(clean_data) == 0:
            return self._create_empty_result(test_id, parameter)

        # Calculate compliance metrics
        compliance_rate = ComplianceMetrics.calculate_compliance_rate(
            clean_data, self.threshold
        )

        is_compliant = compliance_rate >= self.compliance_level

        # Count points
        total_points = len(clean_data)
        compliant_points = int((compliance_rate / 100) * total_points)
        non_compliant_points = total_points - compliant_points

        # Identify violations
        violations = ComplianceMetrics.identify_violations(
            clean_data, self.threshold, max_violations=100
        )

        # Calculate statistics
        stats = StatisticalMetrics.calculate_basic_statistics(clean_data)

        # Add compliance-specific statistics
        exceedance = ComplianceMetrics.calculate_exceedance_hours(
            clean_data, self.threshold
        )
        consecutive = ComplianceMetrics.calculate_consecutive_violations(
            clean_data, self.threshold
        )

        stats.update(exceedance)
        stats.update(consecutive)

        # Build metadata
        metadata = {
            "threshold_type": self.threshold.threshold_type,
            "threshold_lower": self.threshold.lower_limit,
            "threshold_upper": self.threshold.upper_limit,
            "threshold_unit": self.threshold.unit,
            "compliance_level_required": self.compliance_level,
            "parameter": parameter.value,
        }

        return ComplianceResult(
            test_id=test_id,
            standard=self.standard,
            parameter=parameter,
            is_compliant=is_compliant,
            compliance_rate=compliance_rate,
            total_points=total_points,
            compliant_points=compliant_points,
            non_compliant_points=non_compliant_points,
            violations=violations,
            statistics=stats,
            metadata=metadata,
        )

    def _create_empty_result(
        self, test_id: str, parameter: ParameterType
    ) -> ComplianceResult:
        """Create empty result when no data available."""
        return ComplianceResult(
            test_id=test_id,
            standard=self.standard,
            parameter=parameter,
            is_compliant=False,
            compliance_rate=0.0,
            total_points=0,
            compliant_points=0,
            non_compliant_points=0,
            violations=[],
            statistics={},
            metadata={"error": "No data available for evaluation"},
        )
