"""
Spatial and building-related enums.
"""

from enum import Enum


class SpatialEntityType(str, Enum):
    PORTFOLIO = "portfolio"
    BUILDING = "building"
    FLOOR = "floor"
    ROOM = "room"
    ZONE = "zone"


class VentilationType(str, Enum):
    NATURAL = "natural"
    MECHANICAL = "mechanical"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class BuildingType(str, Enum):
    OFFICE = "office"
    EDUCATION = "education"
    SCHOOL = "school"
    UNIVERSITY = "university"
    RETAIL = "retail"
    COMMERCIAL = "commercial"
    RESIDENTIAL = "residential"
    MULTIFAMILY = "multifamily"
    INDUSTRIAL = "industrial"
    LOGISTICS = "logistics"
    WAREHOUSE = "warehouse"
    HOSPITAL = "hospital"
    HEALTHCARE = "healthcare"
    HOTEL = "hotel"
    HOSPITALITY = "hospitality"
    LABORATORY = "laboratory"
    DATA_CENTER = "data_center"
    SPORTS = "sports"
    ENTERTAINMENT = "entertainment"
    TRANSPORT = "transport"
    PARKING = "parking"
    CULTURAL = "cultural"
    GOVERNMENT = "government"
    PUBLIC = "public"
    MIXED_USE = "mixed_use"
    OTHER = "other"


class RoomType(str, Enum):
    CLASSROOM = "classroom"
    LECTURE_HALL = "lecture_hall"
    MEETING_ROOM = "meeting_room"
    CONFERENCE_ROOM = "conference_room"
    OPEN_OFFICE = "open_office"
    PRIVATE_OFFICE = "private_office"
    HOT_DESK = "hot_desk"
    LOBBY = "lobby"
    CORRIDOR = "corridor"
    LABORATORY = "laboratory"
    CLEANROOM = "cleanroom"
    OPERATING_ROOM = "operating_room"
    PATIENT_ROOM = "patient_room"
    HOTEL_ROOM = "hotel_room"
    APARTMENT = "apartment"
    KITCHEN = "kitchen"
    CAFETERIA = "cafeteria"
    CANTEEN = "canteen"
    SERVER_ROOM = "server_room"
    DATA_HALL = "data_hall"
    STORAGE = "storage"
    WAREHOUSE_BAY = "warehouse_bay"
    PARKING_ZONE = "parking_zone"
    RESTROOM = "restroom"
    SHOWER = "shower"
    GYM = "gym"
    AUDITORIUM = "auditorium"
    RETAIL_ZONE = "retail_zone"
    OTHER = "other"


class OpeningHoursProfile(str, Enum):
    OFFICE_STANDARD = "office_standard"
    RETAIL_STANDARD = "retail_standard"
    EDUCATION_STANDARD = "education_standard"
    HOSPITALITY_STANDARD = "hospitality_standard"
    INDUSTRIAL_STANDARD = "industrial_standard"
    TWENTY_FOUR_SEVEN = "around_the_clock"
    CUSTOM = "custom"


__all__ = [
    "SpatialEntityType",
    "VentilationType",
    "BuildingType",
    "RoomType",
    "OpeningHoursProfile",
]
