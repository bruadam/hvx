"""Violation domain model."""

from datetime import datetime

from pydantic import Field

from core.domain.models.base.base_validation import BaseValidation


class Violation(BaseValidation[None]):
    """
    Represents a single compliance violation.

    Records when and how a measurement failed to meet compliance threshold.
    Extends BaseValidation with timestamp for point-in-time violations.
    """

    timestamp: datetime = Field(..., description="When violation occurred")

    # Override is_valid to always be False for violations
    is_valid: bool = Field(default=False, description="Always False for violations")

    model_config = {"frozen": True}  # Immutable

    def __str__(self) -> str:
        """String representation."""
        return (
            f"Violation(value={self.measured_value:.2f}, "
            f"deviation={self.deviation:.2f}, "
            f"at {self.timestamp.isoformat()})"
        )
