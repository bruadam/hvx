#!/usr/bin/env python3
"""
Test script for EN16798-1 and TAIL calculation directly from room data.

This script demonstrates:
1. Loading room data from dummy_data
2. Calculating EN16798-1 compliance from time series data
3. Calculating TAIL ratings from time series data
4. Aggregating ratings across multiple rooms
"""

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.domain.models.entities.room import Room
from core.domain.models.base.base_analysis import MetricsAnalysis


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_subsection(title: str) -> None:
    """Print a formatted subsection header."""
    print(f"\n--- {title} ---")


def test_en16798_calculation() -> bool:
    """Test EN16798-1 calculation from room data."""
    print_section("TEST 1: EN16798-1 Calculation from Room Data")
    
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
        print(f"  Columns: {list(df.columns)}")
        print(f"  Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        
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
        
        # Create a MetricsAnalysis instance
        analysis = MetricsAnalysis(
            entity_id=room.id,
            entity_name=room.name
        )
        
        print_subsection("Calculating EN16798-1 Compliance")
        
        # Calculate EN16798-1 compliance from room data
        analysis.calculate_en16798_from_room_data(
            room=room,
            season="heating"
        )
        
        # Get the results
        en16798_data = analysis.get_standard_compliance("en16798-1")
        
        if en16798_data:
            print("✓ EN16798-1 calculation completed")
            print(f"\n  Achieved Category: {en16798_data.get('achieved_category', 'N/A')}")
            print(f"  IEQ Score: {en16798_data.get('ieq_score', 0):.2f}%")
            print(f"  Total hours analyzed: {en16798_data.get('total_hours_analyzed', 0)}")
            print(f"  Season: {en16798_data.get('season', 'N/A')}")
            print(f"  Calculation method: {en16798_data.get('calculation_method', 'N/A')}")
            
            print("\n  Category Compliance Rates:")
            category_compliance = en16798_data.get('category_compliance', {})
            for category, compliance in category_compliance.items():
                print(f"    Category {category.upper()}: {compliance:.2f}%")
        else:
            print("❌ EN16798-1 calculation failed")
            return False
        
        print("\n✅ EN16798-1 calculation test PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ EN16798-1 calculation test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_tail_calculation() -> bool:
    """Test TAIL calculation from room data."""
    print_section("TEST 2: TAIL Calculation from Room Data")
    
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
        
        # Create a MetricsAnalysis instance
        analysis = MetricsAnalysis(
            entity_id=room.id,
            entity_name=room.name
        )
        
        print_subsection("Calculating TAIL Ratings")
        
        # Define thresholds for TAIL calculation
        parameter_thresholds = {
            'temperature': {'lower': 20.0, 'upper': 26.0},
            'co2': {'lower': 0, 'upper': 1000},
            'humidity': {'lower': 30, 'upper': 60},
        }
        
        # Calculate TAIL ratings from room data
        analysis.calculate_tail_from_room_data(
            room=room,
            parameter_thresholds=parameter_thresholds
        )
        
        # Get the results
        tail_data = analysis.get_standard_compliance("tail")
        
        if tail_data:
            print("✓ TAIL calculation completed")
            print(f"\n  Overall Rating: {tail_data.get('overall_rating', 'N/A')} ({tail_data.get('overall_rating_label', 'N/A')})")
            print(f"  Total hours analyzed: {tail_data.get('total_hours_analyzed', 0)}")
            print(f"  Calculation method: {tail_data.get('calculation_method', 'N/A')}")
            
            print("\n  Category Ratings:")
            categories = tail_data.get('categories', {})
            for category_name, category_data in categories.items():
                rating = category_data.get('rating', 'N/A')
                label = category_data.get('rating_label', 'N/A')
                compliance = category_data.get('average_compliance', 0)
                param_count = category_data.get('parameter_count', 0)
                print(f"    {category_name.upper()}: {rating} ({label}) - {compliance:.2f}% avg compliance ({param_count} parameters)")
            
            print("\n  Parameter Details:")
            parameters = tail_data.get('parameters', {})
            for param_name, param_data in parameters.items():
                rating = param_data.get('rating', 'N/A')
                label = param_data.get('rating_label', 'N/A')
                compliance = param_data.get('compliance_rate', 0)
                print(f"    {param_name}: {rating} ({label}) - {compliance:.2f}% compliance")
        else:
            print("❌ TAIL calculation failed")
            return False
        
        print("\n✅ TAIL calculation test PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ TAIL calculation test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_multiple_rooms() -> bool:
    """Test calculations across multiple rooms with varied quality levels."""
    print_section("TEST 3: Multiple Rooms Analysis (Varied Quality Data)")
    
    try:
        # Path to varied quality sample data
        level_path = project_root / "data" / "samples" / "sample_varied_quality"
        
        if not level_path.exists():
            print(f"❌ Sample data directory not found: {level_path}")
            print(f"   Please run: python tests/generate_sample_room_data.py")
            return False
        
        print(f"✓ Found sample data directory: {level_path.name}")
        
        # Load all room data files
        room_files = sorted(level_path.glob("*.csv"))
        print(f"✓ Found {len(room_files)} room data files")
        
        room_analyses = []
        
        for room_file in room_files:
            room_id = room_file.stem
            room_name = room_id.replace("_", " ").title()
            
            # Load data
            df = pd.read_csv(room_file, parse_dates=['timestamp'])
            
            # Create room
            room = Room(
                id=room_id,
                name=room_name,
                level_id="level_1",
                building_id="building_a",
                area=25.0,
                volume=75.0,
                occupancy=2,
                room_type="office",
                data_file_path=room_file,
                time_series_data=df,
                data_start=df['timestamp'].min(),
                data_end=df['timestamp'].max()
            )
            
            # Create analysis
            analysis = MetricsAnalysis(
                entity_id=room.id,
                entity_name=room.name
            )
            
            # Calculate both EN16798-1 and TAIL
            analysis.calculate_en16798_from_room_data(room=room, season="heating")
            analysis.calculate_tail_from_room_data(room=room)
            
            room_analyses.append(analysis)
            
            # Get results
            en16798 = analysis.get_en16798_category()
            tail = analysis.get_tail_rating()
            
            # Get detailed compliance data
            en16798_data = analysis.get_standard_compliance("en16798-1")
            tail_data = analysis.get_standard_compliance("tail")
            
            print(f"\n  {room_name}:")
            print(f"    EN16798-1: Category {en16798.upper() if en16798 else 'N/A'}")
            
            if en16798_data:
                cat_compliance = en16798_data.get('category_compliance', {})
                ieq_score = en16798_data.get('ieq_score', 0)
                param_compliance = en16798_data.get('parameter_compliance', {})
                
                print(f"      IEQ Score: {ieq_score:.1f}%")
                print(f"      Overall Compliance: Cat I: {cat_compliance.get('cat_i', 0):.1f}%, "
                      f"Cat II: {cat_compliance.get('cat_ii', 0):.1f}%, "
                      f"Cat III: {cat_compliance.get('cat_iii', 0):.1f}%, "
                      f"Cat IV: {cat_compliance.get('cat_iv', 0):.1f}%")
                
                # Display parameter-level compliance
                if param_compliance:
                    print(f"      Parameter Breakdown:")
                    for cat_name in ['cat_i', 'cat_ii', 'cat_iii', 'cat_iv']:
                        cat_params = param_compliance.get(cat_name, {})
                        if cat_params:
                            param_details = []
                            for param_name, param_data in cat_params.items():
                                compliance = param_data.get('compliance_rate', 0)
                                param_details.append(f"{param_name}: {compliance:.1f}%")
                            print(f"        {cat_name.upper()}: {', '.join(param_details)}")
            
            print(f"    TAIL: Rating {tail or 'N/A'}")
            
            if tail_data:
                categories = tail_data.get('categories', {})
                thermal = categories.get('thermal', {})
                iaq = categories.get('iaq', {})
                acoustic = categories.get('acoustic', {})
                luminous = categories.get('luminous', {})
                
                thermal_rating = thermal.get('rating_label', 'N/A')
                thermal_compliance = thermal.get('average_compliance', 0)
                iaq_rating = iaq.get('rating_label', 'N/A')
                iaq_compliance = iaq.get('average_compliance', 0)
                acoustic_rating = acoustic.get('rating_label', 'N/A') if acoustic else 'N/A'
                acoustic_compliance = acoustic.get('average_compliance', 0) if acoustic else 0
                luminous_rating = luminous.get('rating_label', 'N/A') if luminous else 'N/A'
                luminous_compliance = luminous.get('average_compliance', 0) if luminous else 0
                
                print(f"      Thermal: {thermal_rating} ({thermal_compliance:.1f}%), "
                      f"IAQ: {iaq_rating} ({iaq_compliance:.1f}%)")
                print(f"      Acoustic: {acoustic_rating} ({acoustic_compliance:.1f}%), "
                      f"Luminous: {luminous_rating} ({luminous_compliance:.1f}%)")
        
        print_subsection("Aggregating Results")
        
        # Create building-level analysis
        building_analysis = MetricsAnalysis(
            entity_id="building_a",
            entity_name="Building A",
            child_count=len(room_analyses)
        )
        
        # Aggregate EN16798-1 (worst case method)
        building_analysis.aggregate_child_standard_compliance(
            room_analyses,
            standard="both"
        )
        
        # Get aggregated results
        building_en16798 = building_analysis.get_en16798_category()
        building_tail = building_analysis.get_tail_rating()
        
        print(f"\n  Building-level Aggregation:")
        print(f"    EN16798-1: Category {building_en16798 or 'N/A'}")
        print(f"    TAIL: Rating {building_tail or 'N/A'}")
        
        # Show details
        building_en16798_data = building_analysis.get_standard_compliance("en16798-1")
        if building_en16798_data:
            print(f"\n    EN16798-1 Details:")
            print(f"      Aggregation method: {building_en16798_data.get('aggregation_method', 'N/A')}")
            print(f"      Child categories: {building_en16798_data.get('child_categories', [])}")
        
        building_tail_data = building_analysis.get_standard_compliance("tail")
        if building_tail_data:
            print(f"\n    TAIL Details:")
            print(f"      Aggregation method: {building_tail_data.get('aggregation_method', 'N/A')}")
            categories = building_tail_data.get('categories', {})
            for cat_name, cat_data in categories.items():
                rating_label = cat_data.get('rating_label', 'N/A')
                sample_count = cat_data.get('sample_count', 0)
                print(f"      {cat_name.upper()}: {rating_label} ({sample_count} samples)")
        
        print("\n✅ Multiple rooms analysis test PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Multiple rooms analysis test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("  EN16798-1 & TAIL ROOM-LEVEL CALCULATION TEST SUITE")
    print("=" * 80)
    print(f"\nProject root: {project_root}")
    print(f"Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run tests
    results = {
        "EN16798-1 Calculation": test_en16798_calculation(),
        "TAIL Calculation": test_tail_calculation(),
        "Multiple Rooms Analysis": test_multiple_rooms()
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
