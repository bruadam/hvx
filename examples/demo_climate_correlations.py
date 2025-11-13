"""
Demo: Climate correlations analysis.

Demonstrates how to use climate correlation analysis to identify
weather-driven IEQ issues.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.analytics.correlations import (
    ClimateCorrelator,
    WeatherAnalyzer,
    calculate_correlation,
)


def create_sample_data():
    """Create sample indoor and climate data."""
    # Create 30 days of hourly data
    dates = pd.date_range("2024-01-01", periods=30 * 24, freq="H")

    # Simulate outdoor temperature (winter)
    outdoor_temp = 5 + 8 * np.sin(np.arange(len(dates)) * 2 * np.pi / 24)
    outdoor_temp += np.random.normal(0, 2, len(dates))

    # Simulate solar radiation (W/m²)
    hour_of_day = dates.hour
    radiation = np.where(
        (hour_of_day >= 8) & (hour_of_day <= 16),
        400 * np.sin((hour_of_day - 8) * np.pi / 8),
        0,
    )
    radiation += np.random.normal(0, 50, len(dates))
    radiation = np.maximum(radiation, 0)

    # Create climate dataframe
    climate_df = pd.DataFrame(
        {
            "outdoor_temp": outdoor_temp,
            "radiation": radiation,
            "wind_speed": 3 + np.random.normal(0, 1, len(dates)),
        },
        index=dates,
    )

    # Simulate indoor temperature with poor insulation
    # (strongly correlates with outdoor temp)
    indoor_temp = 18 + 0.8 * (outdoor_temp - 5) + np.random.normal(0, 0.5, len(dates))

    # Simulate indoor temperature with solar gain
    # (correlates with both outdoor temp and radiation)
    indoor_temp_solar = (
        20 + 0.4 * (outdoor_temp - 5) + 0.003 * radiation + np.random.normal(0, 0.5, len(dates))
    )

    return pd.Series(indoor_temp, index=dates, name="indoor_temp"), pd.Series(
        indoor_temp_solar, index=dates, name="indoor_temp_solar"
    ), climate_df


def demo_basic_correlation():
    """Demo basic correlation analysis."""
    print("=" * 70)
    print("DEMO 1: Basic Climate Correlation")
    print("=" * 70)

    indoor_temp, indoor_temp_solar, climate_df = create_sample_data()

    # Analyze poor insulation case
    correlator = ClimateCorrelator()
    results = correlator.correlate_with_climate(indoor_temp, climate_df)

    print("\nScenario: Room with poor insulation")
    print("-" * 70)
    for param, result in results.items():
        print(f"\n{param}:")
        print(f"  Correlation: {result.correlation:+.3f}")
        print(f"  Strength: {result.strength}")
        print(f"  P-value: {result.p_value:.4f}")
        print(f"  Interpretation: {result.interpretation}")


def demo_violation_correlation():
    """Demo violation-based correlation."""
    print("\n\n" + "=" * 70)
    print("DEMO 2: Violation-Based Correlation Analysis")
    print("=" * 70)

    indoor_temp, indoor_temp_solar, climate_df = create_sample_data()

    # Create violation mask (too cold = below 18°C)
    violation_mask = indoor_temp < 18.0

    print(f"\nTotal violations: {violation_mask.sum()} / {len(violation_mask)} hours")
    print(f"Violation rate: {violation_mask.mean() * 100:.1f}%")

    # Correlate violations with climate
    correlator = ClimateCorrelator()
    results = correlator.correlate_violations_with_climate(
        violation_mask, climate_df
    )

    print("\nClimate correlations during cold violations:")
    print("-" * 70)
    for param, result in results.items():
        print(f"\n{param}:")
        print(f"  Correlation: {result.correlation:+.3f}")
        print(f"  Mean during violations: {result.mean_during_violations:.1f}")
        print(f"  Mean during compliance: {result.mean_during_compliance:.1f}")
        print(f"  Effect size (Cohen's d): {result.effect_size:.2f}")
        print(f"  {result.interpretation}")


def demo_solar_gain_detection():
    """Demo solar gain detection."""
    print("\n\n" + "=" * 70)
    print("DEMO 3: Solar Gain Detection")
    print("=" * 70)

    indoor_temp, indoor_temp_solar, climate_df = create_sample_data()

    # Create overheating violation mask (too hot = above 24°C)
    violation_mask = indoor_temp_solar > 24.0

    print(f"\nOverheating violations: {violation_mask.sum()} / {len(violation_mask)} hours")

    # Analyze climate correlations
    correlator = ClimateCorrelator()
    results = correlator.correlate_violations_with_climate(
        violation_mask, climate_df
    )

    # Identify significant drivers
    drivers = correlator.identify_climate_drivers(results, threshold=0.4)

    print("\nSignificant climate drivers (|r| > 0.4):")
    print("-" * 70)
    for driver in drivers:
        print(f"\n{driver.parameter}:")
        print(f"  Correlation: {driver.correlation:+.3f} ({driver.strength})")
        print(f"  {driver.interpretation}")

    # Recommendation logic
    print("\n\nRecommendations based on correlations:")
    print("-" * 70)
    for driver in drivers:
        if "radiation" in driver.parameter.lower() and driver.correlation > 0.5:
            print("✓ STRONG SOLAR GAIN DETECTED")
            print("  → Install external solar shading (blinds, awnings)")
            print("  → Expected impact: 20-40% reduction in overheating")
        elif "outdoor_temp" in driver.parameter.lower() and driver.correlation > 0.6:
            print("✓ OUTDOOR TEMPERATURE DRIVES OVERHEATING")
            print("  → Improve building envelope insulation")
            print("  → Consider mechanical cooling if budget allows")


def demo_weather_stats_during_violations():
    """Demo weather statistics analysis."""
    print("\n\n" + "=" * 70)
    print("DEMO 4: Weather Statistics During Violations")
    print("=" * 70)

    indoor_temp, indoor_temp_solar, climate_df = create_sample_data()

    # Create violation mask
    violation_mask = indoor_temp < 18.0

    # Analyze weather during violations
    analyzer = WeatherAnalyzer()
    weather_stats = analyzer.analyze_during_violations(
        violation_mask, climate_df
    )

    print("\nWeather conditions during cold violations:")
    print("-" * 70)
    for param, stats in weather_stats.items():
        print(f"\n{param}:")
        print(f"  Mean: {stats.mean:.1f}")
        print(f"  Range: {stats.min:.1f} to {stats.max:.1f}")
        print(f"  Std Dev: {stats.std:.1f}")
        print(f"  Median: {stats.median:.1f}")
        print(f"  Sample size: {stats.count} hours")

    # Compare violation vs compliance periods
    print("\n\nComparison: Violations vs Compliance")
    print("-" * 70)
    comparison = analyzer.compare_violation_vs_compliance(
        violation_mask, climate_df, "outdoor_temp"
    )

    if "violations" in comparison and "compliance" in comparison:
        viol_stats = comparison["violations"]
        comp_stats = comparison["compliance"]

        print(f"\nOutdoor Temperature:")
        print(f"  During violations: {viol_stats.mean:.1f}°C ± {viol_stats.std:.1f}")
        print(f"  During compliance: {comp_stats.mean:.1f}°C ± {comp_stats.std:.1f}")
        print(f"  Difference: {viol_stats.mean - comp_stats.mean:+.1f}°C")


def main():
    """Run all demos."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "CLIMATE CORRELATION ANALYSIS DEMO" + " " * 20 + "║")
    print("╚" + "═" * 68 + "╝")

    demo_basic_correlation()
    demo_violation_correlation()
    demo_solar_gain_detection()
    demo_weather_stats_during_violations()

    print("\n\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("""
Climate correlation analysis helps identify root causes of IEQ issues:

✓ Strong positive correlation with radiation → Solar gain issue
  → Solution: External solar shading

✓ Strong negative correlation with outdoor temp → Poor insulation
  → Solution: Improve building envelope

✓ Weather statistics during violations → Context for recommendations
  → Helps quantify the relationship between outdoor and indoor conditions

This sensitivity analysis enables targeted, evidence-based recommendations
rather than generic suggestions.
    """)


if __name__ == "__main__":
    main()
