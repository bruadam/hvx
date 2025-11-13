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
    
    # Create simple compliance tests
    tests = [
        {
            'test_id': 'temp_comfort',
            'parameter': 'temperature',
            'standard': 'en16798-1',
            'threshold': {'lower': 20, 'upper': 26},
            'compliance_level': 95.0
        },
        {
            'test_id': 'co2_quality',
            'parameter': 'co2',
            'standard': 'en16798-1',
            'threshold': {'upper': 800},
            'compliance_level': 95.0
        }
    ]
    
    # Rooms analyze themselves with actual compliance tests!
    print("\n🔬 Room 1 analyzing itself with compliance tests...")
    analysis1 = room1.compute_metrics(tests=tests, apply_filters=True)
    if analysis1:
        print(f"   ✓ Overall compliance: {analysis1.overall_compliance_rate:.1f}%")
        print(f"   ✓ Data quality: {analysis1.quality_score:.1f}%")
        print(f"   ✓ Tests performed: {analysis1.test_count}")
    
    print("\n🔬 Room 2 analyzing itself with compliance tests...")
    analysis2 = room2.compute_metrics(tests=tests, apply_filters=True)
    if analysis2:
        print(f"   ✓ Overall compliance: {analysis2.overall_compliance_rate:.1f}%")
        print(f"   ✓ Data quality: {analysis2.quality_score:.1f}%")
        print(f"   ✓ Tests performed: {analysis2.test_count}")
    
    # ============================================================================
    # PART 3: Building-Level Aggregation
    # ============================================================================
    print("\n" + "=" * 80)
    print("PART 3: BUILDING-LEVEL AGGREGATION")
    print("=" * 80)
    
    # Create building
    building = Building(
        id="building-1",
        name="Main Office Building",
        building_type=BuildingType.OFFICE,
        year_built=2015,
        address="123 Main St",
        city="Brussels"
    )
    
    # Building aggregates room analyses automatically!
    print("\n🏢 Building aggregating room analyses...")
    if analysis1 and analysis2:
        building_analysis = building.aggregate_room_analyses([analysis1, analysis2])
        
        print(f"\n📊 Building Analysis (aggregated from {building_analysis.room_count} rooms):")
        print(f"   Average Compliance: {building_analysis.avg_compliance_rate:.1f}%")
        print(f"   Average Quality: {building_analysis.avg_quality_score:.1f}%")
        
        # Access cached best/worst rooms
        best_rooms = building.get_metric('best_performing_rooms')
        worst_rooms = building.get_metric('worst_performing_rooms')
        if best_rooms:
            print(f"   Best Room: {best_rooms[0]['room_name']} ({best_rooms[0]['compliance_rate']}%)")
        if worst_rooms:
            print(f"   Worst Room: {worst_rooms[0]['room_name']} ({worst_rooms[0]['compliance_rate']}%)")
    
    # ============================================================================
    # PART 4: Building EPC and Energy Metrics
    # ============================================================================
    print("\n" + "=" * 80)
    print("PART 4: BUILDING ENERGY PERFORMANCE")
    print("=" * 80)
    
    # Add energy data to building
    building.annual_heating_kwh = 50000
    building.annual_cooling_kwh = 25000
    building.annual_electricity_kwh = 75000
    building.annual_hot_water_kwh = 10000
    building.annual_ventilation_kwh = 15000
    building.annual_solar_pv_kwh = 20000
    building.country = Country.BELGIUM
    building.region = Region.BE_BRUSSELS
    
    # Compute from children to get total area
    building.area = (room1.area or 0) + (room2.area or 0)
    
    print(f"\n🏛️  Created {building.name}:")
    print(f"   Type: {building.building_type.value}")
    print(f"   Location: {building.city}")
    
    print(f"\n📐 Physical Properties:")
    print(f"   Total Area: {building.area} m²")
    
    # Building analyzes itself for EPC!
    print("\n🔬 Building computing EPC and energy metrics...")
    building_metrics = building.compute_metrics(metrics=['epc', 'energy'])
    
    print(f"\n📊 Building Energy Metrics:")
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
    # PART 5: Benefits Summary
    # ============================================================================
    print("\n" + "=" * 80)
    print("✅ KEY BENEFITS OF SELF-ANALYZING ENTITIES")
    print("=" * 80)
    print("""
    1. 📦 FULL ENCAPSULATION
       - Entities perform complete self-analysis
       - room.compute_metrics(tests=tests) - runs compliance, quality, statistics
       - building.aggregate_room_analyses() - aggregates results
       - No external AnalysisEngine needed!
    
    2. 🎯 RADICAL SIMPLICITY
       - One method does everything: room.compute_metrics(tests=...)
       - Building aggregates: building.aggregate_room_analyses([analyses])
       - Energy metrics: building.compute_metrics(metrics=['epc', 'energy'])
    
    3. 💾 INTELLIGENT CACHING
       - All metrics stored directly in entity.computed_metrics
       - Fast access: room.get_metric('overall_compliance_rate')
       - Automatic timestamp tracking
       - Force recompute when needed
    
    4. 🔄 HIERARCHICAL AGGREGATION
       - Buildings aggregate room analyses automatically
       - Best/worst performing rooms identified
       - Test results aggregated across all spaces
       - Complete building-level insights
    
    5. 🔌 MAXIMUM EXTENSIBILITY
       - Pass any tests configuration
       - Add new standards easily
       - Custom metrics stored in flexible dict
       - Works with any compliance framework
    
    6. ⚡ ON-DEMAND + BACKWARD COMPATIBLE
       - Direct: room.compute_metrics() for new code
       - Compatible: AnalysisEngine still works (delegates to entities)
       - Choose your approach - both work!
       - Gradual migration path
    
    7. 🏗️ CLEAN ARCHITECTURE
       - Domain entities own their analysis logic
       - Use cases are thin wrappers
       - Engines deprecated but available
       - True domain-driven design
    """)
    
    print("\n" + "=" * 80)
    print("DEMONSTRATION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
