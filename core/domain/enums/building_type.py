"""Building type enumeration."""

from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


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

    @property
    def typical_occupancy_hours(self) -> tuple[int, int]:
        """
        Get typical occupancy hours (start_hour, end_hour) in 24h format.

        Loads from config file (config/building_types/default_building_types.yaml).
        Users can override by calling building_type_config_loader.load_user_config().

        Returns:
            Tuple of (start_hour, end_hour) where hours are in 24h format (0-23)
        """
        from core.domain.enums.building_type_config import building_type_config_loader
        return building_type_config_loader.get_occupancy_hours(self.value)

    @property
    def display_name(self) -> str:
        """
        Get human-readable display name.

        Loads from config file if available, otherwise formats the enum value.
        """
        from core.domain.enums.building_type_config import building_type_config_loader
        return building_type_config_loader.get_display_name(self.value)

    @classmethod
    def supported_types(cls) -> list['BuildingType']:
        """
        Get a list of currently supported building types.

        Loads from config file where supported=true.
        """
        from core.domain.enums.building_type_config import building_type_config_loader
        supported_ids = building_type_config_loader.get_supported_building_types()
        return [cls(type_id) for type_id in supported_ids if type_id in cls._value2member_map_]

    @property
    def default_parameters(self) -> list[str]:
        """
        Get default parameters to monitor for this building type.

        Returns:
            List of parameter identifiers (e.g., ['temperature', 'co2', 'humidity'])
        """
        from core.domain.enums.building_type_config import building_type_config_loader
        return building_type_config_loader.get_default_parameters(self.value)

    @property
    def is_supported(self) -> bool:
        """Check if this building type is fully supported."""
        from core.domain.enums.building_type_config import building_type_config_loader
        return building_type_config_loader.is_supported(self.value)

    @property
    def is_24_7(self) -> bool:
        """Check if this is a 24/7 facility (e.g., hotel, hospital)."""
        start, end = self.typical_occupancy_hours
        return start == 0 and end == 24
