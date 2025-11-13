"""
Base Spatial Entity Models

Base SpatialEntity class and simple Zone entity.
Enhanced entities (Portfolio, Building, Floor, Room) are in entities.py.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .enums import SpatialEntityType, VentilationType


class SpatialEntity(BaseModel):
    """
    Base spatial entity model.

    Represents any spatial element in a building hierarchy:
    Portfolio → Building → Floor → Room → Zone
    """
    id: str
    name: str
    type: SpatialEntityType

    parent_ids: List[str] = Field(default_factory=list)
    child_ids: List[str] = Field(default_factory=list)

    # Context for rule selection
    country: Optional[str] = None        # e.g. "EU", "US", "DK"
    region: Optional[str] = None         # e.g. "NA", "Nordic", state, etc.
    climate_zone: Optional[str] = None   # any scheme you want

    # Semantic building metadata
    building_type: Optional[str] = None  # e.g. "office", "school", ...
    room_type: Optional[str] = None      # e.g. "classroom", "meeting_room"
    ventilation_type: Optional[VentilationType] = VentilationType.UNKNOWN

    area_m2: Optional[float] = None
    volume_m3: Optional[float] = None
    design_occupancy: Optional[int] = None

    metadata: Dict[str, Any] = Field(default_factory=dict)


class Zone(SpatialEntity):
    """
    Simple zone entity.

    A zone is a logical grouping of rooms or spaces with similar
    characteristics (e.g., same HVAC zone, same orientation).
    """
    type: SpatialEntityType = SpatialEntityType.ZONE


__all__ = [
    "SpatialEntity",
    "Zone",
]
