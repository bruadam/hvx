"""Building model."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
import numpy as np

from src.core.models.domain.level import Level
from src.core.models.domain.room import Room
from src.core.models.domain.climate import ClimateData
from src.core.models.domain.brick_base import BrickSchemaSpace


class Building(BrickSchemaSpace):
    """Enhanced building model with levels, climate data, and Brick Schema compatibility.
    
    This model extends BrickSchemaSpace to represent buildings with semantic
    interoperability while maintaining analytical capabilities.
    """
    
    # Default Brick type for buildings
    _default_brick_type: str = "brick:Building"

    id: str = Field(..., description="Unique building identifier")
    name: str = Field(..., description="Human-readable building name")
    address: Optional[str] = Field(None, description="Building address")
    city: Optional[str] = Field(None, description="City")
    postal_code: Optional[str] = Field(None, description="Postal code")
    country: Optional[str] = Field(default="Denmark", description="Country")
    construction_year: Optional[int] = Field(None, description="Year of construction")
    total_area_m2: Optional[float] = Field(None, description="Total building area in square meters", gt=0)

    # Hierarchical structure
    levels: List[Level] = Field(default_factory=list, description="Building levels/floors")
    rooms: List[Room] = Field(default_factory=list, description="All rooms in building (flat structure)")

    # Climate data
    climate_data: Optional[ClimateData] = Field(None, description="Building climate data")

    # Source information
    source_directory: Optional[str] = Field(None, description="Source data directory")
    loaded_at: datetime = Field(default_factory=datetime.now, description="When data was loaded")

    @field_validator('id', 'name')
    @classmethod
    def validate_non_empty_strings(cls, v):
        if not v or not v.strip():
            raise ValueError("String fields cannot be empty")
        return v.strip()
    
    def __init__(self, **data):
        """Initialize Building with Brick Schema support."""
        super().__init__(**data)
        
        # Auto-generate Brick URI if not provided
        if not self.brick_uri and hasattr(self, 'id'):
            self.brick_uri = f"urn:building:{self.id}"
        
        # Set Brick metadata based on building properties
        if self.address:
            self.brick_metadata['address'] = self.address
        if self.city:
            self.brick_metadata['city'] = self.city
        if self.postal_code:
            self.brick_metadata['postalCode'] = self.postal_code
        if self.country:
            self.brick_metadata['country'] = self.country
        if self.construction_year:
            self.brick_metadata['constructionYear'] = self.construction_year
        if self.total_area_m2:
            self.brick_metadata['totalArea'] = {'value': self.total_area_m2, 'unit': 'squareMeter'}

    def add_level(self, level: Level) -> None:
        """Add a level to the building."""
        if level.building_id != self.id:
            level.building_id = self.id

        # Check for duplicate level IDs
        existing_ids = {l.id for l in self.levels}
        if level.id in existing_ids:
            raise ValueError(f"Level with ID {level.id} already exists in building {self.id}")

        self.levels.append(level)
        
        # Add Brick Schema relationship
        if self.brick_uri and level.brick_uri:
            self.add_brick_relationship('hasPart', level.brick_uri)
            level.add_brick_relationship('isPartOf', self.brick_uri)

    def add_room(self, room: Room, level_id: Optional[str] = None) -> None:
        """Add a room to the building and optionally to a specific level."""
        if room.building_id != self.id:
            room.building_id = self.id

        # Check for duplicate room IDs
        existing_ids = {r.id for r in self.rooms}
        if room.id in existing_ids:
            raise ValueError(f"Room with ID {room.id} already exists in building {self.id}")

        self.rooms.append(room)

        # Add to level if specified
        if level_id:
            level = self.get_level(level_id)
            if level:
                room.level_id = level_id
                level.add_room(room)
        
        # Add Brick Schema relationship (room is part of building)
        if self.brick_uri and room.brick_uri:
            self.add_brick_relationship('hasPart', room.brick_uri)
            room.add_brick_relationship('isPartOf', self.brick_uri)

    def get_level(self, level_id: str) -> Optional[Level]:
        """Get a level by ID."""
        for level in self.levels:
            if level.id == level_id:
                return level
        return None

    def get_room(self, room_id: str) -> Optional[Room]:
        """Get a room by ID from flat structure."""
        for room in self.rooms:
            if room.id == room_id:
                return room
        return None

    def get_room_count(self) -> int:
        """Get total number of rooms in building."""
        return len(self.rooms)

    def get_level_count(self) -> int:
        """Get number of levels in building."""
        return len(self.levels)

    def set_climate_data(self, climate_data: ClimateData) -> None:
        """Set climate data for the building."""
        if climate_data.building_id != self.id:
            climate_data.building_id = self.id
        self.climate_data = climate_data

    def get_data_quality_summary(self) -> Dict[str, Any]:
        """Get overall data quality summary for the building."""
        summary = {
            'building_id': self.id,
            'building_name': self.name,
            'total_rooms': self.get_room_count(),
            'total_levels': self.get_level_count(),
            'rooms_with_data': 0,
            'overall_quality_score': 0.0,
            'climate_data_available': self.climate_data is not None
        }

        if self.rooms:
            rooms_with_data = [r for r in self.rooms if r.timeseries]
            summary['rooms_with_data'] = len(rooms_with_data)

            if rooms_with_data:
                quality_scores = [r.get_overall_quality_score() for r in rooms_with_data]
                summary['overall_quality_score'] = float(np.mean(quality_scores))

        return summary

