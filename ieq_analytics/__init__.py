"""
IEQ Analytics Engine

A comprehensive analytics engine for Indoor Environmental Quality (IEQ) assessment
using IoT indoor climate sensors data.
"""

__version__ = "1.0.0"
__author__ = "Bruno Adam"

from .models import Building, Room, IEQData
from .enums import IEQParameter
from .mapping import DataMapper
from .analytics import IEQAnalytics
from . import utils

__all__ = [
    "Building",
    "Room", 
    "IEQData",
    "IEQParameter",
    "DataMapper",
    "IEQAnalytics",
    "utils",
]
