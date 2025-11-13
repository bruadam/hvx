"""HVAC type enumeration."""

from enum import Enum


class HVACType(str, Enum):
    """Types of HVAC systems."""

    VAV = "vav"
    CAV = "cav"
    RADIANT = "radiant"
    FAN_COIL = "fan_coil"

    @property
    def display_name(self) -> str:
        """Get human-readable display name."""
        names = {
            self.VAV: "Variable Air Volume",
            self.CAV: "Constant Air Volume",
            self.RADIANT: "Radiant Heating/Cooling",
            self.FAN_COIL: "Fan Coil Units",
        }
        return names.get(self, self.value.title())

    @property
    def typical_energy_intensity_kwh_m2(self) -> float:
        """
        Get typical annual energy consumption intensity in kWh/m²/year.

        This is an estimate for office buildings in temperate climates.
        Actual consumption varies with climate, building design, and usage.

        Returns:
            Energy intensity in kWh/m²/year
        """
        intensities = {
            self.VAV: 35.0,  # Variable air volume - more efficient
            self.CAV: 45.0,  # Constant air volume - less efficient
            self.RADIANT: 25.0,  # Radiant systems - most efficient
            self.FAN_COIL: 40.0,  # Fan coil units - moderate efficiency
        }
        return intensities.get(self, 40.0)

    @property
    def fan_power_w_per_l_s(self) -> float:
        """
        Get typical specific fan power in W/(L/s).

        Lower values indicate more efficient systems.

        Returns:
            Specific fan power in W/(L/s)
        """
        sfp = {
            self.VAV: 1.8,  # Variable speed drives reduce power
            self.CAV: 2.5,  # Constant speed, higher power
            self.RADIANT: 0.5,  # Minimal air movement
            self.FAN_COIL: 2.0,  # Local fans
        }
        return sfp.get(self, 2.0)

    @property
    def has_cooling_recovery(self) -> bool:
        """Check if this HVAC type typically includes heat recovery."""
        return self in [self.VAV]  # VAV systems often have heat recovery

    @property
    def maintenance_complexity(self) -> str:
        """Get maintenance complexity level."""
        complexity = {
            self.VAV: "high",  # Complex controls and multiple zones
            self.CAV: "medium",  # Simpler than VAV
            self.RADIANT: "low",  # Few moving parts
            self.FAN_COIL: "medium",  # Multiple units to maintain
        }
        return complexity.get(self, "medium")
