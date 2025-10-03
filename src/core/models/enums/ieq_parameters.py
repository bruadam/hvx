"""IEQ parameter enumerations."""

from enum import Enum
from typing import List


class IEQParameter(Enum):
    """Standardized IEQ parameters for mapping and analysis."""

    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    CO2 = "co2"
    LIGHT = "light"
    PRESENCE = "presence"
    TIMESTAMP = "timestamp"
    BUILDING = "building"
    ROOM = "room"

    @classmethod
    def get_measurement_parameters(cls) -> List['IEQParameter']:
        """Get only the measurement parameters (excluding metadata)."""
        return [
            cls.TEMPERATURE,
            cls.HUMIDITY,
            cls.CO2,
            cls.LIGHT,
            cls.PRESENCE
        ]

    @classmethod
    def get_metadata_parameters(cls) -> List['IEQParameter']:
        """Get only the metadata parameters."""
        return [
            cls.TIMESTAMP,
            cls.BUILDING,
            cls.ROOM
        ]
