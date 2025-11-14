"""
Opening hours and occupancy scheduling utilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import time
from typing import Dict, Iterable, List, Optional, Tuple

import pandas as pd

from .enums import BuildingType, OpeningHoursProfile


def _time(value: str) -> time:
    hour, minute = value.split(":")
    return time(int(hour), int(minute))


OpeningPeriod = Tuple[time, time]


PROFILE_DEFINITIONS: Dict[OpeningHoursProfile, Dict[int, List[OpeningPeriod]]] = {
    OpeningHoursProfile.OFFICE_STANDARD: {
        weekday: [(_time("08:00"), _time("18:00"))] for weekday in range(0, 5)
    },
    OpeningHoursProfile.RETAIL_STANDARD: {
        weekday: [(_time("09:00"), _time("20:00"))] for weekday in range(0, 6)
    },
    OpeningHoursProfile.EDUCATION_STANDARD: {
        weekday: [(_time("07:30"), _time("16:00"))] for weekday in range(0, 5)
    },
    OpeningHoursProfile.HOSPITALITY_STANDARD: {
        weekday: [(_time("06:00"), _time("23:00"))] for weekday in range(0, 7)
    },
    OpeningHoursProfile.INDUSTRIAL_STANDARD: {
        weekday: [(_time("06:00"), _time("22:00"))] for weekday in range(0, 6)
    },
    OpeningHoursProfile.TWENTY_FOUR_SEVEN: {
        weekday: [(_time("00:00"), _time("23:59"))] for weekday in range(0, 7)
    },
}


BUILDING_TYPE_OPENING_PROFILE: Dict[str, OpeningHoursProfile] = {
    BuildingType.OFFICE.value: OpeningHoursProfile.OFFICE_STANDARD,
    BuildingType.COMMERCIAL.value: OpeningHoursProfile.RETAIL_STANDARD,
    BuildingType.RETAIL.value: OpeningHoursProfile.RETAIL_STANDARD,
    BuildingType.EDUCATION.value: OpeningHoursProfile.EDUCATION_STANDARD,
    BuildingType.SCHOOL.value: OpeningHoursProfile.EDUCATION_STANDARD,
    BuildingType.HOSPITAL.value: OpeningHoursProfile.TWENTY_FOUR_SEVEN,
    BuildingType.HEALTHCARE.value: OpeningHoursProfile.TWENTY_FOUR_SEVEN,
    BuildingType.HOTEL.value: OpeningHoursProfile.TWENTY_FOUR_SEVEN,
    BuildingType.HOSPITALITY.value: OpeningHoursProfile.HOSPITALITY_STANDARD,
    BuildingType.INDUSTRIAL.value: OpeningHoursProfile.INDUSTRIAL_STANDARD,
    BuildingType.LOGISTICS.value: OpeningHoursProfile.INDUSTRIAL_STANDARD,
    BuildingType.DATA_CENTER.value: OpeningHoursProfile.TWENTY_FOUR_SEVEN,
    BuildingType.RESIDENTIAL.value: OpeningHoursProfile.TWENTY_FOUR_SEVEN,
    BuildingType.MULTIFAMILY.value: OpeningHoursProfile.TWENTY_FOUR_SEVEN,
}


def get_opening_profile_for_building_type(building_type: Optional[str]) -> OpeningHoursProfile:
    if building_type:
        profile = BUILDING_TYPE_OPENING_PROFILE.get(building_type.lower())
        if profile:
            return profile
    return OpeningHoursProfile.OFFICE_STANDARD


def generate_occupancy_mask(
    index: pd.DatetimeIndex,
    profile: OpeningHoursProfile,
    holiday_dates: Optional[Iterable[pd.Timestamp]] = None,
) -> pd.Series:
    """
    Generate boolean mask for occupied timestamps.
    """
    if index.tz is not None:
        local_index = index.tz_convert("UTC").tz_localize(None)
    else:
        local_index = index

    holidays_lookup = set(pd.to_datetime(list(holiday_dates or [])))
    profile_def = PROFILE_DEFINITIONS.get(profile) or PROFILE_DEFINITIONS[OpeningHoursProfile.OFFICE_STANDARD]

    mask_values: List[bool] = []
    for ts in local_index:
        day = ts.replace(hour=0, minute=0, second=0, microsecond=0)
        if day in holidays_lookup:
            mask_values.append(False)
            continue
        weekday = ts.weekday()
        periods = profile_def.get(weekday, [])
        in_period = False
        for start, end in periods:
            if start <= ts.time() <= end:
                in_period = True
                break
        mask_values.append(in_period)
    return pd.Series(mask_values, index=index)


__all__ = [
    "PROFILE_DEFINITIONS",
    "get_opening_profile_for_building_type",
    "generate_occupancy_mask",
]
