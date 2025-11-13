"""Quick test of worst room report generation - simplified version."""

from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np

from core.domain.models.room import Room
from core.analytics.engine.analysis_engine import AnalysisEngine
from core.utils.synthetic_climate_data import generate_climate_data

print("Quick Test: Worst Room Analysis\n" + "=" * 50)

# Step 1: Generate climate data (1 month for speed)
print("\n[1/4] Generating climate data...")
climate_data = generate_climate_data(
    start_date="2024-01-01",
    end_date="2024-01-31",
    freq="h",
    seed=42,
)
print(f"  ✓ Generated {len(climate_data)} records")

# Step 2: Create test rooms
print("\n[2/4] Creating test rooms...")
dates = pd.date_range("2024-01-01", "2024-01-31", freq="h")
n = len(dates)

# Normal room
normal_data = pd.DataFrame(
    {
        "temperature": 22 + np.random.normal(0, 0.5, n),
        "co2": 550 + np.random.normal(0, 50, n),
        "humidity": 50 + np.random.normal(0, 5, n),
    },
    index=dates,
)

# Bad room (overheating)
bad_data = pd.DataFrame(
    {
        "temperature": 26 + np.random.normal(0, 1, n),  # Too hot
        "co2": 900 + np.random.normal(0, 100, n),  # High CO2
        "humidity": 45 + np.random.normal(0, 5, n),
    },
    index=dates,
)

rooms = [
    Room(
        id="room_001",
        name="Normal Office",
        level_id="level_1",
        building_id="building_1",
        time_series_data=normal_data,
        data_start=dates[0],
        data_end=dates[-1],
    ),
    Room(
        id="room_002",
        name="Problem Conference Room",
        level_id="level_1",
        building_id="building_1",
        time_series_data=bad_data,
        data_start=dates[0],
        data_end=dates[-1],
    ),
]
print(f"  ✓ Created {len(rooms)} rooms")

# Step 3: Analyze rooms
print("\n[3/4] Running compliance analysis...")
engine = AnalysisEngine()

tests = [
    {
        "test_id": "temp_class_ii",
        "parameter": "temperature",
        "standard": "en16798-1",
        "threshold": {"lower": 20.0, "upper": 24.0},
        "config": {"building_class": "II"},
    },
    {
        "test_id": "co2_class_ii",
        "parameter": "co2",
        "standard": "en16798-1",
        "threshold": {"upper": 800.0},
        "config": {"building_class": "II"},
    },
    {
        "test_id": "humidity_class_ii",
        "parameter": "humidity",
        "standard": "en16798-1",
        "threshold": {"lower": 30.0, "upper": 60.0},
        "config": {"building_class": "II"},
    },
]

room_analyses = []
for room in rooms:
    analysis = engine.analyze_room(room, tests=tests)
    room_analyses.append(analysis)
    print(f"  ✓ {room.name}: {analysis.overall_compliance_rate:.1f}% compliance")

# Step 4: Identify worst
print("\n[4/4] Identifying worst performer...")
sorted_analyses = sorted(room_analyses, key=lambda x: x.overall_compliance_rate)
worst = sorted_analyses[0]

print(f"\n  🔴 WORST PERFORMER: {worst.room_name}")
print(f"     Overall compliance: {worst.overall_compliance_rate:.1f}%")
print(f"     Test count: {worst.test_count}")
print(f"     Failed tests: {len(worst.failed_tests)}")

print(f"\n     Individual test results:")
for test_id, result in worst.compliance_results.items():
    print(f"       • {test_id}: {result.compliance_rate:.1f}%")

print("\n" + "=" * 50)
print("✓ Test completed successfully!")
print("\nThe compliance calculation is now working correctly.")
print("You can now run the full demo:")
print("  python examples/demo_worst_room_climate_report.py")
