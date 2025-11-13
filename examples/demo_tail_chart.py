"""Demo script for enhanced TAIL circular chart generation.

This script demonstrates the improved TAIL rating circular charts with:
- Hierarchical structure (IAQ subdivided into parameters)
- Gray color for non-computed values
- White dividers between segments
- Clean design without axes
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parents[1]))

from core.reporting.charts.tail_circular_chart import (
    TAILCircularChart,
    TAILRatingCalculator,
    create_tail_chart_for_building
)


def demo_hierarchical_iaq():
    """Demo 1: Hierarchical IAQ with subdivided parameters."""
    print("=" * 60)
    print("Demo 1: Enhanced Chart with External Labels")
    print("=" * 60)
    
    chart = TAILCircularChart(figsize=(12, 10))
    
    # IAQ subdivided into multiple parameters
    iaq_details = {
        "CO2": 2,        # CO2 - Yellow
        "Humid": 1,      # Humidity - Green
        "PM2.5": 3,      # PM2.5 - Orange
        "VOC": None,     # Not measured - Gray
        "Radon": None,   # Not measured - Gray
        "Mold": 1,       # Mold - Green
    }
    
    fig = chart.create(
        overall_rating=3,  # Overall is worst (Orange)
        thermal_rating=1,  # Green
        acoustic_rating=2,  # Yellow
        iaq_rating=3,      # Orange (worst of IAQ params)
        luminous_rating=1,  # Green
        thermal_details={"Temp": 1},
        acoustic_details={"Noise": 2},
        iaq_details=iaq_details,  # Multiple IAQ params
        luminous_details={"Lux": 1},
        building_name="Office Building",
        date_from="2024-01-01",
        date_to="2024-12-31",
        save_path=Path("output/tail_charts/demo_hierarchical_iaq.png")
    )
    
    print("✓ Enhanced chart with external labels")
    print("  - No internal component labels (T, A, I, L removed)")
    print("  - External parameter labels with connector lines")
    print("  - Horizontal legend at bottom (5 columns)")
    print("  - Date period in title")
    print("  - Bigger center circle")
    print()


def demo_mixed_measured():
    """Demo 2: Mixed measured and non-measured parameters."""
    print("=" * 60)
    print("Demo 2: Mixed Measured/Non-Measured Parameters")
    print("=" * 60)
    
    chart = TAILCircularChart(figsize=(12, 10))
    
    fig = chart.create(
        overall_rating=2,
        thermal_rating=1,      # Measured - Green
        acoustic_rating=None,  # Not measured - Gray
        iaq_rating=2,          # Measured - Yellow
        luminous_rating=None,  # Not measured - Gray
        thermal_details={"Temp": 1},
        acoustic_details=None,  # No acoustic data
        iaq_details={
            "CO2": 2,
            "Humid": 1,
            "PM2.5": 2,
            "VOC": None,  # Not measured
        },
        luminous_details=None,  # No lighting data
        building_name="Partially Monitored Building",
        date_from="2024-06-01",
        date_to="2024-06-30",
        save_path=Path("output/tail_charts/demo_mixed_measured.png")
    )
    
    print("✓ Mixed measured chart: demo_mixed_measured.png")
    print("  - Acoustic: Not measured (gray)")
    print("  - Luminous: Not measured (gray)")
    print("  - IAQ: Partially measured")
    print()


def demo_excellent_building():
    """Demo 3: Excellent building (all green)."""
    print("=" * 60)
    print("Demo 3: Excellent Building Performance")
    print("=" * 60)
    
    chart = TAILCircularChart(figsize=(12, 10))
    
    fig = chart.create(
        overall_rating=1,  # Green - Excellent
        thermal_rating=1,
        acoustic_rating=1,
        iaq_rating=1,
        luminous_rating=1,
        thermal_details={"Temp": 1},
        acoustic_details={"Noise": 1},
        iaq_details={
            "CO2": 1,
            "Humid": 1,
            "PM2.5": 1,
            "VOC": 1,
            "HCHO": 1,
            "Radon": 1,
        },
        luminous_details={"Lux": 1, "Daylight": 1},
        building_name="A+ Certified Green Building",
        date_from="2024-01-01",
        date_to="2024-12-31",
        save_path=Path("output/tail_charts/demo_excellent.png")
    )
    
    print("✓ Excellent building: demo_excellent.png")
    print("  - All parameters green (Rating I)")
    print("  - Full monitoring coverage")
    print()


def demo_poor_building():
    """Demo 4: Poor building with problems."""
    print("=" * 60)
    print("Demo 4: Building with Performance Issues")
    print("=" * 60)
    
    chart = TAILCircularChart(figsize=(12, 10))
    
    fig = chart.create(
        overall_rating=4,  # Red - Poor
        thermal_rating=3,  # Orange
        acoustic_rating=4,  # Red - Major issue
        iaq_rating=4,      # Red - Major issue
        luminous_rating=2,  # Yellow
        thermal_details={"Temp": 3},
        acoustic_details={"Noise": 4},
        iaq_details={
            "CO2": 4,          # Critical
            "Humid": 3,        # Fair
            "PM2.5": 4,        # Critical
            "VOC": 3,
            "HCHO": 4,  # Critical
            "Mold": 3,
        },
        luminous_details={"Lux": 2},
        building_name="Building Requiring Immediate Action",
        date_from="2024-Q3",
        date_to="2024-Q4",
        save_path=Path("output/tail_charts/demo_poor.png")
    )
    
    print("✓ Poor building: demo_poor.png")
    print("  - Multiple critical issues (Rating IV)")
    print("  - Red segments highlight problems")
    print()


def demo_comparison_suite():
    """Demo 5: Create comparison suite across ratings."""
    print("=" * 60)
    print("Demo 5: Building Comparison Suite")
    print("=" * 60)
    
    buildings = [
        {
            "name": "Building A",
            "overall": 1,
            "T": 1, "A": 1, "I": 1, "L": 1,
            "iaq_details": {"CO2": 1, "Humid": 1, "PM2.5": 1, "VOC": 1},
            "date_from": "2024-01", "date_to": "2024-12"
        },
        {
            "name": "Building B",
            "overall": 2,
            "T": 2, "A": 2, "I": 2, "L": 1,
            "iaq_details": {"CO2": 2, "Humid": 1, "PM2.5": 2, "VOC": None},
            "date_from": "2024-01", "date_to": "2024-12"
        },
        {
            "name": "Building C",
            "overall": 3,
            "T": 2, "A": 3, "I": 3, "L": 2,
            "iaq_details": {"CO2": 3, "Humid": 2, "PM2.5": 3, "VOC": None},
            "date_from": "2024-01", "date_to": "2024-12"
        },
        {
            "name": "Building D",
            "overall": 4,
            "T": 3, "A": 4, "I": 4, "L": 3,
            "iaq_details": {"CO2": 4, "Humid": 4, "PM2.5": 4, "VOC": 3},
            "date_from": "2024-01", "date_to": "2024-12"
        },
    ]
    
    for i, building in enumerate(buildings):
        chart = TAILCircularChart(figsize=(10, 9))
        
        safe_name = building["name"].replace(" ", "_")
        save_path = Path(f"output/tail_charts/comparison_{i+1}_{safe_name}.png")
        
        fig = chart.create(
            overall_rating=building["overall"],
            thermal_rating=building["T"],
            acoustic_rating=building["A"],
            iaq_rating=building["I"],
            luminous_rating=building["L"],
            thermal_details={"Temp": building["T"]},
            acoustic_details={"Noise": building["A"]},
            iaq_details=building["iaq_details"],
            luminous_details={"Lux": building["L"]},
            building_name=building["name"],
            date_from=building["date_from"],
            date_to=building["date_to"],
            save_path=save_path
        )
        
        print(f"✓ {building['name']}: {save_path.name}")
    
    print()


def main():
    """Run all enhanced demos."""
    print("\n" + "=" * 60)
    print("TAIL Circular Chart - Enhanced V2 Demonstrations")
    print("Features: External Labels, No Component Text, Horizontal Legend")
    print("=" * 60 + "\n")
    
    # Create output directory
    Path("output/tail_charts").mkdir(parents=True, exist_ok=True)
    
    # Run demos
    demo_hierarchical_iaq()
    demo_mixed_measured()
    demo_excellent_building()
    demo_poor_building()
    demo_comparison_suite()
    
    print("=" * 60)
    print("All enhanced V2 demos completed!")
    print("Charts saved in: output/tail_charts/")
    print()
    print("V2 improvements:")
    print("  ✓ No component labels (T, A, I, L removed)")
    print("  ✓ External parameter labels with connector lines")
    print("  ✓ Horizontal legend at bottom (5 columns)")
    print("  ✓ Date period integrated in title")
    print("  ✓ Bigger center circle")
    print("  ✓ Clean, professional appearance")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()

