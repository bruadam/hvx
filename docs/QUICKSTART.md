# HVX CLI - Quick Start Guide

## Installation

The HVX CLI is already installed. To reinstall or update:

```bash
python3 -m pip install -e .
```

## Verify Installation

```bash
hvx --version
hvx --help
```

## 5-Minute Workflow

### Step 1: Explore Available Charts

```bash
# List all charts
hvx graphs list

# Get info about a specific chart
hvx graphs info co2_compliance_bar

# Preview a chart with dummy data
hvx graphs preview co2_compliance_bar
```

### Step 2: Prepare Your Data

Your CSV file should have:
- A `timestamp` column (datetime format)
- Sensor data columns (e.g., `temperature`, `co2`, `humidity`)

Example: [data/samples/building_sample.csv](data/samples/building_sample.csv)

### Step 3: Run Analytics

```bash
# Run analysis on your data
hvx analytics run data/samples/building_sample.csv --name my_building

# View results
hvx analytics show my_building

# List all analyses
hvx analytics list
```

### Step 4: Create a Template

Option A - Programmatically (recommended):
```bash
python3 -c "
from ieq_analytics.services import TemplateService
ts = TemplateService()
ts.create_simple_template(
    name='my_template',
    title='My Building IEQ Report',
    description='Custom report with selected charts',
    chart_ids=['co2_compliance_bar', 'temperature_timeseries']
)
print('Template created!')
"
```

Option B - Use existing template:
```bash
hvx templates list
```

### Step 5: Generate Report

```bash
# Generate PDF report
hvx reports generate my_template --data my_building

# List generated reports
hvx reports list
```

Your report will be in `output/reports/`!

## Common Commands

### Graphs
```bash
hvx graphs list                          # List all charts
hvx graphs list --category compliance    # Filter by category
hvx graphs info <chart_id>               # Show chart details
hvx graphs preview <chart_id>            # Generate preview
```

### Templates
```bash
hvx templates list                       # List templates
hvx templates show <name>                # Show template details
hvx templates delete <name>              # Delete user template
```

### Analytics
```bash
hvx analytics run <csv_file>             # Run analysis
hvx analytics run <csv_file> --name <n>  # Named analysis
hvx analytics list                       # List analyses
hvx analytics show <name>                # Show details
```

### Reports
```bash
hvx reports generate <template> --data <analysis>  # Generate report
hvx reports list                                   # List reports
```

## Available Charts

1. **co2_compliance_bar** - CO2 compliance by period (bar chart)
2. **temperature_timeseries** - Temperature over time (line chart)
3. **occupancy_heatmap** - Occupancy patterns (heatmap)

## File Locations

- **User templates**: `~/.hvx/templates/`
- **Analysis results**: `output/analysis/`
- **Generated charts**: `output/charts/`
- **PDF reports**: `output/reports/`

## Example: Complete Workflow

```bash
# 1. Check what charts are available
hvx graphs list

# 2. Preview charts with dummy data
hvx graphs preview co2_compliance_bar
hvx graphs preview temperature_timeseries

# 3. Run analysis on your building data
hvx analytics run data/samples/building_sample.csv --name building_001

# 4. Check the results
hvx analytics show building_001

# 5. Create a template (if needed)
python3 -c "
from ieq_analytics.services import TemplateService
TemplateService().create_simple_template(
    'building_report',
    'Building 001 IEQ Report',
    'Monthly IEQ compliance report',
    ['co2_compliance_bar', 'temperature_timeseries']
)
"

# 6. Generate the report
hvx reports generate building_report --data building_001

# 7. Find your report
hvx reports list
open output/reports/*.pdf  # macOS
```

## Troubleshooting

### Command not found: hvx
```bash
# Reinstall
python3 -m pip install -e .
```

### Import errors
```bash
# Check all dependencies are installed
python3 -m pip install -r requirements.txt
```

### No charts in preview
```bash
# Verify fixtures exist
ls ieq_analytics/graphs/fixtures/
```

## Next Steps

- Read [HVX_CLI_IMPLEMENTATION_COMPLETE.md](HVX_CLI_IMPLEMENTATION_COMPLETE.md) for full details
- Check [CLI_ARCHITECTURE.md](CLI_ARCHITECTURE.md) for architecture overview
- See [README_CLI_FIRST.md](README_CLI_FIRST.md) for comprehensive documentation

## Support

For issues or questions:
- Check the documentation in the root directory
- Review example data in `data/samples/`
- Examine generated outputs in `output/`
