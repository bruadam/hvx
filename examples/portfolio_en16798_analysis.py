"""
Portfolio Analysis: EN 16798-1 Compliance Testing

This script performs comprehensive EN 16798-1 compliance testing on all buildings
in the data portfolio, evaluating all 4 categories (I, II, III, IV) and generating
detailed reports for each room and building.
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import json
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.infrastructure.data_loaders.dataset_builder import DatasetBuilder
from core.analytics.engine.analysis_engine import AnalysisEngine
from core.analytics.aggregators.en16798_aggregator import EN16798Aggregator
from core.domain.models.room import Room
from core.domain.models.building import Building
from core.domain.enums.en16798_category import EN16798Category
from core.domain.enums.pollution_level import PollutionLevel
from core.domain.enums.ventilation import VentilationType
from core.domain.enums.occupancy import ActivityLevel
from core.analytics.calculators.en16798_calculator import (
    EN16798StandardCalculator,
    EN16798RoomMetadata,
)


def get_en16798_test_configs() -> List[Dict[str, Any]]:
    """
    Generate EN 16798-1 test configurations for all 4 categories.
    
    Returns:
        List of test configurations
    """
    tests = []
    
    # Category I tests
    tests.extend([
        {
            "test_id": "cat_i_temp_heating",
            "parameter": "temperature",
            "standard": "en16798-1",
            "filter": "opening_hours",
            "period": "heating_season",
            "mode": "bidirectional",
            "threshold": {"lower": 21.0, "upper": 23.0},
            "category": "cat_i",
        },
        {
            "test_id": "cat_i_temp_cooling",
            "parameter": "temperature",
            "standard": "en16798-1",
            "filter": "opening_hours",
            "period": "non_heating_season",
            "mode": "bidirectional",
            "threshold": {"lower": 23.5, "upper": 25.5},
            "category": "cat_i",
        },
        {
            "test_id": "cat_i_co2",
            "parameter": "co2",
            "standard": "en16798-1",
            "filter": "opening_hours",
            "period": "all_year",
            "mode": "unidirectional_ascending",
            "threshold": {"upper": 950},
            "category": "cat_i",
        },
        {
            "test_id": "cat_i_humidity",
            "parameter": "humidity",
            "standard": "en16798-1",
            "filter": "opening_hours",
            "period": "all_year",
            "mode": "bidirectional",
            "threshold": {"lower": 30, "upper": 50},
            "category": "cat_i",
        },
    ])
    
    # Category II tests
    tests.extend([
        {
            "test_id": "cat_ii_temp_heating",
            "parameter": "temperature",
            "standard": "en16798-1",
            "filter": "opening_hours",
            "period": "heating_season",
            "mode": "bidirectional",
            "threshold": {"lower": 20.0, "upper": 24.0},
            "category": "cat_ii",
        },
        {
            "test_id": "cat_ii_temp_cooling",
            "parameter": "temperature",
            "standard": "en16798-1",
            "filter": "opening_hours",
            "period": "non_heating_season",
            "mode": "bidirectional",
            "threshold": {"lower": 23.0, "upper": 26.0},
            "category": "cat_ii",
        },
        {
            "test_id": "cat_ii_co2",
            "parameter": "co2",
            "standard": "en16798-1",
            "filter": "opening_hours",
            "period": "all_year",
            "mode": "unidirectional_ascending",
            "threshold": {"upper": 1200},
            "category": "cat_ii",
        },
        {
            "test_id": "cat_ii_humidity",
            "parameter": "humidity",
            "standard": "en16798-1",
            "filter": "opening_hours",
            "period": "all_year",
            "mode": "bidirectional",
            "threshold": {"lower": 25, "upper": 60},
            "category": "cat_ii",
        },
    ])
    
    # Category III tests
    tests.extend([
        {
            "test_id": "cat_iii_temp_heating",
            "parameter": "temperature",
            "standard": "en16798-1",
            "filter": "opening_hours",
            "period": "heating_season",
            "mode": "bidirectional",
            "threshold": {"lower": 19.0, "upper": 25.0},
            "category": "cat_iii",
        },
        {
            "test_id": "cat_iii_temp_cooling",
            "parameter": "temperature",
            "standard": "en16798-1",
            "filter": "opening_hours",
            "period": "non_heating_season",
            "mode": "bidirectional",
            "threshold": {"lower": 22.0, "upper": 27.0},
            "category": "cat_iii",
        },
        {
            "test_id": "cat_iii_co2",
            "parameter": "co2",
            "standard": "en16798-1",
            "filter": "opening_hours",
            "period": "all_year",
            "mode": "unidirectional_ascending",
            "threshold": {"upper": 1750},
            "category": "cat_iii",
        },
        {
            "test_id": "cat_iii_humidity",
            "parameter": "humidity",
            "standard": "en16798-1",
            "filter": "opening_hours",
            "period": "all_year",
            "mode": "bidirectional",
            "threshold": {"lower": 20, "upper": 70},
            "category": "cat_iii",
        },
    ])
    
    # Category IV tests
    tests.extend([
        {
            "test_id": "cat_iv_temp_heating",
            "parameter": "temperature",
            "standard": "en16798-1",
            "filter": "opening_hours",
            "period": "heating_season",
            "mode": "bidirectional",
            "threshold": {"lower": 17.0, "upper": 27.0},
            "category": "cat_iv",
        },
        {
            "test_id": "cat_iv_temp_cooling",
            "parameter": "temperature",
            "standard": "en16798-1",
            "filter": "opening_hours",
            "period": "non_heating_season",
            "mode": "bidirectional",
            "threshold": {"lower": 20.0, "upper": 29.0},
            "category": "cat_iv",
        },
        {
            "test_id": "cat_iv_co2",
            "parameter": "co2",
            "standard": "en16798-1",
            "filter": "opening_hours",
            "period": "all_year",
            "mode": "unidirectional_ascending",
            "threshold": {"upper": 1750},
            "category": "cat_iv",
        },
        {
            "test_id": "cat_iv_humidity",
            "parameter": "humidity",
            "standard": "en16798-1",
            "filter": "opening_hours",
            "period": "all_year",
            "mode": "bidirectional",
            "threshold": {"lower": 15, "upper": 80},
            "category": "cat_iv",
        },
    ])
    
    return tests


def infer_room_metadata(
    room: Room, 
    building: Building
) -> EN16798RoomMetadata:
    """
    Infer room metadata for EN 16798-1 calculations.
    
    Args:
        room: Room entity
        building: Parent building
        
    Returns:
        EN16798RoomMetadata with inferred values
    """
    # Infer room type from room name/ID
    room_name_lower = room.name.lower()
    room_id_lower = room.id.lower()
    
    room_type = "office"  # default
    if any(x in room_name_lower or x in room_id_lower for x in ["classroom", "class"]):
        room_type = "classroom"
    elif any(x in room_name_lower or x in room_id_lower for x in ["office"]):
        room_type = "office"
    elif any(x in room_name_lower or x in room_id_lower for x in ["meeting", "conference"]):
        room_type = "meeting_room"
    elif any(x in room_name_lower or x in room_id_lower for x in ["lab", "laboratory", "computer"]):
        room_type = "laboratory"
    elif any(x in room_name_lower or x in room_id_lower for x in ["library"]):
        room_type = "library"
    elif any(x in room_name_lower or x in room_id_lower for x in ["staff", "lounge"]):
        room_type = "office"
    elif any(x in room_name_lower or x in room_id_lower for x in ["shop", "retail", "store"]):
        room_type = "retail"
    elif any(x in room_name_lower or x in room_id_lower for x in ["server", "storage"]):
        room_type = "other"
    
    # Estimate floor area and volume if not available
    floor_area = room.area if room.area else 30.0  # default 30 m²
    volume = room.volume if room.volume else floor_area * 3.0  # assume 3m ceiling
    
    # Estimate occupancy based on room type and area
    occupancy_estimates = {
        "classroom": int(floor_area * 0.4),  # ~2.5 m² per student
        "office": max(1, int(floor_area / 10)),  # ~10 m² per person
        "meeting_room": max(2, int(floor_area * 0.3)),  # ~3.3 m² per person
        "laboratory": max(1, int(floor_area / 15)),  # ~15 m² per person
        "library": max(1, int(floor_area / 5)),  # ~5 m² per person
        "retail": max(1, int(floor_area / 5)),  # variable
        "other": 1,
    }
    occupancy = room.occupancy if room.occupancy else occupancy_estimates.get(room_type, 2)
    
    # Default assumptions
    ventilation_type = room.ventilation_type if hasattr(room, 'ventilation_type') and room.ventilation_type else VentilationType.MECHANICAL
    pollution_level = room.pollution_level if hasattr(room, 'pollution_level') and room.pollution_level else PollutionLevel.LOW
    
    # Determine target category based on building type
    building_type_str = building.building_type.value if building.building_type else "office"
    target_category = EN16798Category.get_recommended_for_building_type(building_type_str)
    
    return EN16798RoomMetadata(
        room_type=room_type,
        floor_area=floor_area,
        volume=volume,
        occupancy_count=occupancy,
        ventilation_type=ventilation_type,
        pollution_level=pollution_level,
        target_category=target_category,
    )


def analyze_portfolio(data_dir: Path, output_dir: Optional[Path] = None):
    """
    Analyze complete building portfolio with EN 16798-1 tests.
    
    Args:
        data_dir: Directory containing building data
        output_dir: Optional directory for output reports
    """
    print("=" * 100)
    print("EN 16798-1 PORTFOLIO ANALYSIS")
    print("=" * 100)
    print(f"\nData Directory: {data_dir}")
    print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Load dataset
    print("Loading dataset...")
    builder = DatasetBuilder()
    dataset, buildings, levels, rooms = builder.build_from_directory(data_dir)
    
    print(f"✓ Loaded {len(buildings)} buildings, {len(levels)} levels, {len(rooms)} rooms\n")
    
    # Get EN 16798-1 test configurations
    tests = get_en16798_test_configs()
    print(f"✓ Configured {len(tests)} EN 16798-1 tests (4 tests × 4 categories)\n")
    
    # Initialize analysis engine
    engine = AnalysisEngine()
    
    # Results storage
    portfolio_results = {
        "analysis_date": datetime.now().isoformat(),
        "buildings": {},
        "summary": {
            "total_buildings": len(buildings),
            "total_rooms": len(rooms),
            "category_achievements": {
                "cat_i": 0,
                "cat_ii": 0,
                "cat_iii": 0,
                "cat_iv": 0,
                "none": 0,
            },
        },
    }
    
    # Analyze each building
    for building_id, building in buildings.items():
        print("-" * 100)
        print(f"Building: {building.name} ({building_id})")
        print(f"Type: {building.building_type.display_name if building.building_type else 'Unknown'}")
        print("-" * 100)
        
        building_rooms = [r for r in rooms.values() if r.building_id == building_id]
        print(f"Rooms to analyze: {len(building_rooms)}\n")
        
        building_results = {
            "name": building.name,
            "type": building.building_type.value if building.building_type else "unknown",
            "rooms": {},
            "summary": {
                "total_rooms": len(building_rooms),
                "analyzed_rooms": 0,
                "category_distribution": {
                    "cat_i": 0,
                    "cat_ii": 0,
                    "cat_iii": 0,
                    "cat_iv": 0,
                    "none": 0,
                },
            },
        }
        
        # Analyze each room
        for room in building_rooms:
            if not room.has_data:
                print(f"  ⊘ {room.name}: No data available")
                continue
            
            print(f"  → Analyzing: {room.name}")
            
            try:
                # Run analysis
                analysis = engine.analyze_room(room, tests=tests, apply_filters=True)
                
                # Get EN 16798-1 compliance using the aggregator
                en16798_compliance = EN16798Aggregator.get_en16798_compliance(analysis)
                highest_category = en16798_compliance.get('highest_category')
                
                # Infer room metadata for ventilation calculations
                room_metadata = infer_room_metadata(room, building)
                
                # Calculate ventilation requirements
                vent_requirements = {}
                for category in EN16798Category:
                    vent_data = EN16798StandardCalculator.calculate_required_ventilation_rate(
                        room_metadata, category
                    )
                    vent_requirements[category.value] = vent_data
                
                # Store results
                room_result = {
                    "name": room.name,
                    "data_points": room.get_measurement_count(),
                    "data_completeness": round(room.get_data_completeness(), 2),
                    "overall_compliance": round(analysis.overall_compliance_rate, 2),
                    "achieved_category": highest_category,
                    "achieved_category_name": EN16798Category(highest_category).display_name if highest_category else "None",
                    "test_results": {},
                    "room_metadata": {
                        "room_type": room_metadata.room_type,
                        "floor_area": room_metadata.floor_area,
                        "occupancy": room_metadata.occupancy_count,
                        "ventilation_type": room_metadata.ventilation_type.value,
                        "pollution_level": room_metadata.pollution_level.value,
                    },
                    "ventilation_requirements": vent_requirements,
                }
                
                # Store individual test results
                for test_id, result in analysis.compliance_results.items():
                    room_result["test_results"][test_id] = {
                        "compliance_rate": round(result.compliance_rate, 2),
                        "passed": result.is_compliant,
                        "total_points": result.total_points,
                        "compliant_points": result.compliant_points,
                    }
                
                building_results["rooms"][room.id] = room_result
                building_results["summary"]["analyzed_rooms"] += 1
                
                # Update category distribution
                if highest_category:
                    building_results["summary"]["category_distribution"][highest_category] += 1
                    portfolio_results["summary"]["category_achievements"][highest_category] += 1
                else:
                    building_results["summary"]["category_distribution"]["none"] += 1
                    portfolio_results["summary"]["category_achievements"]["none"] += 1
                
                # Print result
                category_display = EN16798Category(highest_category).display_name if highest_category else "None"
                print(f"     ✓ Category Achieved: {category_display} ({analysis.overall_compliance_rate:.1f}% compliance)")
                
            except Exception as e:
                print(f"     ✗ Error: {e}")
                import traceback
                traceback.print_exc()
        
        portfolio_results["buildings"][building_id] = building_results
        print()
    
    # Print summary
    print("=" * 100)
    print("PORTFOLIO SUMMARY")
    print("=" * 100)
    print(f"\nTotal Buildings: {portfolio_results['summary']['total_buildings']}")
    print(f"Total Rooms: {portfolio_results['summary']['total_rooms']}")
    print(f"\nCategory Achievement Distribution:")
    
    for category, count in portfolio_results["summary"]["category_achievements"].items():
        if category != "none":
            cat_enum = EN16798Category(category)
            pct = (count / portfolio_results['summary']['total_rooms'] * 100) if portfolio_results['summary']['total_rooms'] > 0 else 0
            print(f"  {cat_enum.display_name.ljust(40)}: {count:3d} rooms ({pct:5.1f}%)")
        else:
            pct = (count / portfolio_results['summary']['total_rooms'] * 100) if portfolio_results['summary']['total_rooms'] > 0 else 0
            print(f"  {'No Category Achieved'.ljust(40)}: {count:3d} rooms ({pct:5.1f}%)")
    
    # Save results if output directory specified
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"en16798_portfolio_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(output_file, 'w') as f:
            json.dump(portfolio_results, f, indent=2)
        
        print(f"\n✓ Results saved to: {output_file}")
    
    print("\n" + "=" * 100)
    print("ANALYSIS COMPLETE")
    print("=" * 100 + "\n")
    
    return portfolio_results


def main():
    """Main entry point."""
    # Set paths
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    output_dir = project_root / "output" / "en16798_analysis"
    
    # Run analysis
    try:
        results = analyze_portfolio(data_dir, output_dir)
        print("✓ Portfolio analysis completed successfully!\n")
        return 0
    except Exception as e:
        print(f"\n✗ Error during portfolio analysis: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
