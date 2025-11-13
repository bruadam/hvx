"""
Demonstration of EN 16798-1 compliant IEQ aggregation methods.

This example shows how to:
1. Assess individual parameters per room
2. Aggregate multiple parameters into room-level categories
3. Aggregate multiple rooms into building-level assessment
4. Use different aggregation strategies for different purposes
"""

from datetime import datetime
from typing import Dict

from core.domain.enums.parameter_type import ParameterType
from core.domain.enums.aggregation_method import (
    ParameterAggregationMethod,
    SpatialAggregationMethod,
    AggregationStrategy,
)
from core.domain.value_objects.aggregation_config import (
    AggregationConfig,
    ParameterCategoryResult,
    RoomAggregationResult,
)
from core.domain.models.building_analysis import BuildingAnalysis


def demo_parameter_assessment():
    """
    Demo 1: Assess EN 16798-1 category for individual parameters.
    """
    print("=" * 80)
    print("DEMO 1: Parameter-level Category Assessment")
    print("=" * 80)
    
    # Example: Office room with temperature monitoring
    room_id = "office_301"
    
    # Time-in-category data for temperature
    # These would come from your actual measurements
    temp_data = {
        "percent_in_cat1": 92.3,  # 92.3% of time within Cat I limits (e.g., 20-24°C)
        "percent_in_cat2": 96.8,  # 96.8% within Cat II (e.g., 19-25°C)
        "percent_in_cat3": 99.1,  # 99.1% within Cat III (e.g., 18-26°C)
        "total_occupied_hours": 2080.0,  # Full year of office hours
    }
    
    # Assess temperature category
    temp_result = ParameterCategoryResult.from_time_in_category(
        parameter=ParameterType.TEMPERATURE,
        location_id=room_id,
        **temp_data
    )
    
    print(f"\nRoom: {room_id}")
    print(f"Parameter: {temp_result.parameter.display_name}")
    print(f"Time in Category I:   {temp_result.percent_in_cat1:.1f}%")
    print(f"Time in Category II:  {temp_result.percent_in_cat2:.1f}%")
    print(f"Time in Category III: {temp_result.percent_in_cat3:.1f}%")
    print(f"→ Assessed Category: {temp_result.category}")
    print(f"  (Requires ≥95% in Cat I for 'I', ≥90% in Cat II for 'II', ≥85% in Cat III for 'III')")
    
    # CO2 example
    co2_data = {
        "percent_in_cat1": 88.5,
        "percent_in_cat2": 94.2,
        "percent_in_cat3": 97.8,
        "total_occupied_hours": 2080.0,
    }
    
    co2_result = ParameterCategoryResult.from_time_in_category(
        parameter=ParameterType.CO2,
        location_id=room_id,
        **co2_data
    )
    
    print(f"\nParameter: {co2_result.parameter.display_name}")
    print(f"Time in Category I:   {co2_result.percent_in_cat1:.1f}%")
    print(f"Time in Category II:  {co2_result.percent_in_cat2:.1f}%")
    print(f"Time in Category III: {co2_result.percent_in_cat3:.1f}%")
    print(f"→ Assessed Category: {co2_result.category}")


def demo_parameter_aggregation():
    """
    Demo 2: Aggregate multiple parameters into room-level assessment.
    
    Shows both worst-parameter (categorical) and weighted-average (continuous) methods.
    """
    print("\n\n" + "=" * 80)
    print("DEMO 2: Multi-Parameter Aggregation (Room Level)")
    print("=" * 80)
    
    room_id = "office_301"
    
    # Simulate parameter assessment results
    parameter_categories = {
        ParameterType.TEMPERATURE: "II",   # 92% in Cat I → Category II
        ParameterType.CO2: "II",           # 88% in Cat I → Category II
        ParameterType.HUMIDITY: "I",       # 97% in Cat I → Category I
        ParameterType.ILLUMINANCE: "III",  # 87% in Cat III → Category III
    }
    
    parameter_scores = {
        ParameterType.TEMPERATURE: 96.8,   # % in Cat II
        ParameterType.CO2: 94.2,           # % in Cat II
        ParameterType.HUMIDITY: 99.5,      # % in Cat I
        ParameterType.ILLUMINANCE: 87.3,   # % in Cat III
    }
    
    print(f"\nRoom: {room_id}")
    print("\nIndividual Parameter Results:")
    for param, cat in parameter_categories.items():
        score = parameter_scores[param]
        print(f"  {param.display_name:20s} Category {cat}  ({score:.1f}% compliance)")
    
    # Method 1: Worst-parameter aggregation (conservative)
    print("\n" + "-" * 80)
    print("Method 1: WORST-PARAMETER AGGREGATION (Conservative / Compliance)")
    print("-" * 80)
    
    analysis = BuildingAnalysis(
        building_id="demo_building",
        building_name="Demo Office Building"
    )
    
    overall_category = analysis.aggregate_parameters_worst_case(parameter_categories)
    
    print(f"\nRoom Overall Category: {overall_category}")
    print(f"  (Limited by worst parameter: Illuminance = Category III)")
    print(f"\nUse case: EN 16798-1 compliance certification, official reporting")
    
    # Method 2: Weighted-average aggregation (continuous score)
    print("\n" + "-" * 80)
    print("Method 2: WEIGHTED-AVERAGE AGGREGATION (Performance Tracking)")
    print("-" * 80)
    
    # Use standard weights
    weights = {
        ParameterType.TEMPERATURE: 0.35,
        ParameterType.CO2: 0.25,
        ParameterType.HUMIDITY: 0.10,
        ParameterType.ILLUMINANCE: 0.15,
        ParameterType.NOISE: 0.10,
        ParameterType.PM25: 0.05,
    }
    
    ieq_score = analysis.aggregate_parameters_weighted(parameter_scores, weights)
    
    print(f"\nParameter weights:")
    for param, weight in weights.items():
        if param in parameter_scores:
            score = parameter_scores[param]
            contribution = weight * score
            print(f"  {param.display_name:20s} {weight:4.0%} × {score:5.1f}% = {contribution:5.2f}")
    
    print(f"\nRoom IEQ Score: {ieq_score:.1f}%")
    print(f"\nUse case: KPI dashboards, continuous monitoring, before/after comparisons")


def demo_spatial_aggregation():
    """
    Demo 3: Aggregate multiple rooms into building-level assessment.
    
    Shows different spatial aggregation methods.
    """
    print("\n\n" + "=" * 80)
    print("DEMO 3: Multi-Room Aggregation (Building Level)")
    print("=" * 80)
    
    # Simulate room-level results
    room_data = {
        "office_301": {
            "category": "II",
            "ieq_score": 94.5,
            "occupancy_hours": 2080.0,
            "area_m2": 45.0,
        },
        "office_302": {
            "category": "III",
            "ieq_score": 87.2,
            "occupancy_hours": 2080.0,
            "area_m2": 45.0,
        },
        "meeting_room": {
            "category": "I",
            "ieq_score": 98.3,
            "occupancy_hours": 520.0,  # Less utilized
            "area_m2": 25.0,
        },
        "open_office": {
            "category": "II",
            "ieq_score": 92.1,
            "occupancy_hours": 8320.0,  # 4x occupancy (4 people)
            "area_m2": 120.0,
        },
    }
    
    print("\nRoom-level results:")
    print(f"{'Room':20s} {'Category':10s} {'IEQ Score':12s} {'Occ. Hours':12s} {'Area (m²)':10s}")
    print("-" * 80)
    for room_id, data in room_data.items():
        print(
            f"{room_id:20s} {data['category']:10s} "
            f"{data['ieq_score']:10.1f}% {data['occupancy_hours']:10.0f}h {data['area_m2']:10.1f}"
        )
    
    analysis = BuildingAnalysis(
        building_id="demo_building",
        building_name="Demo Office Building"
    )
    
    # Extract data
    room_categories = {rid: d["category"] for rid, d in room_data.items()}
    room_scores = {rid: d["ieq_score"] for rid, d in room_data.items()}
    occupancy_hours = {rid: d["occupancy_hours"] for rid, d in room_data.items()}
    room_areas = {rid: d["area_m2"] for rid, d in room_data.items()}
    
    # Method 1: Worst-space
    print("\n" + "-" * 80)
    print("Method 1: WORST-SPACE AGGREGATION")
    print("-" * 80)
    
    building_cat = analysis.aggregate_spaces_worst_case(room_categories)
    print(f"\nBuilding Category: {building_cat}")
    print(f"  (Limited by worst room: office_302 = Category III)")
    print(f"\nUse case: Strict compliance certification")
    
    # Method 2: Occupant-weighted
    print("\n" + "-" * 80)
    print("Method 2: OCCUPANT-WEIGHTED AGGREGATION (Recommended)")
    print("-" * 80)
    
    building_score = analysis.aggregate_spaces_occupant_weighted(
        room_scores, occupancy_hours
    )
    
    total_hours = sum(occupancy_hours.values())
    print(f"\nOccupancy-weighted calculation:")
    for room_id, score in room_scores.items():
        hours = occupancy_hours[room_id]
        weight = hours / total_hours
        contribution = weight * score
        print(
            f"  {room_id:20s} {score:5.1f}% × {weight:5.1%} = {contribution:5.2f}"
        )
    
    print(f"\nBuilding IEQ Score: {building_score:.1f}%")
    print(f"  (Open office has most influence due to 4x occupancy)")
    print(f"\nUse case: Most representative of actual occupant experience")
    
    # Method 3: Area-weighted
    print("\n" + "-" * 80)
    print("Method 3: AREA-WEIGHTED AGGREGATION")
    print("-" * 80)
    
    building_score_area = analysis.aggregate_spaces_area_weighted(
        room_scores, room_areas
    )
    
    total_area = sum(room_areas.values())
    print(f"\nArea-weighted calculation:")
    for room_id, score in room_scores.items():
        area = room_areas[room_id]
        weight = area / total_area
        contribution = weight * score
        print(
            f"  {room_id:20s} {score:5.1f}% × {weight:5.1%} = {contribution:5.2f}"
        )
    
    print(f"\nBuilding IEQ Score: {building_score_area:.1f}%")
    print(f"\nUse case: Practical when occupancy data unavailable")


def demo_aggregation_strategies():
    """
    Demo 4: Use pre-defined aggregation strategies.
    """
    print("\n\n" + "=" * 80)
    print("DEMO 4: Pre-defined Aggregation Strategies")
    print("=" * 80)
    
    strategies = [
        AggregationStrategy.STRICT_COMPLIANCE,
        AggregationStrategy.BALANCED_COMPLIANCE,
        AggregationStrategy.PERFORMANCE_TRACKING,
        AggregationStrategy.QUICK_ASSESSMENT,
    ]
    
    for strategy in strategies:
        print(f"\n{'=' * 80}")
        print(f"Strategy: {strategy.value.upper().replace('_', ' ')}")
        print(f"{'=' * 80}")
        
        config = AggregationConfig(strategy=strategy)
        
        print(f"\nParameter aggregation: {config.get_effective_parameter_method().value}")
        print(f"Spatial aggregation:   {config.get_effective_spatial_method().value}")
        print(f"\nDescription: {strategy.description}")
        print(f"\nRecommended use cases:")
        for use_case in strategy.use_cases:
            print(f"  • {use_case}")


def demo_custom_configuration():
    """
    Demo 5: Create custom aggregation configuration.
    """
    print("\n\n" + "=" * 80)
    print("DEMO 5: Custom Aggregation Configuration")
    print("=" * 80)
    
    # Custom config: Conservative parameters, realistic spatial weighting
    config = AggregationConfig(
        strategy=AggregationStrategy.CUSTOM,
        parameter_method=ParameterAggregationMethod.WORST_PARAMETER,
        spatial_method=SpatialAggregationMethod.OCCUPANT_WEIGHTED,
        
        # Custom thresholds (stricter than standard)
        category_1_threshold=98.0,  # Require 98% instead of 95%
        category_2_threshold=95.0,  # Require 95% instead of 90%
        category_3_threshold=90.0,  # Require 90% instead of 85%
        
        # Exclude certain rooms
        excluded_room_ids={"storage", "corridor"},
    )
    
    print("\nCustom Configuration:")
    print(f"  Parameter method: {config.get_effective_parameter_method().value}")
    print(f"  Spatial method:   {config.get_effective_spatial_method().value}")
    print(f"\n  Category thresholds:")
    print(f"    Category I:   ≥{config.category_1_threshold:.0f}% (stricter than standard 95%)")
    print(f"    Category II:  ≥{config.category_2_threshold:.0f}% (stricter than standard 90%)")
    print(f"    Category III: ≥{config.category_3_threshold:.0f}% (stricter than standard 85%)")
    print(f"\n  Excluded rooms: {', '.join(config.excluded_room_ids)}")
    
    print("\nUse case: High-performance building targeting stricter IEQ goals")


def demo_full_workflow():
    """
    Demo 6: Complete workflow from parameters to building assessment.
    """
    print("\n\n" + "=" * 80)
    print("DEMO 6: Complete Building Assessment Workflow")
    print("=" * 80)
    
    # Create building analysis
    analysis = BuildingAnalysis(
        building_id="office_building_2025",
        building_name="Modern Office Building",
        room_count=4,
    )
    
    # Simulate room aggregation results
    room_results = {}
    
    rooms = [
        ("office_301", "II", 94.5, 2080.0, 45.0),
        ("office_302", "III", 87.2, 2080.0, 45.0),
        ("meeting_room", "I", 98.3, 520.0, 25.0),
        ("open_office", "II", 92.1, 8320.0, 120.0),
    ]
    
    for room_id, category, score, hours, area in rooms:
        room_results[room_id] = RoomAggregationResult(
            room_id=room_id,
            room_name=room_id.replace("_", " ").title(),
            overall_category=category,
            ieq_score=score,
            total_occupied_hours=hours,
            floor_area_m2=area,
        )
    
    analysis.room_aggregations = room_results
    
    # Apply different strategies
    print("\n1. STRICT COMPLIANCE Strategy")
    print("-" * 80)
    
    config_strict = AggregationConfig.strict_compliance()
    analysis.apply_aggregation_strategy(config_strict)
    
    summary = analysis.get_aggregation_summary()
    print(f"Building Category:    {summary['building_category']}")
    print(f"Parameter method:     {summary['parameter_method']}")
    print(f"Spatial method:       {summary['spatial_method']}")
    
    print("\n2. BALANCED COMPLIANCE Strategy")
    print("-" * 80)
    
    config_balanced = AggregationConfig.balanced_compliance()
    analysis.apply_aggregation_strategy(config_balanced)
    
    summary = analysis.get_aggregation_summary()
    print(f"Building Category:    {summary['building_category']}")
    print(f"Building IEQ Score:   {summary['building_ieq_score']:.1f}%")
    print(f"Parameter method:     {summary['parameter_method']}")
    print(f"Spatial method:       {summary['spatial_method']}")
    
    print("\n3. PERFORMANCE TRACKING Strategy")
    print("-" * 80)
    
    config_perf = AggregationConfig.performance_tracking()
    analysis.apply_aggregation_strategy(config_perf)
    
    summary = analysis.get_aggregation_summary()
    print(f"Building IEQ Score:   {summary['building_ieq_score']:.1f}%")
    print(f"Parameter method:     {summary['parameter_method']}")
    print(f"Spatial method:       {summary['spatial_method']}")
    
    print("\n" + "=" * 80)
    print("Building Analysis Summary:")
    print("=" * 80)
    print(analysis)
    print(f"\nFull summary dict:")
    import json
    print(json.dumps(analysis.to_summary_dict(), indent=2, default=str))


if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 15 + "EN 16798-1 IEQ AGGREGATION DEMONSTRATION" + " " * 22 + "║")
    print("╚" + "=" * 78 + "╝")
    
    # Run all demos
    demo_parameter_assessment()
    demo_parameter_aggregation()
    demo_spatial_aggregation()
    demo_aggregation_strategies()
    demo_custom_configuration()
    demo_full_workflow()
    
    print("\n\n" + "=" * 80)
    print("END OF DEMONSTRATION")
    print("=" * 80)
    print("\nKey Takeaways:")
    print("  1. EN 16798-1 categories based on time-in-category percentages")
    print("  2. Worst-parameter method for conservative compliance reporting")
    print("  3. Weighted-average method for continuous performance tracking")
    print("  4. Occupant-weighted spatial aggregation most representative")
    print("  5. Pre-defined strategies for common use cases")
    print("  6. Full flexibility with custom configurations")
    print("\n")
