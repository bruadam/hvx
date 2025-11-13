"""Pollution level enumeration for EN 16798-1."""

from enum import Enum


class PollutionLevel(str, Enum):
    """
    Non-occupant related pollution levels according to EN 16798-1.

    This determines the required ventilation rate beyond that needed for occupants.
    Categories:
    - VERY_LOW: Very low-polluting buildings (non-polluting materials)
    - LOW: Low-polluting buildings (careful material selection)
    - NON_LOW: Non-low-polluting buildings (standard materials)
    """

    VERY_LOW = "very_low"
    LOW = "low"
    NON_LOW = "non_low"

    @property
    def display_name(self) -> str:
        """Get human-readable display name."""
        names = {
            self.VERY_LOW: "Very Low Pollution",
            self.LOW: "Low Pollution",
            self.NON_LOW: "Non-Low Pollution",
        }
        return names.get(self, self.value.replace("_", " ").title())

    @property
    def description(self) -> str:
        """Get detailed description."""
        descriptions = {
            self.VERY_LOW: (
                "Very low-polluting buildings with highly controlled emissions. "
                "Requires strict material selection and verification."
            ),
            self.LOW: (
                "Low-polluting buildings with careful material selection. "
                "Default for new buildings with low-emission materials."
            ),
            self.NON_LOW: (
                "Buildings with standard materials. No special measures "
                "for emission control. Typical for existing buildings."
            ),
        }
        return descriptions.get(self, "")

    @property
    def building_emission_factor(self) -> float:
        """
        Get building emission factor in L/(s·m²) for non-occupant pollution.

        This is the additional ventilation rate per floor area needed
        to dilute building emissions (materials, furnishings, etc.)

        Returns:
            Ventilation rate in L/(s·m²)
        """
        factors = {
            self.VERY_LOW: 0.0,  # Negligible building emissions
            self.LOW: 0.5,  # Low building emissions
            self.NON_LOW: 1.0,  # Standard building emissions
        }
        return factors.get(self, 1.0)

    @property
    def verification_required(self) -> bool:
        """Check if emission verification is required."""
        return self in [self.VERY_LOW, self.LOW]

    @classmethod
    def get_default_for_building_age(cls, construction_year: int) -> "PollutionLevel":
        """
        Get typical pollution level based on construction year.

        Args:
            construction_year: Year of construction

        Returns:
            Typical pollution level
        """
        if construction_year >= 2020:
            return cls.LOW  # Modern buildings with emission standards
        elif construction_year >= 2000:
            return cls.LOW  # Relatively modern
        else:
            return cls.NON_LOW  # Older buildings

    @classmethod
    def get_recommended_for_use(cls, room_use: str) -> "PollutionLevel":
        """
        Get recommended pollution level for room use type.

        Args:
            room_use: Type of room use

        Returns:
            Recommended pollution level
        """
        # Sensitive spaces should aim for low pollution
        low_pollution_uses = {
            "classroom", "kindergarten", "hospital", "surgery",
            "laboratory", "clean_room"
        }

        if room_use.lower() in low_pollution_uses:
            return cls.LOW

        return cls.NON_LOW  # Default
