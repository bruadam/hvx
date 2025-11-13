"""
Example: Building Portfolio Analysis with Refactored Service

This example demonstrates the complete refactored service analyzing
a portfolio of buildings with generated datasets.

Demonstrates:
- Data generation for multiple buildings, floors, and rooms
- EN 16798-1 compliance assessment
- TAIL rating calculations
- Ventilation rate estimation
- Occupancy detection
- RC thermal modeling
- Portfolio-level aggregation
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import json

# Add refactored_service to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from engine import AnalysisEngine, AnalysisConfig
from engine.analysis_engine import (
    SpaceData,
    AnalysisType,
    VentilationType,
    PollutionLevel,
)
from calculators.en16798_calculator import EN16798Category


def generate_environmental_data(
    days: int = 30,
    room_type: str = "office",
    quality_level: str = "good"
) -> pd.DataFrame:
    """
    Generate synthetic environmental data for a room.

    Args:
        days: Number of days to generate
        room_type: Type of room (affects patterns)
        quality_level: "excellent", "good", "fair", "poor"

    Returns:
        DataFrame with temperature, co2, humidity, and outdoor data
    """
    n_hours = days * 24
    timestamps = pd.date_range(
        start=datetime(2024, 1, 1),
        periods=n_hours,
        freq='H'
    )

    # Outdoor temperature (sinusoidal with daily variation)
    outdoor_temp = 5 + 10 * np.sin(2 * np.pi * np.arange(n_hours) / (24 * 365))
    outdoor_temp += 5 * np.sin(2 * np.pi * np.arange(n_hours) / 24)  # Daily variation
    outdoor_temp += np.random.normal(0, 1, n_hours)  # Noise

    # Solar irradiance (W/m²)
    hour_of_day = timestamps.hour
    solar = np.maximum(0, 800 * np.sin(np.pi * (hour_of_day - 6) / 12))
    solar = np.where((hour_of_day >= 6) & (hour_of_day <= 18), solar, 0)
    solar += np.random.normal(0, 50, n_hours)
    solar = np.maximum(0, solar)

    # Indoor temperature (climate controlled)
    if quality_level == "excellent":
        indoor_temp = 21 + np.random.normal(0, 0.5, n_hours)
    elif quality_level == "good":
        indoor_temp = 21 + np.random.normal(0, 1.0, n_hours)
        # Add some excursions
        indoor_temp += 2 * np.sin(2 * np.pi * np.arange(n_hours) / 24)
    elif quality_level == "fair":
        indoor_temp = 21 + np.random.normal(0, 2.0, n_hours)
        indoor_temp += 3 * np.sin(2 * np.pi * np.arange(n_hours) / 24)
    else:  # poor
        indoor_temp = 20 + np.random.normal(0, 3.0, n_hours)
        indoor_temp += 5 * np.sin(2 * np.pi * np.arange(n_hours) / 24)

    # CO2 concentration (ppm) - varies with occupancy
    outdoor_co2 = 400
    is_weekday = timestamps.dayofweek < 5
    is_workhours = (timestamps.hour >= 8) & (timestamps.hour <= 17)
    is_occupied = is_weekday & is_workhours

    if quality_level == "excellent":
        co2_occupied = outdoor_co2 + 200 + np.random.normal(0, 30, n_hours)
    elif quality_level == "good":
        co2_occupied = outdoor_co2 + 400 + np.random.normal(0, 50, n_hours)
    elif quality_level == "fair":
        co2_occupied = outdoor_co2 + 700 + np.random.normal(0, 80, n_hours)
    else:  # poor
        co2_occupied = outdoor_co2 + 1000 + np.random.normal(0, 150, n_hours)

    co2_unoccupied = outdoor_co2 + np.random.normal(0, 20, n_hours)
    co2 = np.where(is_occupied, co2_occupied, co2_unoccupied)

    # Add CO2 decay pattern when becoming unoccupied
    for i in range(1, len(co2)):
        if not is_occupied[i] and is_occupied[i-1]:
            # Start of decay
            decay_hours = min(4, len(co2) - i)
            for j in range(decay_hours):
                if i + j < len(co2):
                    decay_factor = np.exp(-0.3 * j)  # Exponential decay
                    co2[i + j] = outdoor_co2 + (co2[i-1] - outdoor_co2) * decay_factor

    co2 = np.maximum(outdoor_co2, co2)

    # Relative humidity (%)
    if quality_level in ["excellent", "good"]:
        humidity = 40 + np.random.normal(0, 5, n_hours)
    elif quality_level == "fair":
        humidity = 45 + np.random.normal(0, 10, n_hours)
    else:  # poor
        humidity = 50 + np.random.normal(0, 15, n_hours)

    humidity = np.clip(humidity, 20, 80)

    return pd.DataFrame({
        'timestamp': timestamps,
        'temperature': indoor_temp,
        'co2': co2,
        'humidity': humidity,
        'outdoor_temperature': outdoor_temp,
        'solar_irradiance': solar,
    }).set_index('timestamp')


def create_sample_portfolio() -> list[SpaceData]:
    """
    Create a sample building portfolio with generated data.

    Portfolio structure:
    - 3 Buildings (Office, School, Retail)
    - Each building has 2 floors
    - Each floor has 3-5 rooms

    Returns:
        List of SpaceData objects
    """
    spaces = []
    space_id_counter = 1

    # Building configurations
    buildings = [
        {
            "name": "Office Building A",
            "type": "office",
            "floors": 2,
            "rooms_per_floor": 5,
            "quality_distribution": ["excellent", "good", "good", "fair", "fair"],
        },
        {
            "name": "School Building B",
            "type": "school",
            "floors": 2,
            "rooms_per_floor": 4,
            "quality_distribution": ["good", "good", "fair", "fair"],
        },
        {
            "name": "Retail Building C",
            "type": "retail",
            "floors": 2,
            "rooms_per_floor": 3,
            "quality_distribution": ["fair", "fair", "poor"],
        },
    ]

    for bldg_idx, building_config in enumerate(buildings):
        building_id = f"building_{bldg_idx + 1}"

        # Create building space (no time series data at building level)
        building_space = SpaceData(
            id=building_id,
            name=building_config["name"],
            type="building",
            area_m2=1000.0,
            volume_m3=3000.0,
            room_type=building_config["type"],
        )
        spaces.append(building_space)

        # Create floors
        for floor_idx in range(building_config["floors"]):
            floor_id = f"{building_id}_floor_{floor_idx + 1}"

            floor_space = SpaceData(
                id=floor_id,
                name=f"Floor {floor_idx + 1}",
                type="floor",
                area_m2=500.0,
                volume_m3=1500.0,
                parent_id=building_id,
            )
            spaces.append(floor_space)

            # Create rooms
            for room_idx in range(building_config["rooms_per_floor"]):
                room_id = f"{floor_id}_room_{room_idx + 1}"
                quality = building_config["quality_distribution"][
                    room_idx % len(building_config["quality_distribution"])
                ]

                # Generate environmental data
                env_data = generate_environmental_data(
                    days=30,
                    room_type=building_config["type"],
                    quality_level=quality
                )

                # Room properties
                area = 25.0 + np.random.uniform(-5, 5)
                volume = area * 3.0
                window_area = area * 0.2

                # Determine ventilation type
                if building_config["type"] == "office":
                    vent_type = VentilationType.MECHANICAL
                    pollution = PollutionLevel.LOW
                    occupancy = 3
                elif building_config["type"] == "school":
                    vent_type = VentilationType.MIXED_MODE
                    pollution = PollutionLevel.NON_LOW
                    occupancy = 25
                else:  # retail
                    vent_type = VentilationType.NATURAL
                    pollution = PollutionLevel.NON_LOW
                    occupancy = 10

                room_space = SpaceData(
                    id=room_id,
                    name=f"Room {room_idx + 1}",
                    type="room",
                    area_m2=area,
                    volume_m3=volume,
                    window_area_m2=window_area,
                    occupancy_count=occupancy,
                    room_type=building_config["type"],
                    ventilation_type=vent_type,
                    pollution_level=pollution,
                    construction_type="medium",
                    temperature=env_data['temperature'],
                    co2=env_data['co2'],
                    humidity=env_data['humidity'],
                    outdoor_temperature=env_data['outdoor_temperature'],
                    solar_irradiance=env_data['solar_irradiance'],
                    parent_id=floor_id,
                    metadata={
                        "quality_level": quality,
                        "building_name": building_config["name"],
                    }
                )
                spaces.append(room_space)

                # Update parent child_ids
                floor_space.child_ids.append(room_id)

            building_space.child_ids.append(floor_id)

    return spaces


def print_analysis_results(result):
    """Print analysis results in a readable format."""
    print("\n" + "=" * 80)
    print(f"PORTFOLIO ANALYSIS RESULTS: {result.portfolio_name}")
    print("=" * 80)

    print("\n📊 PORTFOLIO SUMMARY")
    print("-" * 80)
    summary = result.portfolio_summary
    print(f"Total Spaces: {summary['total_spaces']}")
    print(f"Total Buildings: {summary['total_buildings']}")
    print(f"Average TAIL Compliance: {summary['avg_tail_compliance']:.1f}%")
    print(f"\nSpaces by Type:")
    for space_type, count in summary['spaces_by_type'].items():
        print(f"  - {space_type}: {count}")

    print("\n🏢 BUILDING SUMMARIES")
    print("-" * 80)
    for building_id, bldg_summary in result.building_summaries.items():
        building_name = next(
            (s.name for s in result.space_results.values()
             if s.space_id == building_id),
            building_id
        )
        print(f"\n{building_name} ({building_id}):")
        print(f"  Rooms: {bldg_summary['child_count']}")
        print(f"  Avg TAIL Compliance: {bldg_summary['avg_tail_compliance']:.1f}%")
        if bldg_summary['worst_tail_rating']:
            print(f"  Worst TAIL Rating: {bldg_summary['worst_tail_rating']}")

    print("\n📍 ROOM-LEVEL RESULTS (Sample)")
    print("-" * 80)

    # Show first 5 rooms
    room_results = [
        r for r in result.space_results.values()
        if r.space_type == "room"
    ][:5]

    for room_result in room_results:
        print(f"\n{room_result.space_name} ({room_result.space_id}):")

        # EN 16798-1
        if room_result.en16798_result:
            en_data = room_result.en16798_result.get("compliance", {})
            if isinstance(en_data, dict):
                print("  EN 16798-1 Compliance:")
                for category, data in list(en_data.items())[:2]:  # Show first 2 categories
                    print(f"    Category {category}: {data.get('compliance_rate', 0):.1f}%")

        # TAIL
        if room_result.tail_result:
            tail = room_result.tail_result
            print(f"  TAIL Rating: {tail.get('overall_rating_label', 'N/A')} "
                  f"({tail.get('overall_compliance_rate', 0):.1f}%)")

        # Ventilation
        if room_result.ventilation_result and "ach" in room_result.ventilation_result:
            vent = room_result.ventilation_result
            print(f"  Ventilation: {vent['ach']} ACH ({vent['category']})")

        # Occupancy
        if room_result.occupancy_result:
            occ = room_result.occupancy_result
            print(f"  Occupancy: {occ['estimated_occupants']} persons "
                  f"({occ['occupancy_rate']*100:.1f}% occupied)")


def main():
    """Main example execution."""
    print("\n" + "=" * 80)
    print("BUILDING PORTFOLIO ANALYSIS - REFACTORED SERVICE")
    print("=" * 80)

    print("\n🏗️  Step 1: Generating Sample Portfolio...")
    spaces = create_sample_portfolio()
    print(f"✓ Created {len(spaces)} spaces:")
    print(f"  - Buildings: {sum(1 for s in spaces if s.type == 'building')}")
    print(f"  - Floors: {sum(1 for s in spaces if s.type == 'floor')}")
    print(f"  - Rooms: {sum(1 for s in spaces if s.type == 'room')}")

    print("\n⚙️  Step 2: Configuring Analysis Engine...")
    config = AnalysisConfig(
        analyses_to_run=[
            AnalysisType.EN16798,
            AnalysisType.TAIL,
            AnalysisType.VENTILATION,
            AnalysisType.OCCUPANCY,
        ],
        en16798_categories=[
            EN16798Category.CATEGORY_I,
            EN16798Category.CATEGORY_II,
            EN16798Category.CATEGORY_III,
        ],
        season="heating",
        tail_thresholds={
            "temperature": {"lower": 20.0, "upper": 24.0},
            "co2": {"lower": 0, "upper": 1200},
            "humidity": {"lower": 25, "upper": 60},
        },
    )
    print("✓ Configuration ready")

    print("\n🔬 Step 3: Running Portfolio Analysis...")
    engine = AnalysisEngine(config)
    result = engine.analyze_portfolio(
        spaces=spaces,
        portfolio_id="sample_portfolio",
        portfolio_name="Sample Building Portfolio"
    )
    print("✓ Analysis complete!")

    # Print results
    print_analysis_results(result)

    # Export results to JSON
    print("\n💾 Step 4: Exporting Results...")
    output_file = Path(__file__).parent / "portfolio_analysis_results.json"

    # Prepare JSON-serializable data
    export_data = {
        "portfolio_id": result.portfolio_id,
        "portfolio_name": result.portfolio_name,
        "portfolio_summary": result.portfolio_summary,
        "building_summaries": result.building_summaries,
        "room_count": len([r for r in result.space_results.values() if r.space_type == "room"]),
        "timestamp": datetime.now().isoformat(),
    }

    with open(output_file, 'w') as f:
        json.dump(export_data, f, indent=2)

    print(f"✓ Results exported to: {output_file}")

    print("\n" + "=" * 80)
    print("✅ PORTFOLIO ANALYSIS COMPLETE!")
    print("=" * 80)
    print("\nKey Achievements:")
    print("  ✓ Multi-building portfolio analysis")
    print("  ✓ EN 16798-1 compliance assessment")
    print("  ✓ TAIL rating calculations")
    print("  ✓ Ventilation rate estimation")
    print("  ✓ Occupancy detection")
    print("  ✓ Hierarchical aggregation (room → floor → building → portfolio)")
    print("\nThe refactored service successfully integrated all calculations!")


if __name__ == "__main__":
    main()
