# HVX CLI Documentation

Welcome to the HVX CLI documentation. This guide covers all available commands and their usage.

## Overview

HVX is a command-line tool for analyzing Indoor Environmental Quality (IEQ) and energy efficiency data in buildings. It provides a comprehensive workflow from data loading through analysis to report generation.

## Installation

```bash
# Install in development mode
python3 -m pip install -e .

# Verify installation
hvx --version
```

## Quick Start

```bash
# 1. Load building data
hvx data load data/samples/sample-extensive-data -o output/dataset.pkl -f pickle

# 2. Run hierarchical analysis
hvx analyze run output/dataset.pkl --portfolio-name "My Portfolio"

# 3. View analysis summary
hvx analyze summary output/analysis

# 4. Generate a report (if using older analytics workflow)
hvx reports generate simple_report --data my_building
```

## Command Groups

HVX organizes commands into logical groups:

### [data](./data.md) - Data Loading & Management
Load and inspect building sensor data from directory structures.

- `hvx data load` - Load building data from directories
- `hvx data inspect` - Inspect loaded datasets

### [analyze](./analyze.md) - Hierarchical Analysis
Run comprehensive hierarchical analysis on building portfolios.

- `hvx analyze run` - Run analysis at room, level, building, and portfolio levels
- `hvx analyze summary` - Display analysis summaries

### [analytics](./analytics.md) - Legacy Analytics (Single Building)
Run analytics on individual datasets (CSV files).

- `hvx analytics run` - Run analytics on a CSV file
- `hvx analytics list` - List all saved analyses
- `hvx analytics show` - Show analysis details

### [graphs](./graphs.md) - Graph Library
Discover and preview available charts.

- `hvx graphs list` - List available charts
- `hvx graphs info` - Show chart details
- `hvx graphs preview` - Generate chart previews with dummy data

### [templates](./templates.md) - Template Management
Manage report templates.

- `hvx templates list` - List available templates
- `hvx templates show` - Show template configuration
- `hvx templates create` - Create new templates interactively
- `hvx templates delete` - Delete user templates

### [reports](./reports.md) - Report Generation
Generate PDF reports from analysis data.

- `hvx reports generate` - Generate PDF reports
- `hvx reports list` - List generated reports

## Workflow

### Modern Workflow (Portfolio Analysis)

```
Data Directory → Load → Dataset → Analyze → JSON Results → View Summaries
```

1. **Load Data**: Load building data from structured directories
   ```bash
   hvx data load data/my-buildings -o output/dataset.pkl -f pickle
   ```

2. **Run Analysis**: Perform hierarchical analysis
   ```bash
   hvx analyze run output/dataset.pkl --portfolio-name "My Portfolio"
   ```

3. **View Results**: Explore analysis results
   ```bash
   hvx analyze summary output/analysis --level portfolio
   hvx analyze summary output/analysis --level building --entity-id building-1
   ```

### Legacy Workflow (Single Building)

```
CSV Data → Analytics → JSON → Reports → PDF
```

1. **Run Analytics**: Analyze a single building's CSV data
   ```bash
   hvx analytics run data/building.csv --name my_building
   ```

2. **Generate Report**: Create PDF report
   ```bash
   hvx reports generate simple_report --data my_building
   ```

## Data Format

### Directory Structure (for `hvx data load`)

```
data/
└── buildings/
    ├── building-1/
    │   ├── climate/
    │   │   └── climate-data.csv
    │   └── sensors/
    │       ├── room1.csv
    │       ├── room2.csv
    │       └── room3.csv
    └── building-2/
        └── sensors/
            └── room1.csv
```

### CSV Format

All CSV files should contain:
- `timestamp` column (datetime format)
- Sensor data columns: `temperature`, `co2`, `humidity`, `occupancy`, etc.

Example:
```csv
timestamp,temperature,co2,humidity,occupancy
2024-01-01 00:00:00,20.5,450,55,0
2024-01-01 01:00:00,20.3,430,54,0
```

## Output Structure

```
output/
├── dataset.pkl              # Loaded dataset (binary)
├── dataset.json            # Dataset summary (human-readable)
├── analysis/               # Analysis results
│   ├── portfolio.json     # Portfolio-level analysis
│   ├── buildings/         # Building-level analyses
│   │   ├── building-1.json
│   │   └── building-2.json
│   ├── levels/            # Level-level analyses
│   │   ├── level-1-0.json
│   │   └── level-1-1.json
│   └── rooms/             # Room-level analyses
│       ├── room-1-0-01.json
│       └── room-1-0-02.json
├── charts/                # Generated charts (PNG)
└── reports/               # Generated PDF reports
```

## Configuration Files

### Analysis Configuration (`config/tests.yaml`)

Defines test criteria for IEQ parameters:

```yaml
parameters:
  temperature:
    tests:
      - name: thermal_comfort
        min: 20
        max: 26
        severity: HIGH
  co2:
    tests:
      - name: air_quality
        max: 1000
        severity: CRITICAL
```

### Report Configuration (`config/report_config.yaml`)

Defines report templates and styling.

## Common Options

Most commands support these common options:

- `--help`, `-h` - Show help message
- `--verbose`, `-v` - Show detailed output
- `--output`, `-o` - Specify output path

## Getting Help

For detailed help on any command:

```bash
hvx --help                    # Show all commands
hvx <command> --help          # Show command help
hvx <command> <subcommand> --help  # Show subcommand help
```

## Examples

### Complete Analysis Workflow

```bash
# Load data from multiple buildings
hvx data load data/portfolio -o output/dataset.pkl -f pickle

# Inspect the dataset
hvx data inspect output/dataset.pkl

# Run analysis
hvx analyze run output/dataset.pkl --portfolio-name "Q1 2024 Portfolio"

# View portfolio summary
hvx analyze summary output/analysis --level portfolio

# View specific building
hvx analyze summary output/analysis --level building --entity-id building-1

# View specific room
hvx analyze summary output/analysis --level room --entity-id building-1_0_room-101
```

### Working with Charts

```bash
# List all available charts
hvx graphs list

# Show chart details
hvx graphs info co2_compliance_bar

# Generate preview with dummy data
hvx graphs preview co2_compliance_bar -o output/preview.png
```

### Creating Custom Templates

```bash
# Create template interactively
hvx templates create

# List all templates
hvx templates list

# View template configuration
hvx templates show my_template

# Delete template
hvx templates delete my_template
```

## Troubleshooting

### Data Loading Issues

If `hvx data load` fails:
- Verify directory structure matches expected format
- Check CSV files have required `timestamp` column
- Use `--verbose` flag for detailed error messages
- Disable validation with `--no-validate` to diagnose issues

### Analysis Issues

If `hvx analyze run` fails:
- Ensure dataset file exists and is valid
- Check configuration file exists at `config/tests.yaml`
- Use `--verbose` for detailed output

### Report Generation Issues

If `hvx reports generate` fails:
- Verify analysis data exists with `hvx analytics list`
- Check template exists with `hvx templates list`
- Ensure output directory is writable

## Additional Resources

- [Quick Start Guide](../QUICKSTART.md)
- [Data Loader Guide](../copilot/DATA_LOADER_QUICKSTART.md)
- [Publishing Guide](../copilot/PUBLISHING_QUICKSTART.md)

## Support

For issues or questions:
- Check command help with `--help`
- Review error messages with `--verbose`
- Consult documentation files in `docs/`
