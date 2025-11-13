"""Compliance result model."""

from typing import Any

from pydantic import Field

from core.domain.enums.parameter_type import ParameterType
from core.domain.enums.standard_type import StandardType
from core.domain.models.base.base_validation import ComplianceValidation
from core.domain.models.validation.violation import Violation


class ComplianceResult(ComplianceValidation[None]):
    """
    Result of a single compliance evaluation.

    Contains compliance status, rate, and detailed violation information.
    Extends ComplianceValidation with standard and parameter type enums,
    and detailed violation tracking.
    """

    # Extend base with typed enums
    standard: StandardType = Field(..., description="Standard being evaluated")
    parameter: ParameterType = Field(..., description="Parameter being tested")

    # Override parameter_name from base to use ParameterType
    parameter_name: str = Field(default="", description="Parameter name (auto-populated from parameter)")

    # Detailed violations list
    violations: list[Violation] = Field(
        default_factory=list, description="Detailed violation records"
    )

    # Compliance status (derived from compliance_rate)
    is_compliant: bool = Field(default=False, description="Overall compliance status")

    def model_post_init(self, __context: Any) -> None:
        """Post-initialization to sync parameter_name with parameter enum."""
        if self.parameter:
            object.__setattr__(self, "parameter_name", self.parameter.value)

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
        base_dict = super().to_dict()
        base_dict.update({
            "standard": self.standard.value,
            "parameter": self.parameter.value,
            "is_compliant": self.is_compliant,
            "severity_breakdown": self.get_severity_breakdown(),
            "violations": [v.to_dict() for v in self.violations],
        })
        return base_dict

    def __str__(self) -> str:
        """String representation."""
        return (
            f"ComplianceResult(test={self.test_id}, "
            f"rate={self.compliance_rate:.1f}%, "
            f"violations={self.violation_count})"
        )
