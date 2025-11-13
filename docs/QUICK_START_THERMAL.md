# Quick Start: Thermal Parameter Estimation

## The Formula

```
T_out - T_in = R_env * (C_in * dT_in/dt - Q_in)
```

**What it means**: The temperature difference between outside and inside depends on:
- **R_env**: How well the building is insulated (K/W)
- **C_in**: How much heat the building can store (J/K)
- **dT_in/dt**: How fast the temperature is changing (°C/h)
- **Q_in**: Internal heat from people, equipment, sun (W)

## Installation

No installation needed! Just ensure you have:
```bash
pip install numpy scipy pandas matplotlib
```

## 30-Second Example

```python
from core.analytics.recommendations.thermal_parameter_estimator import ThermalParameterEstimator
import numpy as np

# Your data (replace with actual measurements)
T_in = np.array([20.1, 20.3, 20.5, 20.4, 20.2])   # Indoor °C
T_out = np.array([10.2, 11.1, 12.3, 13.1, 12.8])  # Outdoor °C
Q_in = np.array([1200, 1500, 1800, 1600, 1400])   # Heat gains (W)

# Estimate parameters (one line!)
estimator = ThermalParameterEstimator(time_unit='hour')
params = estimator.fit(T_in, T_out, Q_in, dt=1.0, method='nonlinear')

# Print results
estimator.print_summary()
```

## Test It Immediately

```bash
# Simple test (no dependencies)
python test_thermal_formula.py

# Full demo with visualizations
python examples/thermal_parameter_estimation_demo.py
```

## What Do the Results Mean?

### R_env (Thermal Resistance)
- **Higher is better** - means good insulation
- 0.020 K/W → Good insulation
- 0.010 K/W → Average insulation
- 0.005 K/W → Poor insulation, needs retrofit

### C_in (Thermal Capacitance)
- **Higher means slower temperature changes**
- 10⁷ J/K → Heavy building (concrete, brick)
- 10⁶ J/K → Medium building
- 10⁵ J/K → Light building (wood frame)

### RMSE (Root Mean Square Error)
- < 0.5 °C → Excellent fit
- 0.5 - 1.0 °C → Good fit
- 1.0 - 2.0 °C → Fair fit
- \> 2.0 °C → Poor fit, check data quality

### R² (Goodness of Fit)
- \> 0.85 → Excellent
- 0.70 - 0.85 → Good
- 0.50 - 0.70 → Fair
- < 0.50 → Poor

## Common Use Cases

### 1. Find Buildings That Need Insulation

```python
params = estimator.fit(T_in, T_out, Q_in, dt=1.0)

if params.R_env < 0.01:  # Threshold in K/W
    print("⚠️ Poor insulation detected!")
    print(f"Heat loss rate: {1/params.R_env:.0f} W/°C")
```

### 2. Estimate Energy Savings from Insulation

```python
# Before and after scenarios
R_before = 0.008  # Current poor insulation
R_after = 0.015   # With retrofit

# Average temperature difference
avg_delta_T = np.mean(T_in) - np.mean(T_out)  # e.g., 10°C

# Heat loss comparison
heat_loss_before = avg_delta_T / R_before  # W
heat_loss_after = avg_delta_T / R_after    # W
savings = heat_loss_before - heat_loss_after  # W

print(f"Energy savings: {savings:.0f} W = {savings*24/1000:.1f} kWh/day")
```

### 3. Predict Indoor Temperature

```python
def predict_temp_change(T_in_now, T_out, Q_in, hours):
    """How much will temperature change?"""
    R = params.R_env
    C = params.C_in

    heat_loss = (T_in_now - T_out) / R
    net_heat = Q_in - heat_loss
    change_rate = net_heat / C  # °C per second

    return change_rate * hours * 3600  # Total change

# Example: if heating turns off for 2 hours
temp_drop = predict_temp_change(
    T_in_now=21,    # Current indoor temp
    T_out=5,        # Outdoor temp
    Q_in=500,       # Reduced gains (no heating)
    hours=2
)
print(f"Temperature will drop by {abs(temp_drop):.1f}°C")
```

## Data Requirements

### Minimum

- **Duration**: 3-7 days of data
- **Frequency**: 1 sample per hour
- **Variables**: T_in, T_out, Q_in (or estimate Q_in)

### Recommended

- **Duration**: 2-4 weeks
- **Frequency**: 4 samples per hour (15 min)
- **Quality**: Remove obvious outliers, check sensor calibration

### Estimating Q_in (if unknown)

```python
# Simple occupancy-based model
def estimate_heat_gains(hour_of_day, is_weekend=False):
    """Estimate internal heat gains (W)."""
    base_load = 500  # Lights, equipment always on

    if is_weekend:
        if 8 <= hour_of_day <= 22:
            return base_load + 800  # People at home
        else:
            return base_load
    else:
        if 8 <= hour_of_day <= 17:
            return base_load + 1500  # Business hours
        elif 17 < hour_of_day <= 20:
            return base_load + 800   # Evening
        else:
            return base_load

# Apply to your data
Q_in = np.array([estimate_heat_gains(h) for h in hours_of_day])
```

## Troubleshooting

### "Wide confidence intervals"
→ **Solution**: Collect more data, especially periods with varying temperatures

### "Low R² (< 0.5)"
→ **Solution**: Check Q_in estimates, look for missing heat sources, verify sensor accuracy

### "Unrealistic parameter values"
→ **Solution**: Check time units (hour vs second), verify Q_in units (Watts), check for data quality issues

### "Negative R_env or C_in"
→ **Solution**: Data quality issue - check for sensor drift, time synchronization, or missing/corrupted data

## Visualizations

```python
from core.analytics.recommendations.thermal_diagnostics import ThermalDiagnostics

# After fitting
diagnostics = ThermalDiagnostics(estimator)
dT_in_dt = estimator.compute_temperature_derivative(T_in, dt=1.0)

# Generate all plots
diagnostics.generate_report(T_in, T_out, Q_in, dT_in_dt)
```

Creates:
1. ✅ Actual vs predicted comparison
2. ✅ Residual analysis
3. ✅ Parameter uncertainty bars
4. ✅ Thermal response breakdown
5. ✅ Statistical diagnostics (Q-Q plot, autocorrelation)

## Files

```
📁 Quick reference
   └── QUICK_START_THERMAL.md ← You are here

📁 Detailed docs
   └── docs/thermal_parameter_estimation.md

📁 Implementation
   ├── core/analytics/recommendations/thermal_parameter_estimator.py
   └── core/analytics/recommendations/thermal_diagnostics.py

📁 Examples & tests
   ├── examples/thermal_parameter_estimation_demo.py (full demo)
   └── test_thermal_formula.py (simple test)

📁 Summary
   └── THERMAL_ESTIMATION_SUMMARY.md
```

## Getting Help

1. **Run the demo**: `python examples/thermal_parameter_estimation_demo.py`
2. **Read the docs**: `docs/thermal_parameter_estimation.md`
3. **Check examples**: See demo file for 5 complete scenarios
4. **Verify installation**: `python test_thermal_formula.py`

## One-Line Summary

**Measure temperatures → Estimate R_env & C_in → Identify poor insulation → Predict energy savings** ✨

---

**Pro tip**: Start with the demo to see realistic examples, then adapt to your data structure.
