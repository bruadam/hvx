"""Recommendation value object."""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

from core.domain.enums.priority import Priority


@dataclass
class Recommendation:
    """A recommendation with title, description, and priority."""

    title: str
    description: str
    priority: Priority = Priority.MEDIUM
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert recommendation to dictionary."""
        return {
            "title": self.title,
            "description": self.description,
            "priority": self.priority.value,
            "tags": self.tags,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Recommendation":
        """Create recommendation from dictionary."""
        priority_str = data.get("priority", "medium")
        try:
            priority = Priority(priority_str)
        except ValueError:
            priority = Priority.MEDIUM

        return cls(
            title=data.get("title", ""),
            description=data.get("description", ""),
            priority=priority,
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
        )

    @classmethod
    def from_string(cls, text: str, priority: Priority = Priority.MEDIUM) -> "Recommendation":
        """Create recommendation from a simple string."""
        return cls(
            title="Recommendation",
            description=text,
            priority=priority,
        )
