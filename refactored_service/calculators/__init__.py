"""
Calculation modules for building analytics.

This package contains all core calculation logic for various standards and analyses:
- EN 16798-1: Indoor environmental input parameters
- TAIL: Thermal, Acoustic, Indoor air quality, Luminous rating
- Ventilation rate estimation from CO2 decay
- Occupancy detection from CO2 patterns
- RC thermal models for building simulation
"""

from .en16798_calculator import EN16798Calculator
from .tail_calculator import TAILCalculator
from .ventilation_calculator import VentilationCalculator
from .occupancy_calculator import OccupancyCalculator
from .rc_thermal_model import RCThermalModel

__all__ = [
    "EN16798Calculator",
    "TAILCalculator",
    "VentilationCalculator",
    "OccupancyCalculator",
    "RCThermalModel",
]
