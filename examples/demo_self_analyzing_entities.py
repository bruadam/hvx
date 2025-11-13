"""
Demonstration of self-analyzing entities.

Shows how entities (Room, Level, Building) can compute their own metrics
when data is available, without needing separate analysis objects.

This implements the pattern:
1. Entities store physical properties and data
2. Entities know how to analyze themselves (compute_metrics)
3. Metrics are cached in the entity for quick access
4. Hierarchy automatically aggregates from children
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from core.domain.enums.building_type import BuildingType
from core.domain.enums.countries import Country
from core.domain.enums.belgium_region import Region
from core.domain.models.entities import Building, Level, Room


def create_sample_time_series_data(days: int = 7) -> pd.DataFrame:
    """Create sample sensor data for demonstration."""
    start_date = datetime(2024, 1, 1)
    dates = pd.date_range(start=start_date, periods=days * 24, freq='H')
    
    # Simulate realistic office data
    np.random.seed(42)
    data = pd.DataFrame({
        'temperature': 20 + 3 * np.sin(np.arange(len(dates)) * 2 * np.pi / 24) + np.random.normal(0, 0.5, len(dates)),
        'co2': 400 + 200 * np.sin(np.arange(len(dates)) * 2 * np.pi / 24) + np.random.normal(0, 50, len(dates)),
        'humidity': 45 + 5 * np.sin(np.arange(len(dates)) * 2 * np.pi / 24) + np.random.normal(0, 2, len(dates)),
    }, index=dates)
    
    return data


def main() -> None:
    """Demonstrate self-analyzing entities."""
    
    print("=" * 80)
    print("SELF-ANALYZING ENTITIES DEMONSTRATION")
    print("=" * 80)
    print("\nEntities can compute their own metrics when data is available!")
    print("No need for separate analysis objects or external calculators.")
    
    # ============================================================================
    # PART 1: Room-Level Self-Analysis
    # ============================================================================
    print("\n" + "=" * 80)
    print("PART 1: ROOM SELF-ANALYSIS")
    print("=" * 80)
    
    # Create a room with physical properties
    room1 = Room(
        id="room-101",
        name="Office 101",
        room_type="office",
        area=25.0,
        volume=75.0,
        occupancy=2,
        orientations=[90.0],  # East-facing
        window_areas=[4.0],
        shading_factors=[0.3],
        last_renovation_year=2020
    )
    
    print(f"\n📐 Created {room1.name}:")
    print(f"   Area: {room1.area} m²")
    print(f"   Volume: {room1.volume} m³")
    print(f"   Occupancy: {room1.occupancy}")
    print(f"   Has data: {room1.has_data}")
    
    # Load time series data
    print("\n📊 Loading sensor data...")
    room1.time_series_data = create_sample_time_series_data(days=7)
    room1.data_start = room1.time_series_data.index.min()
    room1.data_end = room1.time_series_data.index.max()
    
    print(f"   ✓ Loaded {len(room1.time_series_data)} measurements")
    print(f"   ✓ Time range: {room1.data_start} to {room1.data_end}")
    print(f"   ✓ Available parameters: {room1.available_parameters}")
    
    # Room analyzes itself!
    print("\n🔬 Room computing its own metrics...")
    analysis = room1.compute_metrics(standards=['en16798', 'tail'])
    
    print(f"   ✓ Metrics computed at: {room1.metrics_computed_at}")
    print(f"   ✓ Analysis object created: {analysis is not None}")
    
    # Access cached metrics directly from room
    print("\n📈 Accessing cached metrics:")
    print(f"   Room ID: {room1.id}")
    print(f"   Has EN16798 metadata: {room1.has_metric('en16798_metadata')}")
    print(f"   Has TAIL calculator: {room1.has_metric('tail_calculator')}")
    print(f"   Has analysis: {room1.has_metric('room_analysis')}")
    
    # Get analysis without recomputing
    cached_analysis = room1.get_analysis()
    print(f"   Cached analysis retrieved: {cached_analysis is not None}")
    
    # ============================================================================
    # PART 2: Hierarchical Aggregation with Multiple Rooms
    # ============================================================================
    print("\n" + "=" * 80)
    print("PART 2: HIERARCHICAL AGGREGATION")
    print("=" * 80)
    
    # Create more rooms with data
    room2 = Room(
        id="room-102",
        name="Office 102",
        room_type="office",
        area=30.0,
        volume=90.0,
        occupancy=3
    )
    room2.time_series_data = create_sample_time_series_data(days=7)
    room2.data_start = room2.time_series_data.index.min()
    room2.data_end = room2.time_series_data.index.max()
    
    # Simulate some metrics for demonstration
    room1.set_metric('overall_compliance_rate', 85.5)
    room1.set_metric('tail_overall_rating', 2)
    room1.set_metric('en16798_category', 'II')
    
    room2.set_metric('overall_compliance_rate', 78.3)
    room2.set_metric('tail_overall_rating', 3)
    room2.set_metric('en16798_category', 'III')
    
    print(f"\n📐 Room 1 Metrics:")
    print(f"   Compliance: {room1.get_metric('overall_compliance_rate')}%")
    print(f"   TAIL Rating: {room1.get_metric('tail_overall_rating')}")
    print(f"   EN16798 Category: {room1.get_metric('en16798_category')}")
    
    print(f"\n📐 Room 2 Metrics:")
    print(f"   Compliance: {room2.get_metric('overall_compliance_rate')}%")
    print(f"   TAIL Rating: {room2.get_metric('tail_overall_rating')}")
    print(f"   EN16798 Category: {room2.get_metric('en16798_category')}")
    
    # Create level and add rooms
    level1 = Level(
        id="level-1",
        name="Ground Floor",
        floor_number=0
    )
    level1.add_room(room1.id)
    level1.add_room(room2.id)
    
    # Level computes aggregated physical properties
    rooms_dict = {room1.id: room1, room2.id: room2}
    level1.compute_from_children(lambda id: rooms_dict[id])
    
    print(f"\n🏢 Level 1 - Physical Properties (aggregated from rooms):")
    print(f"   Total Area: {level1.area} m² (from {room1.area} + {room2.area})")
    print(f"   Total Volume: {level1.volume} m³")
    print(f"   Total Occupancy: {level1.occupancy} people")
    
    # Level computes aggregated metrics
    print("\n🔬 Level computing aggregated metrics from rooms...")
    level_metrics = level1.compute_metrics(room_lookup=lambda id: rooms_dict[id])
    
    print(f"\n📊 Level 1 - Aggregated Metrics:")
    print(f"   Rooms Analyzed: {level_metrics.get('rooms_analyzed', 0)}")
    print(f"   Average Compliance: {level_metrics.get('average_compliance_rate', 0):.1f}%")
    print(f"   Min Compliance: {level_metrics.get('min_compliance_rate', 0):.1f}%")
    print(f"   Max Compliance: {level_metrics.get('max_compliance_rate', 0):.1f}%")
    print(f"   Average TAIL Rating: {level_metrics.get('average_tail_rating', 0):.1f}")
    print(f"   EN16798 Distribution: {level_metrics.get('en16798_category_distribution', {})}")
    
    # ============================================================================
    # PART 3: Building-Level Self-Analysis (EPC)
    # ============================================================================
    print("\n" + "=" * 80)
    print("PART 3: BUILDING SELF-ANALYSIS (EPC)")
    print("=" * 80)
    
    # Create building with energy data
    building = Building(
        id="building-1",
        name="Main Office Building",
        building_type=BuildingType.OFFICE,
        year_built=2015,
        address="123 Main St",
        city="Brussels",
        country=Country.BELGIUM,
        region=Region.BE_BRUSSELS,
        # Energy consumption data
        annual_heating_kwh=50000,
        annual_cooling_kwh=25000,
        annual_electricity_kwh=75000,
        annual_hot_water_kwh=10000,
        annual_ventilation_kwh=15000,
        # Renewable energy
        annual_solar_pv_kwh=20000,
        # Water
        annual_water_m3=500
    )
    
    building.add_level(level1.id)
    
    print(f"\n🏛️  Created {building.name}:")
    print(f"   Type: {building.building_type.value}")
    print(f"   Location: {building.city}, {building.country.value if building.country else 'N/A'}")
    print(f"   Region: {building.region.value if building.region else 'N/A'}")
    
    # Building computes area from level
    levels_dict = {level1.id: level1}
    building.compute_from_children(lambda id: levels_dict[id])
    
    print(f"\n📐 Physical Properties (aggregated from level):")
    print(f"   Total Area: {building.area} m²")
    print(f"   Total Volume: {building.volume} m³")
    print(f"   Total Occupancy: {building.occupancy} people")
    
    # Building analyzes itself for EPC!
    print("\n🔬 Building computing EPC and energy metrics...")
    building_metrics = building.compute_metrics(metrics=['epc', 'energy'])
    
    print(f"\n📊 Building Metrics:")
    print(f"   EPC Rating: {building_metrics.get('epc_rating_value', 'N/A')}")
    print(f"   Primary Energy: {building_metrics.get('primary_energy_kwh_m2', 0):.1f} kWh/m²/year")
    print(f"   Total Energy: {building_metrics.get('total_energy_kwh', 0):.0f} kWh/year")
    print(f"   Energy Intensity: {building_metrics.get('energy_intensity', 0):.1f} kWh/m²/year")
    print(f"   Renewable Fraction: {building_metrics.get('renewable_fraction', 0):.1%}")
    
    # Access cached metrics
    print(f"\n💾 Cached in building:")
    print(f"   EPC rating: {building.get_metric('epc_rating')}")
    print(f"   Primary energy: {building.get_metric('primary_energy_kwh_m2')} kWh/m²")
    print(f"   Metrics computed at: {building.metrics_computed_at}")
    
    # ============================================================================
    # PART 4: Benefits Summary
    # ============================================================================
    print("\n" + "=" * 80)
    print("✅ KEY BENEFITS OF SELF-ANALYZING ENTITIES")
    print("=" * 80)
    print("""
    1. 📦 ENCAPSULATION
       - Entities know how to analyze themselves
       - No need for separate analysis services
       - Business logic stays with domain models
    
    2. 🎯 SIMPLICITY
       - room.compute_metrics() - that's it!
       - building.compute_metrics() - auto-computes EPC
       - level.compute_metrics() - aggregates from rooms
    
    3. 💾 CACHING
       - Metrics stored directly in entity
       - Fast access: room.get_metric('epc_rating')
       - Automatic timestamp tracking
    
    4. 🔄 HIERARCHICAL
       - Physical properties aggregate from children
       - Metrics aggregate from children
       - Consistent pattern across all levels
    
    5. 🔌 EXTENSIBLE
       - Add new standards easily
       - Metrics stored in flexible dict
       - Standards: EN16798, TAIL, EPC, custom
    
    6. ⚡ ON-DEMAND
       - Compute only when data available
       - Force recompute when needed
       - Choose which metrics to compute
    """)
    
    print("\n" + "=" * 80)
    print("DEMONSTRATION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
