"""Level domain entity."""

from typing import Any

from pydantic import BaseModel, Field


class Level(BaseModel):
    """
    Level/floor entity representing a single floor in a building.

    Aggregates multiple rooms on the same floor level.
    """

    # Identity
    id: str = Field(..., description="Unique level identifier")
    name: str = Field(..., description="Level name (e.g., 'Ground Floor', 'Level 1')")

    # Hierarchy
    building_id: str | None = Field(default=None, description="Parent building ID")
    floor_number: int = Field(..., description="Floor number (0=ground, negative=basement)")

    # Contained rooms
    room_ids: list[str] = Field(default_factory=list, description="IDs of rooms on this level")

    # Metadata
    total_area: float | None = Field(default=None, ge=0, description="Total floor area in m²")
    attributes: dict[str, str] = Field(
        default_factory=dict, description="Custom attributes (e.g., usage, access type)"
    )

    def add_room(self, room_id: str) -> None:
        """
        Add a room to this level.

        Args:
            room_id: Room identifier to add
        """
        if room_id not in self.room_ids:
            self.room_ids.append(room_id)

    def remove_room(self, room_id: str) -> bool:
        """
        Remove a room from this level.

        Args:
            room_id: Room identifier to remove

        Returns:
            True if room was removed, False if not found
        """
        if room_id in self.room_ids:
            self.room_ids.remove(room_id)
            return True
        return False

    def has_room(self, room_id: str) -> bool:
        """Check if level contains a specific room."""
        return room_id in self.room_ids

    @property
    def room_count(self) -> int:
        """Get number of rooms on this level."""
        return len(self.room_ids)

    def get_summary(self) -> dict[str, Any]:
        """Get summary information about this level."""
        return {
            "id": self.id,
            "name": self.name,
            "building_id": self.building_id,
            "floor_number": self.floor_number,
            "room_count": self.room_count,
            "total_area_m2": self.total_area,
            "room_ids": self.room_ids,
        }

    def __str__(self) -> str:
        """String representation."""
        return f"Level(name={self.name}, floor={self.floor_number}, rooms={self.room_count})"

    def __repr__(self) -> str:
        """Repr representation."""
        return f"Level(id={self.id!r}, name={self.name!r}, floor_number={self.floor_number})"
