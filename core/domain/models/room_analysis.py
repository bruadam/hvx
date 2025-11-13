"""Room analysis result model."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from core.domain.enums.status import Status
from core.domain.models.compliance_result import ComplianceResult
from core.domain.value_objects.recommendation import Recommendation
from core.domain.value_objects.time_range import TimeRange


class RoomAnalysis(BaseModel):
    """
    Complete analysis results for a single room.

    Aggregates multiple compliance results and provides summary metrics.
    """

    # Identity
    room_id: str = Field(..., description="Room identifier")
    room_name: str = Field(..., description="Room name")
    level_id: str | None = Field(default=None, description="Parent level ID")
    building_id: str | None = Field(default=None, description="Parent building ID")

    # Analysis metadata
    analysis_timestamp: datetime = Field(
        default_factory=datetime.now, description="When analysis was performed"
    )
    status: Status = Field(default=Status.COMPLETED, description="Analysis status")

    # Data coverage
    data_time_range: TimeRange | None = Field(default=None, description="Time range of data")
    data_completeness: float = Field(
        default=0.0, ge=0, le=100, description="Data completeness percentage"
    )

    # Compliance results
    compliance_results: dict[str, ComplianceResult] = Field(
        default_factory=dict, description="Compliance results by test_id"
    )

    # Standard-specific compliance (e.g., EN 16798 categories)
    standard_compliance: dict[str, Any] = Field(
        default_factory=dict, description="Standard-specific compliance data"
    )

    # Aggregated metrics
    overall_compliance_rate: float = Field(
        default=0.0, ge=0, le=100, description="Overall compliance rate (average or standard-specific)"
    )
    data_quality_score: float = Field(
        default=0.0, ge=0, le=100, description="Overall data quality score"
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

    # Additional metadata
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    model_config = {"arbitrary_types_allowed": True}  # Allow TimeRange and Recommendation

    def add_compliance_result(
        self, test_id: str, result: ComplianceResult, standard: str | None = None
    ) -> None:
        """Add a compliance result and recalculate overall compliance.

        Args:
            test_id: The test identifier
            result: The compliance result
            standard: Optional standard type (e.g., 'en16798-1') for standard-specific aggregation
        """
        self.compliance_results[test_id] = result
        self._recalculate_overall_compliance(standard=standard)

    def _recalculate_overall_compliance(self, standard: str | None = None) -> None:
        """Recalculate overall compliance rate.

        For EN 16798-1, uses category-based logic (highest category where ALL tests pass at 95%+).
        For other standards, uses simple averaging.

        Args:
            standard: Optional standard type for standard-specific aggregation
        """
        if not self.compliance_results:
            self.overall_compliance_rate = 0.0
            return

        # EN 16798-1 uses category-based compliance logic
        if standard == "en16798-1":
            from core.analytics.aggregators.en16798_aggregator import EN16798Aggregator

            aggregator = EN16798Aggregator()
            compliance_data = aggregator.get_en16798_compliance(self)
            self.standard_compliance = compliance_data
            # Store the highest category achievement as numeric rate
            # Category I (highest performance) = 100%
            # Category II (medium performance) = 75%
            # Category III (basic performance) = 50%
            # None = 0%
            category_map: dict[str, float] = {"i": 100.0, "ii": 75.0, "iii": 50.0}
            highest_category = compliance_data.get("highest_category")
            if highest_category and isinstance(highest_category, str):
                self.overall_compliance_rate = category_map.get(highest_category, 0.0)
            else:
                self.overall_compliance_rate = 0.0
        else:
            # Default: simple average of all test compliance rates
            rates = [result.compliance_rate for result in self.compliance_results.values()]
            self.overall_compliance_rate = sum(rates) / len(rates) if rates else 0.0

    @property
    def test_count(self) -> int:
        """Get number of compliance tests performed."""
        return len(self.compliance_results)

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

    @property
    def total_violations(self) -> int:
        """Get total number of violations across all tests."""
        return sum(r.violation_count for r in self.compliance_results.values())

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
        return {
            "room_id": self.room_id,
            "room_name": self.room_name,
            "level_id": self.level_id,
            "building_id": self.building_id,
            "status": self.status.value,
            "analysis_timestamp": self.analysis_timestamp.isoformat(),
            "overall_compliance_rate": round(self.overall_compliance_rate, 2),
            "data_quality_score": round(self.data_quality_score, 2),
            "data_completeness": round(self.data_completeness, 2),
            "test_count": self.test_count,
            "passed_tests": len(self.passed_tests),
            "failed_tests": len(self.failed_tests),
            "total_violations": self.total_violations,
            "critical_issues_count": len(self.critical_issues),
            "recommendations_count": len(self.recommendations),
        }

    def __str__(self) -> str:
        """String representation."""
        return (
            f"RoomAnalysis(room={self.room_name}, "
            f"compliance={self.overall_compliance_rate:.1f}%, "
            f"tests={self.test_count})"
        )
