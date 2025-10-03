"""Building level/floor model."""

from typing import Optional, List
from pydantic import BaseModel, Field, field_validator

from src.core.models.domain.room import Room
from src.core.models.domain.brick_base import BrickSchemaSpace


class Level(BrickSchemaSpace):
    """Building level/floor with rooms and Brick Schema compatibility.
    
    This model extends BrickSchemaSpace to represent building floors
    with semantic interoperability.
    """
    
    # Default Brick type for levels/floors
    _default_brick_type: str = "brick:Floor"

    id: str = Field(..., description="Unique level identifier")
    name: str = Field(..., description="Human-readable level name (e.g., 'Ground Floor', '1st Floor')")
    building_id: str = Field(..., description="ID of the building this level belongs to")
    floor_number: Optional[int] = Field(None, description="Floor number (0 for ground, negative for basement)")
    rooms: List[Room] = Field(default_factory=list, description="Rooms on this level")

    @field_validator('id', 'name', 'building_id')
    @classmethod
    def validate_non_empty_strings(cls, v):
        if not v or not v.strip():
            raise ValueError("String fields cannot be empty")
        return v.strip()
    
    def __init__(self, **data):
        """Initialize Level with Brick Schema support."""
        super().__init__(**data)
        
        # Auto-generate Brick URI if not provided
        if not self.brick_uri and hasattr(self, 'id') and hasattr(self, 'building_id'):
            self.brick_uri = f"urn:building:{self.building_id}:floor:{self.id}"
        
        # Set Brick metadata
        if self.floor_number is not None:
            self.brick_metadata['floorNumber'] = self.floor_number

    def add_room(self, room: Room) -> None:
        """Add a room to this level."""
        if room.level_id and room.level_id != self.id:
            room.level_id = self.id

        # Check for duplicate room IDs
        existing_ids = {r.id for r in self.rooms}
        if room.id in existing_ids:
            raise ValueError(f"Room with ID {room.id} already exists in level {self.id}")

        self.rooms.append(room)
        
        # Add Brick Schema relationship
        if self.brick_uri and room.brick_uri:
            self.add_brick_relationship('hasPart', room.brick_uri)
            room.add_brick_relationship('isPartOf', self.brick_uri)

    def get_room(self, room_id: str) -> Optional[Room]:
        """Get a room by ID."""
        for room in self.rooms:
            if room.id == room_id:
                return room
        return None

    def get_room_count(self) -> int:
        """Get number of rooms on this level."""
        return len(self.rooms)

