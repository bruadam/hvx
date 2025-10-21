"""Building type enumeration."""

from enum import Enum


class BuildingType(str, Enum):
    """Types of buildings for IEQ analysis."""

    #? This is the list of building types supported when the system will be fully developed
    OFFICE = "office"
    HOTEL = "hotel"  # Added for TAIL rating scheme support
    SCHOOL = "school"
    RESIDENTIAL = "residential"
    HOSPITAL = "hospital"
    RETAIL = "retail"
    LABORATORY = "laboratory"
    INDUSTRIAL = "industrial"
    MIXED_USE = "mixed_use"
    OTHER = "other"

    # TODO: This should be defined in a config file and should be easily overwritable by users with a user defined building type list and their typical occupancy hours
    @property
    def typical_occupancy_hours(self) -> tuple[int, int]:
        """Get typical occupancy hours (start_hour, end_hour) in 24h format."""
        hours = {
            self.OFFICE: (8, 18),
            self.HOTEL: (0, 24),  # Hotels operate 24/7
            self.SCHOOL: (8, 16),
            self.RESIDENTIAL: (0, 24),
            self.HOSPITAL: (0, 24),
            self.RETAIL: (9, 20),
            self.LABORATORY: (8, 18),
            self.INDUSTRIAL: (6, 22),
            self.MIXED_USE: (7, 22),
            self.OTHER: (8, 18),
        }
        return hours.get(self, (8, 18))

    @property
    def display_name(self) -> str:
        """Get human-readable display name."""
        return self.value.replace("_", " ").title()
    
    #? Add supported types in the enum as it evolves
    @classmethod
    def supported_types(cls) -> list[str]:
        """Get a list of currently supported building types."""
        return [cls.OFFICE, cls.HOTEL, cls.SCHOOL]
