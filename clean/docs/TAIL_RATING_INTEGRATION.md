Move this file to docs/TAIL_RATING_INTEGRATION.md


# TAIL Rating Integration - Complete

## Overview

The TAIL (Thermal, Acoustic, Indoor Air Quality, Luminous) rating visualization has been successfully integrated into the IEQ Analytics toolbox. This implementation is inspired by the [TAIL Rating Scheme](https://github.com/asitkm76/TAILRatingScheme) developed by the ALDREN project.

## What is TAIL?

**TAIL** provides a comprehensive visual rating of building environmental quality using a circular chart with color-coded ratings:

- **T**hermal - Temperature comfort
- **A**coustic - Noise levels
- **I**ndoor Air Quality - CO2, humidity, PM2.5, VOCs, etc.
- **L**uminous - Lighting and daylight

### Rating Scale

| Rating | Roman | Color | Description | Compliance |
|--------|-------|-------|-------------|------------|
| 1 | I | 🟢 Green | Best quality | ≥ 95% |
| 2 | II | 🟡 Yellow | Good quality | 70-95% |
| 3 | III | 🟠 Orange | Fair quality | 50-70% |
| 4 | IV | 🔴 Red | Poor quality | < 50% |

## Implementation

### Files Created

1. **`core/reporting/charts/tail_circular_chart.py`** (419 lines)
   - `TAILCircularChart` - Main visualization class
   - `TAILRatingCalculator` - Rating calculation logic
   - `create_tail_chart_for_building()` - Convenience function

2. **`core/application/use_cases/generate_tail_chart.py`** (88 lines)
   - `GenerateTAILChartUseCase` - Application layer use case
   - Batch processing support for multiple buildings

3. **`core/cli/commands/tail.py`** (167 lines)
   - `hvx tail generate` - Generate charts from sessions
   - `hvx tail about` - Information about TAIL rating

4. **`examples/demo_tail_chart.py`** (180 lines)
   - Complete demo script with 4 demonstrations
   - Shows all features and use cases

### Architecture

```
CLI Commands
    ↓
Use Cases (Application Layer)
    ↓
TAIL Chart Generator (Infrastructure)
    ↓
Matplotlib Visualization
```

## Usage

### 1. CLI Command

Generate TAIL chart from saved analysis session:

```bash
# Basic usage
hvx tail generate --session my_analysis

# Custom output directory
hvx tail generate --session my_analysis --output charts/

# Learn about TAIL
hvx tail about
```

### 2. Python API

```python
from pathlib import Path
from core.reporting.charts.tail_circular_chart import TAILCircularChart

# Create chart
chart = TAILCircularChart(figsize=(10, 10))

fig = chart.create(
    overall_rating=2,      # Yellow - Good
    thermal_rating=1,      # Green - Best
    acoustic_rating=3,     # Orange - Fair
    iaq_rating=2,          # Yellow - Good
    luminous_rating=2,     # Yellow - Good
    detailed_ratings={
        "Temp": 1,
        "CO2": 2,
        "Humid": 1,
        "Noise": 3,
    },
    building_name="My Building",
    save_path=Path("output/my_tail_chart.png")
)
```

### 3. From Building Analysis

```python
from core.reporting.charts.tail_circular_chart import create_tail_chart_for_building

# Automatic rating calculation from analysis
fig = create_tail_chart_for_building(
    building_analysis=building_analysis,
    room_analyses=room_analyses,
    building_name="Downtown Office Tower",
    output_path=Path("output/tail_chart.png")
)
```

### 4. Use Case (Application Layer)

```python
from core.application.use_cases.generate_tail_chart import GenerateTAILChartUseCase

use_case = GenerateTAILChartUseCase()

# Single building
path = use_case.execute(
    building_analysis=building_analysis,
    room_analyses=room_analyses,
    building_name="Building A"
)

# Multiple buildings
paths = use_case.execute_batch(
    buildings_data=[
        (building_analysis_1, room_analyses_1, "Building A"),
        (building_analysis_2, room_analyses_2, "Building B"),
    ]
)
```

## Chart Structure

The circular chart has 3 concentric rings:

```
┌─────────────────────────────────────┐
│        Ring 1 (Center)              │
│     Overall TAIL Rating             │
│     (Roman numeral I-IV)            │
│                                     │
│        Ring 2 (Middle)              │
│     T | A | I | L Components        │
│     (4 quadrants)                   │
│                                     │
│        Ring 3 (Outer)               │
│     Detailed Parameters             │
│     (Temperature, CO2, etc.)        │
└─────────────────────────────────────┘
```

### Color Coding

- **Green (#77dd77)** - Best quality, no concerns
- **Yellow (#ffdd75)** - Good quality, minor issues
- **Orange (#ffb347)** - Fair quality, attention needed
- **Red (#ff6961)** - Poor quality, immediate action required
- **Gray (#d9d9d9)** - Parameter not measured

## Examples

### Demo Script

Run the included demo to see all features:

```bash
cd clean/
python examples/demo_tail_chart.py
```

This creates:
- Simple chart (overall + 4 components)
- Detailed chart (with individual parameters)
- 4 building comparison charts (Excellent → Poor)
- Rating calculation examples

Output saved to: `output/tail_charts/`

### Example Output

The demo creates charts like:

```
Building A - Excellent (I)
  Center: Green (I)
  T: Green, A: Green, I: Green, L: Green
  Details: All parameters green

Building D - Poor (IV)
  Center: Red (IV)
  T: Orange, A: Red, I: Red, L: Orange
  Details: Multiple red parameters
```

## Rating Calculation

### From Compliance Percentage

```python
from core.reporting.charts.tail_circular_chart import TAILRatingCalculator

rating = TAILRatingCalculator._compliance_to_rating(85)
# Returns: 2 (Yellow - Good)
```

### Mapping

```python
Compliance ≥ 95% → Rating 1 (Green)
Compliance 70-95% → Rating 2 (Yellow)
Compliance 50-70% → Rating 3 (Orange)
Compliance < 50% → Rating 4 (Red)
```

### Component Aggregation

The TAIL rating uses the **worst rating** across all measured components:

```python
overall_rating = max(thermal, acoustic, iaq, luminous)
```

This conservative approach highlights areas needing immediate attention.

## Integration with Existing Workflow

### Interactive Workflow

The TAIL chart can be automatically generated after analysis:

```bash
# Run analysis
hvx ieq start

# Generate TAIL chart from saved session
hvx analyze list  # Find session name
hvx tail generate --session <session_name>
```

### Automated Pipeline

```bash
# Complete workflow with TAIL chart
hvx analyze run data/building-a --session-name building_a
hvx report generate --session building_a
hvx tail generate --session building_a
```

## Customization

### Custom Colors

```python
chart = TAILCircularChart()
chart.COLORS = {
    1: "#custom_green",
    2: "#custom_yellow",
    3: "#custom_orange",
    4: "#custom_red",
    None: "#custom_gray"
}
```

### Custom Figure Size

```python
chart = TAILCircularChart(figsize=(15, 15))  # Larger chart
chart = TAILCircularChart(figsize=(6, 6))    # Smaller chart
```

### Custom Output

```python
fig = chart.create(...)

# Save in different formats
fig.savefig("output/chart.png", dpi=300)
fig.savefig("output/chart.pdf")
fig.savefig("output/chart.svg")
```

## Differences from Original TAIL

This implementation adapts the TAIL Rating Scheme for integration with the IEQ Analytics toolbox:

| Aspect | Original TAIL | This Implementation |
|--------|---------------|---------------------|
| Language | R (ggplot2, ggforce) | Python (matplotlib) |
| Input | CSV with specific format | Building/Room Analysis objects |
| Parameters | 12 specific parameters | Flexible, based on available data |
| Standards | EN16798, WHO guidelines | Configurable compliance tests |
| Output | PNG files | PNG + in-memory figures |
| Integration | Standalone script | Full CLI + API integration |

### Maintained Features

✅ 4-color rating system (Green, Yellow, Orange, Red)  
✅ Roman numeral scale (I-IV)  
✅ Circular/round graph design  
✅ Hierarchical visualization (overall → components → details)  
✅ Conservative aggregation (worst rating)  
✅ Gray color for unmeasured parameters  

## Reference

- **Original TAIL Rating Scheme**: https://github.com/asitkm76/TAILRatingScheme
- **TAIL Paper**: [Building and Environment, 2021](https://www.sciencedirect.com/science/article/pii/S0378778821003133)
- **ALDREN Project**: https://aldren.eu

## Future Enhancements

Potential improvements:

1. **Full Parameter Mapping** - Map all 12 TAIL parameters to analysis results
2. **Multiple Standards** - Support EN16798, ASHRAE 55, WELL, etc.
3. **Time-Series TAIL** - Show rating evolution over time
4. **Comparative TAIL** - Side-by-side building comparisons
5. **Interactive TAIL** - Web-based interactive visualization
6. **TAIL Dashboard** - Real-time monitoring dashboard
7. **PredicTAIL** - Predictive ratings for design phase

## Testing

```bash
# Test CLI commands
hvx tail --help
hvx tail about

# Run demos
python examples/demo_tail_chart.py

# Check output
ls -la output/tail_charts/

# Generate from real analysis
hvx analyze run data/ --session-name test
hvx tail generate --session test
```

## Summary

✅ **TAIL circular charts implemented** - Beautiful round graph visualizations  
✅ **Python implementation** - Pure Python using matplotlib  
✅ **CLI integration** - `hvx tail generate` command  
✅ **API access** - Programmatic chart generation  
✅ **Application layer** - Clean architecture with use cases  
✅ **Demo included** - Complete examples script  
✅ **Per-building charts** - Individual visualization for each building  
✅ **Flexible** - Adapts to available parameters  
✅ **Production ready** - Tested and documented  

---

**Status**: ✅ Complete and Tested  
**Version**: 2.0.0  
**Date**: 2024-10-20  
**Inspired by**: TAIL Rating Scheme (ALDREN Project)
