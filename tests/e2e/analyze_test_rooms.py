#!/usr/bin/env python3
"""Analyze test rooms and verify EN 16798-1 category compliance ranking."""

import pandas as pd
from pathlib import Path
import yaml
from typing import Dict, List
from core.domain.models.room import Room
from core.domain.models.building import Building
from core.analytics.engine.analysis_engine import AnalysisEngine
from datetime import datetime

# Create test building/rooms
test_rooms_dir = Path("data/test_rooms")
test_room_files = sorted(test_rooms_dir.glob("*.csv"))

print("EN 16798-1 Compliance Category Ranking Test")
print("=" * 100)
print()

# Load test configurations (without filters for clean testing)
test_configs = {
    "cat_i_temperature": {
        "test_id": "cat_i_temperature",
        "parameter": "temperature",
        "standard": "en16798-1",
        "threshold": {"lower": 21, "upper": 23},
    },
    "cat_i_co2": {
        "test_id": "cat_i_co2",
        "parameter": "co2",
        "standard": "en16798-1",
        "threshold": {"upper": 950},
    },
    "cat_i_humidity": {
        "test_id": "cat_i_humidity",
        "parameter": "humidity",
        "standard": "en16798-1",
        "threshold": {"lower": 30, "upper": 50},
    },
    "cat_ii_temperature": {
        "test_id": "cat_ii_temperature",
        "parameter": "temperature",
        "standard": "en16798-1",
        "threshold": {"lower": 20, "upper": 24},
    },
    "cat_ii_co2": {
        "test_id": "cat_ii_co2",
        "parameter": "co2",
        "standard": "en16798-1",
        "threshold": {"upper": 1200},
    },
    "cat_ii_humidity": {
        "test_id": "cat_ii_humidity",
        "parameter": "humidity",
        "standard": "en16798-1",
        "threshold": {"lower": 25, "upper": 60},
    },
    "cat_iii_temperature": {
        "test_id": "cat_iii_temperature",
        "parameter": "temperature",
        "standard": "en16798-1",
        "threshold": {"lower": 19, "upper": 25},
    },
    "cat_iii_co2": {
        "test_id": "cat_iii_co2",
        "parameter": "co2",
        "standard": "en16798-1",
        "threshold": {"upper": 1500},
    },
    "cat_iii_humidity": {
        "test_id": "cat_iii_humidity",
        "parameter": "humidity",
        "standard": "en16798-1",
        "threshold": {"lower": 20, "upper": 70},
    },
}

# Analyze each room
results = []
engine = AnalysisEngine()

for room_file in test_room_files:
    room_name = room_file.stem
    
    # Load data
    df = pd.read_csv(room_file, parse_dates=["timestamp"], index_col="timestamp")
    
    # Create room object
    room = Room(
        id=room_name,
        name=room_name,
        building_id="test_building",
        level_id="test_level",
        area=50.0,
    )
    
    # Load data into room
    room.time_series_data = df
    room.data_start = df.index.min()
    room.data_end = df.index.max()
    
    # Run analysis
    try:
        analysis = engine.analyze_room(room, tests=list(test_configs.values()), apply_filters=False)
        
        # Extract results
        highest_category = analysis.standard_compliance.get("highest_category")
        category_compliance = analysis.standard_compliance.get("category_compliance", {})
        overall_rate = analysis.overall_compliance_rate
        
        results.append({
            "room": room_name,
            "highest_category": highest_category or "none",
            "cat_i_compliant": category_compliance.get("i", False),
            "cat_ii_compliant": category_compliance.get("ii", False),
            "cat_iii_compliant": category_compliance.get("iii", False),
            "overall_rate": overall_rate,
            "test_count": analysis.test_count,
            "passed_tests": len(analysis.passed_tests),
        })
    except Exception as e:
        print(f"ERROR analyzing {room_name}: {e}")
        import traceback
        traceback.print_exc()

# Display results
print("COMPLIANCE RANKING RESULTS")
print("=" * 100)
print()

# Sort by category (i > ii > iii > none)
category_order = {"i": 3, "ii": 2, "iii": 1, "none": 0}
sorted_results = sorted(results, key=lambda x: category_order.get(x["highest_category"], 0), reverse=True)

print(f"{'Room':<40} {'Category':<12} {'Rate':<8} {'Tests':<8} {'Details':<35}")
print("-" * 100)

for result in sorted_results:
    room_name = result["room"][:40]
    category = result["highest_category"].upper()
    rate = f"{result['overall_rate']:.1f}%"
    test_count = f"{result['passed_tests']}/{result['test_count']}"
    
    # Build compliance details
    details = []
    if result["cat_i_compliant"]:
        details.append("Cat I✓")
    if result["cat_ii_compliant"]:
        details.append("Cat II✓")
    if result["cat_iii_compliant"]:
        details.append("Cat III✓")
    details_str = ", ".join(details) if details else "None"
    
    print(f"{room_name:<40} {category:<12} {rate:<8} {test_count:<8} {details_str:<35}")

print()
print("=" * 100)
print("VERIFICATION CHECKS")
print("-" * 100)

# Expected rankings
expected = {
    "room_cat_i_all": {"category": "i", "rate": 100.0},
    "room_cat_i_temp_cat_iii_co2": {"category": "iii", "rate": 50.0},  # Worst category wins
    "room_cat_ii_all": {"category": "ii", "rate": 75.0},
    "room_cat_ii_temp_cat_iii_other": {"category": "iii", "rate": 50.0},
    "room_cat_iii_all": {"category": "iii", "rate": 50.0},
}

all_pass = True
for result in sorted_results:
    room = result["room"]
    if room in expected:
        exp_cat = expected[room]["category"]
        exp_rate = expected[room]["rate"]
        actual_cat = result["highest_category"]
        actual_rate = result["overall_rate"]
        
        cat_match = actual_cat == exp_cat
        rate_match = abs(actual_rate - exp_rate) < 1.0  # Allow 1% tolerance
        
        status = "✓ PASS" if (cat_match and rate_match) else "✗ FAIL"
        
        print(f"{status} | {room:<40} | Expected: {exp_cat.upper()} ({exp_rate:.0f}%) | Got: {actual_cat.upper()} ({actual_rate:.1f}%)")
        
        if not (cat_match and rate_match):
            all_pass = False

print()
if all_pass:
    print("✓ ALL TESTS PASSED - Compliance ranking is correct!")
else:
    print("✗ SOME TESTS FAILED - Check compliance calculation logic")
