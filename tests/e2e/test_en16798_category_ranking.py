

import pytest
import pandas as pd
from pathlib import Path
from core.domain.models.room import Room
from core.analytics.engine.analysis_engine import AnalysisEngine

# EN16798-1 test configs (copied from analyze_test_rooms.py)
TEST_CONFIGS = [
    {"test_id": "cat_i_temperature", "parameter": "temperature", "standard": "en16798-1", "threshold": {"lower": 21, "upper": 23}},
    {"test_id": "cat_i_co2", "parameter": "co2", "standard": "en16798-1", "threshold": {"upper": 950}},
    {"test_id": "cat_i_humidity", "parameter": "humidity", "standard": "en16798-1", "threshold": {"lower": 30, "upper": 50}},
    {"test_id": "cat_ii_temperature", "parameter": "temperature", "standard": "en16798-1", "threshold": {"lower": 20, "upper": 24}},
    {"test_id": "cat_ii_co2", "parameter": "co2", "standard": "en16798-1", "threshold": {"upper": 1200}},
    {"test_id": "cat_ii_humidity", "parameter": "humidity", "standard": "en16798-1", "threshold": {"lower": 25, "upper": 60}},
    {"test_id": "cat_iii_temperature", "parameter": "temperature", "standard": "en16798-1", "threshold": {"lower": 19, "upper": 25}},
    {"test_id": "cat_iii_co2", "parameter": "co2", "standard": "en16798-1", "threshold": {"upper": 1500}},
    {"test_id": "cat_iii_humidity", "parameter": "humidity", "standard": "en16798-1", "threshold": {"lower": 20, "upper": 70}},
]

# Expected results for each test room (category keys: 'i', 'ii', 'iii')
EXPECTED_RESULTS = {
    "room_cat_i_all": "i",
    "room_cat_ii_all": "ii",
    "room_cat_i_temp_cat_iii_co2": "iii",
    "room_cat_ii_temp_cat_iii_other": "iii",
    "room_cat_iii_all": "iii",
}
CATEGORY_MAP = {"i": 100.0, "ii": 75.0, "iii": 50.0}

@pytest.mark.parametrize("room_name,expected_category", EXPECTED_RESULTS.items())
def test_en16798_category_ranking(room_name, expected_category):
    data_path = Path("data/test_rooms") / f"{room_name}.csv"
    assert data_path.exists(), f"Missing data file: {data_path}"
    # Load data and create Room
    df = pd.read_csv(data_path, parse_dates=["timestamp"], index_col="timestamp")
    room = Room(
        id=room_name,
        name=room_name,
        building_id="test_building",
        level_id="test_level",
        area=50.0,
    )
    room.time_series_data = df
    room.data_start = df.index.min()
    room.data_end = df.index.max()
    # Run analysis with EN16798-1 test configs
    engine = AnalysisEngine()
    analysis = engine.analyze_room(room, tests=TEST_CONFIGS, apply_filters=False)
    # Extract results
    highest_category = analysis.standard_compliance.get("highest_category")
    overall_rate = analysis.overall_compliance_rate
    assert highest_category == expected_category, f"{room_name}: expected {expected_category}, got {highest_category}"
    assert overall_rate == CATEGORY_MAP[expected_category], f"{room_name}: expected rate {CATEGORY_MAP[expected_category]}, got {overall_rate}"
