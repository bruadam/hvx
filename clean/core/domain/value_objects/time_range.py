"""Time range value object."""

from datetime import datetime, timedelta
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class TimeRange(BaseModel):
    """
    Immutable time range value object.

    Represents a continuous period of time with start and end.
    """

    start: datetime = Field(..., description="Start of time range (inclusive)")
    end: datetime = Field(..., description="End of time range (inclusive)")

    model_config = {"frozen": True}

    @field_validator("end")
    @classmethod
    def validate_end_after_start(cls, v: datetime, info: dict) -> datetime:
        """Validate end is after start."""
        if "start" in info.data and v <= info.data["start"]:
            raise ValueError("End time must be after start time")
        return v

    @property
    def duration(self) -> timedelta:
        """Get duration of time range."""
        return self.end - self.start

    @property
    def duration_days(self) -> float:
        """Get duration in days."""
        return self.duration.total_seconds() / 86400

    @property
    def duration_hours(self) -> float:
        """Get duration in hours."""
        return self.duration.total_seconds() / 3600

    def contains(self, timestamp: datetime) -> bool:
        """Check if timestamp is within this range (inclusive)."""
        return self.start <= timestamp <= self.end

    def overlaps_with(self, other: "TimeRange") -> bool:
        """Check if this range overlaps with another range."""
        return not (self.end < other.start or self.start > other.end)

    def intersection(self, other: "TimeRange") -> Optional["TimeRange"]:
        """Get intersection with another time range, or None if no overlap."""
        if not self.overlaps_with(other):
            return None

        start = max(self.start, other.start)
        end = min(self.end, other.end)
        return TimeRange(start=start, end=end)

    def __str__(self) -> str:
        """String representation."""
        return f"{self.start.isoformat()} to {self.end.isoformat()} ({self.duration_days:.1f} days)"

    def __repr__(self) -> str:
        """Repr representation."""
        return f"TimeRange(start={self.start.isoformat()}, end={self.end.isoformat()})"
