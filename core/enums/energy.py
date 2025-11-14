"""
Energy-related enumerations for carriers, units, and primary energy scopes.
"""

from enum import Enum


class EnergyCarrier(str, Enum):
    ELECTRICITY = "electricity"
    DISTRICT_HEATING = "district_heating"
    DISTRICT_COOLING = "district_cooling"
    NATURAL_GAS = "natural_gas"
    LPG = "lpg"
    FUEL_OIL_LIGHT = "fuel_oil_light"
    FUEL_OIL_HEAVY = "fuel_oil_heavy"
    DIESEL = "diesel"
    GASOLINE = "gasoline"
    WOOD_PELLETS = "wood_pellets"
    WOOD_CHIPS = "wood_chips"
    WOOD_LOGS = "wood_logs"
    BIOMASS = "biomass"
    COAL = "coal"
    COKES = "cokes"
    PEAT = "peat"
    HYDROGEN = "hydrogen"
    BIOGAS = "biogas"
    SOLAR_THERMAL = "solar_thermal"
    GEOTHERMAL = "geothermal"
    HEAT_PUMP = "heat_pump"
    CHP = "combined_heat_power"
    WASTE_HEAT = "waste_heat"
    OTHER = "other"


class FuelUnit(str, Enum):
    KWH = "kwh"
    MWH = "mwh"
    GWH = "gwh"
    GJ = "gj"
    MJ = "mj"
    M3 = "m3"
    NORMAL_M3 = "normal_m3"
    LITER = "liter"
    KG = "kg"
    TON = "ton"
    BTU = "btu"


class PrimaryEnergyScope(str, Enum):
    TOTAL = "total"
    NON_RENEWABLE = "non_renewable"
    RENEWABLE = "renewable"


__all__ = [
    "EnergyCarrier",
    "FuelUnit",
    "PrimaryEnergyScope",
]
