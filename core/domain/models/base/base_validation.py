"""Base validation models for compliance and rule checking.

Provides common structure for violations, compliance results, and rule validation.
"""

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field


TEntity = TypeVar("TEntity")


class BaseValidation(BaseModel, Generic[TEntity]):
    """
    Base class for validation results (violations, compliance checks, etc.).

    Used for:
    - Standards compliance (EN 16798-1, ASHRAE, etc.)
    - Custom rule validation
    - Threshold checking
    - Quality control

    Generic type TEntity represents what is being validated (Room, Building, etc.).
    """

    # What was measured/validated
    measured_value: float = Field(
        ...,
        description="Actual measured value"
    )

    # Expected range
    expected_min: float | None = Field(
        default=None,
        description="Expected minimum value (inclusive)"
    )

    expected_max: float | None = Field(
        default=None,
        description="Expected maximum value (inclusive)"
    )

    # Validation result
    is_valid: bool = Field(
        ...,
        description="Whether measurement passes validation"
    )

    deviation: float = Field(
        default=0.0,
        ge=0,
        description="Absolute deviation from expected range"
    )

    # Severity classification
    severity: str = Field(
        default="minor",
        description="Severity level: minor, moderate, major, critical"
    )

    # Metadata
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional validation metadata"
    )

    @property
    def deviation_percentage(self) -> float | None:
        """
        Calculate deviation as percentage of expected range.

        Returns:
            Percentage deviation, or None if range not defined
        """
        if self.expected_min is not None and self.expected_max is not None:
            range_size = self.expected_max - self.expected_min
            if range_size > 0:
                return (self.deviation / range_size) * 100
        return None

    @property
    def is_within_range(self) -> bool:
        """Check if measured value is within expected range."""
        if self.expected_min is not None and self.measured_value < self.expected_min:
            return False
        if self.expected_max is not None and self.measured_value > self.expected_max:
            return False
        return True

    def calculate_deviation(self) -> float:
        """
        Calculate deviation from expected range.

        Returns:
            0 if within range, otherwise distance from nearest bound
        """
        if self.is_within_range:
            return 0.0

        deviations = []

        if self.expected_min is not None and self.measured_value < self.expected_min:
            deviations.append(self.expected_min - self.measured_value)

        if self.expected_max is not None and self.measured_value > self.expected_max:
            deviations.append(self.measured_value - self.expected_max)

        return min(deviations) if deviations else 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "measured_value": self.measured_value,
            "expected_min": self.expected_min,
            "expected_max": self.expected_max,
            "is_valid": self.is_valid,
            "deviation": round(self.deviation, 2),
            "deviation_percentage": (
                round(self.deviation_percentage, 2)
                if self.deviation_percentage is not None
                else None
            ),
            "severity": self.severity,
            "metadata": self.metadata,
        }

    def __str__(self) -> str:
        """String representation."""
        status = "VALID" if self.is_valid else "INVALID"
        return (
            f"{self.__class__.__name__}("
            f"value={self.measured_value:.2f}, "
            f"status={status}, "
            f"deviation={self.deviation:.2f})"
        )


class ComplianceValidation(BaseValidation[TEntity]):
    """
    Extended validation for standards compliance testing.

    Adds:
    - Test identification
    - Standard reference
    - Parameter being tested
    - Compliance rate calculation
    - Multiple violations aggregation
    - Statistical measures
    """

    # Test identification
    test_id: str = Field(
        ...,
        description="Unique test identifier"
    )

    rule_id: str | None = Field(
        default=None,
        description="Rule or standard clause identifier"
    )

    # What's being tested
    parameter_name: str = Field(
        ...,
        description="Parameter being validated (e.g., 'temperature', 'CO2')"
    )

    # Compliance metrics
    compliance_rate: float = Field(
        default=0.0,
        ge=0,
        le=100,
        description="Compliance percentage (0-100)"
    )

    total_points: int = Field(
        default=0,
        ge=0,
        description="Total number of data points evaluated"
    )

    compliant_points: int = Field(
        default=0,
        ge=0,
        description="Number of compliant points"
    )

    non_compliant_points: int = Field(
        default=0,
        ge=0,
        description="Number of non-compliant points"
    )

    # Statistical measures
    statistics: dict[str, float] = Field(
        default_factory=dict,
        description="Statistical measures (mean, std, min, max, p95, etc.)"
    )

    @property
    def violation_count(self) -> int:
        """Get count of non-compliant points."""
        return self.non_compliant_points

    @property
    def has_violations(self) -> bool:
        """Check if there are any violations."""
        return self.non_compliant_points > 0

    @property
    def is_fully_compliant(self) -> bool:
        """Check if 100% compliant."""
        return self.compliance_rate >= 100.0

    def calculate_compliance_rate(self) -> float:
        """
        Calculate compliance rate from point counts.

        Returns:
            Compliance percentage (0-100)
        """
        if self.total_points == 0:
            return 0.0
        return (self.compliant_points / self.total_points) * 100

    def get_severity_level(self, compliance_rate: float | None = None) -> str:
        """
        Determine severity level based on compliance rate.

        Args:
            compliance_rate: Optional compliance rate override

        Returns:
            Severity level: minor, moderate, major, critical
        """
        rate = compliance_rate if compliance_rate is not None else self.compliance_rate

        if rate >= 95:
            return "minor"
        elif rate >= 85:
            return "moderate"
        elif rate >= 70:
            return "major"
        else:
            return "critical"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        base = super().to_dict()
        base.update({
            "test_id": self.test_id,
            "rule_id": self.rule_id,
            "parameter_name": self.parameter_name,
            "compliance_rate": round(self.compliance_rate, 2),
            "total_points": self.total_points,
            "compliant_points": self.compliant_points,
            "non_compliant_points": self.non_compliant_points,
            "violation_count": self.violation_count,
            "statistics": self.statistics,
        })
        return base

    def __str__(self) -> str:
        """String representation."""
        return (
            f"{self.__class__.__name__}("
            f"test={self.test_id}, "
            f"parameter={self.parameter_name}, "
            f"compliance={self.compliance_rate:.1f}%, "
            f"violations={self.violation_count})"
        )
