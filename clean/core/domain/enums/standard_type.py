"""IEQ standard type enumeration."""

from enum import Enum


class StandardType(str, Enum):
    """International and national IEQ standards."""

    EN16798_1 = "en16798-1"
    BR18 = "br18"
    DANISH_GUIDELINES = "danish-guidelines"
    ASHRAE_55 = "ashrae-55"
    WELL = "well"
    LEED = "leed"

    @property
    def full_name(self) -> str:
        """Get full standard name."""
        names = {
            self.EN16798_1: "EN 16798-1: Energy performance of buildings",
            self.BR18: "BR18: Danish Building Regulations",
            self.DANISH_GUIDELINES: "Danish Indoor Climate Guidelines",
            self.ASHRAE_55: "ASHRAE Standard 55: Thermal Environmental Conditions",
            self.WELL: "WELL Building Standard",
            self.LEED: "LEED: Leadership in Energy and Environmental Design",
        }
        return names.get(self, self.value)

    @property
    def region(self) -> str:
        """Get geographic region."""
        regions = {
            self.EN16798_1: "Europe",
            self.BR18: "Denmark",
            self.DANISH_GUIDELINES: "Denmark",
            self.ASHRAE_55: "International",
            self.WELL: "International",
            self.LEED: "International",
        }
        return regions.get(self, "Unknown")
