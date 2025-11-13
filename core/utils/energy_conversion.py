"""Energy unit conversion utilities for EPC calculations."""

from enum import Enum

from core.domain.enums.countries import Country
from core.domain.enums.heating import HeatingType


class EnergyUnit(str, Enum):
    """Energy units supported for conversion."""

    KWH = "kwh"
    MWH = "mwh"
    GJ = "gj"
    THERMS = "therms"
    BTU = "btu"
    KCAL = "kcal"

    # Fuel units
    NATURAL_GAS_M3 = "natural_gas_m3"
    NATURAL_GAS_FT3 = "natural_gas_ft3"
    HEATING_OIL_LITERS = "heating_oil_liters"
    HEATING_OIL_GALLONS = "heating_oil_gallons"
    PROPANE_LITERS = "propane_liters"
    COAL_KG = "coal_kg"
    WOOD_KG = "wood_kg"
    PELLETS_KG = "pellets_kg"


class WaterUnit(str, Enum):
    """Water volume units."""

    LITERS = "liters"
    CUBIC_METERS = "m3"
    GALLONS_US = "gallons_us"
    GALLONS_UK = "gallons_uk"


# Conversion factors to kWh
ENERGY_TO_KWH: dict[EnergyUnit, float] = {
    EnergyUnit.KWH: 1.0,
    EnergyUnit.MWH: 1000.0,
    EnergyUnit.GJ: 277.778,  # 1 GJ = 277.778 kWh
    EnergyUnit.THERMS: 29.3071,  # 1 therm = 29.3071 kWh
    EnergyUnit.BTU: 0.000293071,  # 1 BTU = 0.000293071 kWh
    EnergyUnit.KCAL: 0.001163,  # 1 kcal = 0.001163 kWh

    # Fuel conversions (approximate heating values)
    EnergyUnit.NATURAL_GAS_M3: 10.0,  # 1 m³ natural gas ≈ 10.0 kWh
    EnergyUnit.NATURAL_GAS_FT3: 0.293,  # 1 ft³ natural gas ≈ 0.293 kWh
    EnergyUnit.HEATING_OIL_LITERS: 10.0,  # 1 liter heating oil ≈ 10.0 kWh
    EnergyUnit.HEATING_OIL_GALLONS: 37.85,  # 1 US gallon heating oil ≈ 37.85 kWh
    EnergyUnit.PROPANE_LITERS: 6.97,  # 1 liter propane ≈ 6.97 kWh
    EnergyUnit.COAL_KG: 8.14,  # 1 kg coal ≈ 8.14 kWh
    EnergyUnit.WOOD_KG: 4.4,  # 1 kg wood ≈ 4.4 kWh (moisture dependent)
    EnergyUnit.PELLETS_KG: 4.9,  # 1 kg wood pellets ≈ 4.9 kWh
}

# Water volume conversions to liters
WATER_TO_LITERS: dict[WaterUnit, float] = {
    WaterUnit.LITERS: 1.0,
    WaterUnit.CUBIC_METERS: 1000.0,
    WaterUnit.GALLONS_US: 3.78541,
    WaterUnit.GALLONS_UK: 4.54609,
}


def convert_to_kwh(value: float, unit: EnergyUnit) -> float:
    """
    Convert energy value to kWh.

    Args:
        value: Energy value in the specified unit
        unit: Energy unit

    Returns:
        Energy value in kWh
    """
    if unit not in ENERGY_TO_KWH:
        raise ValueError(f"Unsupported energy unit: {unit}")

    return value * ENERGY_TO_KWH[unit]


def convert_water_to_liters(value: float, unit: WaterUnit) -> float:
    """
    Convert water volume to liters.

    Args:
        value: Water volume in the specified unit
        unit: Water unit

    Returns:
        Water volume in liters
    """
    if unit not in WATER_TO_LITERS:
        raise ValueError(f"Unsupported water unit: {unit}")

    return value * WATER_TO_LITERS[unit]


def convert_hot_water_to_kwh(
    volume_liters: float,
    inlet_temp_celsius: float = 10.0,
    outlet_temp_celsius: float = 60.0,
    efficiency: float = 0.85
) -> float:
    """
    Convert hot water consumption to energy in kWh.

    Formula: Energy = Volume (L) × Specific Heat (4.18 kJ/L·K) × ΔT / 3600 / efficiency

    Args:
        volume_liters: Hot water volume in liters
        inlet_temp_celsius: Cold water inlet temperature (default: 10°C)
        outlet_temp_celsius: Hot water outlet temperature (default: 60°C)
        efficiency: Water heater efficiency (default: 0.85)

    Returns:
        Energy required in kWh
    """
    delta_t = outlet_temp_celsius - inlet_temp_celsius

    # Specific heat capacity of water: 4.18 kJ/(L·K)
    # Convert to kWh: divide by 3600
    energy_kwh = (volume_liters * 4.18 * delta_t) / 3600.0

    # Account for heater efficiency
    energy_kwh = energy_kwh / efficiency

    return energy_kwh


def get_heating_system_efficiency(heating_type: HeatingType) -> float:
    """
    Get typical efficiency for heating system type.

    Args:
        heating_type: Type of heating system

    Returns:
        Typical efficiency (0.0 to 1.0)
    """
    efficiencies = {
        HeatingType.HEAT_PUMP: 3.0,  # COP (Coefficient of Performance)
        HeatingType.DISTRICT_HEATING: 0.95,
        HeatingType.BOILER: 0.85,  # Modern condensing boiler
        HeatingType.ELECTRIC_HEATING: 1.0,
    }

    return efficiencies.get(heating_type, 0.80)


def calculate_primary_energy_factors(country: Country) -> dict[str, float]:
    """
    Get primary energy conversion factors for a country.

    These factors convert final energy (delivered to building) to primary energy
    (total energy including production, transmission losses, etc.)

    Args:
        country: Country

    Returns:
        Dictionary with factors for different energy types
    """
    # Default factors based on European standards
    factors = {
        "electricity": 2.0,  # Grid electricity
        "natural_gas": 1.1,  # Natural gas
        "district_heating": 1.0,  # District heating
        "heating_oil": 1.1,  # Heating oil
        "renewable": 1.0,  # On-site renewable
        "biomass": 1.0,  # Biomass
    }

    # Country-specific overrides (from EPCRating.calculate_primary_energy)
    country_factors = {
        Country.DENMARK: {"electricity": 1.9, "natural_gas": 1.0},
        Country.GERMANY: {"electricity": 1.8, "natural_gas": 1.1},
        Country.FRANCE: {"electricity": 2.3, "natural_gas": 1.0},
        Country.NETHERLANDS: {"electricity": 2.0, "natural_gas": 1.1},
        Country.SWEDEN: {"electricity": 1.6, "natural_gas": 1.0},
        Country.FINLAND: {"electricity": 1.7, "natural_gas": 1.0},
        Country.SPAIN: {"electricity": 1.9, "natural_gas": 1.1},
        Country.ITALY: {"electricity": 2.0, "natural_gas": 1.05},
        Country.BELGIUM: {"electricity": 2.0, "natural_gas": 1.1},
        Country.AUSTRIA: {"electricity": 1.9, "natural_gas": 1.05},
        Country.PORTUGAL: {"electricity": 2.5, "natural_gas": 1.0},
        Country.IRELAND: {"electricity": 2.1, "natural_gas": 1.1},
        Country.POLAND: {"electricity": 3.0, "natural_gas": 1.2},
        Country.CZECH_REPUBLIC: {"electricity": 2.5, "natural_gas": 1.2},
        Country.CROATIA: {"electricity": 2.0, "natural_gas": 1.1},
        Country.LUXEMBOURG: {"electricity": 2.0, "natural_gas": 1.1},
        Country.BULGARIA: {"electricity": 2.5, "natural_gas": 1.2},
        Country.ROMANIA: {"electricity": 2.5, "natural_gas": 1.2},
        Country.SLOVAKIA: {"electricity": 2.5, "natural_gas": 1.2},
        Country.HUNGARY: {"electricity": 2.3, "natural_gas": 1.15},
        Country.GREECE: {"electricity": 2.2, "natural_gas": 1.1},
        Country.NORWAY: {"electricity": 1.5, "natural_gas": 1.0},
    }

    if country in country_factors:
        factors.update(country_factors[country])

    return factors


def calculate_ventilation_energy(
    air_volume_m3_h: float,
    operating_hours_per_year: float,
    pressure_drop_pa: float = 300.0,
    fan_efficiency: float = 0.6,
    motor_efficiency: float = 0.9
) -> float:
    """
    Calculate annual energy consumption for mechanical ventilation.

    Args:
        air_volume_m3_h: Air flow rate in m³/h
        operating_hours_per_year: Annual operating hours
        pressure_drop_pa: System pressure drop in Pascals (default: 300 Pa)
        fan_efficiency: Fan efficiency (default: 0.6)
        motor_efficiency: Motor efficiency (default: 0.9)

    Returns:
        Annual energy consumption in kWh
    """
    # Convert m³/h to m³/s
    air_volume_m3_s = air_volume_m3_h / 3600.0

    # Fan power (W) = (Air flow × Pressure drop) / (Fan efficiency × Motor efficiency)
    fan_power_w = (air_volume_m3_s * pressure_drop_pa) / (fan_efficiency * motor_efficiency)

    # Annual energy (kWh) = Power (kW) × Operating hours
    annual_energy_kwh = (fan_power_w / 1000.0) * operating_hours_per_year

    return annual_energy_kwh


def estimate_cooling_energy(
    floor_area_m2: float,
    cooling_degree_days: float,
    building_u_value: float = 0.3,
    internal_gains_w_m2: float = 10.0,
    cop: float = 3.0
) -> float:
    """
    Estimate annual cooling energy consumption.

    Args:
        floor_area_m2: Building floor area in m²
        cooling_degree_days: Annual cooling degree days
        building_u_value: Average U-value in W/(m²·K) (default: 0.3)
        internal_gains_w_m2: Internal heat gains in W/m² (default: 10)
        cop: Coefficient of performance for cooling system (default: 3.0)

    Returns:
        Annual cooling energy consumption in kWh
    """
    # Simplified cooling load calculation
    # This is a rough estimate and should be refined with detailed building data

    # Transmission losses
    transmission_load_kwh = floor_area_m2 * building_u_value * cooling_degree_days * 24 / 1000

    # Internal gains (converted to annual)
    internal_gains_kwh = floor_area_m2 * internal_gains_w_m2 * 2000 / 1000  # Assume 2000 cooling hours

    # Total cooling demand
    total_cooling_demand = transmission_load_kwh + internal_gains_kwh

    # Energy consumption accounting for COP
    energy_consumption = total_cooling_demand / cop

    return max(0, energy_consumption)
