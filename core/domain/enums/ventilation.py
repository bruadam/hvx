"""Ventilation type enumeration."""

from enum import Enum


class VentilationType(str, Enum):
    """Types of ventilation systems."""

    NATURAL = "natural"
    MECHANICAL = "mechanical"
    MIXED_MODE = "mixed_mode"

    @property
    def display_name(self) -> str:
        """Get human-readable display name."""
        names = {
            self.NATURAL: "Natural Ventilation",
            self.MECHANICAL: "Mechanical Ventilation",
            self.MIXED_MODE: "Mixed-mode Ventilation",
        }
        return names.get(self, self.value.title())

    @property
    def typical_energy_intensity_kwh_m2(self) -> float:
        """
        Get typical annual energy consumption for ventilation in kWh/m²/year.

        Returns:
            Energy intensity in kWh/m²/year
        """
        intensities = {
            self.NATURAL: 0.0,  # No energy consumption (passive)
            self.MECHANICAL: 15.0,  # Fan energy
            self.MIXED_MODE: 8.0,  # Reduced fan usage when natural ventilation is used
        }
        return intensities.get(self, 10.0)

    @property
    def has_heat_recovery(self) -> bool:
        """Check if this ventilation type typically includes heat recovery."""
        return self in [self.MECHANICAL, self.MIXED_MODE]

    @property
    def heat_recovery_efficiency(self) -> float:
        """
        Get typical heat recovery efficiency (if applicable).

        Returns:
            Efficiency (0.0 to 1.0), or 0.0 if no heat recovery
        """
        efficiencies = {
            self.NATURAL: 0.0,  # No heat recovery
            self.MECHANICAL: 0.75,  # Typical mechanical ventilation with heat recovery
            self.MIXED_MODE: 0.60,  # Lower efficiency due to bypass modes
        }
        return efficiencies.get(self, 0.0)

    @property
    def air_change_rate_range(self) -> tuple[float, float]:
        """
        Get typical air change rate range in ACH (air changes per hour).

        Returns:
            Tuple of (minimum, maximum) air change rates
        """
        rates = {
            self.NATURAL: (0.5, 3.0),  # Varies with weather
            self.MECHANICAL: (1.0, 4.0),  # Controlled rate
            self.MIXED_MODE: (0.8, 5.0),  # Wide range depending on mode
        }
        return rates.get(self, (0.5, 2.0))

    @property
    def control_precision(self) -> str:
        """
        Get control precision level.

        Returns:
            Control precision: 'low', 'medium', or 'high'
        """
        precision = {
            self.NATURAL: "low",  # Weather-dependent
            self.MECHANICAL: "high",  # Fully controlled
            self.MIXED_MODE: "medium",  # Some control with natural variation
        }
        return precision.get(self, "medium")

    @property
    def specific_fan_power_w_per_l_s(self) -> float:
        """
        Get typical specific fan power in W/(L/s).

        Returns:
            Specific fan power in W/(L/s), or 0.0 for natural ventilation
        """
        sfp = {
            self.NATURAL: 0.0,  # No fans
            self.MECHANICAL: 1.5,  # Modern mechanical ventilation
            self.MIXED_MODE: 1.2,  # Lower usage due to natural ventilation periods
        }
        return sfp.get(self, 1.5)
