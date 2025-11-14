"""
Country and region enumeration utilities.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Dict, Optional


class CountryCode(str, Enum):
    """ISO-aligned country codes used across analytics modules."""

    EU = "EU"
    AD = "AD"
    AL = "AL"
    AM = "AM"
    AT = "AT"
    AZ = "AZ"
    BA = "BA"
    BE = "BE"
    BE_BRU = "BE-BRU"
    BE_VLG = "BE-VLG"
    BE_WAL = "BE-WAL"
    BG = "BG"
    BY = "BY"
    CH = "CH"
    CY = "CY"
    CZ = "CZ"
    DE = "DE"
    DK = "DK"
    EE = "EE"
    ES = "ES"
    FI = "FI"
    FR = "FR"
    GB = "GB"
    GE = "GE"
    GR = "GR"
    HR = "HR"
    HU = "HU"
    IE = "IE"
    IS = "IS"
    IT = "IT"
    LI = "LI"
    LT = "LT"
    LU = "LU"
    LV = "LV"
    MC = "MC"
    MD = "MD"
    ME = "ME"
    MK = "MK"
    MT = "MT"
    NL = "NL"
    NO = "NO"
    PL = "PL"
    PT = "PT"
    RO = "RO"
    RS = "RS"
    RU = "RU"
    SE = "SE"
    SI = "SI"
    SK = "SK"
    SM = "SM"
    TR = "TR"
    UA = "UA"
    VA = "VA"
    XK = "XK"

    @classmethod
    def from_value(cls, value: Optional["str | CountryCode"]) -> Optional["CountryCode"]:
        """
        Normalize a string or CountryCode into a CountryCode instance.
        """
        if value is None:
            return None
        if isinstance(value, cls):
            return value

        normalized = cls._normalize(str(value))
        if normalized in _ALIASES:
            return _ALIASES[normalized]

        upper_value = str(value).strip().upper()
        try:
            return cls(upper_value)
        except ValueError:
            return None

    @staticmethod
    def _normalize(raw: str) -> str:
        cleaned = re.sub(r"[^a-z0-9]+", " ", raw.lower()).strip()
        return re.sub(r"\s+", " ", cleaned)


def _build_aliases() -> Dict[str, CountryCode]:
    aliases: Dict[str, CountryCode] = {}

    def add_alias(key: str, code: CountryCode) -> None:
        aliases[CountryCode._normalize(key)] = code

    for code in CountryCode:
        add_alias(code.value, code)
        add_alias(code.name, code)

    manual_aliases = {
        # ISO-3 codes
        "and": CountryCode.AD,
        "andorra": CountryCode.AD,
        "aut": CountryCode.AT,
        "alb": CountryCode.AL,
        "arm": CountryCode.AM,
        "aze": CountryCode.AZ,
        "bih": CountryCode.BA,
        "blr": CountryCode.BY,
        "bel": CountryCode.BE,
        "bgr": CountryCode.BG,
        "che": CountryCode.CH,
        "cyp": CountryCode.CY,
        "cze": CountryCode.CZ,
        "czr": CountryCode.CZ,
        "dnk": CountryCode.DK,
        "est": CountryCode.EE,
        "fin": CountryCode.FI,
        "fra": CountryCode.FR,
        "deu": CountryCode.DE,
        "ger": CountryCode.DE,
        "grc": CountryCode.GR,
        "hun": CountryCode.HU,
        "irl": CountryCode.IE,
        "isl": CountryCode.IS,
        "ita": CountryCode.IT,
        "lva": CountryCode.LV,
        "lie": CountryCode.LI,
        "ltu": CountryCode.LT,
        "lux": CountryCode.LU,
        "mlt": CountryCode.MT,
        "mda": CountryCode.MD,
        "mco": CountryCode.MC,
        "mne": CountryCode.ME,
        "mkd": CountryCode.MK,
        "nld": CountryCode.NL,
        "nor": CountryCode.NO,
        "pol": CountryCode.PL,
        "prt": CountryCode.PT,
        "rou": CountryCode.RO,
        "rus": CountryCode.RU,
        "srb": CountryCode.RS,
        "svk": CountryCode.SK,
        "svn": CountryCode.SI,
        "esp": CountryCode.ES,
        "swe": CountryCode.SE,
        "che": CountryCode.CH,
        "tur": CountryCode.TR,
        "ukr": CountryCode.UA,
        "gbr": CountryCode.GB,
        "vat": CountryCode.VA,
        "imn": CountryCode.GB,
        "cze republic": CountryCode.CZ,
        "czech republic": CountryCode.CZ,
        "england": CountryCode.GB,
        "scotland": CountryCode.GB,
        "wales": CountryCode.GB,
        "northern ireland": CountryCode.GB,
        "great britain": CountryCode.GB,
        "united kingdom": CountryCode.GB,
        "unitedkingdom": CountryCode.GB,
        "uk": CountryCode.GB,
        "republic of ireland": CountryCode.IE,
        "bosnia and herzegovina": CountryCode.BA,
        "bosnia": CountryCode.BA,
        "herzegovina": CountryCode.BA,
        "holy see": CountryCode.VA,
        "macedonia": CountryCode.MK,
        "fyrom": CountryCode.MK,
        "moldavia": CountryCode.MD,
        "czechia": CountryCode.CZ,
        "north macedonia": CountryCode.MK,
        "san marino": CountryCode.SM,
        "vatican city": CountryCode.VA,
        "kosovo": CountryCode.XK,
        "kv": CountryCode.XK,
        "dk": CountryCode.DK,
        "denmark": CountryCode.DK,
        "spain": CountryCode.ES,
        "portugal": CountryCode.PT,
        "france": CountryCode.FR,
        "germany": CountryCode.DE,
        "netherlands": CountryCode.NL,
        "belgium": CountryCode.BE,
        "flanders": CountryCode.BE_VLG,
        "wallonia": CountryCode.BE_WAL,
        "brussels": CountryCode.BE_BRU,
        "luxembourg": CountryCode.LU,
        "switzerland": CountryCode.CH,
        "austria": CountryCode.AT,
        "italy": CountryCode.IT,
        "norway": CountryCode.NO,
        "sweden": CountryCode.SE,
        "finland": CountryCode.FI,
        "estonia": CountryCode.EE,
        "latvia": CountryCode.LV,
        "lithuania": CountryCode.LT,
        "poland": CountryCode.PL,
        "czech": CountryCode.CZ,
        "slovakia": CountryCode.SK,
        "slovenia": CountryCode.SI,
        "hungary": CountryCode.HU,
        "romania": CountryCode.RO,
        "bulgaria": CountryCode.BG,
        "greece": CountryCode.GR,
        "cyprus": CountryCode.CY,
        "turkiye": CountryCode.TR,
        "turkey": CountryCode.TR,
        "croatia": CountryCode.HR,
        "serbia": CountryCode.RS,
        "montenegro": CountryCode.ME,
        "albania": CountryCode.AL,
        "northmacedonia": CountryCode.MK,
        "kos": CountryCode.XK,
        "georgia": CountryCode.GE,
        "armenia": CountryCode.AM,
        "azerbaijan": CountryCode.AZ,
        "ukraine": CountryCode.UA,
        "belarus": CountryCode.BY,
        "russia": CountryCode.RU,
        "iceland": CountryCode.IS,
        "andorra": CountryCode.AD,
        "liechtenstein": CountryCode.LI,
        "malta": CountryCode.MT,
        "monaco": CountryCode.MC,
    }

    for name, code in manual_aliases.items():
        add_alias(name, code)

    return aliases


_ALIASES = _build_aliases()

__all__ = ["CountryCode"]
