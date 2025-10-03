"""
Manual test script for the recommendation system.
Tests boolean-float correlation and recommendation generation.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Test correlation functionality
print("=" * 80)
print("Testing Boolean-Float Correlation")
print("=" * 80)

from src.core.analytics.ieq.library.correlations import (
    calculate_boolean_float_correlation,
    calculate_multiple_boolean_float_correlations
)

# Create test data: non-compliance vs outdoor temperature
timestamps = pd.date_range('2024-06-01', periods=100, freq='H')

# Simulate outdoor temperature (summer variation)
np.random.seed(42)
outdoor_temp = pd.Series(
    24 + 6 * np.sin(np.linspace(0, 2*np.pi, 100)) + np.random.normal(0, 1.5, 100),
    index=timestamps
)

# Simulate non-compliance: more likely when temp > 28°C
non_compliance = pd.Series(
    (outdoor_temp > 28) & (np.random.random(100) > 0.25),
    index=timestamps
)

print(f"\nTest Data Summary:")
print(f"  Total data points: {len(timestamps)}")
print(f"  Non-compliant periods: {non_compliance.sum()}")
print(f"  Compliant periods: {(~non_compliance).sum()}")
print(f"  Temperature range: {outdoor_temp.min():.1f}°C - {outdoor_temp.max():.1f}°C")

# Calculate correlation
result = calculate_boolean_float_correlation(non_compliance, outdoor_temp)

print(f"\n--- Single Parameter Correlation ---")
print(f"  Correlation coefficient: {result['correlation']:+.3f}")
print(f"  P-value: {result['p_value']:.4f}")
print(f"  Statistical significance: {'YES' if result['p_value'] < 0.05 else 'NO'}")
print(f"\n  Temperature when non-compliant: {result['mean_when_true']:.1f}°C ± {result['std_when_true']:.1f}")
print(f"  Temperature when compliant: {result['mean_when_false']:.1f}°C ± {result['std_when_false']:.1f}")
print(f"  Mean difference: {result['mean_when_true'] - result['mean_when_false']:+.1f}°C")
print(f"  Effect size (Cohen's d): {result['effect_size']:.3f}")
print(f"\n  Interpretation: {result['interpretation']}")

# Test multiple weather parameters
print(f"\n--- Multiple Weather Parameters ---")

solar_radiation = pd.Series(
    600 + 300 * np.sin(np.linspace(0, 2*np.pi, 100)) + np.random.normal(0, 50, 100),
    index=timestamps
).clip(0, 1000)

weather_df = pd.DataFrame({
    'outdoor_temperature': outdoor_temp,
    'solar_radiation': solar_radiation,
    'wind_speed': 2 + 3 * np.random.random(100)
}, index=timestamps)

multi_results = calculate_multiple_boolean_float_correlations(
    non_compliance,
    weather_df
)

for param, corr_data in multi_results.items():
    print(f"\n  {param}:")
    print(f"    Correlation: {corr_data['correlation']:+.3f} (p={corr_data['p_value']:.4f})")
    print(f"    Mean when non-compliant: {corr_data['mean_when_true']:.1f}")
    print(f"    Mean when compliant: {corr_data['mean_when_false']:.1f}")

# Test recommendation engine
print("\n" + "=" * 80)
print("Testing Recommendation Engine")
print("=" * 80)

from src.core.analytics.ieq.library.recommendations import (
    analyze_solar_shading_need,
    generate_solar_shading_recommendation
)

# Test solar shading recommendation
print("\n--- Solar Shading Analysis ---")

# Scenario 1: Poor compliance with strong correlation
summer_compliance = 55.0  # 55% compliance (poor)
outdoor_temp_corr = 0.65  # Strong positive correlation
solar_rad_corr = 0.72  # Very strong positive correlation

needs_shading, priority, rationale = analyze_solar_shading_need(
    summer_compliance_rate=summer_compliance,
    outdoor_temp_correlation=outdoor_temp_corr,
    solar_radiation_correlation=solar_rad_corr,
    avg_outdoor_temp_during_issues=29.5,
    avg_radiation_during_issues=850
)

print(f"\n  Scenario: {summer_compliance:.0f}% summer compliance")
print(f"  Outdoor temp correlation: {outdoor_temp_corr:+.2f}")
print(f"  Solar radiation correlation: {solar_rad_corr:+.2f}")
print(f"\n  Needs shading: {needs_shading}")
print(f"  Priority: {priority}")
print(f"  Rationale:")
for i, reason in enumerate(rationale, 1):
    print(f"    {i}. {reason}")

if needs_shading:
    recommendation = generate_solar_shading_recommendation(
        needs_shading,
        priority,
        rationale,
        summer_compliance
    )

    if recommendation:
        print(f"\n  Recommendation:")
        print(f"    Type: {recommendation['type']}")
        print(f"    Title: {recommendation['title']}")
        print(f"    Impact: {recommendation['estimated_impact']}")
        print(f"    Cost: {recommendation['implementation_cost']}")

print("\n" + "=" * 80)
print("All tests completed successfully!")
print("=" * 80)
