"""
Simulation models package.

This namespace hosts analytical models that operate on telemetry to
produce simulation-style outputs (occupancy inference, ventilation
rates, RC thermal dynamics, EPC estimation, etc.).
"""

from .models.occupancy import OccupancyCalculator, OccupancyPattern
from .models.ventilation import VentilationCalculator, VentilationRateResult
from .models.rc_thermal import (
    RCThermalModel,
    RCModelParameters,
    RCModelResult,
    RCModelType,
)
from .models.real_epc import calculate_epc_rating
from .config import (
    list_simulation_models,
    load_simulation_config,
    load_all_simulation_configs,
    applicable_models_for_entity,
)

__all__ = [
    "OccupancyCalculator",
    "OccupancyPattern",
    "VentilationCalculator",
    "VentilationRateResult",
    "RCThermalModel",
    "RCModelParameters",
    "RCModelResult",
    "RCModelType",
    "calculate_epc_rating",
    "list_simulation_models",
    "load_simulation_config",
    "load_all_simulation_configs",
    "applicable_models_for_entity",
]
