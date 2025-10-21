"""Room type enumeration for TAIL assessments."""

from enum import Enum


class RoomType(str, Enum):
    """Types of rooms for IEQ analysis, particularly for noise assessments."""

    # TAIL-specific room types
    SMALL_OFFICE = "small_office"
    OPEN_OFFICE = "open_office"
    HOTEL_ROOM = "hotel_room"
    
    # Additional common room types
    CLASSROOM = "classroom"
    MEETING_ROOM = "meeting_room"
    LABORATORY = "laboratory"
    CORRIDOR = "corridor"
    LOBBY = "lobby"
    OTHER = "other"

    @property
    def display_name(self) -> str:
        """Get human-readable display name."""
        names = {
            self.SMALL_OFFICE: "Small Office",
            self.OPEN_OFFICE: "Open Office",
            self.HOTEL_ROOM: "Hotel Room", 
            self.CLASSROOM: "Classroom",
            self.MEETING_ROOM: "Meeting Room",
            self.LABORATORY: "Laboratory",
            self.CORRIDOR: "Corridor",
            self.LOBBY: "Lobby",
            self.OTHER: "Other",
        }
        return names.get(self, self.value.replace("_", " ").title())

    @classmethod
    def get_tail_supported_types(cls) -> list['RoomType']:
        """Get room types specifically supported by TAIL method."""
        return [cls.SMALL_OFFICE, cls.OPEN_OFFICE, cls.HOTEL_ROOM]