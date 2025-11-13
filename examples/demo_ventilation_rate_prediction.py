"""
Demo: Ventilation rate prediction from CO2 decay.

Demonstrates how to estimate air change rate (ACH) from CO2 decay
patterns when a room becomes unoccupied.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.analytics.special import (
    VentilationRatePredictor,
    predict_ventilation_rate_from_co2_decay,
)


def create_co2_decay_scenario(ach: float, duration_hours: int = 8) -> pd.Series:
    """
    Create synthetic CO2 decay data.

    Args:
        ach: Target air changes per hour
        duration_hours: Duration of simulation

    Returns:
        Time series of CO2 data
    """
    # Parameters
    outdoor_co2 = 400  # ppm
    initial_co2 = 1200  # ppm (room just became unoccupied)

    # Time points (hourly data)
    dates = pd.date_range("2024-01-01 09:00", periods=duration_hours, freq="H")
    time_hours = np.arange(duration_hours)

    # Exponential decay: CO2(t) = C_outdoor + (C0 - C_outdoor) * exp(-ACH * t)
    co2_decay = outdoor_co2 + (initial_co2 - outdoor_co2) * np.exp(-ach * time_hours)

    # Add small noise
    co2_decay += np.random.normal(0, 10, len(co2_decay))

    return pd.Series(co2_decay, index=dates, name="CO2")


def create_realistic_co2_pattern() -> pd.Series:
    """
    Create realistic CO2 pattern with occupancy and decay periods.
    """
    dates = pd.date_range("2024-01-01", periods=24 * 3, freq="H")
    co2_values = []

    outdoor_co2 = 400
    current_co2 = outdoor_co2

    for i, hour in enumerate(dates):
        hour_of_day = hour.hour

        # Occupied hours: 8 AM to 6 PM
        if 8 <= hour_of_day <= 18:
            # CO2 builds up during occupancy
            target_co2 = 900 + np.random.normal(0, 50)
            current_co2 = current_co2 * 0.7 + target_co2 * 0.3
        else:
            # CO2 decays when unoccupied (ACH = 2.5)
            ach = 2.5
            current_co2 = outdoor_co2 + (current_co2 - outdoor_co2) * np.exp(
                -ach / 24
            )

        # Add noise
        current_co2 += np.random.normal(0, 5)
        co2_values.append(max(current_co2, outdoor_co2))

    return pd.Series(co2_values, index=dates, name="CO2")


def demo_simple_decay():
    """Demo with simple decay curve."""
    print("=" * 70)
    print("DEMO 1: Simple CO2 Decay Analysis")
    print("=" * 70)

    # Create decay scenarios with different ACH values
    scenarios = [
        (1.5, "Poor ventilation"),
        (3.0, "Fair ventilation"),
        (5.0, "Good ventilation"),
        (8.0, "Excellent ventilation"),
    ]

    print("\nScenario comparison:")
    print("-" * 70)

    for true_ach, description in scenarios:
        co2_data = create_co2_decay_scenario(true_ach, duration_hours=6)

        # Predict ACH
        result = predict_ventilation_rate_from_co2_decay(co2_data)

        if result:
            error = abs(result.ach - true_ach)
            print(f"\n{description} (True ACH: {true_ach:.1f})")
            print(f"  Predicted ACH: {result.ach:.2f} (error: {error:.2f})")
            print(f"  Confidence interval: {result.confidence_interval}")
            print(f"  R²: {result.r_squared:.3f}")
            print(f"  Category: {result.ventilation_category}")
            print(f"  Quality score: {result.quality_score:.3f}")
        else:
            print(f"\n{description} (True ACH: {true_ach:.1f})")
            print("  Could not estimate ACH (no decay detected)")


def demo_realistic_pattern():
    """Demo with realistic occupancy pattern."""
    print("\n\n" + "=" * 70)
    print("DEMO 2: Realistic Daily CO2 Pattern")
    print("=" * 70)

    co2_data = create_realistic_co2_pattern()

    print(f"\nData: {len(co2_data)} hours of CO2 measurements")
    print(f"Range: {co2_data.min():.0f} - {co2_data.max():.0f} ppm")
    print(f"Mean: {co2_data.mean():.0f} ppm")

    # Predict ventilation rate
    predictor = VentilationRatePredictor(outdoor_co2=400)
    result = predictor.predict_from_multiple_periods(co2_data)

    if result:
        print("\n" + "-" * 70)
        print("VENTILATION RATE PREDICTION")
        print("-" * 70)
        print(f"Estimated ACH: {result.ach:.2f} air changes per hour")
        print(f"Category: {result.ventilation_category.upper()}")
        print(f"Confidence interval (95%): {result.confidence_interval}")
        print(f"Model fit (R²): {result.r_squared:.3f}")
        print(f"Quality score: {result.quality_score:.3f}")
        print(f"\n{result.description}")

        # Recommendations based on ACH
        print("\n" + "-" * 70)
        print("RECOMMENDATIONS")
        print("-" * 70)

        if result.ventilation_category == "poor":
            print("⚠️  POOR VENTILATION DETECTED")
            print("   • Current ACH is below recommended levels")
            print("   • Consider installing mechanical ventilation")
            print("   • Or increase natural ventilation (larger/more windows)")
        elif result.ventilation_category == "fair":
            print("⚠️  FAIR VENTILATION")
            print("   • Meets minimum standards but could be improved")
            print("   • Monitor CO2 levels during peak occupancy")
            print("   • Consider demand-controlled ventilation")
        elif result.ventilation_category == "good":
            print("✓ GOOD VENTILATION")
            print("  • Adequate for most occupancy scenarios")
            print("  • Continue current ventilation practices")
        else:  # excellent
            print("✓ EXCELLENT VENTILATION")
            print("  • Well above recommended levels")
            print("  • May be opportunity to optimize energy use")

    else:
        print("\nCould not estimate ventilation rate (no clear decay periods)")


def demo_multiple_decay_periods():
    """Demo analyzing multiple decay periods."""
    print("\n\n" + "=" * 70)
    print("DEMO 3: Multiple Decay Periods Analysis")
    print("=" * 70)

    # Create data with multiple decay events
    dates = pd.date_range("2024-01-01", periods=24 * 7, freq="H")
    co2_values = []

    outdoor_co2 = 400
    ach = 3.5  # True ACH

    for i in range(len(dates)):
        hour_of_day = dates[i].hour

        # Morning: occupied, CO2 rises
        if 8 <= hour_of_day <= 12:
            co2_values.append(800 + np.random.normal(0, 30))
        # Afternoon: occupied, CO2 high
        elif 13 <= hour_of_day <= 17:
            co2_values.append(950 + np.random.normal(0, 30))
        # Evening/night: unoccupied, CO2 decays
        else:
            if i > 0:
                prev_co2 = co2_values[-1]
                decay_co2 = outdoor_co2 + (prev_co2 - outdoor_co2) * np.exp(
                    -ach / 24
                )
                co2_values.append(max(decay_co2, outdoor_co2))
            else:
                co2_values.append(outdoor_co2)

    co2_data = pd.Series(co2_values, index=dates, name="CO2")

    # Analyze
    predictor = VentilationRatePredictor()

    # Identify decay periods
    decay_segments = predictor._identify_decay_periods(co2_data, min_decay=100)

    print(f"\nIdentified {len(decay_segments)} decay periods")

    # Analyze each period
    print("\nIndividual decay period results:")
    print("-" * 70)

    for i, segment in enumerate(decay_segments[:5], 1):  # Show first 5
        result = predictor._analyze_decay_segment(segment)
        if result:
            print(f"\nPeriod {i}:")
            print(f"  Duration: {len(segment)} hours")
            print(f"  Estimated ACH: {result.ach:.2f}")
            print(f"  R²: {result.r_squared:.3f}")
            print(
                f"  CO2 range: {segment.iloc[0]:.0f} → {segment.iloc[-1]:.0f} ppm"
            )

    # Combined analysis
    result = predictor.predict_from_multiple_periods(co2_data)

    if result:
        print("\n" + "-" * 70)
        print("COMBINED ANALYSIS (all decay periods)")
        print("-" * 70)
        print(f"Estimated ACH: {result.ach:.2f} (true: {ach:.2f})")
        print(f"Error: {abs(result.ach - ach):.2f}")
        print(f"Average R²: {result.r_squared:.3f}")
        print(f"Quality score: {result.quality_score:.3f}")


def main():
    """Run all demos."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 12 + "VENTILATION RATE PREDICTION DEMO" + " " * 23 + "║")
    print("╚" + "═" * 68 + "╝")

    demo_simple_decay()
    demo_realistic_pattern()
    demo_multiple_decay_periods()

    print("\n\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("""
Ventilation rate prediction from CO2 decay provides:

✓ Non-invasive measurement of air change rate (ACH)
  → No need for tracer gas tests or expensive equipment

✓ Uses existing CO2 sensor data
  → Analyze historical data to estimate ventilation

✓ Identifies periods of poor ventilation
  → Helps diagnose air quality issues

✓ Validates ventilation system performance
  → Compare actual ACH to design specifications

Method: Fits exponential decay model to CO2 concentration when
room becomes unoccupied. The decay rate directly corresponds to
the air change rate.

Formula: CO2(t) = CO2_outdoor + (CO2_initial - CO2_outdoor) × e^(-ACH×t)
    """)


if __name__ == "__main__":
    main()
