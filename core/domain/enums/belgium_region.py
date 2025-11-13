"""Belgian regions enumeration for region-specific regulations."""

from enum import Enum


class Region(str, Enum):
    """Regions within Europe with different building regulations."""

    BE_FLANDERS = "Flanders"
    BE_WALLONIA = "Wallonia"
    BE_BRUSSELS = "Brussels"

    @property
    def display_name(self) -> str:
        """Get human-readable display name."""
        return self.value

    @property
    def code(self) -> str:
        """Get region code."""
        codes = {
            self.BE_FLANDERS: "VLG",
            self.BE_WALLONIA: "WAL",
            self.BE_BRUSSELS: "BRU",
        }
        return codes.get(self, "")