"""Priority levels for recommendations and issues."""

from enum import Enum


class Priority(str, Enum):
    """Priority levels for recommendations and actions."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    def __str__(self) -> str:
        """Return the value as string."""
        return self.value
