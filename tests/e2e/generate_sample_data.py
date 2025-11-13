#!/usr/bin/env python3
"""Generate sample building data for testing."""

import pandas as pd
from pathlib import Path
import json
import numpy as np
from datetime import datetime, timedelta


def generate_room_data(
    room_name: str, days: int = 7, start_date: str = "2024-01-01"
) -> pd.DataFrame:
    """
    Generate realistic IEQ data for a room.

    Args:
        room_name: Room identifier
        days: Number of days to generate
        start_date: Start date (YYYY-MM-DD format)

    Returns:
        DataFrame with timestamp and IEQ parameters
    """
    start = pd.Timestamp(start_date)
    timestamps = pd.date_range(start=start, periods=days * 24, freq="h")

    # Generate realistic patterns
    np.random.seed(hash(room_name) % 2**32)

    # Temperature: 19-25°C with daily pattern
    base_temp = 21 + 3 * np.sin(np.arange(len(timestamps)) * 2 * np.pi / 24)
    temperature = base_temp + np.random.normal(0, 0.5, len(timestamps))

    # CO2: 400-1200 ppm, higher during occupancy
    occupancy_pattern = 0.8 * np.sin(np.arange(len(timestamps)) * 2 * np.pi / 24 - np.pi / 2)
    occupancy_pattern = np.maximum(occupancy_pattern, 0)  # Only positive
    co2 = 400 + occupancy_pattern * 600 + np.random.normal(0, 30, len(timestamps))

    # Humidity: 30-60% with daily pattern
    humidity = 45 + 10 * np.sin(np.arange(len(timestamps)) * 2 * np.pi / 24 - np.pi / 4)
    humidity = np.clip(humidity + np.random.normal(0, 2, len(timestamps)), 20, 80)

    # Some rooms have occasional violations
    if "problematic" in room_name.lower():
        # Increase violations
        mask = np.random.random(len(timestamps)) < 0.15
        co2[mask] = np.random.uniform(1200, 2000, mask.sum())
        temperature[mask] = np.random.uniform(26, 30, mask.sum())

    df = pd.DataFrame({
        "timestamp": timestamps,
        "temperature": temperature,
        "co2": co2,
        "humidity": humidity,
    })

    return df


def create_building_a():
    """Create Building A: Hierarchical with levels/rooms structure."""
    print("Creating Building A (hierarchical levels/rooms)...")
    base_path = Path("data/building_a")

    # Building metadata
    metadata = {
        "name": "Downtown Office Tower",
        "type": "office",
        "address": "123 Main Street",
        "city": "Copenhagen",
        "country": "Denmark",
    }

    with open(base_path / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    # Level 1 rooms
    rooms_level_1 = ["conference_room_1", "office_1", "office_2"]
    for room in rooms_level_1:
        df = generate_room_data(room)
        df.to_csv(base_path / "level_1" / f"{room}.csv", index=False)
        print(f"  ✓ {room}.csv")

    # Level 2 rooms (including problematic ones)
    rooms_level_2 = ["meeting_room", "office_3", "problematic_office"]
    for room in rooms_level_2:
        df = generate_room_data(room)
        df.to_csv(base_path / "level_2" / f"{room}.csv", index=False)
        print(f"  ✓ {room}.csv")


def create_building_b():
    """Create Building B: Flat structure with levels_rooms naming."""
    print("Creating Building B (flat structure with levels_rooms naming)...")
    base_path = Path("data/building_b")

    # Building metadata
    metadata = {
        "name": "Modern Shopping Mall",
        "type": "retail",
        "address": "456 Shopping Avenue",
        "city": "Aarhus",
        "country": "Denmark",
    }

    with open(base_path / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    # Flat structure with naming convention
    rooms = [
        "ground_floor_reception",
        "ground_floor_shop_1",
        "ground_floor_shop_2",
        "first_floor_office",
        "first_floor_storage",
        "basement_server_room",
    ]

    for room in rooms:
        df = generate_room_data(room)
        df.to_csv(base_path / f"{room}.csv", index=False)
        print(f"  ✓ {room}.csv")


def create_building_c():
    """Create Building C: Flat structure with only rooms."""
    print("Creating Building C (flat rooms only)...")
    base_path = Path("data/building_c")

    # Building metadata
    metadata = {
        "name": "School Building",
        "type": "school",
        "address": "789 Learning Lane",
        "city": "Odense",
        "country": "Denmark",
    }

    with open(base_path / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    # Flat structure with simple room names
    rooms = ["classroom_1", "classroom_2", "library", "computer_lab", "staff_room"]

    for room in rooms:
        df = generate_room_data(room)
        df.to_csv(base_path / f"{room}.csv", index=False)
        print(f"  ✓ {room}.csv")


def main():
    """Generate all sample data."""
    print("🏢 Generating sample building data...\n")

    create_building_a()
    print()
    create_building_b()
    print()
    create_building_c()

    print("\n✅ Sample data generated successfully!")
    print("\nDirectory structure:")
    print("data/")
    print("  building_a/          (hierarchical: level_1/, level_2/)")
    print("  building_b/          (flat: levels_rooms naming)")
    print("  building_c/          (flat: rooms only)")
    print("\nYou can now run analysis on this data:")
    print("  uv run hvx start --directory data/building_a")
    print("  uv run hvx start --directory data/building_b")
    print("  uv run hvx start --directory data/building_c")


if __name__ == "__main__":
    main()
