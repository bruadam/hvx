"""
Demonstration of building type configuration system.

Shows how to:
1. Use default building type configurations
2. Load user-defined configurations
3. Override default settings
4. Add custom building types
"""

from pathlib import Path
from core.domain.enums.building_type import BuildingType
from core.domain.enums.building_type_config import (
    building_type_config_loader,
    BuildingTypeConfig,
)


def demo_default_configs():
    """Demo 1: Using default building type configurations."""
    print("=" * 80)
    print("DEMO 1: Default Building Type Configurations")
    print("=" * 80)
    
    building_types = [
        BuildingType.OFFICE,
        BuildingType.HOTEL,
        BuildingType.SCHOOL,
        BuildingType.HOSPITAL,
        BuildingType.RETAIL,
    ]
    
    print(f"\n{'Building Type':20s} {'Display Name':25s} {'Hours':15s} {'24/7':6s} {'Supported':10s}")
    print("-" * 80)
    
    for bt in building_types:
        start, end = bt.typical_occupancy_hours
        hours_str = f"{start:02d}:00 - {end:02d}:00"
        is_24_7 = "Yes" if bt.is_24_7 else "No"
        supported = "Yes" if bt.is_supported else "No"
        
        print(f"{bt.value:20s} {bt.display_name:25s} {hours_str:15s} {is_24_7:6s} {supported:10s}")
    
    # Show default parameters for office
    print("\n" + "-" * 80)
    print(f"Default parameters for {BuildingType.OFFICE.display_name}:")
    for param in BuildingType.OFFICE.default_parameters:
        print(f"  • {param}")


def demo_supported_types():
    """Demo 2: Getting list of supported building types."""
    print("\n\n" + "=" * 80)
    print("DEMO 2: Supported Building Types")
    print("=" * 80)
    
    supported = BuildingType.supported_types()
    
    print(f"\nCurrently {len(supported)} building types are fully supported:\n")
    for bt in supported:
        config = building_type_config_loader.get_config(bt.value)
        print(f"  ✓ {bt.display_name:20s} - {config.description if config else ''}")


def demo_user_config():
    """Demo 3: Loading user-defined configurations."""
    print("\n\n" + "=" * 80)
    print("DEMO 3: User-Defined Configuration Override")
    print("=" * 80)
    
    # Show current office hours
    office = BuildingType.OFFICE
    start, end = office.typical_occupancy_hours
    print(f"\nBefore user config:")
    print(f"  Office hours: {start:02d}:00 - {end:02d}:00")
    print(f"  Display name: {office.display_name}")
    
    # Load user config
    user_config_path = Path(__file__).parent.parent / "config" / "building_types" / "user_building_types_example.yaml"
    
    if user_config_path.exists():
        print(f"\nLoading user config from: {user_config_path.name}")
        building_type_config_loader.load_user_config(user_config_path)
        
        # Show updated office hours
        start, end = office.typical_occupancy_hours
        print(f"\nAfter user config:")
        print(f"  Office hours: {start:02d}:00 - {end:02d}:00")
        print(f"  Display name: {office.display_name}")
        
        # Show new custom types
        print("\n" + "-" * 80)
        print("New custom building types added:")
        
        all_types = building_type_config_loader.get_all_building_types()
        custom_types = [t for t in all_types if t not in [bt.value for bt in BuildingType]]
        
        for type_id in custom_types:
            config = building_type_config_loader.get_config(type_id)
            if config:
                start, end = config.occupancy_hours_tuple
                print(f"\n  {config.display_name} ('{type_id}')")
                print(f"    Hours: {start:02d}:00 - {end:02d}:00")
                print(f"    Description: {config.description}")
                print(f"    Parameters: {', '.join(config.default_parameters)}")
    else:
        print(f"\nUser config file not found: {user_config_path}")


def demo_config_access():
    """Demo 4: Accessing configuration details."""
    print("\n\n" + "=" * 80)
    print("DEMO 4: Accessing Configuration Details")
    print("=" * 80)
    
    # Direct config loader access
    print("\nDirect Config Loader Access:")
    
    office_config = building_type_config_loader.get_config("office")
    if office_config:
        print(f"\nOffice building configuration:")
        print(f"  Display name: {office_config.display_name}")
        print(f"  Occupancy: {office_config.occupancy_hours_tuple}")
        print(f"  24/7 facility: {office_config.is_24_7}")
        print(f"  Supported: {office_config.supported}")
        print(f"  Default parameters: {office_config.default_parameters}")
        print(f"  Description: {office_config.description}")
    
    # Via BuildingType enum
    print("\n" + "-" * 80)
    print("Via BuildingType Enum Properties:")
    
    hotel = BuildingType.HOTEL
    print(f"\nHotel building ({hotel.value}):")
    print(f"  Display name: {hotel.display_name}")
    print(f"  Occupancy hours: {hotel.typical_occupancy_hours}")
    print(f"  Is 24/7: {hotel.is_24_7}")
    print(f"  Supported: {hotel.is_supported}")
    print(f"  Default parameters: {hotel.default_parameters}")


def demo_programmatic_config():
    """Demo 5: Creating config programmatically."""
    print("\n\n" + "=" * 80)
    print("DEMO 5: Programmatic Configuration")
    print("=" * 80)
    
    # Create custom config programmatically
    custom_config = BuildingTypeConfig(
        display_name="24/7 Call Center",
        typical_occupancy_hours={"start": 0, "end": 24},
        description="Customer service call center with 24/7 operations",
        supported=True,
        default_parameters=["temperature", "co2", "humidity", "noise"],
    )
    
    print("\nCreated custom configuration:")
    print(f"  Display name: {custom_config.display_name}")
    print(f"  Hours: {custom_config.occupancy_hours_tuple}")
    print(f"  24/7: {custom_config.is_24_7}")
    print(f"  Parameters: {custom_config.default_parameters}")
    
    # You could add this to the loader if needed:
    # building_type_config_loader._configs["call_center"] = custom_config


def demo_use_case_examples():
    """Demo 6: Real-world use case examples."""
    print("\n\n" + "=" * 80)
    print("DEMO 6: Real-World Use Case Examples")
    print("=" * 80)
    
    print("\n1. Setting up building analysis with correct occupancy hours:")
    print("-" * 80)
    
    building_type = BuildingType.SCHOOL
    start_hour, end_hour = building_type.typical_occupancy_hours
    
    print(f"Building type: {building_type.display_name}")
    print(f"Analysis will focus on occupied hours: {start_hour:02d}:00 - {end_hour:02d}:00")
    print(f"This is {end_hour - start_hour} hours per day")
    
    print("\n2. Selecting appropriate parameters for building type:")
    print("-" * 80)
    
    params = building_type.default_parameters
    print(f"For {building_type.display_name}, monitoring these parameters:")
    for param in params:
        print(f"  • {param}")
    
    print("\n3. Filtering building types for analysis:")
    print("-" * 80)
    
    supported_types = BuildingType.supported_types()
    print(f"Running batch analysis on {len(supported_types)} supported building types:")
    for bt in supported_types:
        print(f"  • {bt.display_name}")
    
    print("\n4. Identifying 24/7 facilities:")
    print("-" * 80)
    
    all_building_types = [bt for bt in BuildingType]
    facilities_24_7 = [bt for bt in all_building_types if bt.is_24_7]
    
    print(f"Found {len(facilities_24_7)} building types with 24/7 operation:")
    for bt in facilities_24_7:
        print(f"  • {bt.display_name}")


if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "BUILDING TYPE CONFIGURATION DEMONSTRATION" + " " * 17 + "║")
    print("╚" + "=" * 78 + "╝")
    
    # Run all demos
    demo_default_configs()
    demo_supported_types()
    demo_user_config()
    demo_config_access()
    demo_programmatic_config()
    demo_use_case_examples()
    
    print("\n\n" + "=" * 80)
    print("END OF DEMONSTRATION")
    print("=" * 80)
    
    print("\nKey Takeaways:")
    print("  1. Default configs loaded from YAML (config/building_types/)")
    print("  2. Users can override with custom YAML files")
    print("  3. Easy to add new building types without code changes")
    print("  4. BuildingType enum provides clean API access")
    print("  5. Occupancy hours, parameters, and metadata all configurable")
    print("  6. Supports both default and user-defined building types")
    print("\n")
