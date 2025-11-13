#!/usr/bin/env python3
"""
Test script for core domain models using dummy_data samples.

This script tests:
1. Room model instantiation and data loading
2. Level model with multiple rooms
3. Building model with hierarchy
4. Dataset model with multiple buildings
5. Data validation and properties
"""

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.domain.models.entities.room import Room
from core.domain.models.entities.level import Level
from core.domain.models.entities.building import Building
from core.domain.models.datasets.dataset import Dataset


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_subsection(title: str) -> None:
    """Print a formatted subsection header."""
    print(f"\n--- {title} ---")


def test_room_model() -> bool:
    """Test Room model with dummy data."""
    print_section("TEST 1: Room Model")
    
    try:
        # Path to sample room data
        room_data_path = project_root / "data" / "samples" / "dummy_data" / "building_a" / "level_1" / "office_1.csv"
        
        if not room_data_path.exists():
            print(f"❌ Room data file not found: {room_data_path}")
            return False
        
        print(f"✓ Found room data file: {room_data_path.name}")
        
        # Load CSV data
        df = pd.read_csv(room_data_path, parse_dates=['timestamp'])
        print(f"✓ Loaded {len(df)} rows of data")
        
        # Create Room instance
        room = Room(
            id="office_1",
            name="Office 1",
            level_id="level_1",
            building_id="building_a",
            area=25.0,
            volume=75.0,
            occupancy=2,
            room_type="office",
            data_file_path=room_data_path,
            time_series_data=df,
            data_start=df['timestamp'].min(),
            data_end=df['timestamp'].max()
        )
        
        print(f"✓ Created room: {room.name}")
        print(f"  - ID: {room.id}")
        print(f"  - Area: {room.area} m²")
        print(f"  - Volume: {room.volume} m³")
        print(f"  - Occupancy: {room.occupancy}")
        
        # Test properties
        print_subsection("Testing Room Properties")
        print(f"  - Has data: {room.has_data}")
        print(f"  - Available parameters: {room.available_parameters}")
        print(f"  - Data time range: {room.data_time_range}")
        
        # Test data access
        print_subsection("Testing Data Access")
        if room.has_data and room.time_series_data is not None:
            print(f"  - Data shape: {room.time_series_data.shape}")
            print(f"  - Columns: {list(room.time_series_data.columns)}")
            print(f"  - First timestamp: {room.data_start}")
            print(f"  - Last timestamp: {room.data_end}")
            
            # Show sample data
            print("\n  Sample data (first 5 rows):")
            print(room.time_series_data.head().to_string(index=False))
        
        print("\n✅ Room model test PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Room model test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_level_model() -> bool:
    """Test Level model with multiple rooms."""
    print_section("TEST 2: Level Model")
    
    try:
        # Path to level data
        level_path = project_root / "data" / "samples" / "dummy_data" / "building_a" / "level_1"
        
        if not level_path.exists():
            print(f"❌ Level directory not found: {level_path}")
            return False
        
        print(f"✓ Found level directory: {level_path.name}")
        
        # Create Level instance
        level = Level(
            id="level_1",
            name="Level 1",
            building_id="building_a",
            floor_number=1
        )
        
        print(f"✓ Created level: {level.name}")
        
        # Load all room data files in the level
        room_files = sorted(level_path.glob("*.csv"))
        print(f"✓ Found {len(room_files)} room data files")
        
        rooms = {}
        for room_file in room_files:
            room_id = room_file.stem
            room_name = room_id.replace("_", " ").title()
            
            # Load data
            df = pd.read_csv(room_file, parse_dates=['timestamp'])
            
            # Create room
            room = Room(
                id=room_id,
                name=room_name,
                level_id=level.id,
                building_id=level.building_id,
                data_file_path=room_file,
                time_series_data=df,
                data_start=df['timestamp'].min(),
                data_end=df['timestamp'].max()
            )
            
            # Add room ID to level
            level.add_room(room.id)
            rooms[room.id] = room
            print(f"  ✓ Added room: {room_name} ({len(df)} records)")
        
        print_subsection("Testing Level Properties")
        print(f"  - Level ID: {level.id}")
        print(f"  - Level name: {level.name}")
        print(f"  - Floor number: {level.floor_number}")
        print(f"  - Room count: {level.room_count}")
        print(f"  - Room IDs: {level.room_ids}")
        
        # Test room retrieval
        print_subsection("Testing Room Retrieval")
        if level.room_count > 0:
            first_room_id = level.room_ids[0]
            # Room is in our dictionary
            retrieved_room = rooms.get(first_room_id)
            if retrieved_room:
                print(f"  ✓ Retrieved room '{retrieved_room.name}' by ID")
            else:
                print(f"  ❌ Failed to retrieve room by ID")
                return False
        
        print("\n✅ Level model test PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Level model test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_building_model() -> bool:
    """Test Building model with hierarchy."""
    print_section("TEST 3: Building Model")
    
    try:
        # Path to building data
        building_path = project_root / "data" / "samples" / "dummy_data" / "building_a"
        
        if not building_path.exists():
            print(f"❌ Building directory not found: {building_path}")
            return False
        
        # Load building metadata
        metadata_path = building_path / "metadata.json"
        if metadata_path.exists():
            import json
            with open(metadata_path) as f:
                metadata = json.load(f)
            print(f"✓ Loaded building metadata: {metadata.get('name')}")
        else:
            metadata = {}
            print("⚠ No metadata.json found, using defaults")
        
        # Create Building instance
        building = Building(
            id="building_a",
            name=metadata.get("name", "Building A"),
            building_type=metadata.get("type", "office"),
            address=metadata.get("address"),
            city=metadata.get("city"),
            country=metadata.get("country")
        )
        
        print(f"✓ Created building: {building.name}")
        print(f"  - Type: {building.building_type}")
        print(f"  - Location: {building.city}, {building.country}")
        
        # Load levels
        level_dirs = sorted([d for d in building_path.iterdir() if d.is_dir() and d.name.startswith("level_")])
        print(f"✓ Found {len(level_dirs)} level directories")
        
        levels = {}
        rooms = {}
        
        for level_dir in level_dirs:
            level_id = level_dir.name
            level_name = level_id.replace("_", " ").title()
            floor_number = int(level_id.split("_")[1])
            
            # Create level
            level = Level(
                id=level_id,
                name=level_name,
                building_id=building.id,
                floor_number=floor_number
            )
            
            # Load rooms in this level
            room_files = sorted(level_dir.glob("*.csv"))
            for room_file in room_files:
                room_id = f"{level_id}_{room_file.stem}"
                room_name = room_file.stem.replace("_", " ").title()
                
                # Load data
                df = pd.read_csv(room_file, parse_dates=['timestamp'])
                
                # Create room
                room = Room(
                    id=room_id,
                    name=room_name,
                    level_id=level.id,
                    building_id=building.id,
                    data_file_path=room_file,
                    time_series_data=df,
                    data_start=df['timestamp'].min(),
                    data_end=df['timestamp'].max()
                )
                
                # Add room ID to level
                level.add_room(room.id)
                rooms[room.id] = room
            
            # Add level ID to building
            building.add_level(level.id)
            levels[level.id] = level
            print(f"  ✓ Added {level_name} with {level.room_count} rooms")
        
        print_subsection("Testing Building Properties")
        print(f"  - Building ID: {building.id}")
        print(f"  - Building name: {building.name}")
        print(f"  - Level count: {building.level_count}")
        print(f"  - Direct room count: {building.room_count}")
        print(f"  - Total rooms (all levels): {building.total_rooms}")
        print(f"  - Level IDs: {building.level_ids}")
        
        # Calculate total rooms in all levels
        total_level_rooms = sum(levels[lid].room_count for lid in building.level_ids)
        print(f"  - Rooms in levels: {total_level_rooms}")
        
        # Test hierarchy navigation
        print_subsection("Testing Hierarchy Navigation")
        if building.level_count > 0:
            first_level_id = building.level_ids[0]
            first_level = levels.get(first_level_id)
            if first_level:
                print(f"  ✓ Retrieved level '{first_level.name}' from building")
                if first_level.room_count > 0:
                    first_room_id = first_level.room_ids[0]
                    first_room = rooms.get(first_room_id)
                    if first_room:
                        print(f"  ✓ Retrieved room '{first_room.name}' from level")
                    else:
                        print("  ❌ Failed to retrieve room from level")
                        return False
            else:
                print("  ❌ Failed to retrieve level from building")
                return False
        
        print("\n✅ Building model test PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Building model test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_dataset_model() -> bool:
    """Test Dataset model with multiple buildings."""
    print_section("TEST 4: Dataset Model")
    
    try:
        # Path to dummy data
        data_path = project_root / "data" / "samples" / "dummy_data"
        
        if not data_path.exists():
            print(f"❌ Data directory not found: {data_path}")
            return False
        
        # Create Dataset instance
        dataset = Dataset(
            id="dummy_dataset",
            name="Dummy Dataset",
            description="Test dataset with sample buildings",
            source_directory=data_path,
            version="1.0"
        )
        
        print(f"✓ Created dataset: {dataset.name}")
        print(f"  - Source: {dataset.source_directory}")
        
        # Find all building directories
        building_dirs = sorted([d for d in data_path.iterdir() if d.is_dir() and d.name.startswith("building_")])
        print(f"✓ Found {len(building_dirs)} building directories")
        
        # Add buildings to dataset
        for building_dir in building_dirs:
            building_id = building_dir.name
            dataset.add_building(building_id)
            print(f"  ✓ Added building: {building_id}")
        
        print_subsection("Testing Dataset Properties")
        print(f"  - Dataset ID: {dataset.id}")
        print(f"  - Dataset name: {dataset.name}")
        print(f"  - Building count: {dataset.building_count}")
        print(f"  - Is empty: {dataset.is_empty}")
        print(f"  - Building IDs: {dataset.building_ids}")
        
        # Test building operations
        print_subsection("Testing Building Operations")
        if dataset.building_count > 0:
            first_building_id = dataset.building_ids[0]
            has_building = dataset.has_building(first_building_id)
            print(f"  ✓ Has building '{first_building_id}': {has_building}")
            
            # Test remove/add
            removed = dataset.remove_building(first_building_id)
            print(f"  ✓ Removed building: {removed}")
            print(f"    New building count: {dataset.building_count}")
            
            dataset.add_building(first_building_id)
            print(f"  ✓ Re-added building")
            print(f"    Building count restored: {dataset.building_count}")
        
        # Test summary
        print_subsection("Dataset Summary")
        summary = dataset.get_summary()
        for key, value in summary.items():
            if key != "building_ids":  # Skip the list for brevity
                print(f"  - {key}: {value}")
        
        print("\n✅ Dataset model test PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Dataset model test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_complete_hierarchy() -> bool:
    """Test complete hierarchy: Dataset -> Buildings -> Levels -> Rooms."""
    print_section("TEST 5: Complete Hierarchy")
    
    try:
        data_path = project_root / "data" / "samples" / "dummy_data"
        
        # Create dataset
        dataset = Dataset(
            id="complete_test",
            name="Complete Hierarchy Test",
            source_directory=data_path
        )
        
        buildings = []
        levels_dict = {}
        rooms_dict = {}
        total_levels = 0
        total_rooms = 0
        
        # Load all buildings
        building_dirs = sorted([d for d in data_path.iterdir() if d.is_dir() and d.name.startswith("building_")])
        
        for building_dir in building_dirs:
            building_id = building_dir.name
            
            # Load metadata
            metadata_path = building_dir / "metadata.json"
            if metadata_path.exists():
                import json
                with open(metadata_path) as f:
                    metadata = json.load(f)
            else:
                metadata = {}
            
            # Create building
            building = Building(
                id=building_id,
                name=metadata.get("name", building_id),
                building_type=metadata.get("type", "office")
            )
            
            # Load levels
            level_dirs = sorted([d for d in building_dir.iterdir() if d.is_dir() and d.name.startswith("level_")])
            
            for level_dir in level_dirs:
                level_id = level_dir.name
                floor_number = int(level_id.split("_")[1])
                
                # Create level
                level = Level(
                    id=level_id,
                    name=level_id.replace("_", " ").title(),
                    building_id=building.id,
                    floor_number=floor_number
                )
                
                # Load rooms
                room_files = sorted(level_dir.glob("*.csv"))
                for room_file in room_files:
                    room_id = f"{building_id}_{level_id}_{room_file.stem}"
                    
                    # Load data
                    df = pd.read_csv(room_file, parse_dates=['timestamp'])
                    
                    # Create room
                    room = Room(
                        id=room_id,
                        name=room_file.stem.replace("_", " ").title(),
                        level_id=level.id,
                        building_id=building.id,
                        data_file_path=room_file,
                        time_series_data=df,
                        data_start=df['timestamp'].min(),
                        data_end=df['timestamp'].max()
                    )
                    
                    level.add_room(room.id)
                    rooms_dict[room.id] = room
                    total_rooms += 1
                
                building.add_level(level.id)
                levels_dict[level.id] = level
                total_levels += 1
            
            dataset.add_building(building.id)
            buildings.append(building)
        
        print(f"✓ Loaded complete hierarchy:")
        print(f"  - Dataset: {dataset.name}")
        print(f"  - Buildings: {len(buildings)}")
        print(f"  - Total levels: {total_levels}")
        print(f"  - Total rooms: {total_rooms}")
        
        # Print detailed hierarchy
        print_subsection("Hierarchy Details")
        for building in buildings:
            print(f"\n  Building: {building.name} ({building.id})")
            print(f"    - Levels: {building.level_count}")
            print(f"    - Rooms: {building.total_rooms}")
            
            for level_id in building.level_ids:
                level = levels_dict.get(level_id)
                if level:
                    print(f"      Level: {level.name} ({level.room_count} rooms)")
                    room_ids_to_show = level.room_ids[:3]  # Show first 3 rooms
                    for room_id in room_ids_to_show:
                        room = rooms_dict.get(room_id)
                        if room:
                            data_count = len(room.time_series_data) if room.has_data and room.time_series_data is not None else 0
                            print(f"        - {room.name} ({data_count} records)")
                    if level.room_count > 3:
                        print(f"        ... and {level.room_count - 3} more rooms")
        
        print("\n✅ Complete hierarchy test PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Complete hierarchy test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("  CORE MODELS TEST SUITE - Using Dummy Data")
    print("=" * 80)
    print(f"\nProject root: {project_root}")
    print(f"Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run tests
    results = {
        "Room Model": test_room_model(),
        "Level Model": test_level_model(),
        "Building Model": test_building_model(),
        "Dataset Model": test_dataset_model(),
        "Complete Hierarchy": test_complete_hierarchy()
    }
    
    # Print summary
    print_section("TEST SUMMARY")
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {status}: {test_name}")
    
    print(f"\n  Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n  🎉 All tests PASSED!")
        return 0
    else:
        print(f"\n  ⚠️  {total - passed} test(s) FAILED")
        return 1


if __name__ == "__main__":
    exit(main())
