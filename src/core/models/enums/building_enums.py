"""Building-related enumerations."""

from enum import Enum


class RoomType(Enum):
    """Common room types for IEQ analysis."""

    CLASSROOM = "classroom"
    OFFICE = "office"
    MEETING_ROOM = "meeting_room"
    LIBRARY = "library"
    LABORATORY = "laboratory"
    CAFETERIA = "cafeteria"
    GYMNASIUM = "gymnasium"
    AUDITORIUM = "auditorium"
    CORRIDOR = "corridor"
    OTHER = "other"
