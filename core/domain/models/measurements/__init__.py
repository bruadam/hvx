"""Measurement models package.

Contains utility consumption and resource tracking models for energy, water, fuel,
and other measurable resources with time-series data support.
"""

from core.domain.models.measurements.energy_consumption import EnergyConsumption
from core.domain.models.measurements.fuel_consumption import FuelConsumption
from core.domain.models.measurements.water_consumption import WaterConsumption

__all__ = [
    "EnergyConsumption",
    "WaterConsumption",
    "FuelConsumption",
]
