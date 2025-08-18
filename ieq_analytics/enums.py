"""
Enums for IEQ parameters and data mapping.
"""

from enum import Enum
from typing import Dict, List


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


class DataResolution(Enum):
    """Supported data resolutions."""
    
    HOURLY = "H"
    DAILY = "D"
    WEEKLY = "W"
    MONTHLY = "M"


class ComfortCategory(Enum):
    """Comfort categories based on EN 16798-1 standard."""
    
    CATEGORY_I = "I"    # High level of expectation
    CATEGORY_II = "II"  # Normal level of expectation  
    CATEGORY_III = "III" # Acceptable level of expectation
    CATEGORY_IV = "IV"  # Values outside the criteria for the above categories


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


# Default column mappings for common sensor data formats
DEFAULT_COLUMN_MAPPINGS: Dict[str, List[str]] = {
    IEQParameter.TEMPERATURE.value: [
        "temperature", "temp", "temperatur", "temperature_c", "temp_c",
        "air_temperature", "room_temperature", "indoor_temperature"
    ],
    IEQParameter.HUMIDITY.value: [
        "humidity", "rh", "relative_humidity", "fugtighed", "humidity_percent",
        "rh_percent", "air_humidity", "indoor_humidity"
    ],
    IEQParameter.CO2.value: [
        "co2", "carbon_dioxide", "co2_ppm", "co2_concentration",
        "carbon_dioxide_ppm", "air_co2"
    ],
    IEQParameter.LIGHT.value: [
        "light", "lux", "illuminance", "lys", "light_level",
        "brightness", "lighting", "light_intensity"
    ],
    IEQParameter.PRESENCE.value: [
        "presence", "occupancy", "tilstedeværelse", "motion",
        "pir", "people_count", "occupied"
    ],
    IEQParameter.TIMESTAMP.value: [
        "timestamp", "datetime", "time", "date_time", "date",
        "time_stamp", "measurement_time"
    ]
}
