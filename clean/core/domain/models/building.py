"""Building domain entity."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from core.domain.enums.building_type import BuildingType


class Building(BaseModel):
    """
    Building entity representing a physical building with hierarchical structure.

    Contains levels, which contain rooms.
    """

    # Identity
    id: str = Field(..., description="Unique building identifier")
    name: str = Field(..., description="Building name or address")

    # Classification
    building_type: BuildingType = Field(
        default=BuildingType.OFFICE, description="Type of building"
    )

    # Hierarchy
    level_ids: List[str] = Field(default_factory=list, description="IDs of levels in building")
    room_ids: List[str] = Field(
        default_factory=list, 
        description="IDs of rooms in building (can be assigned directly without levels)"
    )

    # Physical properties
    total_area: Optional[float] = Field(default=None, ge=0, description="Total building area in m²")
    year_built: Optional[int] = Field(
        default=None, ge=1800, le=2100, description="Year of construction"
    )

    # Location
    address: Optional[str] = Field(default=None, description="Building address")
    city: Optional[str] = Field(default=None, description="City")
    country: Optional[str] = Field(default=None, description="Country")
    latitude: Optional[float] = Field(default=None, ge=-90, le=90, description="Latitude")
    longitude: Optional[float] = Field(default=None, ge=-180, le=180, description="Longitude")

    # Metadata
    attributes: Dict[str, str] = Field(
        default_factory=dict,
        description="Custom attributes (e.g., HVAC type, insulation level)",
    )

    def add_level(self, level_id: str) -> None:
        """
        Add a level to this building.

        Args:
            level_id: Level identifier to add
        """
        if level_id not in self.level_ids:
            self.level_ids.append(level_id)

    def remove_level(self, level_id: str) -> bool:
        """
        Remove a level from this building.

        Args:
            level_id: Level identifier to remove

        Returns:
            True if level was removed, False if not found
        """
        if level_id in self.level_ids:
            self.level_ids.remove(level_id)
            return True
        return False

    def has_level(self, level_id: str) -> bool:
        """Check if building contains a specific level."""
        return level_id in self.level_ids

    def add_room(self, room_id: str) -> None:
        """
        Add a room directly to this building (without assigning to a level).

        Args:
            room_id: Room identifier to add
        """
        if room_id not in self.room_ids:
            self.room_ids.append(room_id)

    def add_rooms(self, room_ids: List[str]) -> None:
        """
        Add multiple rooms directly to this building.

        Args:
            room_ids: List of room identifiers to add
        """
        for room_id in room_ids:
            self.add_room(room_id)

    def remove_room(self, room_id: str) -> bool:
        """
        Remove a room from this building.

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
        """Check if building contains a specific room."""
        return room_id in self.room_ids

    @property
    def level_count(self) -> int:
        """Get number of levels in building."""
        return len(self.level_ids)

    @property
    def room_count(self) -> int:
        """Get number of rooms directly assigned to building."""
        return len(self.room_ids)

    @property
    def total_rooms(self) -> int:
        """Get total number of rooms (direct rooms + rooms in levels)."""
        return len(self.room_ids)

    @property
    def typical_opening_hours(self) -> tuple[int, int]:
        """Get typical opening hours based on building type."""
        return self.building_type.typical_occupancy_hours

    def get_summary(self) -> Dict[str, Any]:
        """Get summary information about this building."""
        return {
            "id": self.id,
            "name": self.name,
            "building_type": self.building_type.value,
            "level_count": self.level_count,
            "room_count": self.room_count,
            "total_rooms": self.total_rooms,
            "total_area_m2": self.total_area,
            "year_built": self.year_built,
            "location": {
                "address": self.address,
                "city": self.city,
                "country": self.country,
                "coordinates": (
                    {"lat": self.latitude, "lon": self.longitude}
                    if self.latitude and self.longitude
                    else None
                ),
            },
            "level_ids": self.level_ids,
            "room_ids": self.room_ids,
        }

    def __str__(self) -> str:
        """String representation."""
        return f"Building(name={self.name}, type={self.building_type.value}, levels={self.level_count}, rooms={self.room_count})"

    def __repr__(self) -> str:
        """Repr representation."""
        return (
            f"Building(id={self.id!r}, name={self.name!r}, "
            f"type={self.building_type.value})"
        )
