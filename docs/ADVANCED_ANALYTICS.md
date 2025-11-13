# Advanced Analytics Features

This document describes the advanced analytics capabilities in the clean/ infrastructure.

## Overview

Three new analytics modules have been added:

1. **Climate Correlations** - Sensitivity analysis identifying weather-driven issues
2. **Smart Recommendations** - Evidence-based recommendations using correlation analysis
3. **Special Analytics** - Advanced analytics like ventilation rate prediction from CO2 decay

---

## 1. Climate Correlations

**Location**: `clean/core/analytics/correlations/`

### Purpose

Identify root causes of IEQ issues by correlating indoor parameters with outdoor climate conditions.

### Key Features

- **Pearson/Spearman correlation** between indoor and outdoor parameters
- **Point-biserial correlation** for violation-climate relationships
- **Weather statistics** during violation periods
- **Climate driver identification** with interpretations

### Usage Example

```python
from core.analytics.correlations import ClimateCorrelator

# Create correlator
correlator = ClimateCorrelator()

# Correlate indoor temp with climate
results = correlator.correlate_with_climate(
    indoor_temp_series,
    climate_df  # Contains: outdoor_temp, radiation, wind_speed, etc.
)

# Check for solar gain
for param, result in results.items():
    if "radiation" in param and result.correlation > 0.5:
        print(f"Strong solar gain detected! r={result.correlation:.2f}")
```

### Correlation Interpretations

| Correlation | Parameter | Interpretation | Recommended Action |
|------------|-----------|----------------|-------------------|
| r > 0.6 | radiation | Strong solar heat gain | Install external solar shading |
| r < -0.6 | outdoor_temp | Poor thermal insulation | Improve building envelope |
| r > 0.5 | outdoor_temp | Overheating correlates with hot weather | Consider cooling system |
| r < -0.4 | outdoor_temp (CO2) | Natural ventilation insufficient in cold | Mechanical ventilation needed |

### Demo

```bash
cd clean/
python examples/demo_climate_correlations.py
```

---

## 2. Smart Recommendations

**Location**: `clean/core/analytics/recommendations/`

### Purpose

Generate prioritized, evidence-based recommendations using:
- Compliance test results
- Climate correlations (sensitivity analysis)
- Violation patterns

### Key Features

- **Automatic root cause detection** using correlations
- **Priority assignment** (Critical/High/Medium/Low)
- **Evidence-based rationale** with supporting data
- **Cost-benefit estimates**
- **Specialized analyzers** for solar shading, insulation, ventilation

### Usage Example

```python
from core.analytics.recommendations import RecommendationEngine

engine = RecommendationEngine()

# Generate recommendations for a room
recommendations = engine.generate_recommendations(
    room_analysis,  # RoomAnalysis object
    climate_data    # Optional climate DataFrame
)

# Recommendations are sorted by priority
for rec in recommendations:
    print(f"[{rec.priority.value}] {rec.title}")
    print(f"  {rec.description}")
    print(f"  Impact: {rec.estimated_impact}")
    print(f"  Cost: {rec.implementation_cost}")
```

### Recommendation Types

1. **SOLAR_SHADING**: External blinds/awnings for solar gain issues
2. **INSULATION**: Thermal envelope improvements for heat loss
3. **MECHANICAL_VENTILATION**: For severe air quality issues
4. **NATURAL_VENTILATION**: Enhanced natural ventilation strategy
5. **HVAC_OPTIMIZATION**: System tuning and control improvements
6. **OPERATIONAL**: Behavioral/operational changes

### How It Works

```
1. Analyze compliance results
   ↓
2. Correlate violations with climate
   ↓
3. Identify root cause (solar gain, insulation, ventilation, etc.)
   ↓
4. Generate targeted recommendation with evidence
   ↓
5. Assign priority based on severity and correlation strength
```

### Example Output

```
[CRITICAL] Install External Solar Shading

Overheating compliance is only 45.2%. Analysis shows solar heat
gain is a major factor. Installing external solar shading will
significantly reduce solar heat gain while maintaining natural
light and views.

Rationale:
  • Strong positive correlation with solar radiation (r=0.87)
  • Overheating occurs primarily during high-radiation periods
  • Mean radiation during violations: 680 W/m²

Estimated Impact: Could improve summer compliance by 20-40 percentage points
Implementation Cost: Medium (€100-300 per window)

Evidence:
  - outdoor_temp correlation: +0.42
  - radiation correlation: +0.87 (very strong)
  - Mean outdoor temp during violations: 28.5°C
```

### Demo

```bash
cd clean/
python examples/demo_smart_recommendations.py
```

---

## 3. Special Analytics

**Location**: `clean/core/analytics/special/`

### Purpose

Advanced analytics beyond standard compliance testing.

### 3.1 Ventilation Rate Prediction

**Estimate air change rate (ACH) from CO2 decay patterns**

#### How It Works

When a room becomes unoccupied, CO2 decays exponentially:

```
CO2(t) = CO2_outdoor + (CO2_initial - CO2_outdoor) × e^(-ACH×t)
```

The algorithm:
1. Identifies CO2 decay periods (when room becomes unoccupied)
2. Fits exponential decay curve
3. Extracts ACH (air changes per hour)
4. Validates with R² goodness-of-fit

#### Usage Example

```python
from core.analytics.special import predict_ventilation_rate_from_co2_decay

# CO2 time series
co2_series = pd.Series([950, 880, 780, 680, 590, 520, 470, 430, 410])

# Predict ACH
result = predict_ventilation_rate_from_co2_decay(co2_series)

if result:
    print(f"ACH: {result.ach:.2f} air changes/hour")
    print(f"Category: {result.ventilation_category}")
    print(f"Confidence: {result.confidence_interval}")
    print(f"R²: {result.r_squared:.3f}")
```

#### Ventilation Categories

| ACH Range | Category | Description |
|-----------|----------|-------------|
| < 2.0 | Poor | Below recommended levels |
| 2.0 - 4.0 | Fair | Meets minimum standards |
| 4.0 - 6.0 | Good | Adequate for most uses |
| > 6.0 | Excellent | Well above standards |

#### Benefits

- **Non-invasive**: Uses existing CO2 sensor data
- **No special equipment**: No tracer gas tests needed
- **Historical analysis**: Analyze past data
- **Performance validation**: Compare actual vs design ACH

### 3.2 Occupancy Detection

**Infer occupancy patterns from CO2 data**

#### Usage Example

```python
from core.analytics.special import detect_occupancy_from_co2

pattern = detect_occupancy_from_co2(
    co2_series,
    occupied_threshold=600.0  # ppm
)

print(f"Occupancy rate: {pattern.occupancy_rate * 100:.1f}%")
print(f"Typical hours: {pattern.typical_occupancy_hours}")
print(f"Avg CO2 occupied: {pattern.avg_co2_occupied:.0f} ppm")
print(f"Avg CO2 unoccupied: {pattern.avg_co2_unoccupied:.0f} ppm")
```

### Demo

```bash
cd clean/
python examples/demo_ventilation_rate_prediction.py
```

---

## Integration with Analysis Pipeline

### Example: Complete Analysis with Recommendations

```python
from core.analytics.engine import AnalysisEngine
from core.analytics.correlations import ClimateCorrelator
from core.analytics.recommendations import RecommendationEngine
from core.analytics.special import predict_ventilation_rate_from_co2_decay

# 1. Run standard compliance analysis
engine = AnalysisEngine()
room_analysis = engine.analyze_room(room, tests=tests)

# 2. Calculate climate correlations
correlator = ClimateCorrelator()
correlations = correlator.correlate_with_climate(
    room.time_series_data['temperature'],
    climate_df
)

# 3. Generate smart recommendations
rec_engine = RecommendationEngine()
recommendations = rec_engine.generate_recommendations(
    room_analysis,
    climate_df
)

# 4. Predict ventilation rate (if CO2 data available)
if 'co2' in room.time_series_data:
    ach_result = predict_ventilation_rate_from_co2_decay(
        room.time_series_data['co2']
    )
    if ach_result:
        print(f"Estimated ACH: {ach_result.ach:.2f}")

# 5. Display prioritized recommendations
for rec in recommendations:
    print(f"{rec.priority.value}: {rec.title}")
```

---

## Architecture

```
clean/core/analytics/
├── correlations/
│   ├── climate_correlator.py      # Main correlation engine
│   ├── weather_analyzer.py        # Weather statistics during violations
│   └── __init__.py
│
├── recommendations/
│   ├── recommendation_engine.py   # Main recommendation engine
│   ├── solar_shading_analyzer.py  # Solar gain detection
│   ├── insulation_analyzer.py     # Insulation need detection
│   ├── ventilation_optimizer.py   # Ventilation recommendations
│   └── __init__.py
│
└── special/
    ├── ventilation_rate_predictor.py  # ACH from CO2 decay
    ├── occupancy_detector.py          # Occupancy from CO2
    └── __init__.py
```

---

## Best Practices

### 1. Climate Correlations

- **Require sufficient data**: Minimum 100-200 data points for reliable correlations
- **Check p-values**: p < 0.05 for statistical significance
- **Use appropriate method**: Pearson for linear, Spearman for monotonic
- **Interpret carefully**: Correlation ≠ causation, but provides evidence

### 2. Smart Recommendations

- **Always provide climate data** when available for better recommendations
- **Trust the priority system**: Critical/High recommendations are evidence-based
- **Review evidence**: Check correlation values and statistics in evidence field
- **Combine multiple sources**: Use recommendations alongside expert judgment

### 3. Ventilation Rate Prediction

- **Look for clear decay periods**: R² > 0.7 indicates good fit
- **Use multiple periods**: Average from multiple decay events for accuracy
- **Check confidence intervals**: Wide intervals = less reliable estimate
- **Verify with known values**: If available, compare to design ACH

---

## Testing

Run the comprehensive test suite:

```bash
cd clean/
python -m pytest tests/test_climate_correlations.py
python -m pytest tests/test_recommendations.py
python -m pytest tests/test_ventilation_rate.py
```

---

## References

### Scientific Basis

1. **Climate Correlations**
   - Pearson correlation for linear relationships
   - Point-biserial correlation for dichotomous variables
   - Cohen's d for effect size estimation

2. **Ventilation Rate**
   - Exponential decay model: Sherman (1990), "Tracer-gas techniques for measuring ventilation in a single zone"
   - ASTM E741 - Standard Test Method for Determining Air Change in a Single Zone

3. **CO2-based Analysis**
   - ASHRAE 62.1 - Ventilation for Acceptable Indoor Air Quality
   - EN 16798-1 - Energy performance of buildings — Indoor environmental quality

---

## Migration from Old Infrastructure

The new modules in `clean/` replace and enhance:

- `src/core/analytics/ieq/library/correlations/` → `clean/core/analytics/correlations/`
- `src/core/analytics/smart_recommendations_service.py` → `clean/core/analytics/recommendations/`
- New: `clean/core/analytics/special/` (no equivalent in old infrastructure)

### Key Improvements

✓ **Type-safe**: Full Pydantic models and dataclasses
✓ **Modular**: Single responsibility per analyzer
✓ **Testable**: Pure functions, no side effects
✓ **Documented**: Comprehensive docstrings and examples
✓ **Scientific**: References to standards and methods

---

## Future Enhancements

Planned additions:

1. **Thermal Mass Analysis**: Detect thermal inertia from temperature lag
2. **HVAC Fingerprinting**: Identify system operation from parameter patterns
3. **Anomaly Detection**: Identify unusual patterns in time series
4. **Predictive Modeling**: Forecast future conditions based on trends
5. **Multi-parameter Correlations**: Cross-correlation matrices

---

## Support

For questions or issues:
- Review examples in `clean/examples/`
- Check docstrings in module files
- Run demos to see expected output
- Consult this documentation

---

*Last updated: 2025-01-20*
