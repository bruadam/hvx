"""
Demo: EN 16798-1 Standard Implementation

This script demonstrates the comprehensive EN 16798-1 implementation including:
- Room categorization (Category I, II, III, IV)
- Ventilation rate calculations based on occupancy and pollution
- Temperature, CO2, and humidity thresholds for each category
- Category achievement based on measured data
- Separate from TAIL, BR18, Danish Guidelines, and user-defined standards
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.analytics.calculators.en16798_calculator import (
    EN16798StandardCalculator,
    EN16798RoomMetadata,
)
from core.domain.enums.en16798_category import EN16798Category
from core.domain.enums.pollution_level import PollutionLevel
from core.domain.enums.occupancy import ActivityLevel, OccupancyDensity
from core.domain.enums.ventilation import VentilationType


def print_section(title: str):
    """Print formatted section header."""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)


def print_subsection(title: str):
    """Print formatted subsection header."""
    print(f"\n{title}")
    print("-" * 80)


def demo_category_overview():
    """Demonstrate EN 16798-1 category system."""
    print_section("EN 16798-1 Category System Overview")
    
    for category in EN16798Category:
        print(f"\n{category.display_name}")
        print(f"  Value: {category.value}")
        print(f"  Performance Level: {category.performance_level}/4")
        print(f"  Compliance Target: {category.compliance_percentage}%")
        print(f"  Description: {category.description}")


def demo_room_type_recommendations():
    """Show recommended categories for different building types."""
    print_section("Recommended Categories by Building Type")
    
    building_types = [
        "school", "kindergarten", "hospital", "nursing_home",
        "office", "hotel", "residential", "retail", "warehouse"
    ]
    
    for building_type in building_types:
        recommended = EN16798Category.get_recommended_for_building_type(building_type)
        print(f"{building_type.ljust(20)}: {recommended.display_name}")


def demo_office_room():
    """Demonstrate calculations for a typical office room."""
    print_section("Example 1: Office Room (Category II Target)")
    
    # Define office room metadata
    office = EN16798RoomMetadata(
        room_type="office",
        floor_area=20.0,  # m²
        volume=60.0,  # m³ (3m ceiling height)
        occupancy_count=2,
        ventilation_type=VentilationType.MECHANICAL,
        pollution_level=PollutionLevel.LOW,
        activity_level=ActivityLevel.LIGHT_ACTIVITY,
        target_category=EN16798Category.CATEGORY_II,
    )
    
    print(f"\nRoom Metadata:")
    print(f"  Type: {office.room_type}")
    print(f"  Floor Area: {office.floor_area} m²")
    print(f"  Volume: {office.volume} m³")
    print(f"  Occupancy: {office.occupancy_count} persons")
    print(f"  Ventilation: {office.ventilation_type.display_name}")
    print(f"  Pollution Level: {office.pollution_level.display_name}")
    if office.activity_level:
        print(f"  Activity Level: {office.activity_level.display_name}")
    
    # Get thresholds for all categories
    print_subsection("Thresholds for All Categories")
    
    all_thresholds = EN16798StandardCalculator.get_all_thresholds_for_room(office)
    
    for category, data in all_thresholds.items():
        print(f"\n{data['category_name']}:")
        print(f"  Temperature (Heating): {data['temperature_heating']['lower']}-{data['temperature_heating']['upper']}°C")
        print(f"  Temperature (Cooling): {data['temperature_cooling']['lower']}-{data['temperature_cooling']['upper']}°C")
        print(f"  CO2 Max: {data['co2_threshold_ppm']} ppm")
        print(f"  Humidity: {data['humidity_thresholds']['lower']}-{data['humidity_thresholds']['upper']}%")
        vent = data['ventilation']
        print(f"  Ventilation Required: {vent['total_ventilation_l_s']} L/s ({vent['air_change_rate_ach']} ACH)")
        print(f"    - Per person: {vent['occupant_contribution_l_s']} L/s ({vent['ventilation_per_person_l_s']} L/(s·person))")
        print(f"    - Building: {vent['building_contribution_l_s']} L/s ({vent['ventilation_per_area_l_s_m2']} L/(s·m²))")
    
    # Determine achieved category from measurements
    print_subsection("Category Achievement from Measured Data")
    
    # Scenario 1: Good conditions
    measured_good = {
        "temperature": 22.0,  # °C
        "co2": 800,  # ppm
        "humidity": 45,  # %
    }
    
    print("\nScenario 1: Good Conditions")
    print(f"  Temperature: {measured_good['temperature']}°C")
    print(f"  CO2: {measured_good['co2']} ppm")
    print(f"  Humidity: {measured_good['humidity']}%")
    
    result_good = EN16798StandardCalculator.determine_achieved_category(
        office, measured_good, season="heating"
    )
    
    print(f"\n  ✓ Achieved: {result_good['achieved_category_name']}")
    print(f"  All compliant categories: {', '.join(result_good['all_compliant_categories'])}")
    
    # Scenario 2: Marginal conditions
    measured_marginal = {
        "temperature": 24.5,  # °C (edge of Cat II)
        "co2": 1100,  # ppm
        "humidity": 58,  # %
    }
    
    print("\nScenario 2: Marginal Conditions")
    print(f"  Temperature: {measured_marginal['temperature']}°C")
    print(f"  CO2: {measured_marginal['co2']} ppm")
    print(f"  Humidity: {measured_marginal['humidity']}%")
    
    result_marginal = EN16798StandardCalculator.determine_achieved_category(
        office, measured_marginal, season="heating"
    )
    
    print(f"\n  ✓ Achieved: {result_marginal['achieved_category_name']}")
    print(f"  All compliant categories: {', '.join(result_marginal['all_compliant_categories'])}")


def demo_classroom():
    """Demonstrate calculations for a classroom."""
    print_section("Example 2: Classroom (Category I Target)")
    
    classroom = EN16798RoomMetadata(
        room_type="classroom",
        floor_area=60.0,  # m²
        volume=180.0,  # m³
        occupancy_count=25,  # 1 teacher + 24 students
        ventilation_type=VentilationType.MECHANICAL,
        pollution_level=PollutionLevel.LOW,
        target_category=EN16798Category.CATEGORY_I,
    )
    
    print(f"\nRoom Metadata:")
    print(f"  Type: {classroom.room_type}")
    print(f"  Floor Area: {classroom.floor_area} m²")
    print(f"  Occupancy: {classroom.occupancy_count} persons")
    if classroom.occupancy_count and classroom.floor_area:
        print(f"  Occupancy Density: {classroom.occupancy_count / classroom.floor_area:.2f} persons/m²")
    print(f"  Target: {classroom.target_category.display_name}")
    
    # Category I requirements
    print_subsection("Category I Requirements (High Expectation)")
    
    cat_i_reqs = EN16798StandardCalculator.get_all_thresholds_for_room(
        classroom, categories=[EN16798Category.CATEGORY_I]
    )[EN16798Category.CATEGORY_I]
    
    print(f"\nTemperature (Heating): {cat_i_reqs['temperature_heating']['lower']}-{cat_i_reqs['temperature_heating']['upper']}°C")
    print(f"CO2 Max: {cat_i_reqs['co2_threshold_ppm']} ppm")
    print(f"Humidity: {cat_i_reqs['humidity_thresholds']['lower']}-{cat_i_reqs['humidity_thresholds']['upper']}%")
    
    vent = cat_i_reqs['ventilation']
    print(f"\nVentilation Requirements:")
    print(f"  Total: {vent['total_ventilation_l_s']} L/s")
    print(f"  Per person: {vent['ventilation_per_person_l_s']} L/(s·person)")
    print(f"  Air change rate: {vent['air_change_rate_ach']} ACH")
    print(f"  Breakdown:")
    print(f"    - Occupants ({classroom.occupancy_count} persons): {vent['occupant_contribution_l_s']} L/s")
    print(f"    - Building ({classroom.floor_area} m²): {vent['building_contribution_l_s']} L/s")


def demo_hotel_room():
    """Demonstrate calculations for a hotel room."""
    print_section("Example 3: Hotel Room (Category II Target)")
    
    hotel_room = EN16798RoomMetadata(
        room_type="hotel_room",
        floor_area=25.0,  # m²
        volume=75.0,  # m³
        occupancy_count=2,
        ventilation_type=VentilationType.MIXED_MODE,
        pollution_level=PollutionLevel.NON_LOW,  # Existing building
        target_category=EN16798Category.CATEGORY_II,
    )
    
    print(f"\nRoom Metadata:")
    print(f"  Type: {hotel_room.room_type}")
    print(f"  Floor Area: {hotel_room.floor_area} m²")
    print(f"  Ventilation: {hotel_room.ventilation_type.display_name}")
    print(f"  Pollution: {hotel_room.pollution_level.display_name}")
    
    # Compare ventilation for different pollution levels
    print_subsection("Impact of Pollution Level on Ventilation Requirements")
    
    for pollution in [PollutionLevel.VERY_LOW, PollutionLevel.LOW, PollutionLevel.NON_LOW]:
        hotel_room.pollution_level = pollution
        vent = EN16798StandardCalculator.calculate_required_ventilation_rate(
            hotel_room, EN16798Category.CATEGORY_II
        )
        
        print(f"\n{pollution.display_name}:")
        print(f"  Building factor: {pollution.building_emission_factor} L/(s·m²)")
        print(f"  Total ventilation: {vent['total_ventilation_l_s']} L/s")
        print(f"  Air changes: {vent['air_change_rate_ach']} ACH")


def demo_comparison_across_room_types():
    """Compare ventilation requirements across different room types."""
    print_section("Comparison: Ventilation Requirements by Room Type")
    
    room_configs = [
        ("Office", "office", 20, 2),
        ("Classroom", "classroom", 60, 25),
        ("Meeting Room", "meeting_room", 30, 10),
        ("Hotel Room", "hotel_room", 25, 2),
        ("Laboratory", "laboratory", 40, 4),
    ]
    
    print("\n{:<20} {:<10} {:<12} {:<15} {:<12}".format(
        "Room Type", "Area (m²)", "Occupants", "Vent. (L/s)", "ACH"
    ))
    print("-" * 80)
    
    for name, room_type, area, occupancy in room_configs:
        room = EN16798RoomMetadata(
            room_type=room_type,
            floor_area=area,
            volume=area * 3.0,  # Assume 3m ceiling
            occupancy_count=occupancy,
            ventilation_type=VentilationType.MECHANICAL,
            pollution_level=PollutionLevel.LOW,
        )
        
        vent = EN16798StandardCalculator.calculate_required_ventilation_rate(
            room, EN16798Category.CATEGORY_II
        )
        
        print("{:<20} {:<10} {:<12} {:<15} {:<12}".format(
            name,
            f"{area}",
            f"{occupancy}",
            f"{vent['total_ventilation_l_s']}",
            f"{vent['air_change_rate_ach']}"
        ))


def demo_category_hierarchy():
    """Demonstrate category hierarchy and automatic achievement."""
    print_section("Category Hierarchy and Automatic Achievement")
    
    print("\nEN 16798-1 Category Hierarchy (Best to Worst):")
    print("  Category I   (Performance Level 4) → Highest expectation")
    print("  Category II  (Performance Level 3) → Normal expectation")
    print("  Category III (Performance Level 2) → Moderate expectation")
    print("  Category IV  (Performance Level 1) → Outside standard")
    
    print("\nAutomatic Achievement Logic:")
    print("  If Category I is achieved  → All categories (I, II, III, IV) are achieved")
    print("  If Category II is achieved → Categories II, III, IV are achieved")
    print("  If Category III is achieved → Categories III, IV are achieved")
    print("  If Category IV is achieved → Only Category IV is achieved")
    
    print("\nCategory Achievement Requires:")
    print("  ALL tests in that category must have ≥95% compliance")
    print("  Tests include: temperature_heating, temperature_cooling, co2, humidity")


def main():
    """Run all demonstrations."""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "EN 16798-1 COMPREHENSIVE IMPLEMENTATION DEMO".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("║" + "Independent Standard for Indoor Environmental Quality".center(78) + "║")
    print("║" + "Separate from TAIL, BR18, Danish Guidelines, User-Defined".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "═" * 78 + "╝")
    
    try:
        demo_category_overview()
        demo_room_type_recommendations()
        demo_office_room()
        demo_classroom()
        demo_hotel_room()
        demo_comparison_across_room_types()
        demo_category_hierarchy()
        
        print_section("Summary")
        print("""
The EN 16798-1 implementation provides:

✓ Four categories (I, II, III, IV) with clear performance hierarchy
✓ Category-specific thresholds for temperature, CO2, and humidity
✓ Ventilation calculations based on:
  - Occupancy count and activity level
  - Floor area and pollution level
  - Ventilation system type
✓ Automatic category achievement based on measured data
✓ Independent from other standards (TAIL, BR18, Danish, User-Defined)
✓ Suitable for various building types and room types
✓ Complies with EN 16798-1:2019 specifications

Next Steps:
- Integrate with building analysis workflows
- Configure room metadata (occupancy, ventilation type, pollution level)
- Run compliance tests against all 4 categories
- Generate category-specific recommendations
- Use for building certification and optimization
        """)
        
        print("\n✓ Demo completed successfully!\n")
        
    except Exception as e:
        print(f"\n✗ Error during demo: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
