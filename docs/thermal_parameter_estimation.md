# Thermal Parameter Estimation

## Overview

This module implements parameter estimation for building thermal models using the heat transfer equation:

```
T_out - T_in = R_env * (C_in * dT_in/dt - Q_in)
```

### Parameters

- **T_out**: Outdoor temperature (°C)
- **T_in**: Indoor temperature (°C)
- **R_env**: Thermal resistance of building envelope (K/W) - **to be estimated**
- **C_in**: Thermal capacitance of building interior (J/K or Wh/K) - **to be estimated**
- **dT_in/dt**: Rate of change of indoor temperature (°C/h or K/s)
- **Q_in**: Internal heat gains from occupants, equipment, solar radiation (W)

## Physical Interpretation

### Thermal Resistance (R_env)
- Represents the building envelope's ability to resist heat flow
- Higher values indicate better insulation
- Typical range: 0.001 - 0.1 K/W (depends on building size and insulation quality)
- Units: K/W (temperature difference per unit heat flow)

### Thermal Capacitance (C_in)
- Represents the building's ability to store thermal energy
- Related to building mass, construction materials, and furnishings
- Higher values mean slower temperature changes
- Typical range: 1×10⁵ - 1×10⁸ J/K (depends on building size and mass)
- Units: J/K (energy per unit temperature change)

### Heat Balance Equation

The equation represents energy conservation:
```
Heat loss through envelope = Thermal storage + Internal gains
(T_in - T_out) / R_env = C_in * dT_in/dt - Q_in
```

Rearranging:
```
T_out - T_in = R_env * (C_in * dT_in/dt - Q_in)
```

## Implementation

### Core Module: `thermal_parameter_estimator.py`

Main class: `ThermalParameterEstimator`

#### Key Features

1. **Two Estimation Methods**:
   - **Linear (Grid Search)**: Fast but less accurate, searches over C_in range
   - **Nonlinear (L-BFGS-B)**: More accurate, optimizes both parameters simultaneously

2. **Automatic Derivative Computation**:
   - Computes dT_in/dt from temperature time series
   - Supports both uniform and non-uniform time steps
   - Uses central differences for accuracy

3. **Uncertainty Quantification**:
   - Standard errors for both parameters
   - 95% confidence intervals using t-distribution
   - Covariance matrix estimation via Hessian

4. **Model Validation**:
   - RMSE, MAE, R² metrics
   - Residual analysis
   - Train-test split support

### Usage Example

```python
from core.analytics.recommendations.thermal_parameter_estimator import (
    ThermalParameterEstimator
)
import numpy as np

# Your data
T_in = np.array([...])      # Indoor temperature (°C)
T_out = np.array([...])     # Outdoor temperature (°C)
Q_in = np.array([...])      # Internal heat gains (W)

# Create estimator
estimator = ThermalParameterEstimator(time_unit='hour')

# Fit parameters
params = estimator.fit(
    T_in=T_in,
    T_out=T_out,
    Q_in=Q_in,
    dt=1.0,  # 1 hour time step
    method='nonlinear',
    initial_guess=(0.01, 1e6)  # (R_env, C_in)
)

# View results
estimator.print_summary()

# Results include:
print(f"R_env: {params.R_env:.6f} ± {params.R_env_std:.6f} K/W")
print(f"C_in: {params.C_in:.4e} ± {params.C_in_std:.4e} J/K")
print(f"RMSE: {params.rmse:.4f} °C")
print(f"R²: {params.r_squared:.4f}")
```

### Diagnostic Tools: `thermal_diagnostics.py`

Class: `ThermalDiagnostics`

#### Available Plots

1. **Fit Diagnostics** (6 subplots):
   - Actual vs predicted outdoor temperature
   - Residuals over time
   - Scatter plot (actual vs predicted)
   - Residual histogram with normal overlay
   - Q-Q plot for normality check
   - Residual autocorrelation

2. **Parameter Uncertainty**:
   - Bar plots with error bars
   - 95% confidence intervals
   - Visual representation of estimation quality

3. **Thermal Response Components**:
   - Heat balance breakdown
   - Temperature dynamics
   - Internal heat gains visualization

#### Usage Example

```python
from core.analytics.recommendations.thermal_diagnostics import ThermalDiagnostics

# After fitting the model
diagnostics = ThermalDiagnostics(estimator)

# Compute derivative for visualization
dT_in_dt = estimator.compute_temperature_derivative(T_in, dt=1.0)

# Generate all diagnostic plots
diagnostics.generate_report(
    T_in=T_in,
    T_out=T_out,
    Q_in=Q_in,
    dT_in_dt=dT_in_dt,
    save_path='./results/building_thermal_analysis'
)
```

## Data Requirements

### Minimum Requirements

1. **Time series data** with consistent sampling:
   - Indoor temperature (T_in)
   - Outdoor temperature (T_out)
   - Internal heat gains (Q_in) or estimates

2. **Sampling frequency**:
   - Recommended: 15-60 minutes
   - Minimum: 1 hour
   - Maximum: Real-time (seconds) with proper time unit setting

3. **Duration**:
   - Minimum: 3-7 days for stable estimates
   - Recommended: 2-4 weeks for better statistics
   - Longer periods improve accuracy

### Data Quality Considerations

1. **Remove outliers** before fitting
2. **Handle missing data** appropriately
3. **Ensure measurements are synchronized**
4. **Account for sensor accuracy** (typically ±0.5°C for temperature)

## Example: Synthetic Data Demo

See `examples/thermal_parameter_estimation_demo.py` for comprehensive demonstrations:

```bash
python examples/thermal_parameter_estimation_demo.py
```

This demo includes:
1. Basic parameter estimation with known true values
2. Comparison of linear vs nonlinear methods
3. Train-test validation
4. Comprehensive diagnostic visualizations
5. Sensitivity analysis to measurement noise

## Mathematical Details

### Problem Formulation

Given measurements (T_in, T_out, Q_in) over time, find (R_env, C_in) that minimize:

```
∑ [(T_out[i] - T_in[i]) - R_env * (C_in * dT_in/dt[i] - Q_in[i])]²
```

### Nonlinear Optimization

Uses scipy's L-BFGS-B optimizer with bounds:
- R_env: [1×10⁻⁶, 1.0] K/W
- C_in: [1×10³, 1×10⁸] J/K

### Uncertainty Estimation

Standard errors computed from the inverse Hessian at the optimum:

```
Cov(θ) = σ² * (J^T J)^(-1)
```

Where:
- θ = [R_env, C_in]
- σ² = residual variance
- J = Jacobian matrix (numerical approximation)

95% confidence intervals:
```
CI = θ ± t_(α/2, df) * SE(θ)
```

## Validation Metrics

### Root Mean Square Error (RMSE)
```
RMSE = √(∑(T_out - T_out_pred)² / n)
```
Typical range: 0.2 - 2.0 °C (depending on data quality)

### R-squared (R²)
```
R² = 1 - SS_res / SS_tot
```
Target: R² > 0.7 for good fit

### Residual Analysis
- Check for normality (Q-Q plot)
- Check for autocorrelation (should be minimal)
- Check for heteroscedasticity (constant variance)

## Interpreting Results

### Good Fit Indicators
- ✓ R² > 0.7
- ✓ RMSE < 1.0 °C
- ✓ Residuals approximately normal
- ✓ Low autocorrelation in residuals
- ✓ Narrow confidence intervals (<20% of estimate)

### Poor Fit Indicators
- ✗ R² < 0.5
- ✗ RMSE > 2.0 °C
- ✗ Systematic patterns in residuals
- ✗ High autocorrelation
- ✗ Very wide confidence intervals

### Common Issues

1. **Wide confidence intervals for C_in**:
   - Insufficient temperature variation
   - Short data period
   - High measurement noise
   - Solution: Collect more data, especially periods with changing temperatures

2. **Biased R_env estimates**:
   - Inaccurate Q_in estimates
   - Missing heat sources/sinks
   - Solution: Improve Q_in modeling, include all heat sources

3. **Poor fit (low R²)**:
   - Model too simple for the building
   - Non-linearities not captured
   - External factors not included
   - Solution: Consider more complex models or additional predictors

## Integration with Building Analytics

### Use Cases

1. **Energy Audit**:
   - Quantify insulation effectiveness
   - Identify buildings needing retrofits
   - Estimate energy savings potential

2. **Model Predictive Control**:
   - Use estimated parameters for temperature forecasting
   - Optimize HVAC scheduling
   - Reduce energy consumption

3. **Anomaly Detection**:
   - Monitor parameter drift over time
   - Detect equipment degradation
   - Identify envelope damage

4. **Benchmarking**:
   - Compare buildings in portfolio
   - Normalize for weather and usage patterns
   - Prioritize retrofit investments

### Integration Example

```python
from core.analytics.recommendations.insulation_analyzer import InsulationAnalyzer
from core.analytics.recommendations.thermal_parameter_estimator import (
    ThermalParameterEstimator
)

# Fit thermal model
estimator = ThermalParameterEstimator(time_unit='hour')
params = estimator.fit(T_in, T_out, Q_in, dt=1.0)

# Use R_env to inform insulation analysis
# Lower R_env indicates poor insulation
insulation_severity = 1.0 / (params.R_env * 100)  # Normalized severity

# Check if R_env is below acceptable threshold
R_env_threshold = 0.01  # K/W (example threshold)
needs_insulation = params.R_env < R_env_threshold

print(f"Thermal Resistance: {params.R_env:.6f} K/W")
print(f"Needs Insulation: {needs_insulation}")
print(f"Estimated Energy Loss: {(T_in.mean() - T_out.mean()) / params.R_env:.0f} W")
```

## References

1. **Building Physics**:
   - Clarke, J. A. (2001). Energy Simulation in Building Design
   - Incropera, F. P., & DeWitt, D. P. (2002). Fundamentals of Heat and Mass Transfer

2. **Parameter Estimation**:
   - Ljung, L. (1999). System Identification: Theory for the User
   - Rabl, A. (1988). Parameter Estimation in Buildings

3. **Grey-box Modeling**:
   - Madsen, H., & Holst, J. (1995). Estimation of continuous-time models
   - Jiménez, M. J., & Madsen, H. (2008). Models for describing the thermal characteristics of building components

## Files

- `core/analytics/recommendations/thermal_parameter_estimator.py` - Main estimation class
- `core/analytics/recommendations/thermal_diagnostics.py` - Visualization and diagnostics
- `examples/thermal_parameter_estimation_demo.py` - Comprehensive demonstrations
- `test_thermal_formula.py` - Basic formula verification
- `docs/thermal_parameter_estimation.md` - This documentation

## Future Enhancements

Potential improvements:
1. Multi-zone models (multiple rooms)
2. Time-varying parameters (seasonal effects)
3. Bayesian estimation with priors
4. Online/recursive parameter updates
5. Integration with weather forecasts
6. Solar radiation modeling
7. HVAC system dynamics
8. Occupancy detection and estimation

## License

This implementation is part of the IEQ Analytics system and follows the project's GPL v3.0 license.
