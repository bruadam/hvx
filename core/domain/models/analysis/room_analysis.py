"""Room analysis result model."""

from typing import Any

from pydantic import Field

from core.domain.models.base.base_analysis import MetricsAnalysis
from core.domain.models.validation.compliance_result import ComplianceResult
from core.domain.value_objects.recommendation import Recommendation
from core.domain.value_objects.time_range import TimeRange


class RoomAnalysis(MetricsAnalysis[None, ComplianceResult]):
    """
    Complete analysis results for a single room.

    Aggregates multiple compliance results and provides summary metrics.
    Extends BaseAnalysis with room-specific fields and compliance logic.
    """

    # Parent references (room-specific)
    level_id: str | None = Field(default=None, description="Parent level ID")
    building_id: str | None = Field(default=None, description="Parent building ID")

    # Data coverage (room-specific)
    data_time_range: TimeRange | None = Field(default=None, description="Time range of data")
    data_completeness: float = Field(
        default=0.0, ge=0, le=100, description="Data completeness percentage"
    )

    # Metrics (from MetricsAnalysis pattern)
    compliance_rate: float = Field(
        default=0.0, ge=0, le=100, description="Overall compliance rate"
    )
    quality_score: float = Field(
        default=0.0, ge=0, le=100, description="Data quality score"
    )

    # Compliance results (room-specific structure)
    compliance_results: dict[str, ComplianceResult] = Field(
        default_factory=dict, description="Compliance results by test_id"
    )

    # Standard-specific compliance (e.g., EN 16798 categories)
    standard_compliance: dict[str, Any] = Field(
        default_factory=dict, description="Standard-specific compliance data"
    )

    # Test aggregations
    test_aggregations: dict[str, dict[str, Any]] = Field(
        default_factory=dict, description="Aggregated results per test"
    )

    # Statistics by parameter
    parameter_statistics: dict[str, dict[str, float]] = Field(
        default_factory=dict, description="Statistics for each parameter"
    )

    # Issues and recommendations
    critical_issues: list[str] = Field(default_factory=list, description="Critical issues found")
    recommendations: list[Recommendation] = Field(
        default_factory=list, description="Recommended actions"
    )

    # Override base field names for room-specific terminology
    @property
    def room_id(self) -> str:
        """Alias for entity_id."""
        return self.entity_id

    @property
    def room_name(self) -> str:
        """Alias for entity_name."""
        return self.entity_name

    @property
    def overall_compliance_rate(self) -> float:
        """Alias for compliance_rate."""
        return self.compliance_rate

    @property
    def data_quality_score(self) -> float:
        """Alias for quality_score."""
        return self.quality_score

    @property
    def test_count(self) -> int:
        """Get number of compliance tests performed."""
        return len(self.compliance_results)

    @property
    def total_violations(self) -> int:
        """Get total number of violations across all tests."""
        return sum(r.violation_count for r in self.compliance_results.values())

    def model_post_init(self, __context: Any) -> None:
        """Post-initialization to sync compliance results with base test_aggregations."""
        # Convert compliance_results to test_aggregations format
        for test_id, result in self.compliance_results.items():
            self.test_aggregations[test_id] = result.to_dict()

    def add_compliance_result(
        self, test_id: str, result: ComplianceResult, standard: str | None = None
    ) -> None:
        """Add a compliance result and recalculate overall compliance.

        Args:
            test_id: The test identifier
            result: The compliance result
            standard: Optional standard type (e.g., 'en16798') for standard-specific aggregation
        """
        self.compliance_results[test_id] = result
        self.test_aggregations[test_id] = result.to_dict()
        self._recalculate_overall_compliance(standard=standard)

    def _recalculate_overall_compliance(self, standard: str | None = None) -> None:
        """Recalculate overall compliance rate based on test results.

        Note: For EN 16798, standard compliance (category determination) is separate
        from test compliance and should be set via set_standard_compliance() using
        the EN16798StandardCalculator.

        Args:
            standard: Optional standard type (not used for EN 16798)
        """
        if not self.compliance_results:
            self.compliance_rate = 0.0
            return

        # Calculate average compliance rate from all test results
        rates = [result.compliance_rate for result in self.compliance_results.values()]
        self.compliance_rate = sum(rates) / len(rates) if rates else 0.0

    def set_standard_compliance(self, standard: str, compliance_data: dict[str, Any]) -> None:
        """Set standard-specific compliance data (e.g., EN 16798 category).

        This is separate from test compliance and should be calculated externally
        using the appropriate standard calculator (e.g., EN16798StandardCalculator).

        Args:
            standard: The standard identifier (e.g., 'en16798-1')
            compliance_data: Standard-specific compliance data from calculator
        """
        self.standard_compliance[standard] = compliance_data

    @property
    def passed_tests(self) -> list[str]:
        """Get IDs of tests that passed (100% compliance)."""
        return [
            test_id
            for test_id, result in self.compliance_results.items()
            if result.is_compliant
        ]

    @property
    def failed_tests(self) -> list[str]:
        """Get IDs of tests that failed."""
        return [
            test_id
            for test_id, result in self.compliance_results.items()
            if not result.is_compliant
        ]

    def get_result_by_test(self, test_id: str) -> ComplianceResult | None:
        """Get compliance result for specific test."""
        return self.compliance_results.get(test_id)

    def get_results_by_parameter(self, parameter: str) -> list[ComplianceResult]:
        """Get all compliance results for a specific parameter."""
        return [
            result
            for result in self.compliance_results.values()
            if result.parameter.value == parameter
        ]

    def to_summary_dict(self) -> dict[str, Any]:
        """Get summary as dictionary."""
        base_summary = super().to_summary_dict()
        base_summary.update({
            "room_id": self.room_id,
            "room_name": self.room_name,
            "level_id": self.level_id,
            "building_id": self.building_id,
            "overall_compliance_rate": round(self.overall_compliance_rate, 2),
            "data_quality_score": round(self.quality_score, 2),
            "data_completeness": round(self.data_completeness, 2),
            "passed_tests": len(self.passed_tests),
            "failed_tests": len(self.failed_tests),
        })
        return base_summary

    def __str__(self) -> str:
        """String representation."""
        return (
            f"RoomAnalysis(room={self.room_name}, "
            f"compliance={self.overall_compliance_rate:.1f}%, "
            f"tests={self.test_count})"
        )
