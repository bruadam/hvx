"""
Enhanced Entities Demonstration

This example demonstrates how to use the enhanced Portfolio, Building, Floor,
and Room entities with their full functionality including:
- Hierarchy management
- Property aggregation
- Self-analysis capabilities
- Energy metrics
"""

from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.models import (
    Portfolio,
    Building,
    Floor,
    Room,
    VentilationType,
)


def main():
    print("=" * 80)
    print("ENHANCED SPATIAL ENTITIES DEMONSTRATION")
    print("=" * 80)

    # ============================================================
    # 1. CREATE PORTFOLIO
    # ============================================================
    print("\n1. Creating Portfolio...")
    portfolio = Portfolio(
        id="portfolio_001",
        name="Green Building Portfolio",
        country="Denmark",
        region="Nordic",
    )
    print(f"   Created: {portfolio.name}")
    print(f"   Building count: {portfolio.building_count}")

    # ============================================================
    # 2. CREATE BUILDINGS
    # ============================================================
    print("\n2. Creating Buildings...")

    building1 = Building(
        id="building_001",
        name="Copenhagen Office Tower",
        building_type="office",
        area_m2=5000.0,
        year_built=2015,
        address="Nørrebrogade 123",
        city="Copenhagen",
        country="Denmark",
        ventilation_type=VentilationType.MECHANICAL,
        annual_heating_kwh=150000.0,
        annual_electricity_kwh=200000.0,
        annual_cooling_kwh=50000.0,
        epc_rating="B",
    )

    building2 = Building(
        id="building_002",
        name="Aarhus Innovation Center",
        building_type="office",
        area_m2=3000.0,
        year_built=2018,
        city="Aarhus",
        country="Denmark",
        ventilation_type=VentilationType.MECHANICAL,
        annual_heating_kwh=90000.0,
        annual_electricity_kwh=120000.0,
        epc_rating="A",
    )

    # Add buildings to portfolio
    portfolio.add_building(building1.id)
    portfolio.add_building(building2.id)

    print(f"   Created building: {building1.name}")
    print(f"   Created building: {building2.name}")
    print(f"   Portfolio now has {portfolio.building_count} buildings")

    # ============================================================
    # 3. CREATE FLOORS
    # ============================================================
    print("\n3. Creating Floors...")

    floor1 = Floor(
        id="floor_001",
        name="Ground Floor",
        floor_number=0,
        building_id=building1.id,
        area_m2=1250.0,
    )

    floor2 = Floor(
        id="floor_002",
        name="First Floor",
        floor_number=1,
        building_id=building1.id,
        area_m2=1250.0,
    )

    # Add floors to building
    building1.add_floor(floor1.id)
    building1.add_floor(floor2.id)

    print(f"   Created floor: {floor1.name} (Floor {floor1.floor_number})")
    print(f"   Created floor: {floor2.name} (Floor {floor2.floor_number})")
    print(f"   Building {building1.name} now has {building1.floor_count} floors")

    # ============================================================
    # 4. CREATE ROOMS
    # ============================================================
    print("\n4. Creating Rooms...")

    room1 = Room(
        id="room_001",
        name="Conference Room A",
        room_type="meeting_room",
        floor_id=floor1.id,
        building_id=building1.id,
        area_m2=50.0,
        volume_m3=150.0,
        design_occupancy=12,
        ventilation_type=VentilationType.MECHANICAL,
    )

    room2 = Room(
        id="room_002",
        name="Open Office Space",
        room_type="office",
        floor_id=floor1.id,
        building_id=building1.id,
        area_m2=200.0,
        volume_m3=600.0,
        design_occupancy=40,
        ventilation_type=VentilationType.MECHANICAL,
    )

    room3 = Room(
        id="room_003",
        name="Executive Office",
        room_type="office",
        floor_id=floor2.id,
        building_id=building1.id,
        area_m2=30.0,
        volume_m3=90.0,
        design_occupancy=2,
        ventilation_type=VentilationType.MECHANICAL,
    )

    # Add rooms to floors
    floor1.add_room(room1.id)
    floor1.add_room(room2.id)
    floor2.add_room(room3.id)

    print(f"   Created room: {room1.name} ({room1.area_m2}m²)")
    print(f"   Created room: {room2.name} ({room2.area_m2}m²)")
    print(f"   Created room: {room3.name} ({room3.area_m2}m²)")
    print(f"   Floor {floor1.name} now has {floor1.room_count} rooms")
    print(f"   Floor {floor2.name} now has {floor2.room_count} rooms")

    # ============================================================
    # 5. ADD TIME SERIES DATA TO ROOMS
    # ============================================================
    print("\n5. Adding Time Series Data to Rooms...")

    # Simulate some temperature data for room1
    timestamps = [f"2024-01-{i:02d} 12:00:00" for i in range(1, 8)]
    temperatures = [21.5, 22.0, 21.8, 22.2, 21.7, 22.1, 21.9]
    co2_values = [450, 480, 460, 490, 470, 485, 475]
    humidity_values = [45, 46, 44, 47, 45, 46, 45]

    room1.add_timeseries("temperature", temperatures, timestamps)
    room1.add_timeseries("co2", co2_values)
    room1.add_timeseries("humidity", humidity_values)

    print(f"   Added time series data to {room1.name}")
    print(f"   Available metrics: {room1.available_metrics}")
    print(f"   Data points: {len(room1.timestamps)}")

    # ============================================================
    # 6. COMPUTE BUILDING ENERGY METRICS
    # ============================================================
    print("\n6. Computing Building Energy Metrics...")

    energy_metrics = building1.compute_metrics(metrics=['energy'])
    energy_summary = building1.get_energy_summary()

    print(f"   Building: {building1.name}")
    print(f"   Total Energy: {energy_metrics.get('total_energy_kwh', 0):.0f} kWh/year")
    print(f"   Energy Intensity: {energy_metrics.get('energy_intensity', 0):.1f} kWh/m²/year")
    print(f"   Primary Energy: {energy_summary.get('primary_energy_kwh_m2', 0):.1f} kWh/m²/year")
    print(f"   EPC Rating: {building1.epc_rating}")

    # ============================================================
    # 7. COMPUTE ROOM METRICS
    # ============================================================
    print("\n7. Computing Room Metrics...")

    room_metrics = room1.compute_metrics()

    print(f"   Room: {room1.name}")
    print(f"   Has data: {room_metrics['has_data']}")
    print(f"   Temperature mean: {room_metrics.get('temperature_mean', 0):.1f}°C")
    print(f"   Temperature range: {room_metrics.get('temperature_min', 0):.1f} - {room_metrics.get('temperature_max', 0):.1f}°C")
    print(f"   CO2 mean: {room_metrics.get('co2_mean', 0):.0f} ppm")
    print(f"   Humidity mean: {room_metrics.get('humidity_mean', 0):.0f}%")

    # ============================================================
    # 8. COMPUTE FLOOR AGGREGATION
    # ============================================================
    print("\n8. Computing Floor Aggregation...")

    # Create a simple lookup function
    rooms_dict = {room1.id: room1, room2.id: room2, room3.id: room3}

    def room_lookup(room_id):
        return rooms_dict.get(room_id)

    # Compute room metrics first
    room2.compute_metrics()
    room3.compute_metrics()

    floor_metrics = floor1.compute_metrics(room_lookup=room_lookup)

    print(f"   Floor: {floor1.name}")
    print(f"   Room count: {floor_metrics['room_count']}")
    print(f"   Total area: {floor_metrics.get('total_area_m2', 0):.0f} m²")

    # ============================================================
    # 9. COMPUTE PORTFOLIO AGGREGATION
    # ============================================================
    print("\n9. Computing Portfolio Aggregation...")

    buildings_dict = {building1.id: building1, building2.id: building2}

    def building_lookup(building_id):
        return buildings_dict.get(building_id)

    # Compute building metrics
    building2.compute_metrics(metrics=['energy'])

    portfolio_metrics = portfolio.compute_metrics(building_lookup=building_lookup)

    print(f"   Portfolio: {portfolio.name}")
    print(f"   Building count: {portfolio_metrics['building_count']}")
    print(f"   Total area: {portfolio_metrics.get('total_area_m2', 0):.0f} m²")
    print(f"   Total energy: {portfolio_metrics.get('total_energy_kwh', 0):.0f} kWh/year")
    print(f"   Energy intensity: {portfolio_metrics.get('energy_intensity_kwh_m2', 0):.1f} kWh/m²/year")

    # ============================================================
    # 10. DISPLAY SUMMARIES
    # ============================================================
    print("\n10. Entity Summaries...")

    print("\n   Portfolio Summary:")
    portfolio_summary = portfolio.get_summary()
    for key, value in portfolio_summary.items():
        print(f"      {key}: {value}")

    print("\n   Building Summary:")
    building_summary = building1.get_summary()
    for key in ['id', 'name', 'building_type', 'floor_count', 'total_area_m2', 'epc_rating']:
        print(f"      {key}: {building_summary.get(key)}")

    print("\n   Floor Summary:")
    floor_summary = floor1.get_summary()
    for key in ['id', 'name', 'floor_number', 'room_count', 'total_area_m2']:
        print(f"      {key}: {floor_summary.get(key)}")

    print("\n   Room Summary:")
    room_summary = room1.get_summary()
    for key in ['id', 'name', 'room_type', 'area_m2', 'has_data', 'available_metrics']:
        print(f"      {key}: {room_summary.get(key)}")

    print("\n" + "=" * 80)
    print("DEMONSTRATION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
