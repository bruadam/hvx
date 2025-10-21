"""
Demo: Smart recommendations using sensitivity analysis.

Demonstrates intelligent recommendation generation based on:
- Compliance test results
- Climate correlations (sensitivity analysis)
- Evidence-based reasoning
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
from datetime import datetime

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.analytics.recommendations import (
    RecommendationEngine,
    RecommendationType,
)
from core.analytics.correlations import ClimateCorrelator
from core.domain.models.room_analysis import RoomAnalysis
from core.domain.models.compliance_result import ComplianceResult
from core.domain.enums.status import Status
from core.domain.enums.priority import Priority


def create_mock_room_analysis(scenario: str) -> RoomAnalysis:
    """Create mock room analysis for different scenarios."""

    if scenario == "solar_gain":
        # Overheating issue with strong solar correlation
        return RoomAnalysis(
            room_id="room_001",
            room_name="South Facing Office",
            analysis_timestamp=datetime.now(),
            status=Status.COMPLETED,
            compliance_results={
                "temp_above_summer": ComplianceResult(
                    test_id="temp_above_summer",
                    parameter="temperature",
                    compliance_rate=45.5,  # Poor compliance
                    violation_count=450,
                    total_count=1000,
                    threshold_lower=None,
                    threshold_upper=26.0,
                ),
            },
        )

    elif scenario == "poor_insulation":
        # Cold issues with outdoor temp correlation
        return RoomAnalysis(
            room_id="room_002",
            room_name="North Facing Room",
            analysis_timestamp=datetime.now(),
            status=Status.COMPLETED,
            compliance_results={
                "temp_below_winter": ComplianceResult(
                    test_id="temp_below_winter",
                    parameter="temperature",
                    compliance_rate=52.0,
                    violation_count=520,
                    total_count=1000,
                    threshold_lower=20.0,
                    threshold_upper=None,
                ),
            },
        )

    elif scenario == "poor_ventilation":
        # Severe CO2 issues
        return RoomAnalysis(
            room_id="room_003",
            room_name="Conference Room",
            analysis_timestamp=datetime.now(),
            status=Status.COMPLETED,
            compliance_results={
                "co2_limit": ComplianceResult(
                    test_id="co2_limit",
                    parameter="co2",
                    compliance_rate=38.0,  # Severe issues
                    violation_count=620,
                    total_count=1000,
                    threshold_lower=None,
                    threshold_upper=800.0,
                ),
            },
        )

    else:  # moderate_ventilation
        return RoomAnalysis(
            room_id="room_004",
            room_name="Classroom",
            analysis_timestamp=datetime.now(),
            status=Status.COMPLETED,
            compliance_results={
                "co2_limit": ComplianceResult(
                    test_id="co2_limit",
                    parameter="co2",
                    compliance_rate=72.0,  # Moderate issues
                    violation_count=280,
                    total_count=1000,
                    threshold_lower=None,
                    threshold_upper=800.0,
                ),
            },
        )


def create_mock_climate_data_with_solar() -> pd.DataFrame:
    """Create climate data showing solar gain pattern."""
    dates = pd.date_range("2024-06-01", periods=30 * 24, freq="H")

    # Summer pattern
    outdoor_temp = 22 + 6 * np.sin(np.arange(len(dates)) * 2 * np.pi / 24)
    outdoor_temp += np.random.normal(0, 2, len(dates))

    # Strong solar radiation during day
    hour_of_day = dates.hour
    radiation = np.where(
        (hour_of_day >= 8) & (hour_of_day <= 18),
        600 * np.sin((hour_of_day - 8) * np.pi / 10),
        0,
    )
    radiation += np.random.normal(0, 50, len(dates))
    radiation = np.maximum(radiation, 0)

    return pd.DataFrame(
        {
            "outdoor_temp": outdoor_temp,
            "radiation": radiation,
            "wind_speed": 2.5 + np.random.normal(0, 0.5, len(dates)),
        },
        index=dates,
    )


def create_mock_climate_data_winter() -> pd.DataFrame:
    """Create winter climate data."""
    dates = pd.date_range("2024-01-01", periods=30 * 24, freq="H")

    outdoor_temp = 5 + 5 * np.sin(np.arange(len(dates)) * 2 * np.pi / 24)
    outdoor_temp += np.random.normal(0, 2, len(dates))

    return pd.DataFrame(
        {
            "outdoor_temp": outdoor_temp,
            "radiation": 100 + np.random.normal(0, 20, len(dates)),
            "wind_speed": 4.0 + np.random.normal(0, 1, len(dates)),
        },
        index=dates,
    )


def demo_solar_shading_recommendation():
    """Demo recommendation for solar gain issue."""
    print("=" * 70)
    print("DEMO 1: Solar Shading Recommendation (Overheating)")
    print("=" * 70)

    # Create scenario
    room_analysis = create_mock_room_analysis("solar_gain")
    climate_data = create_mock_climate_data_with_solar()

    print(f"\nRoom: {room_analysis.room_name}")
    print(f"Issue: Summer overheating")

    # Show compliance
    for test_id, result in room_analysis.compliance_results.items():
        print(f"\n{test_id}:")
        print(f"  Compliance rate: {result.compliance_rate:.1f}%")
        print(f"  Violations: {result.violation_count}/{result.total_count} hours")

    # Generate recommendations
    engine = RecommendationEngine()
    recommendations = engine.generate_recommendations(room_analysis, climate_data)

    # Display recommendations
    print("\n" + "-" * 70)
    print("RECOMMENDATIONS")
    print("-" * 70)

    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. {rec.title}")
        print(f"   Priority: {rec.priority.value.upper()}")
        print(f"   Type: {rec.type.value}")
        print(f"\n   {rec.description}")

        if rec.rationale:
            print(f"\n   Rationale:")
            for rationale in rec.rationale:
                print(f"   • {rationale}")

        print(f"\n   Estimated Impact: {rec.estimated_impact}")
        print(f"   Implementation Cost: {rec.implementation_cost}")


def demo_insulation_recommendation():
    """Demo recommendation for insulation issue."""
    print("\n\n" + "=" * 70)
    print("DEMO 2: Insulation Recommendation (Cold Issues)")
    print("=" * 70)

    # Create scenario
    room_analysis = create_mock_room_analysis("poor_insulation")
    climate_data = create_mock_climate_data_winter()

    print(f"\nRoom: {room_analysis.room_name}")
    print(f"Issue: Winter underheating")

    # Show compliance
    for test_id, result in room_analysis.compliance_results.items():
        print(f"\n{test_id}:")
        print(f"  Compliance rate: {result.compliance_rate:.1f}%")

    # Generate recommendations
    engine = RecommendationEngine()
    recommendations = engine.generate_recommendations(room_analysis, climate_data)

    # Display
    print("\n" + "-" * 70)
    print("RECOMMENDATIONS")
    print("-" * 70)

    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. {rec.title}")
        print(f"   Priority: {rec.priority.value.upper()}")
        print(f"\n   {rec.description}")
        print(f"\n   Impact: {rec.estimated_impact}")
        print(f"   Cost: {rec.implementation_cost}")


def demo_ventilation_recommendations():
    """Demo ventilation recommendations."""
    print("\n\n" + "=" * 70)
    print("DEMO 3: Ventilation Recommendations")
    print("=" * 70)

    scenarios = [
        ("poor_ventilation", "Severe CO2 Issues"),
        ("moderate_ventilation", "Moderate CO2 Issues"),
    ]

    for scenario, description in scenarios:
        print(f"\n{description}")
        print("-" * 70)

        room_analysis = create_mock_room_analysis(scenario)

        # Show issue
        for test_id, result in room_analysis.compliance_results.items():
            print(f"Compliance: {result.compliance_rate:.1f}%")

        # Generate recommendations
        engine = RecommendationEngine()
        recommendations = engine.generate_recommendations(room_analysis)

        # Display
        for rec in recommendations:
            print(f"\n→ {rec.title}")
            print(f"  Priority: {rec.priority.value.upper()}")
            print(f"  Type: {rec.type.value}")
            print(f"  {rec.description[:150]}...")


def demo_prioritization():
    """Demo recommendation prioritization."""
    print("\n\n" + "=" * 70)
    print("DEMO 4: Recommendation Prioritization")
    print("=" * 70)

    # Create room with multiple issues
    room_analysis = RoomAnalysis(
        room_id="room_multi",
        room_name="Problem Room",
        analysis_timestamp=datetime.now(),
        status=Status.COMPLETED,
        compliance_results={
            "temp_above": ComplianceResult(
                test_id="temp_above",
                parameter="temperature",
                compliance_rate=45.0,
                violation_count=450,
                total_count=1000,
                threshold_lower=None,
                threshold_upper=26.0,
            ),
            "co2_limit": ComplianceResult(
                test_id="co2_limit",
                parameter="co2",
                compliance_rate=35.0,
                violation_count=650,
                total_count=1000,
                threshold_lower=None,
                threshold_upper=800.0,
            ),
        },
    )

    engine = RecommendationEngine()
    recommendations = engine.generate_recommendations(room_analysis)

    print(f"\nRoom: {room_analysis.room_name}")
    print(f"Issues: Multiple compliance failures")
    print(f"Total recommendations: {len(recommendations)}")

    print("\n" + "-" * 70)
    print("PRIORITIZED ACTION PLAN")
    print("-" * 70)

    for i, rec in enumerate(recommendations, 1):
        priority_emoji = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🟢",
        }

        print(
            f"\n{i}. {priority_emoji.get(rec.priority.value, '⚪')} "
            f"[{rec.priority.value.upper()}] {rec.title}"
        )
        print(f"   Type: {rec.type.value}")
        print(f"   Impact: {rec.estimated_impact}")


def main():
    """Run all demos."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "SMART RECOMMENDATIONS DEMO" + " " * 26 + "║")
    print("╚" + "═" * 68 + "╝")

    demo_solar_shading_recommendation()
    demo_insulation_recommendation()
    demo_ventilation_recommendations()
    demo_prioritization()

    print("\n\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("""
Smart recommendations use sensitivity analysis to provide:

✓ Evidence-based recommendations
  → Based on compliance results AND climate correlations

✓ Root cause identification
  → Solar gain vs poor insulation vs ventilation issues

✓ Prioritized action plans
  → Critical/High/Medium/Low priority

✓ Cost-benefit analysis
  → Estimated impact and implementation cost

✓ Targeted solutions
  → Specific to the detected issue pattern

Key insight: Generic advice like "improve ventilation" is replaced
with specific, evidence-based recommendations like "install external
solar shading due to strong correlation (r=0.85) between solar
radiation and overheating."
    """)


if __name__ == "__main__":
    main()
