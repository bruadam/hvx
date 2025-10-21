"""Measurement type enumeration."""

from enum import Enum


class MeasurementType(str, Enum):
    """Types of measurement/data collection methods."""

    CONTINUOUS = "continuous"
    SIMULATED = "simulated"
    INSPECTION = "inspection"

    @property
    def display_name(self) -> str:
        """Get human-readable display name."""
        names = {
            self.CONTINUOUS: "Continuous Measurement",
            self.SIMULATED: "Simulated/Computed",
            self.INSPECTION: "Point-in-time Inspection",
        }
        return names.get(self, self.value.title())

    @property
    def description(self) -> str:
        """Get description of the measurement type."""
        descriptions = {
            self.CONTINUOUS: "Data collected continuously over time using sensors",
            self.SIMULATED: "Data computed through simulation or modeling",
            self.INSPECTION: "Data collected through visual inspection or one-time assessment",
        }
        return descriptions.get(self, "")