#!/usr/bin/env python3
"""Debug single room analysis."""

import pandas as pd
from pathlib import Path
from core.domain.models.room import Room
from core.analytics.engine.analysis_engine import AnalysisEngine

room_file = Path("data/test_rooms/room_cat_i_all.csv")
df = pd.read_csv(room_file, parse_dates=["timestamp"], index_col="timestamp")

# Create room
room = Room(
    id="test",
    name="Test Room",
    building_id="test_building",
    level_id="test_level",
    area=50.0,
)

room.time_series_data = df
room.data_start = df.index.min()
room.data_end = df.index.max()

print("Room data:")
print(f"  Has data: {room.has_data}")
print(f"  Available params: {room.available_parameters}")
if room.available_parameters:
    param_data = room.get_parameter_data(room.available_parameters[0])
    if param_data is not None:
        print(f"  {room.available_parameters[0].value}: {param_data.min():.1f} - {param_data.max():.1f}")

# Define one test
test = {
    "test_id": "cat_i_co2",
    "parameter": "co2",
    "standard": "en16798-1",
    "threshold": {"upper": 950},
}

engine = AnalysisEngine()

try:
    analysis = engine.analyze_room(room, tests=[test], apply_filters=False)
    print(f"\nAnalysis Results:")
    print(f"  Overall rate: {analysis.overall_compliance_rate:.1f}%")
    print(f"  Test count: {analysis.test_count}")
    print(f"  Compliance results: {analysis.compliance_results}")
    if analysis.compliance_results:
        for test_id, result in analysis.compliance_results.items():
            print(f"    {test_id}: {result.compliance_rate:.1f}%")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
