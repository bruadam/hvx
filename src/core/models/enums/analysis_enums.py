"""Analysis-related enumerations."""

from enum import Enum


class Severity(str, Enum):
    """Severity levels for analysis findings."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Status(str, Enum):
    """Analysis completion status."""
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"
    PENDING = "pending"
