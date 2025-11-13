"""Compliance result model."""

from typing import Any

from pydantic import BaseModel, Field

from core.domain.enums.parameter_type import ParameterType
from core.domain.enums.standard_type import StandardType
from core.domain.models.violation import Violation


class ComplianceResult(BaseModel):
    """
    Result of a single compliance evaluation.

    Contains compliance status, rate, and detailed violation information.
    """

    # Test identification
    test_id: str = Field(..., description="Unique test identifier")
    standard: StandardType = Field(..., description="Standard being evaluated")
    parameter: ParameterType = Field(..., description="Parameter being tested")

    # Compliance metrics
    is_compliant: bool = Field(..., description="Overall compliance status")
    compliance_rate: float = Field(..., ge=0, le=100, description="Compliance percentage (0-100)")

    # Data points
    total_points: int = Field(..., ge=0, description="Total number of data points evaluated")
    compliant_points: int = Field(..., ge=0, description="Number of compliant points")
    non_compliant_points: int = Field(..., ge=0, description="Number of non-compliant points")

    # Violations
    violations: list[Violation] = Field(
        default_factory=list, description="Detailed violation records"
    )

    # Statistics
    statistics: dict[str, float] = Field(
        default_factory=dict, description="Statistical measures (mean, std, min, max, etc.)"
    )

    # Metadata
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (threshold, filter applied, etc.)",
    )

    @property
    def violation_count(self) -> int:
        """Get total number of violations."""
        return len(self.violations)

    @property
    def has_violations(self) -> bool:
        """Check if there are any violations."""
        return len(self.violations) > 0

    def get_severity_breakdown(self) -> dict[str, int]:
        """Get count of violations by severity."""
        breakdown = {"minor": 0, "moderate": 0, "major": 0, "critical": 0}
        for violation in self.violations:
            if violation.severity in breakdown:
                breakdown[violation.severity] += 1
        return breakdown

    def get_worst_violation(self) -> Violation | None:
        """Get violation with largest deviation."""
        if not self.violations:
            return None
        return max(self.violations, key=lambda v: v.deviation)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "test_id": self.test_id,
            "standard": self.standard.value,
            "parameter": self.parameter.value,
            "is_compliant": self.is_compliant,
            "compliance_rate": round(self.compliance_rate, 2),
            "total_points": self.total_points,
            "compliant_points": self.compliant_points,
            "non_compliant_points": self.non_compliant_points,
            "violation_count": self.violation_count,
            "severity_breakdown": self.get_severity_breakdown(),
            "statistics": self.statistics,
            "metadata": self.metadata,
        }

    def __str__(self) -> str:
        """String representation."""
        return (
            f"ComplianceResult(test={self.test_id}, "
            f"rate={self.compliance_rate:.1f}%, "
            f"violations={self.violation_count})"
        )
