"""
Demo: Integrated Advanced Analytics

Demonstrates all three advanced analytics features working together:
1. Climate correlations (sensitivity analysis)
2. Smart recommendations
3. Ventilation rate prediction from CO2 decay

This shows a complete workflow from data analysis to actionable insights.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
from datetime import datetime

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.analytics.correlations import ClimateCorrelator, WeatherAnalyzer
from core.analytics.recommendations import RecommendationEngine
from core.analytics.special import (
    predict_ventilation_rate_from_co2_decay,
    detect_occupancy_from_co2,
)
from core.domain.models.room_analysis import RoomAnalysis
from core.domain.models.compliance_result import ComplianceResult
from core.domain.enums.status import Status


def create_realistic_room_data():
    """Create realistic room data with multiple issues."""
    # 60 days of hourly data
    dates = pd.date_range("2024-01-01", periods=60 * 24, freq="H")

    # Climate data
    outdoor_temp = 8 + 10 * np.sin(np.arange(len(dates)) * 2 * np.pi / 24)
    outdoor_temp += np.random.normal(0, 2, len(dates))

    radiation = np.zeros(len(dates))
    for i, date in enumerate(dates):
        if 8 <= date.hour <= 16:
            radiation[i] = 300 * np.sin((date.hour - 8) * np.pi / 8)
        radiation[i] += np.random.normal(0, 30)
    radiation = np.maximum(radiation, 0)

    climate_df = pd.DataFrame(
        {
            "outdoor_temp": outdoor_temp,
            "radiation": radiation,
            "wind_speed": 3.5 + np.random.normal(0, 1, len(dates)),
        },
        index=dates,
    )

    # Indoor temperature with poor insulation
    # Strongly correlates with outdoor temp
    indoor_temp = 18 + 0.7 * (outdoor_temp - 8) + np.random.normal(0, 0.5, len(dates))

    # CO2 with occupancy pattern
    co2_values = []
    outdoor_co2 = 400
    current_co2 = outdoor_co2

    for i, date in enumerate(dates):
        hour = date.hour

        # Office hours: 8 AM - 6 PM on weekdays
        is_weekday = date.weekday() < 5
        is_office_hours = 8 <= hour <= 18

        if is_weekday and is_office_hours:
            # Occupied - CO2 builds up
            target_co2 = 950 + np.random.normal(0, 50)
            current_co2 = current_co2 * 0.6 + target_co2 * 0.4
        else:
            # Unoccupied - CO2 decays (ACH = 2.8)
            ach = 2.8
            current_co2 = outdoor_co2 + (current_co2 - outdoor_co2) * np.exp(
                -ach / 24
            )

        current_co2 += np.random.normal(0, 5)
        co2_values.append(max(current_co2, outdoor_co2))

    co2_series = pd.Series(co2_values, index=dates, name="CO2")
    temp_series = pd.Series(indoor_temp, index=dates, name="Temperature")

    return temp_series, co2_series, climate_df


def analyze_complete_room():
    """Perform complete analysis with all advanced features."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 12 + "INTEGRATED ADVANCED ANALYTICS DEMO" + " " * 21 + "║")
    print("╚" + "═" * 68 + "╝")

    # Generate data
    print("\n[1/5] Generating synthetic room data...")
    temp_series, co2_series, climate_df = create_realistic_room_data()

    print(f"✓ Created {len(temp_series)} hours of data")
    print(f"  Temperature range: {temp_series.min():.1f} - {temp_series.max():.1f}°C")
    print(f"  CO2 range: {co2_series.min():.0f} - {co2_series.max():.0f} ppm")

    # Step 1: Climate Correlation Analysis
    print("\n" + "=" * 70)
    print("[2/5] CLIMATE CORRELATION ANALYSIS (Sensitivity Analysis)")
    print("=" * 70)

    # Create violation mask (too cold)
    temp_violation_mask = temp_series < 18.0
    violation_rate = temp_violation_mask.mean() * 100

    print(f"\nCold temperature violations: {temp_violation_mask.sum()} hours ({violation_rate:.1f}%)")

    # Correlate with climate
    correlator = ClimateCorrelator()
    correlations = correlator.correlate_violations_with_climate(
        temp_violation_mask, climate_df
    )

    print("\nClimate correlations:")
    print("-" * 70)
    for param, result in correlations.items():
        print(f"{param}:")
        print(f"  r = {result.correlation:+.3f} ({result.strength})")
        print(f"  During violations: {result.mean_during_violations:.1f}")
        print(f"  During compliance: {result.mean_during_compliance:.1f}")
        print(f"  {result.interpretation[:80]}...")

    # Identify drivers
    drivers = correlator.identify_climate_drivers(correlations, threshold=0.4)
    if drivers:
        print(f"\n✓ Identified {len(drivers)} significant climate driver(s)")

    # Step 2: Occupancy Detection
    print("\n" + "=" * 70)
    print("[3/5] OCCUPANCY PATTERN DETECTION")
    print("=" * 70)

    from core.analytics.special import OccupancyDetector

    detector = OccupancyDetector(occupied_threshold=600)
    occupancy = detector.detect_occupancy(co2_series)

    print(f"\n{occupancy.description}")
    print(f"\nOccupancy details:")
    print(f"  Occupancy rate: {occupancy.occupancy_rate * 100:.1f}%")
    print(f"  Avg CO2 (occupied): {occupancy.avg_co2_occupied:.0f} ppm")
    print(f"  Avg CO2 (unoccupied): {occupancy.avg_co2_unoccupied:.0f} ppm")
    if occupancy.typical_occupancy_hours:
        hours_str = ", ".join([f"{h:02d}:00" for h in occupancy.typical_occupancy_hours[:5]])
        if len(occupancy.typical_occupancy_hours) > 5:
            hours_str += ", ..."
        print(f"  Typical hours: {hours_str}")

    # Step 3: Ventilation Rate Prediction
    print("\n" + "=" * 70)
    print("[4/5] VENTILATION RATE PREDICTION (from CO2 Decay)")
    print("=" * 70)

    ach_result = predict_ventilation_rate_from_co2_decay(co2_series, outdoor_co2=400)

    if ach_result:
        print(f"\n✓ Successfully estimated ventilation rate")
        print(f"\nResults:")
        print(f"  ACH: {ach_result.ach:.2f} air changes per hour")
        print(f"  Category: {ach_result.ventilation_category.upper()}")
        print(f"  Confidence interval (95%): {ach_result.confidence_interval}")
        print(f"  Model fit (R²): {ach_result.r_squared:.3f}")
        print(f"  Quality score: {ach_result.quality_score:.3f}")

        # Ventilation assessment
        if ach_result.ventilation_category == "poor":
            print("\n⚠️  POOR VENTILATION - Action required")
        elif ach_result.ventilation_category == "fair":
            print("\n⚠️  FAIR VENTILATION - Monitor and consider improvements")
        elif ach_result.ventilation_category == "good":
            print("\n✓ GOOD VENTILATION - Adequate")
        else:
            print("\n✓ EXCELLENT VENTILATION")
    else:
        print("\n✗ Could not estimate ventilation rate (no clear decay periods)")

    # Step 4: Smart Recommendations
    print("\n" + "=" * 70)
    print("[5/5] SMART RECOMMENDATIONS (Evidence-Based)")
    print("=" * 70)

    # Create mock room analysis
    room_analysis = RoomAnalysis(
        room_id="demo_room",
        room_name="Sample Office",
        analysis_timestamp=datetime.now(),
        status=Status.COMPLETED,
        compliance_results={
            "temp_below": ComplianceResult(
                test_id="temp_below",
                parameter="temperature",
                compliance_rate=100 - violation_rate,
                violation_count=int(temp_violation_mask.sum()),
                total_count=len(temp_violation_mask),
                threshold_lower=18.0,
                threshold_upper=None,
            ),
            "co2_limit": ComplianceResult(
                test_id="co2_limit",
                parameter="co2",
                compliance_rate=75.0,  # Moderate CO2 issues
                violation_count=600,
                total_count=2400,
                threshold_lower=None,
                threshold_upper=800.0,
            ),
        },
    )

    # Generate recommendations
    engine = RecommendationEngine()
    recommendations = engine.generate_recommendations(room_analysis, climate_df)

    print(f"\nGenerated {len(recommendations)} recommendation(s)")
    print("-" * 70)

    for i, rec in enumerate(recommendations, 1):
        priority_icon = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🟢",
        }

        print(f"\n{i}. {priority_icon.get(rec.priority.value, '⚪')} [{rec.priority.value.upper()}] {rec.title}")
        print(f"   Type: {rec.type.value}")
        print(f"\n   {rec.description[:200]}...")

        if rec.rationale:
            print(f"\n   Rationale:")
            for rationale in rec.rationale[:2]:  # Show first 2
                print(f"   • {rationale}")

        print(f"\n   Impact: {rec.estimated_impact}")
        print(f"   Cost: {rec.implementation_cost}")

    # Final Summary
    print("\n\n" + "=" * 70)
    print("INTEGRATED ANALYSIS SUMMARY")
    print("=" * 70)

    print(f"""
Room: {room_analysis.room_name}
Analysis Period: {len(temp_series)} hours

FINDINGS:

1. Climate Correlations (Sensitivity Analysis)
   • Temperature violations: {violation_rate:.1f}%
   • Significant climate drivers: {len(drivers)}
   • Root cause identified through correlation analysis

2. Occupancy Patterns
   • Occupancy rate: {occupancy.occupancy_rate * 100:.1f}%
   • Typical usage: Office hours on weekdays
   • CO2 patterns confirm occupancy schedule

3. Ventilation Performance
   • Estimated ACH: {ach_result.ach if ach_result else 'N/A'}
   • Category: {ach_result.ventilation_category.upper() if ach_result else 'N/A'}
   • Assessment: {'Adequate' if ach_result and ach_result.ach >= 2.0 else 'Needs improvement'}

4. Recommendations
   • Total recommendations: {len(recommendations)}
   • Priority actions: {sum(1 for r in recommendations if r.priority.value in ['critical', 'high'])}
   • Evidence-based with climate correlation support

WORKFLOW COMPLETE ✓
    """)

    print("\n" + "=" * 70)
    print("KEY INSIGHTS")
    print("=" * 70)
    print("""
The integrated analytics workflow provides:

✓ ROOT CAUSE IDENTIFICATION
  Climate correlations reveal WHY issues occur (not just WHAT)

✓ OPERATIONAL CONTEXT
  Occupancy detection provides usage patterns for better recommendations

✓ PERFORMANCE VALIDATION
  Ventilation rate prediction validates actual vs design performance

✓ ACTIONABLE RECOMMENDATIONS
  Evidence-based recommendations with estimated impact and cost

This replaces generic advice with specific, data-driven solutions
tailored to the actual building performance and usage patterns.
    """)


def main():
    """Run integrated demo."""
    analyze_complete_room()


if __name__ == "__main__":
    main()
