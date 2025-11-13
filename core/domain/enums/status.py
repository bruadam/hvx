"""Status enumeration for analysis and operations."""

from enum import Enum


class Status(str, Enum):
    """Status of analysis or operation."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"

    @property
    def is_terminal(self) -> bool:
        """Check if status is terminal (no further processing)."""
        return self in (self.COMPLETED, self.FAILED)

    @property
    def is_successful(self) -> bool:
        """Check if status indicates success."""
        return self in (self.COMPLETED, self.PARTIAL)
