

# Building Performance Evaluation Guide

## What This System Does

This system **evaluates how well buildings are insulated** and **recommends specific improvements** by:

1. **Estimating thermal parameters** (R_env, C_in) from temperature and energy consumption data
2. **Benchmarking** against building standards
3. **Identifying problems**: poor insulation, inefficient HVAC, overheating, etc.
4. **Recommending solutions**: better insulation, solar shading, heat pump, solar PV, etc.
5. **Quantifying savings**: energy reduction, cost savings, CO₂ reduction, payback periods

## The Formula in Action

```
T_out - T_in = R_env * (C_in * dT_in/dt - Q_in)

Where Q_in = Heating Power + Electricity (heat fraction) + Solar Gains
```

By analyzing how indoor temperature responds to:
- Outdoor temperature changes
- Heating input
- Internal gains

We can determine:
- **R_env**: How well the building resists heat loss (insulation quality)
- **C_in**: How much thermal mass the building has (temperature stability)

## Quick Start

### 1. Prepare Your Data

You need:
- Indoor temperature (T_in) - hourly or better
- Outdoor temperature (T_out) - hourly or better
- Heating consumption (kWh or W) - district heating, gas, electric
- Electricity consumption (kWh or W)
- Building floor area (m²)

**Minimum period**: 7 days
**Recommended**: 30 days
**Optimal**: Full heating season

### 2. Run the Evaluation

```python
from core.analytics.recommendations.building_performance_evaluator import (
    BuildingPerformanceEvaluator,
    BuildingType
)

# Initialize
evaluator = BuildingPerformanceEvaluator(
    building_type=BuildingType.RESIDENTIAL_DETACHED,
    floor_area_m2=150,
    energy_cost_per_kwh=0.15,  # Your energy price
    co2_per_kwh_heating=0.25,   # Your heating CO2 factor
    co2_per_kwh_electricity=0.40
)

# Step 1: Estimate thermal parameters
thermal_params = evaluator.estimate_thermal_parameters(
    T_in=indoor_temps,           # Array of indoor temps
    T_out=outdoor_temps,         # Array of outdoor temps
    heating_power=heating_watts, # Array of heating power
    electricity_power=elec_watts,# Array of electricity power
    dt=1.0,                      # Time step (1 hour)
    method='nonlinear'
)

# Step 2: Evaluate performance and get recommendations
report = evaluator.evaluate_performance(
    thermal_params=thermal_params,
    T_in=indoor_temps,
    T_out=outdoor_temps,
    heating_energy_kwh=annual_heating_kwh,
    electricity_kwh=annual_electricity_kwh
)

# Step 3: Print the report
evaluator.print_report(report)
```

### 3. Understand the Results

The report tells you:

#### **Thermal Resistance (R_env)**
```
Rating: Poor / Average / Good / Excellent
```
- **Excellent (>0.020)**: Modern, well-insulated building
- **Good (0.012-0.020)**: Above average insulation
- **Average (0.008-0.012)**: Typical existing building
- **Poor (<0.008)**: Needs insulation improvement! 🚨

#### **Thermal Capacitance (C_in)**
```
Rating: Heavy / Medium / Light construction
```
- **Heavy**: Good thermal mass, stable temperatures (concrete, brick)
- **Medium**: Moderate thermal mass
- **Light**: Low thermal mass, quick temperature changes (wood frame)

#### **Heating System Efficiency (COP)**
```
COP = 0.75 → Old inefficient boiler
COP = 0.95 → Modern condensing boiler
COP = 3.5 → Heat pump
```

Lower COP = more expensive to run!

## What You Get: Specific Recommendations

### Example Output

```
RECOMMENDED INTERVENTIONS
================================================================================

1. INSULATION WALLS
   Priority: 1 (1=highest)
   Improve wall and roof insulation to reduce heat loss. Current thermal
   resistance is poor.
   Estimated Cost: €12,000 (€80/m²)
   Energy Savings: 35%
   CO₂ Reduction: 2,450 kg/year
   Simple Payback: 6.2 years
   Additional Benefits:
     • Improved thermal comfort
     • Reduced temperature fluctuations
     • Lower peak heating demand
     • Increased property value

2. HVAC UPGRADE
   Priority: 1
   Upgrade heating system. Current efficiency (COP: 0.75) is below
   recommended (0.92).
   Estimated Cost: €7,500 (€50/m²)
   Energy Savings: 25%
   CO₂ Reduction: 1,750 kg/year
   Simple Payback: 4.8 years

3. HEAT PUMP
   Priority: 2
   Install air-source or ground-source heat pump system.
   Estimated Cost: €15,000 (€100/m²)
   Energy Savings: 45%
   CO₂ Reduction: 4,200 kg/year
   Simple Payback: 8.5 years
   Additional Benefits:
     • Renewable heating source
     • Cooling capability in summer
     • Very low carbon emissions
     • Government incentives may apply

SUMMARY OF TOP 3 INTERVENTIONS
--------------------------------------------------------------------------------
Total Energy Savings: 5,040 kWh/year (35%)
Total Cost Savings: €756/year
Total CO₂ Reduction: 4,200 kg/year
```

## Use Cases

### 1. **Energy Audit**

```python
# Evaluate a building's insulation quality
report = evaluator.evaluate_performance(...)

if report.r_env_rating == "Poor":
    print(f"⚠️ POOR INSULATION DETECTED")
    print(f"Heat loss: {report.heat_loss_coefficient:.0f} W/K")
    print(f"Recommended: {report.interventions[0].description}")
    print(f"Savings: {report.total_savings_potential_cost:.0f} €/year")
```

### 2. **Retrofit Planning**

```python
# Compare interventions
for intervention in report.interventions[:5]:
    print(f"{intervention.intervention_type.value}:")
    print(f"  Cost: €{intervention.estimated_cost_per_m2 * floor_area:.0f}")
    print(f"  Savings: {intervention.estimated_savings_percent}%")
    print(f"  Payback: {intervention.payback_years:.1f} years")
```

### 3. **Portfolio Benchmarking**

```python
# Evaluate multiple buildings
buildings = [...]

for building in buildings:
    report = evaluate_building(building)

    if report.r_env_per_m2 < 0.010:  # Below standard
        priority_buildings.append({
            'id': building.id,
            'r_env': report.r_env_per_m2,
            'savings_potential': report.total_savings_potential_cost,
            'payback': report.interventions[0].payback_years
        })

# Sort by savings potential
priority_buildings.sort(key=lambda x: -x['savings_potential'])
```

### 4. **Sustainability Reporting**

```python
report = evaluator.evaluate_performance(...)

print(f"Current CO₂ emissions: {report.current_co2_kg_per_year:.0f} kg/year")
print(f"Potential reduction: {report.potential_co2_reduction_kg_per_year:.0f} kg/year")
print(f"Solar PV potential: {report.renewable_energy_potential['solar_pv_kwh_per_year']:.0f} kWh/year")
```

## Interpreting Results

### Good Building Example

```
R_env: 0.022 K/W (Excellent)
C_in: 6.0e6 J/K (Medium-Heavy)
Heating COP: 3.5 (Heat pump)
Annual heating: 45 kWh/m²
```
**Diagnosis**: Well-performing building, minimal intervention needed.
**Recommendation**: Consider solar PV for further sustainability.

### Poor Insulation Example

```
R_env: 0.006 K/W (Poor) ⚠️
C_in: 4.0e6 J/K (Medium)
Heating COP: 0.75 (Old boiler)
Annual heating: 180 kWh/m²
```
**Diagnosis**: Major heat loss through envelope, inefficient heating.
**Recommendations**:
1. **Priority 1**: Improve insulation (35% savings)
2. **Priority 1**: Upgrade HVAC (25% savings)
3. Combined savings: ~50% energy reduction

### Old HVAC Example

```
R_env: 0.015 K/W (Good)
C_in: 8.0e6 J/K (Heavy)
Heating COP: 0.65 (Very old system) ⚠️
Annual heating: 120 kWh/m²
```
**Diagnosis**: Good building fabric, but wasting energy with old system.
**Recommendation**: Heat pump upgrade (45% savings, 8-year payback)

## Building Types and Benchmarks

The system includes benchmarks for:

- **Residential Detached**: Single-family homes
- **Residential Apartment**: Multi-family buildings
- **Office Small**: < 1000 m²
- **Office Large**: > 1000 m²
- **School**: Educational buildings
- **Retail**: Commercial spaces
- **Warehouse**: Industrial/storage
- **Healthcare**: Medical facilities

Each type has specific R_env and C_in benchmarks.

## Intervention Types

The system can recommend:

| Intervention | Typical Savings | Priority For |
|--------------|-----------------|--------------|
| **Insulation (walls/roof)** | 20-40% | Poor R_env |
| **Window upgrades** | 10-20% | Old windows, poor R_env |
| **HVAC upgrade** | 20-30% | Low COP |
| **Heat pump** | 40-60% | Fossil fuel heating |
| **Solar shading** | 5-15% | Overheating issues |
| **Solar PV** | 30-80% electricity | Good roof area |
| **Thermal mass** | 5-10% | Light construction |
| **Air sealing** | 10-20% | Drafty buildings |
| **Ventilation HRV** | 15-25% | High ventilation losses |

## Data Quality Tips

### Good Data
✅ Consistent hourly measurements
✅ Synchronized timestamps
✅ Covers heating season
✅ No major sensor errors
✅ Calibrated sensors (±0.5°C)

### Problem Data
❌ Missing values (>10%)
❌ Outliers not removed
❌ Summertime only (no heating)
❌ Uncalibrated sensors
❌ Time synchronization issues

### Handling Solar Gains

If you don't have measured solar data:

```python
# Simple estimation
def estimate_solar_gains(hour_of_day, is_clear_sky=True, window_area_m2=20):
    """Rough solar gain estimate."""
    if 6 <= hour_of_day <= 18:
        base = 200 * window_area_m2  # W
        peak_factor = np.sin(np.pi * (hour_of_day - 6) / 12)
        return base * peak_factor * (1.0 if is_clear_sky else 0.3)
    return 0

solar_gains = np.array([estimate_solar_gains(h) for h in hours])

# Use in evaluation
thermal_params = evaluator.estimate_thermal_parameters(
    ...,
    solar_gains=solar_gains  # Add estimated solar
)
```

## Advanced: Custom Interventions

You can add custom interventions:

```python
from core.analytics.recommendations.building_performance_evaluator import (
    Intervention,
    InterventionType
)

custom_intervention = Intervention(
    intervention_type=InterventionType.INSULATION_WALLS,
    priority=1,
    description="Custom insulation package for heritage building",
    estimated_cost_per_m2=120,  # Higher due to special requirements
    estimated_savings_percent=30,
    estimated_r_env_improvement=0.008,
    payback_years=9.5,
    co2_reduction_kg_per_year=2100,
    additional_benefits=[
        "Preserves historic facade",
        "Internal insulation approach",
        "Improved acoustics"
    ]
)
```

## Running the Demo

```bash
# Full demonstration with synthetic data
python examples/demo_building_performance_evaluation.py
```

This shows:
1. Complete evaluation workflow
2. Scenario comparison (poor insulation vs old HVAC vs good building)
3. Intervention ranking and cumulative analysis
4. Payback calculations

## Integration with Existing Systems

### With Your Climate Analytics

```python
# After analyzing climate compliance
if cold_compliance_rate < 70:  # Poor cold performance

    # Run thermal evaluation
    report = evaluator.evaluate_performance(...)

    if report.r_env_rating in ["Poor", "Average"]:
        recommendation = f"Poor insulation (R={report.thermal_params.R_env:.4f}) " \
                        f"is causing cold discomfort. " \
                        f"Recommended: {report.interventions[0].description}"
```

### Export to Reports

```python
# Generate structured data for reports
report_data = {
    'building_id': building_id,
    'thermal_performance': {
        'r_env': report.thermal_params.R_env,
        'r_env_rating': report.r_env_rating,
        'c_in': report.thermal_params.C_in,
        'heat_loss_w_per_k': report.heat_loss_coefficient
    },
    'energy_performance': {
        'heating_kwh_per_m2': report.annual_heating_kwh / report.floor_area_m2,
        'electricity_kwh_per_m2': report.annual_electricity_kwh / report.floor_area_m2,
        'heating_cop': report.heating_cop_estimated
    },
    'recommendations': [
        {
            'type': i.intervention_type.value,
            'priority': i.priority,
            'savings_percent': i.estimated_savings_percent,
            'cost': i.estimated_cost_per_m2 * report.floor_area_m2,
            'payback_years': i.payback_years
        }
        for i in report.interventions[:3]
    ],
    'savings_potential': {
        'energy_kwh_per_year': report.total_savings_potential_kwh,
        'cost_per_year': report.total_savings_potential_cost,
        'co2_kg_per_year': report.potential_co2_reduction_kg_per_year
    }
}
```

## Troubleshooting

### "R_env estimate is too low"
→ Check if heating power includes losses (e.g., boiler inefficiency)
→ Verify temperature sensors are calibrated
→ Check for missing heat sources (solar, occupancy)

### "Very wide confidence intervals"
→ Collect more data (longer period)
→ Ensure data covers temperature variations
→ Check for measurement noise

### "COP estimate seems wrong"
→ Verify heating power units (W vs kW)
→ Check if measuring thermal output vs electrical input
→ Consider distribution losses

### "Interventions not appropriate"
→ Verify building_type matches actual building
→ Check floor_area_m2 is correct
→ Review energy_cost_per_kwh and CO2 factors

## Files

```
core/analytics/recommendations/
├── building_performance_evaluator.py  (Main system - 900+ lines)
├── thermal_parameter_estimator.py     (Parameter estimation)
└── thermal_diagnostics.py             (Visualization tools)

examples/
└── demo_building_performance_evaluation.py  (Complete demo)

docs/
├── BUILDING_PERFORMANCE_GUIDE.md  (This file)
└── thermal_parameter_estimation.md (Technical details)
```

## Summary

**Input**: Temperature data + Energy consumption
**Output**: Thermal parameters + Specific recommendations
**Result**: Know exactly what needs fixing and how much you'll save

The system bridges the gap between **theoretical building physics** and **practical energy improvements** by quantifying insulation quality, HVAC efficiency, and renewable potential in real buildings.

---

**Next Steps**: Run the demo, then adapt it to your actual building data!
