"""Data-related enumerations."""

from enum import Enum


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
