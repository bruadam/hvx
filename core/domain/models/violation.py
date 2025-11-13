"""Violation domain model."""

from datetime import datetime

from pydantic import BaseModel, Field


class Violation(BaseModel):
    """
    Represents a single compliance violation.

    Records when and how a measurement failed to meet compliance threshold.
    """

    timestamp: datetime = Field(..., description="When violation occurred")
    measured_value: float = Field(..., description="Actual measured value")
    expected_min: float | None = Field(default=None, description="Expected minimum value")
    expected_max: float | None = Field(default=None, description="Expected maximum value")
    deviation: float = Field(..., description="How far from compliance (absolute value)")
    severity: str = Field(
        default="minor", description="Severity: minor, moderate, major, critical"
    )

    model_config = {"frozen": True}  # Immutable

    @property
    def deviation_percentage(self) -> float | None:
        """Calculate deviation as percentage of expected range."""
        if self.expected_min is not None and self.expected_max is not None:
            range_size = self.expected_max - self.expected_min
            if range_size > 0:
                return (self.deviation / range_size) * 100
        return None

    def __str__(self) -> str:
        """String representation."""
        return (
            f"Violation(value={self.measured_value:.2f}, "
            f"deviation={self.deviation:.2f}, "
            f"at {self.timestamp.isoformat()})"
        )
