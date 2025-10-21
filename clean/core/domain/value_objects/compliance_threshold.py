"""Compliance threshold value object."""

from typing import Optional, Literal

from pydantic import BaseModel, Field, field_validator


class ComplianceThreshold(BaseModel):
    """
    Immutable compliance threshold value object.

    Represents acceptable ranges or limits for environmental parameters.
    Supports both bidirectional (range) and unidirectional (single limit) thresholds.
    """

    lower_limit: Optional[float] = Field(default=None, description="Lower acceptable limit")
    upper_limit: Optional[float] = Field(default=None, description="Upper acceptable limit")
    threshold_type: Literal["bidirectional", "unidirectional_min", "unidirectional_max"] = Field(
        ..., description="Type of threshold"
    )
    unit: str = Field(..., description="Unit of measurement")
    tolerance: float = Field(default=0.0, ge=0.0, description="Tolerance margin")

    model_config = {"frozen": True}

    @field_validator("lower_limit", "upper_limit")
    @classmethod
    def validate_limits(cls, v: Optional[float], info: dict) -> Optional[float]:
        """Validate limits are reasonable."""
        if v is not None and not (-1e10 < v < 1e10):
            raise ValueError(f"Limit value out of reasonable range: {v}")
        return v

    def model_post_init(self, __context: dict) -> None:
        """Additional validation after model initialization."""
        if self.threshold_type == "bidirectional":
            if self.lower_limit is None or self.upper_limit is None:
                raise ValueError("Bidirectional threshold requires both lower and upper limits")
            if self.lower_limit >= self.upper_limit:
                raise ValueError("Lower limit must be less than upper limit")
        elif self.threshold_type == "unidirectional_min":
            if self.lower_limit is None:
                raise ValueError("Unidirectional min threshold requires lower limit")
        elif self.threshold_type == "unidirectional_max":
            if self.upper_limit is None:
                raise ValueError("Unidirectional max threshold requires upper limit")

    def is_compliant(self, value: float) -> bool:
        """Check if a value is compliant with this threshold."""
        if self.threshold_type == "bidirectional":
            assert self.lower_limit is not None and self.upper_limit is not None
            return (self.lower_limit - self.tolerance) <= value <= (
                self.upper_limit + self.tolerance
            )
        elif self.threshold_type == "unidirectional_min":
            assert self.lower_limit is not None
            return value >= (self.lower_limit - self.tolerance)
        elif self.threshold_type == "unidirectional_max":
            assert self.upper_limit is not None
            return value <= (self.upper_limit + self.tolerance)
        return False

    def distance_from_compliance(self, value: float) -> float:
        """
        Calculate distance from compliance.

        Returns 0 if compliant, positive if too high, negative if too low.
        """
        if self.threshold_type == "bidirectional":
            assert self.lower_limit is not None and self.upper_limit is not None
            if value < self.lower_limit:
                return self.lower_limit - value
            elif value > self.upper_limit:
                return value - self.upper_limit
            return 0.0
        elif self.threshold_type == "unidirectional_min":
            assert self.lower_limit is not None
            if value < self.lower_limit:
                return self.lower_limit - value
            return 0.0
        elif self.threshold_type == "unidirectional_max":
            assert self.upper_limit is not None
            if value > self.upper_limit:
                return value - self.upper_limit
            return 0.0
        return 0.0

    def __str__(self) -> str:
        """String representation."""
        if self.threshold_type == "bidirectional":
            return f"{self.lower_limit}-{self.upper_limit} {self.unit}"
        elif self.threshold_type == "unidirectional_min":
            return f"≥ {self.lower_limit} {self.unit}"
        elif self.threshold_type == "unidirectional_max":
            return f"≤ {self.upper_limit} {self.unit}"
        return f"threshold ({self.unit})"
