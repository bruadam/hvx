"""Belgian regions enumeration for region-specific regulations."""

from enum import Enum


class BelgiumRegion(str, Enum):
    """Regions of Belgium with different building regulations."""

    FLANDERS = "Flanders"
    WALLONIA = "Wallonia"
    BRUSSELS = "Brussels"

    @property
    def display_name(self) -> str:
        """Get human-readable display name."""
        return self.value

    @property
    def code(self) -> str:
        """Get region code."""
        codes = {
            self.FLANDERS: "VLG",
            self.WALLONIA: "WAL",
            self.BRUSSELS: "BRU",
        }
        return codes.get(self, "")

    @property
    def official_language(self) -> str:
        """Get primary official language of the region."""
        languages = {
            self.FLANDERS: "Dutch",
            self.WALLONIA: "French",
            self.BRUSSELS: "French/Dutch",
        }
        return languages.get(self, "")
