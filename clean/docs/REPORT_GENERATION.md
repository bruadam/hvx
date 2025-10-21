# Report Generation Guide

Complete guide to generating IEQ Analytics reports using YAML templates.

## Overview

The IEQ Analytics reporting system provides a flexible, template-driven approach to generating comprehensive Indoor Environmental Quality reports. Reports can be customized through YAML configuration files to show exactly the data and visualizations you need.

## Key Features

### 📊 Chart Types

**Heatmaps** (Hours on Y-axis)
- `heatmap_hourly_daily`: Temperature/parameter patterns by hour and day of week
- `heatmap_daily_monthly`: Patterns by day and month
- `heatmap_compliance`: Compliance rates by time of day

**Timeseries** (Non-compliance in RED)
- `timeseries_compliance`: Parameter over time with violations highlighted in RED
- `timeseries_multi_parameter`: Multiple parameters on same chart
- `violation_timeline`: Timeline showing only violations with severity

**Bar Charts** (Room/Building Comparison)
- `bar_room_comparison`: Compare rooms by compliance/quality/violations
- `bar_building_comparison`: Compare multiple buildings
- `bar_test_comparison`: Compare different tests within a room
- `bar_stacked_comparison`: Compliant vs non-compliant breakdown

**Compliance Charts** (KPIs)
- `compliance_matrix`: All rooms × all tests matrix
- `compliance_gauge`: Single gauge for compliance rate
- `building_kpi_dashboard`: Building-level KPI gauges
- `portfolio_overview`: Portfolio-level overview

### 🔍 Filtering Options

**Room Filtering**
- `all`: Include all rooms
- `failing`: Only rooms below compliance threshold
- `top_n`: Best N performing rooms
- `bottom_n`: Worst N performing rooms

**Seasonal Filtering**
- `winter`: Winter season only
- `summer`: Summer season only
- `spring`: Spring season
- `fall`: Fall season
- `heating`: Heating season
- `cooling`: Cooling season
- `all`: All seasons

### 📋 Report Types

- **Room Reports**: Detailed analysis of individual rooms
- **Building Reports**: Building-level analysis with room breakdowns
- **Portfolio Reports**: Multi-building portfolio overview

## Quick Start

### 1. Create Sample Data

```python
from pathlib import Path
from ieq_analytics.infrastructure.data_loaders.csv_loader import CSVDataLoader

# Create sample CSV file
output_path = Path("data/room_01.csv")
CSVDataLoader.create_sample_csv(output_path, periods=168)  # 7 days
```

### 2. Load Room Data

```python
from ieq_analytics.infrastructure.data_loaders.csv_loader import CSVDataLoader

loader = CSVDataLoader()
room = loader.load_room(
    file_path=Path("data/room_01.csv"),
    room_id="room_01",
    room_name="Conference Room A"
)
```

### 3. Generate Report from Template

```python
from pathlib import Path
from ieq_analytics.reporting import ReportGenerator

# Initialize generator
generator = ReportGenerator()

# Generate report
generator.generate_from_template(
    template_path=Path("config/report_templates/comprehensive_building_report.yaml"),
    rooms=[room],
    building_name="Building A",
    output_path=Path("output/report.html")
)
```

## YAML Template Structure

### Basic Template

```yaml
template_name: "my_custom_report"
report_type: "building"  # room, building, or portfolio
title: "My Custom IEQ Report"
description: "Custom report description"
author: "Your Name"

# Room filtering
room_filter:
  mode: "all"  # all, failing, top_n, bottom_n
  sort_by: "compliance"  # compliance, quality, violations, name
  ascending: false

# Report sections
sections:
  - type: "kpi_cards"
    title: "Key Metrics"

  - type: "chart"
    title: "Room Comparison"
    chart:
      type: "bar_room_comparison"
      metric: "compliance"
      sort: true

# Output settings
output_format: ["html"]
include_interactive_charts: true
theme: "professional"

# Compliance settings
compliance_standard: "EN16798-1"
building_class: "II"
```

### Section Types

#### 1. KPI Cards
```yaml
- type: "kpi_cards"
  title: "Performance Overview"
  description: "Key performance indicators"
```

#### 2. Chart Section
```yaml
- type: "chart"
  title: "Temperature Analysis"
  description: "Temperature with violations in RED"
  chart:
    type: "timeseries_compliance"
    parameters: ["temperature"]
    season: "winter"
    show_threshold: true
```

#### 3. Table Section
```yaml
- type: "table"
  title: "Room Details"
  description: "Detailed metrics for all rooms"
```

#### 4. Recommendations
```yaml
- type: "recommendations"
  title: "Improvement Actions"
  max_recommendations: 10
```

#### 5. Summary
```yaml
- type: "summary"
  title: "Executive Summary"
```

## Chart Configuration Examples

### Heatmap with Hours on Y-axis

```yaml
chart:
  type: "heatmap_hourly_daily"
  parameters: ["temperature"]
  season: "winter"
  title: "Temperature Patterns - Winter"
```

### Timeseries with RED Highlighting

```yaml
chart:
  type: "timeseries_compliance"
  parameters: ["temperature"]
  season: "winter"
  show_threshold: true
  title: "Temperature Violations"
```

### Room Comparison Bar Chart

```yaml
chart:
  type: "bar_room_comparison"
  metric: "compliance"  # compliance, quality, or violations
  sort: true
  ascending: false
  show_only_failing: true
  failing_threshold: 95.0
```

### Building KPI Dashboard

```yaml
chart:
  type: "building_kpi_dashboard"
  title: "Building Performance KPIs"
```

## Pre-built Templates

### 1. Comprehensive Building Report
**File**: `comprehensive_building_report.yaml`

Shows all rooms with detailed analysis including:
- Building KPI dashboard
- Room comparison charts
- Temperature and CO2 timeseries with RED violations
- Hourly heatmaps
- Compliance matrix
- Detailed metrics table
- Recommendations

**Use when**: You need complete analysis of all rooms

### 2. Problematic Rooms Report
**File**: `problematic_rooms_report.yaml`

Focuses on failing rooms only:
- Only rooms below 95% compliance
- Sorted by worst performers first
- Violation timelines
- Detailed violation analysis
- Urgent recommendations

**Use when**: You need to identify and fix problems

### 3. Building KPI Report
**File**: `building_kpi_report.yaml`

Executive summary with KPIs only:
- Building-level metrics
- No individual room details
- Strategic recommendations
- Performance gauges

**Use when**: Reporting to management

### 4. Portfolio Overview Report
**File**: `portfolio_overview_report.yaml`

Multi-building portfolio analysis:
- Portfolio-level KPIs
- Building comparisons
- Best/worst performers
- Strategic recommendations

**Use when**: Managing multiple buildings

### 5. Seasonal Analysis Report
**File**: `seasonal_analysis_report.yaml`

Focus on specific season:
- All charts filtered to winter/summer
- Seasonal patterns
- Season-specific recommendations
- Temperature focus for winter

**Use when**: Analyzing seasonal performance

### 6. Top/Bottom Performers Report
**File**: `top_bottom_performers_report.yaml`

Compare best and worst rooms:
- Top 10 or bottom 10 rooms
- Side-by-side comparisons
- Identify success factors
- Learn from best practices

**Use when**: Benchmarking rooms

## Advanced Usage

### Custom Chart Generation

```python
from ieq_analytics.reporting.charts import TimeseriesChart
from ieq_analytics.domain.enums.parameter_type import ParameterType

# Create custom timeseries chart
fig = TimeseriesChart.create_timeseries_with_compliance(
    room=room,
    parameter=ParameterType.TEMPERATURE,
    compliance_result=compliance_result,
    season="winter",
    title="Custom Temperature Chart",
    show_threshold=True
)

# Save chart
TimeseriesChart.save_chart(fig, Path("output/custom_chart.html"), format="html")
```

### Portfolio Report with Multiple Buildings

```python
from ieq_analytics.reporting import ReportGenerator

generator = ReportGenerator()

# Dictionary of building_name -> rooms
buildings_data = {
    "Building A": [room1, room2, room3],
    "Building B": [room4, room5, room6],
    "Building C": [room7, room8, room9],
}

generator.generate_portfolio_report_multi_building(
    template=template,
    buildings_data=buildings_data,
    output_path=Path("output/portfolio_report.html")
)
```

### Validate Template Before Generation

```python
from ieq_analytics.reporting import TemplateLoader, TemplateValidator

# Load template
template = TemplateLoader.load_from_file(Path("my_template.yaml"))

# Validate
is_valid, errors = TemplateValidator.validate(template)

if not is_valid:
    print("Template errors:")
    for error in errors:
        print(f"  - {error}")
else:
    print("Template is valid!")
```

## Parameters Available

All IEQ parameters can be visualized:
- `temperature` - Temperature (°C)
- `co2` - CO2 concentration (ppm)
- `humidity` - Relative humidity (%)
- `illuminance` - Light level (lux)
- `pm25` - PM2.5 particles (µg/m³)
- `pm10` - PM10 particles (µg/m³)
- `voc` - Volatile Organic Compounds (ppb)
- `noise` - Noise level (dB)
- `radon` - Radon concentration (Bq/m³)

## Color Coding

All charts use consistent color coding:
- 🟢 **Green** (#2E7D32): ≥95% compliance (excellent)
- 🟡 **Orange** (#F57C00): 80-95% compliance (warning)
- 🔴 **Red** (#C62828): <80% compliance (critical)

## Best Practices

1. **Start with pre-built templates**: Customize existing templates rather than building from scratch

2. **Use seasonal filtering**: Identify problematic seasons with `season: "winter"` or `season: "summer"`

3. **Filter to problematic rooms**: Use `show_only_failing: true` to focus on issues

4. **Sort strategically**: Sort by compliance to see worst performers first

5. **Include recommendations**: Always include recommendations section for actionable insights

6. **Use appropriate report types**:
   - Room reports for detailed analysis
   - Building reports for management
   - Portfolio reports for executives

7. **Validate templates**: Always validate before running on production data

## Troubleshooting

### Template validation errors
```python
# Check template structure
is_valid, errors = TemplateValidator.validate(template)
for error in errors:
    print(error)
```

### No data in charts
- Check parameter names match exactly (lowercase)
- Verify seasonal filter doesn't exclude all data
- Ensure room has data for requested parameters

### Reports missing sections
- Check room_filter settings aren't too restrictive
- Verify compliance threshold is appropriate
- Ensure rooms have been analyzed before rendering

## Testing

Run the comprehensive test script:

```bash
python test_report_generation.py
```

This will:
1. Create sample IEQ data for 8 rooms
2. Load all available templates
3. Generate reports for each template
4. Save HTML files to `output/reports/generated_reports/`

## Next Steps

1. Review the generated sample reports
2. Customize existing templates for your needs
3. Create custom templates for specific use cases
4. Integrate with your data pipeline
5. Schedule automated report generation

## Support

For issues or questions:
- Check template validation errors first
- Review example templates in `config/report_templates/`
- Ensure room data is properly loaded
- Verify parameter names and compliance settings
