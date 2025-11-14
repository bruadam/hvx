"""
EPC rating calculator using configuration-backed EU thresholds.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Dict, List, Optional, Tuple

from core.config import load_epc_thresholds
from core.enums.country import CountryCode


@lru_cache(maxsize=1)
def _threshold_config() -> Dict[str, List[dict]]:
    """
    Cached threshold lookup loaded from YAML configuration.
    """
    return load_epc_thresholds()


def _resolve_country_code(country_code: Optional[str | CountryCode]) -> Optional[str]:
    if isinstance(country_code, CountryCode):
        return country_code.value
    if country_code:
        resolved = CountryCode.from_value(country_code)
        if resolved:
            return resolved.value
        return str(country_code).strip().upper()
    return None


def _thresholds_for_country(
    country_code: Optional[str | CountryCode],
) -> List[Tuple[str, float]]:
    config = _threshold_config()
    lookup_code = _resolve_country_code(country_code)
    if not lookup_code:
        entries = config.get(CountryCode.EU.value, [])
    else:
        mapped_code = lookup_code.replace("_", "-")
        entries = config.get(mapped_code) or config.get(lookup_code)
        if entries is None and lookup_code.startswith("BE"):
            entries = config.get(CountryCode.BE.value, [])
        if entries is None:
            entries = config.get(CountryCode.EU.value, [])
    return [(entry["rating"], float(entry["limit"])) for entry in entries]


def calculate_epc_rating(
    primary_energy_kwh_m2: Optional[float],
    country_code: Optional[str | CountryCode] = None,
) -> Dict[str, Optional[float | str]]:
    """
    Compute EPC rating for a given primary energy intensity.
    """
    if primary_energy_kwh_m2 is None:
        return {"rating": None, "primary_energy_kwh_m2": None}

    rating = None
    for label, limit in _thresholds_for_country(country_code):
        if primary_energy_kwh_m2 <= limit:
            rating = label
            break

    return {
        "rating": rating,
        "primary_energy_kwh_m2": primary_energy_kwh_m2,
    }
