"""TAIL category enumeration."""

from enum import Enum


class TAILCategory(str, Enum):
    """TAIL rating categories for indoor environmental quality assessment."""

    THERMAL = "thermal"
    ACOUSTICS = "acoustics"
    INDOOR_AIR_QUALITY = "indoor_air_quality"
    LIGHTING = "lighting"
    OTHER = "other"

    @property
    def display_name(self) -> str:
        """Get human-readable display name."""
        names = {
            self.THERMAL: "Thermal (T)",
            self.ACOUSTICS: "Acoustics (A)",
            self.INDOOR_AIR_QUALITY: "Indoor Air Quality (I)",
            self.LIGHTING: "Lighting (L)",
            self.OTHER: "Other Parameters",
        }
        return names.get(self, self.value.title())

    @property
    def description(self) -> str:
        """Get description of the TAIL category."""
        descriptions = {
            self.THERMAL: "Temperature and thermal comfort parameters",
            self.ACOUSTICS: "Noise and acoustic environment parameters",
            self.INDOOR_AIR_QUALITY: "Air quality, ventilation, and chemical pollutants",
            self.LIGHTING: "Illumination and daylight parameters",
            self.OTHER: "Parameters not included in TAIL rating scheme",
        }
        return descriptions.get(self, "")

    @property
    def tail_letter(self) -> str:
        """Get the TAIL acronym letter for this category."""
        letters = {
            self.THERMAL: "T",
            self.ACOUSTICS: "A",
            self.INDOOR_AIR_QUALITY: "I",
            self.LIGHTING: "L",
            self.OTHER: "",
        }
        return letters.get(self, "")
