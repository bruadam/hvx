"""
Demonstration of hierarchical aggregation pattern.

Shows how physical properties (area, volume, occupancy, etc.) are:
- Stored at the Room level (leaf nodes)
- Computed/aggregated at Level and Building levels (parent nodes)

This avoids data duplication and ensures consistency.
"""

from core.domain.enums.building_type import BuildingType
from core.domain.models.entities import Building, Level, Room


def main() -> None:
    """Demonstrate hierarchical property aggregation."""
    
    # Create rooms with physical properties
    room1 = Room(
        id="room-101",
        name="Office 101",
        area=25.0,
        volume=75.0,
        occupancy=2,
        orientations=[90.0],  # East-facing
        window_areas=[4.0],
        shading_factors=[0.3],
        last_renovation_year=2020
    )
    
    room2 = Room(
        id="room-102",
        name="Office 102",
        area=30.0,
        volume=90.0,
        occupancy=3,
        orientations=[180.0],  # South-facing
        window_areas=[5.0],
        shading_factors=[0.2],
        last_renovation_year=2022
    )
    
    room3 = Room(
        id="room-201",
        name="Conference Room",
        area=50.0,
        volume=150.0,
        occupancy=10,
        orientations=[90.0, 180.0],  # Corner room, East and South
        window_areas=[6.0, 6.0],
        shading_factors=[0.3, 0.2],
        last_renovation_year=2021
    )
    
    print("=" * 80)
    print("HIERARCHICAL AGGREGATION DEMONSTRATION")
    print("=" * 80)
    
    # Show individual room properties
    print("\n📐 Individual Room Properties:")
    print(f"\n  {room1.name}:")
    print(f"    Area: {room1.area} m²")
    print(f"    Volume: {room1.volume} m³")
    print(f"    Occupancy: {room1.occupancy}")
    print(f"    Orientations: {room1.orientations}°")
    print(f"    Window areas: {room1.window_areas} m²")
    
    print(f"\n  {room2.name}:")
    print(f"    Area: {room2.area} m²")
    print(f"    Volume: {room2.volume} m³")
    print(f"    Occupancy: {room2.occupancy}")
    
    print(f"\n  {room3.name}:")
    print(f"    Area: {room3.area} m²")
    print(f"    Volume: {room3.volume} m³")
    print(f"    Occupancy: {room3.occupancy}")
    
    # Create levels and add rooms
    level1 = Level(
        id="level-1",
        name="Ground Floor",
        floor_number=0
    )
    level1.add_room(room1.id)
    level1.add_room(room2.id)
    
    level2 = Level(
        id="level-2",
        name="First Floor",
        floor_number=1
    )
    level2.add_room(room3.id)
    
    # Create a simple room lookup function
    rooms_by_id = {
        room1.id: room1,
        room2.id: room2,
        room3.id: room3
    }
    
    def get_room(room_id: str) -> Room | None:
        return rooms_by_id.get(room_id)
    
    # Compute aggregated properties for Level 1
    print("\n" + "=" * 80)
    print("🏢 LEVEL 1 - BEFORE AGGREGATION")
    print("=" * 80)
    print(f"  Area: {level1.area}")
    print(f"  Volume: {level1.volume}")
    print(f"  Occupancy: {level1.occupancy}")
    print(f"  Orientations: {level1.orientations}")
    
    level1.compute_from_children(get_room)
    
    print("\n🏢 LEVEL 1 - AFTER AGGREGATION (from rooms 101, 102)")
    print("=" * 80)
    print(f"  Area: {level1.area} m² (should be 25 + 30 = 55)")
    print(f"  Volume: {level1.volume} m³ (should be 75 + 90 = 165)")
    print(f"  Occupancy: {level1.occupancy} people (should be 2 + 3 = 5)")
    print(f"  Orientations: {level1.orientations}° (combined from both rooms)")
    print(f"  Window areas: {level1.window_areas} m²")
    print(f"  Last renovation: {level1.last_renovation_year} (most recent)")
    
    # Compute aggregated properties for Level 2
    level2.compute_from_children(get_room)
    
    print("\n🏢 LEVEL 2 - AFTER AGGREGATION (from room 201)")
    print("=" * 80)
    print(f"  Area: {level2.area} m²")
    print(f"  Volume: {level2.volume} m³")
    print(f"  Occupancy: {level2.occupancy} people")
    print(f"  Orientations: {level2.orientations}°")
    
    # Create building and aggregate from levels
    building = Building(
        id="building-1",
        name="Main Office Building",
        building_type=BuildingType.OFFICE
    )
    building.add_level(level1.id)
    building.add_level(level2.id)
    
    # Create level lookup
    levels_by_id = {
        level1.id: level1,
        level2.id: level2
    }
    
    def get_level(level_id: str) -> Level | None:
        return levels_by_id.get(level_id)
    
    print("\n" + "=" * 80)
    print("🏛️  BUILDING - BEFORE AGGREGATION")
    print("=" * 80)
    print(f"  Area: {building.area}")
    print(f"  Volume: {building.volume}")
    print(f"  Occupancy: {building.occupancy}")
    
    building.compute_from_children(get_level)
    
    print("\n🏛️  BUILDING - AFTER AGGREGATION (from both levels)")
    print("=" * 80)
    print(f"  Total Area: {building.area} m² (should be 55 + 50 = 105)")
    print(f"  Total Volume: {building.volume} m³ (should be 165 + 150 = 315)")
    print(f"  Total Occupancy: {building.occupancy} people (should be 5 + 10 = 15)")
    print(f"  All Orientations: {building.orientations}° (combined from all rooms)")
    print(f"  All Window Areas: {building.window_areas} m²")
    print(f"  Most Recent Renovation: {building.last_renovation_year}")
    print(f"  Estimated Glass-to-Wall Ratio: {building.glass_to_wall_ratio:.2f}" if building.glass_to_wall_ratio else "  Glass-to-Wall Ratio: Not computed")
    
    # Alternative: Use getter methods for on-demand calculation
    print("\n" + "=" * 80)
    print("📊 ON-DEMAND CALCULATIONS (without storing)")
    print("=" * 80)
    print(f"  Building area (calculated): {building.get_aggregated_area(get_level)} m²")
    print(f"  Building volume (calculated): {building.get_aggregated_volume(get_level)} m³")
    print(f"  Building occupancy (calculated): {building.get_aggregated_occupancy(get_level)} people")
    
    print("\n" + "=" * 80)
    print("✅ KEY BENEFITS:")
    print("=" * 80)
    print("  1. Data stored ONLY at leaf level (Rooms)")
    print("  2. Parent nodes (Levels, Buildings) compute on-demand or cache")
    print("  3. No data duplication or inconsistency")
    print("  4. Easy to update: change room properties and re-aggregate")
    print("  5. Flexible: can store OR compute based on needs")
    print("=" * 80)


if __name__ == "__main__":
    main()
