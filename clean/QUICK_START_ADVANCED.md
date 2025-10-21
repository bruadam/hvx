# Quick Start: Advanced Analytics

Get started with climate correlations, smart recommendations, and ventilation rate prediction in 5 minutes.

---

## Installation

The modules are already installed if you have the clean/ infrastructure. Dependencies:

```bash
pip install pandas numpy scipy
```

---

## 1. Climate Correlations (30 seconds)

**Identify root causes of IEQ issues through weather correlations.**

```python
from core.analytics.correlations import ClimateCorrelator
import pandas as pd

# Your data
indoor_temp = pd.Series([...])  # Indoor temperature time series
climate_df = pd.DataFrame({     # Climate data
    'outdoor_temp': [...],
    'radiation': [...],
    'wind_speed': [...]
})

# Analyze
correlator = ClimateCorrelator()
results = correlator.correlate_with_climate(indoor_temp, climate_df)

# Check results
for param, result in results.items():
    print(f"{param}: r={result.correlation:.2f} ({result.strength})")
    if abs(result.correlation) > 0.5:
        print(f"  → {result.interpretation}")
```

**Output example**:
```
radiation: r=+0.87 (very_strong)
  → Solar heat gain is a significant factor (consider shading).
outdoor_temp: r=-0.72 (strong)
  → Indoor issues worsen when outdoor temperature decreases (poor insulation likely).
```

---

## 2. Smart Recommendations (30 seconds)

**Get evidence-based recommendations with priority and cost estimates.**

```python
from core.analytics.recommendations import RecommendationEngine

# Your data
room_analysis = RoomAnalysis(...)  # Your room analysis results
climate_data = pd.DataFrame(...)    # Optional climate data

# Generate recommendations
engine = RecommendationEngine()
recommendations = engine.generate_recommendations(
    room_analysis,
    climate_data
)

# Display
for rec in recommendations:
    print(f"[{rec.priority.value.upper()}] {rec.title}")
    print(f"  {rec.description[:100]}...")
    print(f"  Impact: {rec.estimated_impact}")
    print(f"  Cost: {rec.implementation_cost}")
```

**Output example**:
```
[HIGH] Install External Solar Shading
  Room experiences significant overheating (45.2% compliant). Analysis shows solar heat gain...
  Impact: Could improve summer compliance by 20-40 percentage points
  Cost: Medium (€100-300 per window)
```

---

## 3. Ventilation Rate Prediction (30 seconds)

**Estimate air change rate from CO2 decay patterns.**

```python
from core.analytics.special import predict_ventilation_rate_from_co2_decay
import pandas as pd

# Your CO2 data
co2_series = pd.Series([...])  # Time series of CO2 measurements

# Predict ventilation rate
result = predict_ventilation_rate_from_co2_decay(co2_series)

if result:
    print(f"ACH: {result.ach:.2f} air changes/hour")
    print(f"Category: {result.ventilation_category}")
    print(f"Confidence: {result.confidence_interval}")
    print(f"Quality: R²={result.r_squared:.3f}")
```

**Output example**:
```
ACH: 2.8 air changes/hour
Category: fair
Confidence: (2.45, 3.15)
Quality: R²=0.891
```

---

## Complete Example (2 minutes)

**Integrated workflow from data to recommendations:**

```python
from core.analytics.correlations import ClimateCorrelator
from core.analytics.recommendations import RecommendationEngine
from core.analytics.special import predict_ventilation_rate_from_co2_decay

# Step 1: Analyze climate correlations
correlator = ClimateCorrelator()

# Create violation mask
temp_violations = indoor_temp < 18.0  # Too cold

# Correlate violations with climate
correlations = correlator.correlate_violations_with_climate(
    temp_violations,
    climate_df
)

# Identify drivers
drivers = correlator.identify_climate_drivers(correlations, threshold=0.5)

print(f"Found {len(drivers)} significant climate drivers:")
for driver in drivers:
    print(f"  {driver.parameter}: r={driver.correlation:.2f}")

# Step 2: Predict ventilation rate
ach_result = predict_ventilation_rate_from_co2_decay(co2_series)

if ach_result:
    print(f"\nVentilation: {ach_result.ach:.1f} ACH ({ach_result.ventilation_category})")

# Step 3: Generate smart recommendations
engine = RecommendationEngine()
recommendations = engine.generate_recommendations(
    room_analysis,
    climate_df
)

print(f"\nGenerated {len(recommendations)} recommendations:")
for i, rec in enumerate(recommendations, 1):
    print(f"\n{i}. [{rec.priority.value}] {rec.title}")
    print(f"   {rec.description[:150]}...")
```

---

## Running the Demos

Try the interactive demos:

```bash
cd clean/

# Climate correlations
python examples/demo_climate_correlations.py

# Smart recommendations
python examples/demo_smart_recommendations.py

# Ventilation rate prediction
python examples/demo_ventilation_rate_prediction.py

# Integrated workflow (all features)
python examples/demo_integrated_advanced_analytics.py
```

---

## Common Patterns

### Pattern 1: Check for Solar Gain

```python
correlator = ClimateCorrelator()
results = correlator.correlate_with_climate(indoor_temp, climate_df)

if 'radiation' in results and results['radiation'].correlation > 0.6:
    print("Strong solar gain detected!")
    print("→ Recommendation: External solar shading")
```

### Pattern 2: Check for Poor Insulation

```python
if 'outdoor_temp' in results and results['outdoor_temp'].correlation < -0.6:
    print("Poor insulation detected!")
    print("→ Recommendation: Improve building envelope")
```

### Pattern 3: Assess Ventilation Performance

```python
result = predict_ventilation_rate_from_co2_decay(co2_series)

if result:
    if result.ach < 2.0:
        print("Poor ventilation - Action required")
    elif result.ach < 4.0:
        print("Fair ventilation - Monitor")
    else:
        print("Good ventilation")
```

### Pattern 4: Priority-Based Action Plan

```python
recommendations = engine.generate_recommendations(room_analysis, climate_df)

critical = [r for r in recommendations if r.priority.value == 'critical']
high = [r for r in recommendations if r.priority.value == 'high']

print(f"Immediate action items: {len(critical)}")
print(f"High priority items: {len(high)}")

# Show critical actions
for rec in critical:
    print(f"  🔴 {rec.title}")
```

---

## Data Requirements

### Climate Correlations
- Minimum: 100 data points
- Recommended: 500+ data points
- Format: Pandas Series/DataFrame with datetime index

### Smart Recommendations
- Required: RoomAnalysis object with compliance results
- Optional: Climate DataFrame for correlation-based recommendations
- Format: Standard Pydantic models from clean/

### Ventilation Rate
- Minimum: 5 hours of CO2 data showing decay
- Recommended: Multiple decay periods for averaging
- Format: Pandas Series with datetime index

---

## Interpretation Guide

### Correlation Strength

| r value | Strength | Meaning |
|---------|----------|---------|
| |r| < 0.2 | Negligible | Weak or no relationship |
| 0.2 ≤ |r| < 0.4 | Weak | Some relationship |
| 0.4 ≤ |r| < 0.6 | Moderate | Noticeable relationship |
| 0.6 ≤ |r| < 0.8 | Strong | Clear relationship |
| |r| ≥ 0.8 | Very Strong | Very clear relationship |

### Recommendation Priorities

| Priority | When Assigned | Action Timeline |
|----------|---------------|-----------------|
| Critical | Compliance < 30% OR severe issues | Immediate (within 1 week) |
| High | Compliance < 50% OR major issues | Short-term (1-4 weeks) |
| Medium | Compliance < 75% OR moderate issues | Medium-term (1-3 months) |
| Low | Compliance < 90% OR minor issues | Long-term (3-12 months) |

### Ventilation Categories

| ACH Range | Category | Assessment |
|-----------|----------|------------|
| < 2.0 | Poor | Below standards - action required |
| 2.0 - 4.0 | Fair | Meets minimum - monitor |
| 4.0 - 6.0 | Good | Adequate for most uses |
| > 6.0 | Excellent | Well above standards |

---

## Troubleshooting

### "No decay periods found"
- Check that CO2 actually decays in your data
- Room may be continuously occupied
- Try longer time period or different threshold

### "Correlation coefficient is NaN"
- Check for sufficient overlapping data points
- Ensure both series have datetime index
- Remove constant values (no variation = no correlation)

### "No recommendations generated"
- Check compliance results exist in room_analysis
- Verify test_id names contain expected keywords (temp, co2, etc.)
- Ensure compliance_rate is set correctly

---

## Next Steps

1. **Read full documentation**: `ADVANCED_ANALYTICS.md`
2. **Run demos**: Try all four demo scripts
3. **Review migration guide**: `MIGRATION_SUMMARY.md`
4. **Explore source code**: Check inline docstrings
5. **Integrate with your workflow**: Add to existing analysis pipeline

---

## Quick Reference

```python
# Imports
from core.analytics.correlations import ClimateCorrelator, WeatherAnalyzer
from core.analytics.recommendations import RecommendationEngine
from core.analytics.special import (
    predict_ventilation_rate_from_co2_decay,
    detect_occupancy_from_co2,
)

# Climate correlations
correlator = ClimateCorrelator()
results = correlator.correlate_with_climate(indoor_series, climate_df)
drivers = correlator.identify_climate_drivers(results, threshold=0.5)

# Recommendations
engine = RecommendationEngine()
recommendations = engine.generate_recommendations(room_analysis, climate_df)

# Ventilation rate
ach_result = predict_ventilation_rate_from_co2_decay(co2_series)

# Occupancy
occupancy = detect_occupancy_from_co2(co2_series, occupied_threshold=600)
```

---

**Ready to use! Start with the demos and consult ADVANCED_ANALYTICS.md for details.**
