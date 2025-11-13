"""
Demo: Worst Performing Room Report with Climate Analysis

This script demonstrates the complete workflow for generating a comprehensive
report focused on the worst performing room, including:
- Identification of worst performer
- Climate correlation analysis
- Heatmap visualizations showing temporal patterns
- Trend analysis over time
- Root cause identification (climate factors)
- Targeted, evidence-based recommendations

Usage:
    python examples/demo_worst_room_climate_report.py
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.domain.models.room import Room
from core.domain.enums.parameter_type import ParameterType
from core.reporting.report_generator import ReportGenerator
from core.utils.synthetic_climate_data import generate_climate_data
from core.analytics.engine.analysis_engine import AnalysisEngine
from core.analytics.recommendations.recommendation_engine import RecommendationEngine


def generate_synthetic_room_data(
    room_id: str,
    room_name: str,
    start_date: str,
    end_date: str,
    scenario: str = "normal",
    climate_data: pd.DataFrame = None,
) -> Room:
    """
    Generate synthetic room data for testing.

    Args:
        room_id: Room identifier
        room_name: Room name
        start_date: Start date
        end_date: End date
        scenario: Performance scenario ("normal", "overheating", "poor_ventilation", "cold")
        climate_data: Climate data to correlate with

    Returns:
        Room entity with synthetic data
    """
    dates = pd.date_range(start_date, end_date, freq="h")
    n = len(dates)

    # Generate base indoor conditions
    if scenario == "overheating":
        # Room with severe overheating issues (solar-driven)
        # Correlate strongly with solar radiation if available
        if climate_data is not None and "solar_radiation" in climate_data.columns:
            solar = climate_data["solar_radiation"].reindex(dates).fillna(0).values
            # Indoor temp increases with solar gain
            base_temp = 20 + 0.006 * solar  # Strong solar correlation
            temperature = base_temp + np.random.normal(0, 0.5, n)
        else:
            # Default overheating pattern
            hour = dates.hour.values
            temperature = 22 + 5 * (hour > 10) * (hour < 18) + np.random.normal(0, 1, n)

        # Poor ventilation contributes to high CO2
        co2 = 600 + np.random.normal(0, 100, n)
        co2 += 300 * (dates.hour > 8) * (dates.hour < 18)  # Higher during day
        humidity = 45 + np.random.normal(0, 5, n)

    elif scenario == "poor_ventilation":
        # Room with severe CO2 issues
        temperature = 22 + np.random.normal(0, 1, n)
        # Very high CO2
        co2 = 800 + np.random.normal(0, 150, n)
        co2 += 400 * (dates.hour > 8) * (dates.hour < 18)
        humidity = 50 + np.random.normal(0, 8, n)

    elif scenario == "cold":
        # Room with underheating issues (poor insulation)
        # Correlate with outdoor temperature
        if climate_data is not None and "outdoor_temp" in climate_data.columns:
            outdoor = climate_data["outdoor_temp"].reindex(dates).fillna(15).values
            # Indoor temp tracks outdoor (poor insulation)
            temperature = 18 + 0.3 * (outdoor - 5) + np.random.normal(0, 0.8, n)
        else:
            temperature = 18 + np.random.normal(0, 2, n)

        co2 = 500 + np.random.normal(0, 80, n)
        humidity = 40 + np.random.normal(0, 5, n)

    else:  # "normal"
        # Well-performing room
        temperature = 22 + np.random.normal(0, 0.5, n)
        co2 = 550 + np.random.normal(0, 50, n)
        co2 += 150 * (dates.hour > 8) * (dates.hour < 18)
        humidity = 50 + np.random.normal(0, 5, n)

    # Create DataFrame
    data = pd.DataFrame(
        {
            "temperature": temperature,
            "co2": co2,
            "humidity": humidity,
        },
        index=dates,
    )

    # Create Room entity with time series data
    room = Room(
        id=room_id,
        name=room_name,
        level_id="level_1",
        building_id="building_1",
        area=25.0,
        volume=75.0,
        occupancy=4,
        time_series_data=data,
        data_start=data.index[0],
        data_end=data.index[-1],
    )

    return room


def main():
    """Run the demo."""
    print("\n" + "=" * 80)
    print("WORST PERFORMING ROOM - CLIMATE ANALYSIS REPORT DEMO")
    print("=" * 80)

    # Configuration
    start_date = "2024-01-01"
    end_date = "2024-12-31"
    building_name = "Demo Office Building"

    print(f"\nGenerating synthetic data for: {building_name}")
    print(f"Period: {start_date} to {end_date}")

    # Step 1: Generate synthetic climate data
    print("\n[1/6] Generating synthetic climate data...")
    climate_data = generate_climate_data(
        start_date=start_date,
        end_date=end_date,
        freq="h",
        location_type="temperate",
        seed=42,
    )
    print(f"  ✓ Generated {len(climate_data)} hourly climate records")
    print(f"  ✓ Parameters: {', '.join(climate_data.columns)}")
    print(f"  ✓ Temperature range: {climate_data['outdoor_temp'].min():.1f}°C to {climate_data['outdoor_temp'].max():.1f}°C")

    # Step 2: Generate synthetic room data (mix of scenarios)
    print("\n[2/6] Generating synthetic room data...")
    rooms = []

    # Create several normal rooms
    for i in range(3):
        room = generate_synthetic_room_data(
            room_id=f"room_{i+1:03d}",
            room_name=f"Office {i+1}",
            start_date=start_date,
            end_date=end_date,
            scenario="normal",
            climate_data=climate_data,
        )
        rooms.append(room)
        print(f"  ✓ Created {room.name} (normal performance)")

    # Create one room with overheating issues (THIS WILL BE THE WORST)
    worst_room = generate_synthetic_room_data(
        room_id="room_004",
        room_name="South-Facing Conference Room",
        start_date=start_date,
        end_date=end_date,
        scenario="overheating",
        climate_data=climate_data,
    )
    rooms.append(worst_room)
    print(f"  ✓ Created {worst_room.name} (overheating issues - EXPECTED WORST)")

    # Create one with moderate issues
    moderate_room = generate_synthetic_room_data(
        room_id="room_005",
        room_name="Meeting Room B",
        start_date=start_date,
        end_date=end_date,
        scenario="poor_ventilation",
        climate_data=climate_data,
    )
    rooms.append(moderate_room)
    print(f"  ✓ Created {moderate_room.name} (ventilation issues)")

    print(f"\n  Total rooms created: {len(rooms)}")

    # Step 3: Analyze all rooms
    print("\n[3/6] Running IEQ compliance analysis on all rooms...")
    analysis_engine = AnalysisEngine()

    # Define compliance tests (EN16798-1 Class II)
    tests = [
        {
            "test_id": "temp_class_ii",
            "parameter": "temperature",
            "standard": "en16798-1",
            "threshold": {"lower": 20.0, "upper": 24.0},
            "config": {"building_class": "II", "season": "winter"},
        },
        {
            "test_id": "co2_class_ii",
            "parameter": "co2",
            "standard": "en16798-1",
            "threshold": {"upper": 800.0},
            "config": {"building_class": "II"},
        },
        {
            "test_id": "humidity_class_ii",
            "parameter": "humidity",
            "standard": "en16798-1",
            "threshold": {"lower": 30.0, "upper": 60.0},
            "config": {"building_class": "II"},
        },
    ]

    room_analyses = []
    for room in rooms:
        analysis = analysis_engine.analyze_room(room, tests=tests)
        room_analyses.append(analysis)
        print(f"  ✓ {room.name}: {analysis.overall_compliance_rate:.1f}% compliance")

    # Step 4: Identify worst performing room
    print("\n[4/6] Identifying worst performing room...")
    sorted_analyses = sorted(room_analyses, key=lambda x: x.overall_compliance_rate)
    worst_analysis = sorted_analyses[0]

    print(f"\n  🔴 WORST PERFORMER: {worst_analysis.room_name}")
    print(f"     Overall compliance: {worst_analysis.overall_compliance_rate:.1f}%")
    print(f"     Failed tests: {worst_analysis.failed_tests}/{worst_analysis.test_count}")
    print(f"     Total violations: {worst_analysis.total_violations}")

    # Show breakdown by parameter
    print(f"\n     Compliance by parameter:")
    for test_id, result in worst_analysis.compliance_results.items():
        print(f"       • {result.parameter}: {result.compliance_rate:.1f}%")

    # Step 5: Generate climate-based recommendations
    print("\n[5/6] Generating evidence-based recommendations with climate analysis...")

    # Find the Room entity for the worst performer
    worst_room_entity = next(r for r in rooms if r.id == worst_analysis.room_id)

    rec_engine = RecommendationEngine()
    recommendations = rec_engine.generate_recommendations(
        worst_analysis,
        climate_data=climate_data,
        room_data=worst_room_entity.time_series_data,
    )

    print(f"  ✓ Generated {len(recommendations)} prioritized recommendations\n")

    # Display top 3 recommendations
    print("  Top recommendations:")
    for i, rec in enumerate(recommendations[:3], 1):
        print(f"\n  {i}. [{rec.priority.value.upper()}] {rec.title}")
        print(f"     Type: {rec.type.value}")
        print(f"     {rec.description[:150]}...")

        if rec.climate_correlations:
            print(f"     Climate evidence:")
            for param, corr in rec.climate_correlations.items():
                print(f"       • {param}: r={corr.correlation:.3f} ({corr.strength})")

        print(f"     Estimated impact: {rec.estimated_impact}")

    # Step 6: Generate comprehensive HTML report
    print("\n[6/6] Generating comprehensive HTML report...")

    report_generator = ReportGenerator(analysis_engine)
    template_path = Path(__file__).parent.parent / "config" / "report_templates" / "worst_room_climate_analysis.yaml"
    output_path = Path(__file__).parent.parent / "outputs" / f"worst_room_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

    try:
        report_generator.generate_from_template(
            template_path=template_path,
            rooms=rooms,
            building_name=building_name,
            output_path=output_path,
        )
        print(f"  ✓ Report generated successfully!")
        print(f"  ✓ Location: {output_path}")
        print(f"\n  Open the report in your browser to view:")
        print(f"    - Compliance heatmaps (hour x day, day x month)")
        print(f"    - Temperature violation timelines (winter/summer)")
        print(f"    - CO2 and humidity trends")
        print(f"    - Climate correlation analysis")
        print(f"    - Targeted recommendations with evidence")
        print(f"    - Room performance comparison")

    except Exception as e:
        print(f"  ✗ Report generation failed: {e}")
        print(f"\nNote: Some report sections may require additional implementation.")
        print(f"The template is ready at: {template_path}")

    # Summary
    print("\n" + "=" * 80)
    print("DEMO SUMMARY")
    print("=" * 80)
    print(f"""
This demo showcased the complete workflow for worst-performing room analysis:

✓ Generated realistic synthetic climate data
  • Outdoor temperature, solar radiation, humidity, wind speed/direction
  • 1-year hourly data with realistic seasonal and diurnal patterns

✓ Created synthetic room data with various performance scenarios
  • Normal performing rooms
  • Overheating issues (solar-driven)
  • Poor ventilation (high CO2)

✓ Performed IEQ compliance analysis (EN16798-1 Class II)
  • Temperature compliance
  • CO2 (air quality) compliance
  • Humidity compliance

✓ Identified worst performing room: {worst_analysis.room_name}
  • Compliance rate: {worst_analysis.overall_compliance_rate:.1f}%
  • Primary issue: {sorted(worst_analysis.compliance_results.items(),
                          key=lambda x: x[1].compliance_rate)[0][1].parameter}

✓ Generated {len(recommendations)} evidence-based recommendations
  • Prioritized by severity (CRITICAL → LOW)
  • Backed by climate correlation analysis
  • Specific to detected root causes

✓ Created comprehensive HTML report
  • Temporal pattern analysis (heatmaps)
  • Violation timelines with trends
  • Climate driver identification
  • Targeted improvement actions

KEY INSIGHTS:
• Climate correlation reveals root causes (e.g., solar gain vs poor insulation)
• Heatmaps identify when problems occur (time of day, season)
• Evidence-based recommendations are more actionable than generic advice
• Worst performer identified automatically for focused intervention

NEXT STEPS:
1. Review the generated HTML report
2. Apply to real building data
3. Customize report template for specific needs
4. Integrate with building management systems
    """)

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
