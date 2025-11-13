"""Heating system enumeration."""

from enum import Enum


class HeatingType(str, Enum):
    """Types of heating systems."""

    BOILER = "boiler"
    HEAT_PUMP = "heat_pump"
    DISTRICT_HEATING = "district_heating"
    ELECTRIC_HEATING = "electric_heating"

    @property
    def display_name(self) -> str:
        """Get human-readable display name."""
        names = {
            self.BOILER: "Boiler",
            self.HEAT_PUMP: "Heat Pump",
            self.DISTRICT_HEATING: "District Heating",
            self.ELECTRIC_HEATING: "Electric Heating",
        }
        return names.get(self, self.value.title())

    @property
    def typical_efficiency(self) -> float:
        """
        Get typical seasonal efficiency for this heating system.

        For heat pumps, this is the Seasonal Coefficient of Performance (SCOP).
        For other systems, this is the seasonal efficiency factor.

        Returns:
            Efficiency factor (0.0 to 1.0 for most systems, >1.0 for heat pumps)
        """
        efficiencies = {
            self.BOILER: 0.85,  # Modern condensing boiler
            self.HEAT_PUMP: 3.0,  # SCOP for air-source heat pump
            self.DISTRICT_HEATING: 0.95,  # District heating efficiency
            self.ELECTRIC_HEATING: 1.0,  # Direct electric heating
        }
        return efficiencies.get(self, 0.80)

    @property
    def efficiency_range(self) -> tuple[float, float]:
        """
        Get typical efficiency range (min, max) for this heating system.

        Returns:
            Tuple of (minimum, maximum) efficiency
        """
        ranges = {
            self.BOILER: (0.75, 0.95),  # Old to new condensing boilers
            self.HEAT_PUMP: (2.5, 4.5),  # Air-source to ground-source heat pumps
            self.DISTRICT_HEATING: (0.90, 0.98),
            self.ELECTRIC_HEATING: (0.98, 1.0),  # Nearly 100% efficient
        }
        return ranges.get(self, (0.70, 0.90))

    @property
    def fuel_type(self) -> str:
        """
        Get primary fuel/energy type for this heating system.

        Returns:
            Fuel type identifier
        """
        fuels = {
            self.BOILER: "natural_gas",  # Most common, but could be oil
            self.HEAT_PUMP: "electricity",
            self.DISTRICT_HEATING: "district_heat",
            self.ELECTRIC_HEATING: "electricity",
        }
        return fuels.get(self, "unknown")

    @property
    def co2_intensity_kg_kwh(self) -> float:
        """
        Get typical CO2 emission intensity in kg CO2 per kWh of heat delivered.

        Note: This is approximate and depends heavily on the energy source.
        For electricity-based systems, it varies significantly by country grid mix.

        Returns:
            CO2 emissions in kg per kWh
        """
        # These are European averages and should ideally be country-specific
        intensities = {
            self.BOILER: 0.215,  # Natural gas boiler (0.18 kg/kWh gas × 1.2 for efficiency)
            self.HEAT_PUMP: 0.15,  # Based on EU average grid (0.45 kg/kWh ÷ COP 3.0)
            self.DISTRICT_HEATING: 0.10,  # Often combined heat and power
            self.ELECTRIC_HEATING: 0.45,  # EU average grid electricity
        }
        return intensities.get(self, 0.25)

    @property
    def requires_distribution_system(self) -> bool:
        """Check if this heating system requires a water distribution system."""
        return self in [self.BOILER, self.HEAT_PUMP, self.DISTRICT_HEATING]

    @property
    def maintenance_frequency_months(self) -> int:
        """Get recommended maintenance interval in months."""
        intervals = {
            self.BOILER: 12,  # Annual service
            self.HEAT_PUMP: 12,  # Annual service
            self.DISTRICT_HEATING: 24,  # Less frequent maintenance needed
            self.ELECTRIC_HEATING: 24,  # Minimal maintenance
        }
        return intervals.get(self, 12)
