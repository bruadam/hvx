# HVX CLI Implementation - Complete ✓

## Overview

Successfully implemented a fully functional CLI for IEQ Analytics with a simplified architecture focusing on 3 graphs maximum. The implementation follows the JSON-first workflow: **Analytics → JSON → Graphs → PDF**.

## What Was Built

### 1. Service Layer (`ieq_analytics/services/`)

#### GraphService
- Manages 3 chart types: CO2 compliance bar chart, temperature time series, occupancy heatmap
- Loads chart registry from YAML
- Generates previews with dummy data fixtures
- Renders charts using matplotlib/seaborn
- **Location**: [ieq_analytics/services/graph_service.py](ieq_analytics/services/graph_service.py)

#### TemplateService
- Creates and manages report templates
- Stores user templates in `~/.hvx/templates/`
- Supports built-in templates from `ieq_analytics/reporting/templates/library/`
- Simple template creation with chart selection
- **Location**: [ieq_analytics/services/template_service.py](ieq_analytics/services/template_service.py)

#### AnalyticsService
- Runs simplified analytics on IEQ data
- Analyzes CO2 and temperature compliance
- Exports results to JSON format in `output/analysis/`
- Calculates compliance rates and statistics
- **Location**: [ieq_analytics/services/analytics_service.py](ieq_analytics/services/analytics_service.py)

#### ReportService
- Generates PDF reports from JSON data and templates
- Renders charts based on template configuration
- Creates professional PDF layout with ReportLab
- Outputs to `output/reports/`
- **Location**: [ieq_analytics/services/report_service.py](ieq_analytics/services/report_service.py)

### 2. CLI Commands (`ieq_analytics/cli/`)

All commands use Rich library for beautiful terminal output.

#### `hvx graphs`
- `hvx graphs list` - List all available charts
- `hvx graphs list --category compliance` - Filter by category
- `hvx graphs info <chart_id>` - Show detailed chart information
- `hvx graphs preview <chart_id>` - Generate preview with dummy data
- **Location**: [ieq_analytics/cli/commands/graphs.py](ieq_analytics/cli/commands/graphs.py)

#### `hvx templates`
- `hvx templates list` - List all templates (user + built-in)
- `hvx templates show <name>` - Show template YAML
- `hvx templates create` - Interactive template creation
- `hvx templates delete <name>` - Delete user template
- **Location**: [ieq_analytics/cli/commands/templates.py](ieq_analytics/cli/commands/templates.py)

#### `hvx analytics`
- `hvx analytics run <data_path>` - Run analysis on CSV/parquet data
- `hvx analytics run <data_path> --name <analysis_name>` - Named analysis
- `hvx analytics list` - List all saved analyses
- `hvx analytics show <name>` - Show analysis summary
- **Location**: [ieq_analytics/cli/commands/analytics.py](ieq_analytics/cli/commands/analytics.py)

#### `hvx reports`
- `hvx reports generate <template> --data <analysis_name>` - Generate PDF report
- `hvx reports generate <template> --data <json_file>` - Generate from JSON file
- `hvx reports list` - List all generated reports
- **Location**: [ieq_analytics/cli/commands/reports.py](ieq_analytics/cli/commands/reports.py)

### 3. Graph Library

#### Registry (`ieq_analytics/graphs/registry.yaml`)
Defines 3 charts:
1. **co2_compliance_bar** - CO2 compliance by period
2. **temperature_timeseries** - Temperature over time
3. **occupancy_heatmap** - Occupancy patterns by day/hour

#### Dummy Data Fixtures (`ieq_analytics/graphs/fixtures/`)
- `sample_co2_compliance.json` - Sample CO2 compliance data
- `sample_temperature.json` - Sample temperature time series
- `sample_occupancy.json` - Sample occupancy heatmap data

### 4. Installation

Created [setup.py](setup.py) with:
- Package name: `hvx`
- Entry point: `hvx` command
- All dependencies included
- Installed in development mode

## End-to-End Workflow (Tested ✓)

### 1. Explore Available Charts
```bash
hvx graphs list
hvx graphs info temperature_timeseries
hvx graphs preview co2_compliance_bar
```

### 2. Create a Template
```bash
# Programmatically (interactive mode has input issues)
python3 -c "
from ieq_analytics.services import TemplateService
ts = TemplateService()
ts.create_simple_template(
    name='my_report',
    title='My Building Report',
    description='Custom IEQ report',
    chart_ids=['co2_compliance_bar', 'temperature_timeseries']
)
"
```

### 3. Run Analytics
```bash
hvx analytics run data/samples/building_sample.csv --name my_building
hvx analytics show my_building
```

### 4. Generate Report
```bash
hvx reports generate my_report --data my_building
hvx reports list
```

## Test Results

### Sample Data Generated
- **File**: `data/samples/building_sample.csv`
- **Records**: 168 hours (7 days)
- **Parameters**: timestamp, temperature, co2, humidity, occupancy

### Analysis Results
- **Name**: test_building
- **Overall Compliance**: 75.6%
- **Rules Evaluated**: 2 (CO2 All Year: 100%, Temperature Comfort: 51.2%)
- **Data Quality**: 100%
- **Output**: `output/analysis/test_building.json`

### Report Generated
- **Template**: simple_report
- **Charts**: 2 (CO2 compliance bar + temperature time series)
- **Output**: `output/reports/report_simple_report_20251002_102052.pdf`
- **Size**: 405 KB

### Charts Generated
- `output/charts/co2_compliance_bar.png` (85 KB)
- `output/charts/temperature_timeseries.png` (236 KB)

## Architecture Highlights

### JSON-First Workflow
1. **Analytics Service** reads CSV data → runs analysis → saves to JSON
2. **Report Service** reads JSON → generates charts → creates PDF

### Service Layer Benefits
- CLI commands are thin wrappers around services
- Services can be reused in future Flask API
- Clear separation of concerns
- Testable independently

### Simplified Analytics
For this implementation, used simplified analytics engine that:
- Analyzes CO2 levels against 1000 ppm threshold
- Analyzes temperature against 20-24°C comfort range
- Calculates compliance rates and statistics
- Can be replaced with full `UnifiedAnalyticsEngine` when needed

## File Structure

```
ieq_analytics/
├── cli/
│   ├── __init__.py
│   ├── main.py                    # CLI entry point
│   └── commands/
│       ├── __init__.py
│       ├── graphs.py              # Graph commands
│       ├── templates.py           # Template commands
│       ├── analytics.py           # Analytics commands
│       └── reports.py             # Report commands
│
├── services/
│   ├── __init__.py
│   ├── graph_service.py           # Graph management
│   ├── template_service.py        # Template management
│   ├── analytics_service.py       # Analytics execution
│   └── report_service.py          # Report generation
│
├── graphs/
│   ├── __init__.py
│   ├── registry.yaml              # Chart definitions
│   └── fixtures/
│       ├── sample_co2_compliance.json
│       ├── sample_temperature.json
│       └── sample_occupancy.json
│
└── ... (existing modules)

User storage:
~/.hvx/
└── templates/                     # User templates
    └── simple_report.yaml

Output:
output/
├── analysis/                      # JSON analysis results
│   └── test_building.json
├── charts/                        # Generated charts
│   ├── co2_compliance_bar.png
│   └── temperature_timeseries.png
└── reports/                       # PDF reports
    └── report_simple_report_*.pdf
```

## Next Steps (Future Enhancements)

1. **Full Analytics Integration**
   - Replace simplified analytics with `UnifiedAnalyticsEngine`
   - Support all rules from `config/tests.yaml`
   - Add EN16798 compliance analysis

2. **Interactive Template Builder**
   - Fix interactive prompts in `hvx templates create`
   - Add template preview before saving
   - Support more template customization options

3. **Flask API Layer**
   - Create REST API using existing services
   - Enable web-based access to all functionality
   - Add authentication and multi-user support

4. **Next.js Frontend**
   - Build web UI with shadcn components
   - Interactive chart builder
   - Template designer
   - Report preview and download

5. **Additional Charts**
   - Add more chart types beyond the 3 implemented
   - Support custom chart configurations
   - Enable chart combinations and dashboards

6. **Data Management**
   - Add `hvx data upload` command
   - Data validation and quality checks
   - Support for multiple data sources

## Dependencies Installed

- click >= 8.0.0 (CLI framework)
- rich >= 13.0.0 (Terminal formatting)
- pandas >= 2.0.0 (Data processing)
- numpy >= 1.24.0 (Numerical computing)
- matplotlib >= 3.7.0 (Plotting)
- seaborn >= 0.12.0 (Statistical visualization)
- pyyaml >= 6.0 (YAML parsing)
- reportlab >= 4.0.0 (PDF generation)
- holidays >= 0.35 (Holiday calendars)

## Conclusion

The HVX CLI is now fully functional with:
- ✓ 3 graph types with dummy data previews
- ✓ Template management (user + built-in)
- ✓ Analytics execution with JSON output
- ✓ PDF report generation
- ✓ End-to-end workflow tested

The architecture is modular, maintainable, and ready for future enhancements including Flask API and Next.js frontend integration.
