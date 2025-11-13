# Thermal Comfort Cost Analysis - Implementation Summary

## Overview

This implementation adds comprehensive cost analysis capabilities for thermal comfort optimization based on EN 16798-1 standards. The system calculates the exact cost per delta T (temperature differential) and simulates potential savings by optimizing temperature control to the lower boundaries of comfort categories.

## What Was Added

### 1. Climate Data (New Files)
Climate data has been added for all sample buildings to enable outdoor temperature correlation:

- `data/building_a/climate_data.csv` - Office tower climate data
- `data/building_b/climate_data.csv` - Retail/mixed building climate data  
- `data/building_c/climate_data.csv` - School building climate data

**Columns:**
- `timestamp` - Hourly timestamps
- `outdoor_temperature` - Outdoor temperature (°C)
- `outdoor_humidity` - Outdoor relative humidity (%)
- `solar_radiation` - Solar radiation (W/m²)

### 2. Energy Consumption Data (New Files)
Energy data enables cost calculations for heating and electricity:

- `data/building_a/energy_data.csv`
- `data/building_b/energy_data.csv`
- `data/building_c/energy_data.csv`

**Columns:**
- `timestamp` - Hourly timestamps
- `district_heating_kwh` - District heating consumption (kWh)
- `pv_production_kwh` - Solar PV electricity production (kWh)
- `grid_electricity_kwh` - Grid electricity consumption (kWh)

### 3. Thermal Comfort Cost Calculator (New Module)
**File:** `core/analytics/calculators/thermal_comfort_cost_calculator.py`

This module provides comprehensive cost analysis for thermal comfort:

#### Key Classes:

**`EnergyCosts`** - Energy pricing configuration
- District heating cost per kWh
- Electricity cost per kWh
- PV feed-in tariff

**`ThermalComfortCostResult`** - Detailed cost analysis results
- Temperature statistics (indoor/outdoor averages, comfort bounds)
- Energy consumption totals
- Cost breakdown (heating, electricity, PV revenue)
- Efficiency metrics (cost per delta T, cost per degree-hour)
- Comfort compliance metrics

**`OptimizationResult`** - Cost optimization analysis
- Original vs. optimized performance comparison
- Cost savings calculations
- Temperature reduction recommendations
- Feasibility scoring
- ROI estimation

**`ThermalComfortCostCalculator`** - Main calculator class

Key methods:
- `calculate_comfort_cost()` - Calculate cost for maintaining comfort in a specific EN16798 category
- `optimize_to_lower_boundary()` - Simulate savings by targeting lower comfort boundary
- `compare_categories()` - Compare costs across all EN16798 categories

### 4. Demonstration Script (New File)
**File:** `examples/demo_thermal_comfort_cost_optimization.py`

Comprehensive example showing:
- Loading climate, energy, and room data
- Cost analysis per room and building
- Optimization recommendations
- Portfolio-level summaries

## How It Works

### Cost Calculation Methodology

1. **Temperature Analysis:**
   - Compares indoor temperatures against EN16798 category boundaries
   - Calculates comfort compliance rates
   - Identifies hours below/above comfort range

2. **Energy Cost Calculation:**
   ```
   Heating Cost = Total Heating (kWh) × Heating Rate (€/kWh)
   Electricity Cost = (Grid Usage - PV Production) × Electricity Rate
   PV Revenue = Excess PV × Feed-in Tariff
   Total Cost = Heating Cost + Electricity Cost - PV Revenue
   ```

3. **Efficiency Metrics:**
   - **Cost per Delta T:** Total cost divided by average temperature differential (indoor - outdoor)
   - **Heating per Delta T:** Heating consumption per degree of temperature differential
   - **Cost per Degree-Hour:** Cost per degree of comfort above the lower boundary

### Optimization Strategy

The optimizer simulates reducing setpoints to the **lower boundary** of the current EN16798 category:

1. **Calculate Reduction Potential:**
   - Current average temperature minus lower comfort boundary
   - Example: If current = 21.0°C and lower boundary = 20.0°C, potential = 1.0°C

2. **Estimate Energy Savings:**
   - Rule of thumb: 6% heating reduction per 1°C setpoint reduction
   - Conservative estimate based on building physics

3. **Calculate Cost Savings:**
   - Apply reduction to heating costs
   - Account for minor electricity savings (fans/pumps)
   - Preserve PV production/revenue

4. **Feasibility Assessment:**
   - Scores 0-100 based on:
     - Size of temperature reduction (larger = harder)
     - Current comfort compliance (lower = riskier)
     - Season (cooling harder than heating)

5. **ROI Calculation:**
   - Assumes €500 implementation cost per zone (controls upgrade)
   - Calculates payback period in months

## Key Results from Demo

The demonstration analysis shows:

### Building B (Retail/Mixed)
- **Current Cost:** €19,921.72 (for 2-day period)
- **Optimized Cost:** €19,422.93
- **Savings:** €498.79 (2.5%)
- **Best opportunities:**
  - First Floor Storage: €129.02 savings with 2.1°C reduction (Cat III)
  - Ground Floor shops: ~€93 each with 1.0°C reduction

### Building C (School)
- **Current Cost:** €9,896.28
- **Optimized Cost:** €9,666.90
- **Savings:** €229.38 (2.3%)
- **Best opportunities:**
  - Classroom 2: €60.90 savings with 1.2°C reduction
  - All classrooms show optimization potential

### Portfolio Total
- **Current:** €29,818.00
- **Optimized:** €29,089.83
- **Total Savings:** €728.17 (2.4%)
- **Extrapolated Annual Savings:** ~€133,000/year (based on 2-day sample)

## Usage Example

```python
from pathlib import Path
import pandas as pd
from core.analytics.calculators.thermal_comfort_cost_calculator import (
    ThermalComfortCostCalculator,
    EnergyCosts,
    calculate_cost_per_room
)
from core.domain.enums.en16798_category import EN16798Category

# Define energy costs
energy_costs = EnergyCosts(
    district_heating_cost_per_kwh=0.12,  # €/kWh
    electricity_cost_per_kwh=0.30,       # €/kWh
    pv_feed_in_tariff=0.08               # €/kWh
)

# Load data
room_data = pd.read_csv('data/building_b/first_floor_office.csv', 
                        index_col='timestamp', parse_dates=True)
climate_data = pd.read_csv('data/building_b/climate_data.csv',
                           index_col='timestamp', parse_dates=True)
energy_data = pd.read_csv('data/building_b/energy_data.csv',
                         index_col='timestamp', parse_dates=True)

# Calculate costs and optimization
cost_result, opt_result = calculate_cost_per_room(
    room_data=room_data,
    climate_data=climate_data,
    energy_data=energy_data,
    energy_costs=energy_costs,
    room_category=EN16798Category.CATEGORY_II,
    season="heating"
)

# Access results
print(f"Current cost: €{cost_result.total_energy_cost:.2f}")
print(f"Cost per delta T: €{cost_result.cost_per_delta_t:.3f}/°C")
print(f"Potential savings: €{opt_result.cost_savings:.2f}")
print(f"Temperature reduction: {opt_result.temp_reduction:.1f}°C")
```

## Key Insights

### 1. Cost Per Delta T
This metric shows the cost to maintain each degree of temperature differential from outdoor conditions:
- Typical range: €100-200/°C for the sample period
- Higher values indicate less efficient buildings or systems
- Useful for comparing buildings and identifying poor performers

### 2. Lower Boundary Strategy
Operating at the lower comfort boundary maximizes energy savings while maintaining compliance:
- Category I: 21°C lower bound (high expectation)
- Category II: 20°C lower bound (normal expectation)
- Category III: 19°C lower bound (moderate expectation)

### 3. Feasibility Considerations
High feasibility (80-100):
- Small reductions (< 1°C)
- Currently high comfort compliance (> 95%)
- Heating season

Lower feasibility (50-70):
- Larger reductions (> 1.5°C)
- Already struggling with compliance (< 90%)
- May require additional measures

### 4. Room Type Optimization
Different room types have different optimization potential:
- **Storage rooms:** Highest potential (can use Category III, 19°C)
- **Offices:** Moderate potential (Category II, 20°C)
- **Server/Computer rooms:** Limited potential (Category I, 21°C)
- **Already optimized rooms:** Show 0°C reduction potential

## Integration Points

This cost analysis can be integrated with existing systems:

1. **EN16798 Compliance:** Uses existing EN16798Calculator for comfort boundaries
2. **Room Analysis:** Can be added to room-level analysis results
3. **Building Performance:** Complements existing building performance metrics
4. **Recommendations:** Cost-based recommendations can enhance the recommendation engine

## Next Steps

To extend this implementation:

1. **Add Cooling Season:** Implement cooling cost analysis (already supported in calculator)
2. **Adaptive Comfort:** Integrate outdoor running mean temperature for adaptive thresholds
3. **Multi-Period Analysis:** Analyze seasonal variations and annual totals
4. **Cost Optimization Service:** Create a service layer for automated optimization
5. **Reporting Integration:** Add cost metrics to HTML/PDF reports
6. **Real-time Optimization:** Connect to building management systems for live optimization

## Files Changed/Added

**New Files:**
- `data/building_a/climate_data.csv`
- `data/building_a/energy_data.csv`
- `data/building_b/climate_data.csv`
- `data/building_b/energy_data.csv`
- `data/building_c/climate_data.csv`
- `data/building_c/energy_data.csv`
- `core/analytics/calculators/thermal_comfort_cost_calculator.py`
- `examples/demo_thermal_comfort_cost_optimization.py`

**No existing files were modified** - this is a purely additive feature.

## Running the Demo

```bash
# Activate virtual environment
source .venv/bin/activate

# Run the demonstration
python examples/demo_thermal_comfort_cost_optimization.py
```

The demo will analyze all buildings with available data and provide detailed cost analysis and optimization recommendations.
