"""European countries enumeration."""

from enum import Enum


class Country(str, Enum):
    """European countries."""

    DENMARK = "Denmark"
    GERMANY = "Germany"
    FRANCE = "France"
    ITALY = "Italy"
    SPAIN = "Spain"
    SWEDEN = "Sweden"
    FINLAND = "Finland"
    NETHERLANDS = "Netherlands"
    BELGIUM = "Belgium"
    AUSTRIA = "Austria"
    PORTUGAL = "Portugal"
    GREECE = "Greece"
    IRELAND = "Ireland"
    POLAND = "Poland"
    CZECH_REPUBLIC = "Czech Republic"
    HUNGARY = "Hungary"
    ROMANIA = "Romania"
    BULGARIA = "Bulgaria"
    CROATIA = "Croatia"
    SLOVAKIA = "Slovakia"
    SLOVENIA = "Slovenia"
    LUXEMBOURG = "Luxembourg"
    MALTA = "Malta"
    CYPRUS = "Cyprus"
    LATVIA = "Latvia"
    LITHUANIA = "Lithuania"
    ESTONIA = "Estonia"
    NORWAY = "Norway"


    @property
    def code(self) -> str:
        """Get ISO country code."""
        codes = {
            self.DENMARK: "DK",
            self.GERMANY: "DE",
            self.FRANCE: "FR",
            self.ITALY: "IT",
            self.SPAIN: "ES",
            self.SWEDEN: "SE",
            self.FINLAND: "FI",
            self.NETHERLANDS: "NL",
            self.BELGIUM: "BE",
            self.AUSTRIA: "AT",
            self.PORTUGAL: "PT",
            self.GREECE: "GR",
            self.IRELAND: "IE",
            self.POLAND: "PL",
            self.CZECH_REPUBLIC: "CZ",
            self.HUNGARY: "HU",
            self.ROMANIA: "RO",
            self.BULGARIA: "BG",
            self.CROATIA: "HR",
            self.SLOVAKIA: "SK",
            self.SLOVENIA: "SI",
            self.LUXEMBOURG: "LU",
            self.MALTA: "MT",
            self.CYPRUS: "CY",
            self.LATVIA: "LV",
            self.LITHUANIA: "LT",
            self.ESTONIA: "EE",
            self.NORWAY: "NO",
        }
        return codes.get(self, "Unknown")
