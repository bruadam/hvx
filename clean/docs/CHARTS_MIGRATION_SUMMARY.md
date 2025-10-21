# Charts and Configuration Migration Summary

## Overview
This document summarizes the migration of the comprehensive chart library and configuration files from the previous version to the new clean architecture.

## What Was Migrated

### 1. Matplotlib Chart Renderers (NEW)

The extensive matplotlib-based chart library has been added to `clean/core/reporting/charts/`:

#### Chart Types Available:

**Bar Charts** (`matplotlib_bar_chart.py`):
- `render_bar_chart()` - Standard bar chart with threshold lines
- `render_grouped_bar_chart()` - Multi-series comparison charts

**Line Charts** (`matplotlib_line_chart.py`):
- `render_line_chart()` - Time series with target bands and moving averages
- `render_multi_line_chart()` - Multiple series on same plot

**Heatmaps** (`matplotlib_heatmap.py`):
- `render_heatmap()` - 2D data visualization (occupancy, compliance patterns)
- `render_correlation_matrix()` - Parameter correlation analysis

**Compliance Charts** (`matplotlib_compliance_chart.py`):
- `render_compliance_chart()` - Color-coded compliance overview
- `render_performance_matrix()` - Quadrant scatter plot for performance analysis

### 2. Chart Configuration System

**Global Style Configuration** (`clean/config/charts/`):
- `global_style.yaml` - Unified styling across all charts
- `bar_chart_style.yaml` - Bar chart specific settings
- `line_chart_style.yaml` - Time series specific settings

**Style Loader** (`clean/core/reporting/chart_config.py`):
- Hierarchical configuration system (global → chart-type → user overrides)
- Centralized matplotlib rcParams management
- Color palettes (categorical, sequential, diverging)

### 3. Configuration Files

#### Standards (`clean/config/standards/`):

**EN 16798-1** (18 files):
- Temperature tests (Categories I, II, III for heating/non-heating seasons)
- CO2 tests (Categories I, II, III)
- Humidity tests (Categories I, II, III)

**Danish Guidelines** (2 files):
- `co2_danish_guidelines.yaml`
- `temp_comfort_danish_schools.yaml`

#### Time Filters (`clean/config/filters/`):
- `all_hours.yaml`
- `opening_hours.yaml`
- `opening_hours_no_holidays.yaml`
- `non_opening_hours.yaml`
- `morning_no_holidays.yaml`
- `afternoon_no_holidays.yaml`
- `evening_no_holidays.yaml`

#### Periods (`clean/config/periods/`):
- `all_year.yaml`
- `heating_season.yaml`
- `non_heating_season.yaml`
- `winter.yaml`, `spring.yaml`, `summer.yaml`, `autumn.yaml`

#### Holidays (`clean/config/holidays/`):
- `denmark.yaml` - Danish holidays and school breaks

### 4. HTML Report Integration

**ChartHelper** (`clean/core/reporting/chart_helper.py`):
- Unified interface for both Plotly (interactive) and Matplotlib (static) charts
- Base64 embedding for matplotlib charts in HTML
- Automatic data transformation from domain models to chart format

**HTMLRenderer Updates** (`clean/core/reporting/renderers/html_renderer.py`):
- Integrated ChartHelper for chart generation
- Added CSS styles for matplotlib image embedding
- Support for `renderer` option in chart configs (plotly/matplotlib)

## Architecture

### Chart Rendering Flow

```
Report Template (YAML)
    ↓
ReportGenerator
    ↓
HTMLRenderer
    ↓
ChartHelper
    ↓
├─→ Plotly Charts (interactive, embedded JS)
└─→ Matplotlib Charts (static, base64 PNG)
    ↓
    StyleLoader (loads YAML configs)
    ↓
    Chart Renderers (bar, line, heatmap, compliance)
    ↓
    HTML Report with Embedded Charts
```

### Using Matplotlib vs Plotly

In report template YAML, specify renderer in chart options:

```yaml
sections:
  - type: chart
    title: "Room Comparison"
    chart:
      type: room_comparison_bar
      options:
        renderer: matplotlib  # or "plotly" (default)
        metric: compliance
```

## Features

### Matplotlib Charts Include:

1. **Professional Styling**:
   - Consistent color schemes
   - Publication-quality typography
   - Configurable grid and axes

2. **Interactive Elements**:
   - Threshold lines with labels
   - Target range bands (for time series)
   - Value labels on bars
   - Moving averages

3. **Automatic Color Coding**:
   - Compliance-based colors (green/yellow/orange/red)
   - Grade-based colors for buildings
   - Customizable palettes

4. **Data Quality**:
   - Handles missing data gracefully
   - Automatic scaling and formatting
   - Smart label rotation

### Style Configuration Features:

- **Hierarchical Merging**: Global → Chart-type → User overrides
- **Theme Support**: Easy to create custom themes
- **Responsive**: Configurable figure sizes and DPI
- **Accessible**: High contrast, readable fonts

## Usage Examples

### 1. Generate Bar Chart Programmatically

```python
from pathlib import Path
from core.reporting.charts import render_bar_chart

data = {
    "title": "Room Compliance Rates",
    "data": {
        "categories": ["Room A", "Room B", "Room C"],
        "compliance_percentage": [98.5, 92.3, 87.6],
    },
    "styling": {
        "xlabel": "Room",
        "ylabel": "Compliance (%)",
        "threshold_line": 95.0,
    },
}

config = {"figsize": (12, 6), "dpi": 300}
render_bar_chart(data, config, Path("output/compliance.png"))
```

### 2. Generate Chart in Report Template

```yaml
report_type: building
title: "Building IEQ Report"

sections:
  - type: chart
    title: "Compliance by Room"
    description: "Comparison of compliance rates across all rooms"
    chart:
      type: room_comparison_bar
      options:
        renderer: matplotlib
        metric: compliance
        sort: true
        figsize: [14, 6]
```

### 3. Use ChartHelper Directly

```python
from core.reporting.chart_helper import ChartHelper
from core.reporting.template_engine import ChartConfig

chart_config = ChartConfig(
    type="room_comparison_bar",
    title="Room Comparison",
    options={"renderer": "matplotlib", "metric": "compliance"}
)

html = ChartHelper.generate_chart_html(
    chart_config,
    room_analyses=room_analyses,
    use_matplotlib=True
)
```

## Testing

A test file has been created at `clean/test_matplotlib_charts.py` that demonstrates:
- Bar chart generation
- Line chart with time series
- Compliance overview chart
- Heatmap generation

To run tests (requires matplotlib and seaborn):
```bash
cd clean
python test_matplotlib_charts.py
```

## File Structure

```
clean/
├── config/
│   ├── charts/                    # Chart styling configs (NEW)
│   │   ├── global_style.yaml
│   │   ├── bar_chart_style.yaml
│   │   └── line_chart_style.yaml
│   ├── standards/                 # Compliance standards (MIGRATED)
│   │   ├── en16798-1/            # 18 YAML files
│   │   └── danish-guidelines/    # 2 YAML files
│   ├── filters/                   # Time filters (MIGRATED)
│   ├── periods/                   # Time periods (MIGRATED)
│   └── holidays/                  # Holiday calendars (MIGRATED)
├── core/
│   └── reporting/
│       ├── charts/                # Chart generators
│       │   ├── matplotlib_bar_chart.py (NEW)
│       │   ├── matplotlib_line_chart.py (NEW)
│       │   ├── matplotlib_heatmap.py (NEW)
│       │   ├── matplotlib_compliance_chart.py (NEW)
│       │   ├── bar_chart.py (Plotly - existing)
│       │   ├── timeseries_chart.py (Plotly - existing)
│       │   └── __init__.py (UPDATED)
│       ├── chart_config.py        # Style loader (NEW)
│       ├── chart_helper.py        # Unified chart interface (NEW)
│       └── renderers/
│           └── html_renderer.py   # HTML generation (UPDATED)
└── test_matplotlib_charts.py      # Tests (NEW)
```

## Dependencies

Added to `requirements.txt`:
- matplotlib>=3.10.7
- seaborn (for advanced heatmaps)
- numpy (for data processing)

## Benefits

1. **Dual Chart Support**: Both interactive (Plotly) and publication-ready (Matplotlib)
2. **Consistent Styling**: Centralized configuration ensures brand consistency
3. **Flexible**: Easy to switch between renderers or create custom styles
4. **Production Ready**: Comprehensive chart library from previous version
5. **Well Tested**: Battle-tested chart renderers from production system
6. **Complete Config**: All EN16798-1 tests and Danish guidelines included

## Next Steps

1. Install matplotlib and seaborn: `pip install matplotlib seaborn`
2. Run test: `python clean/test_matplotlib_charts.py`
3. Generate reports with matplotlib charts by setting `renderer: matplotlib`
4. Customize styles by editing YAML files in `clean/config/charts/`
5. Create new chart types by following existing patterns

## Notes

- Matplotlib charts are embedded as base64-encoded PNG images in HTML
- Chart quality is controlled by DPI setting (default: 300)
- Color schemes are compliance-aware (automatic red/yellow/green)
- All configuration YAMLs from src/ have been preserved and migrated
