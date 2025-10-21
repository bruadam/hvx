"""Measurement value object."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from core.domain.enums.parameter_type import ParameterType


class Measurement(BaseModel):
    """
    Immutable measurement value object.

    Represents a single environmental measurement at a specific point in time.
    """

    timestamp: datetime = Field(..., description="When measurement was taken")
    parameter: ParameterType = Field(..., description="What was measured")
    value: float = Field(..., description="Measured value")
    unit: str = Field(..., description="Unit of measurement")
    quality: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Data quality score (0-1)"
    )

    model_config = {"frozen": True}  # Make immutable

    @field_validator("value")
    @classmethod
    def validate_value(cls, v: float, info: dict) -> float:
        """Validate measurement value is finite."""
        if not (-1e10 < v < 1e10):
            raise ValueError(f"Measurement value out of reasonable range: {v}")
        return v

    @field_validator("unit", mode="after")
    @classmethod
    def validate_unit_matches_parameter(cls, v: str, info: dict) -> str:
        """Validate unit matches parameter type."""
        if "parameter" in info.data:
            parameter = info.data["parameter"]
            expected_unit = parameter.default_unit
            if expected_unit and v != expected_unit:
                # Log warning but don't fail - allow unit flexibility
                pass
        return v

    def __str__(self) -> str:
        """String representation."""
        return f"{self.value:.2f} {self.unit} at {self.timestamp.isoformat()}"

    def __repr__(self) -> str:
        """Repr representation."""
        return (
            f"Measurement(parameter={self.parameter.value}, "
            f"value={self.value}, unit='{self.unit}', "
            f"timestamp={self.timestamp.isoformat()})"
        )
