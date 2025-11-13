from __future__ import annotations
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

class SpatialEntityType(str, Enum):
    PORTFOLIO = "portfolio"
    BUILDING = "building"
    FLOOR = "floor"
    ROOM = "room"
    ZONE = "zone"

class BrickCompatible(BaseModel):
    brick_class: Optional[str] = None
    brick_uri: Optional[str] = None
    brick_properties: Dict[str, str] = Field(default_factory=dict)

class SpatialEntity(BrickCompatible):
    id: str
    name: str
    type: SpatialEntityType

    parent_id: Optional[str] = None
    child_ids: List[str] = Field(default_factory=list)

    area_m2: Optional[float] = None
    volume_m3: Optional[float] = None
    country: Optional[str] = None
    region: Optional[str] = None
    climate_zone: Optional[str] = None
    building_type: Optional[str] = None
    room_type: Optional[str] = None
    ventilation_type: Optional[str] = None

    metadata: Dict[str, Any] = Field(default_factory=dict)
