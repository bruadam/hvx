from __future__ import annotations

from typing import Dict, Iterable, Optional

import pandas as pd

from core import (
    Room,
    Building,
    generate_occupancy_mask,
    get_opening_profile_for_building_type,
)
from core.utils.calendar import get_holiday_dates
from standards.en16798.analysis import EN16798Calculator, VentilationType as ENVentilationType


def _room_dataframe(room: Room) -> Optional[pd.DataFrame]:
    if not room.timeseries_data:
        return None
    df = pd.DataFrame(room.timeseries_data)
    if room.timestamps and len(room.timestamps) == len(df.index):
        idx = pd.to_datetime(room.timestamps, errors="coerce")
        df.index = idx
        df = df[~df.index.isna()]
    elif "timestamp" in df.columns:
        idx = pd.to_datetime(df["timestamp"], errors="coerce")
        df = df.drop(columns=["timestamp"])
        df.index = idx
        df = df[~df.index.isna()]
    else:
        df.index = pd.RangeIndex(len(df))
    if df.empty:
        return None
    return df


def run_en16798_for_room(
    room: Room,
    season: str = "heating",
    building: Optional[Building] = None,
) -> Optional[Dict]:
    df = _room_dataframe(room)
    if df is None:
        return None

    occupancy_mask: Optional[pd.Series] = None
    if isinstance(df.index, pd.DatetimeIndex):
        building_type = getattr(building, "building_type", None)
        profile = get_opening_profile_for_building_type(
            building_type.lower() if isinstance(building_type, str) else building_type
        )
        holiday_dates = get_holiday_dates(getattr(building, "country", None))
        occupancy_mask = generate_occupancy_mask(df.index, profile, holiday_dates=holiday_dates)
        df = df[occupancy_mask]

    if df.empty:
        return None

    temperature = df["temperature"] if "temperature" in df else None
    co2 = df["co2"] if "co2" in df else None
    humidity = df["humidity"] if "humidity" in df else None

    ventilation_type = ENVentilationType.MECHANICAL
    if room.ventilation_type:
        try:
            ventilation_type = ENVentilationType(room.ventilation_type.value)
        except ValueError:
            ventilation_type = ENVentilationType.MECHANICAL

    results = EN16798Calculator.assess_timeseries_compliance(
        temperature=temperature,
        co2=co2,
        humidity=humidity,
        season=season,
        ventilation_type=ventilation_type,
    )
    return results


def run_en16798_for_rooms(
    rooms: Iterable[Room],
    season: str = "heating",
    buildings: Optional[Dict[str, Building]] = None,
) -> Dict[str, Dict]:
    summaries: Dict[str, Dict] = {}
    for room in rooms:
        building_obj = None
        if buildings:
            if room.building_id and room.building_id in buildings:
                building_obj = buildings.get(room.building_id)
            else:
                for parent_id in room.parent_ids:
                    if parent_id in buildings:
                        building_obj = buildings[parent_id]
                        break
        result = run_en16798_for_room(room, season=season, building=building_obj)
        if result:
            summaries[room.id] = result
    return summaries
