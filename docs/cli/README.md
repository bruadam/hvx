# HVX CLI Documentation

Welcome to the HVX CLI documentation. This guide covers all available commands and their usage.

## Overview

HVX is a command-line tool for analyzing Indoor Environmental Quality (IEQ) and energy efficiency data in buildings. It provides an interactive, guided workflow that walks you through the complete analysis process from data loading to professional report generation.

## Installation

```bash
# Install in development mode
python3 -m pip install -e .

# Verify installation
hvx --version
```

## Quick Start

```bash
# Start the interactive IEQ analysis workflow
hvx ieq start

# Or start with a specific data directory
hvx ieq start --directory data/samples/sample-extensive-data

# Run in automated mode (no prompts)
hvx ieq start --directory data/my-buildings --auto
```

## Command Groups

HVX organizes commands by domain:

### [ieq](./ieq.md) - Indoor Environmental Quality Analysis
Interactive workflow for comprehensive IEQ analysis.

- `hvx ieq start` - Launch interactive IEQ analysis workflow
- `hvx ieq start --directory <path>` - Start with specific data directory
- `hvx ieq start --auto` - Run in automated mode with defaults
- `hvx ieq info` - Display IEQ terminology and concepts

### energy - Energy Efficiency Analysis
Energy analysis commands (coming soon).

- `hvx energy` - Energy efficiency analysis commands

### settings - Settings & Configuration
Manage HVX settings and configurations.

- `hvx settings` - Configuration management

## Interactive Workflow

The `hvx ieq start` command provides a guided, step-by-step workflow:

```
Data Directory → Load → Standards Selection → Analysis → Exploration → Reports → Export
```

### Workflow Steps

1. **Load Building Data**
   - Point to your data directory
   - System auto-detects building structure
   - Validates data quality

2. **Select Building Type**
   - Office, school, residential, healthcare, or mixed
   - Determines applicable standards

3. **Choose Standards & Tests**
   - EN16798-1 (European standard with Categories I-IV)
   - BR18 (Danish Building Regulations)
   - Danish Guidelines
   - Auto-selection based on building type
   - Custom selection available

4. **Process Analytics**
   - Hierarchical analysis (portfolio → building → level → room)
   - Compliance checking against selected standards
   - Data quality scoring
   - Issue identification

5. **Explore Results**
   - Interactive summary display
   - Navigate through hierarchy
   - View detailed metrics
   - Smart recommendations

6. **Generate Reports**
   - Choose from predefined templates
   - Create custom templates
   - HTML and PDF output formats
   - Professional formatting

7. **Export Data**
   - JSON (full structure)
   - Excel/CSV (tabular data)
   - Markdown (documentation)
   - Text files

### Automated Mode

For scripting or CI/CD pipelines:

```bash
hvx ieq start --directory data/buildings --auto
```

This runs the complete workflow with default settings and no user interaction.

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

The interactive workflow generates a structured output directory:

```
output/
├── analysis/               # Analysis results (JSON)
│   ├── portfolio.json     # Portfolio-level analysis
│   ├── buildings/         # Building-level analyses
│   │   ├── building-1.json
│   │   └── building-2.json
│   ├── levels/            # Level-level analyses
│   │   └── *.json
│   └── rooms/             # Room-level analyses
│       └── *.json
├── reports/               # Generated reports
│   ├── *.html            # HTML reports
│   └── *.pdf             # PDF reports (if backend available)
├── charts/               # Generated charts (if any)
└── recommendations/      # Smart recommendations (JSON)
```

## Configuration

### Built-in Standards

HVX includes pre-configured standards:

- **EN16798-1** - European standard with Categories I-IV
  - Category I: High level (15-25°C, <800 ppm CO2)
  - Category II: Normal level (16-26°C, <1000 ppm CO2)
  - Category III: Moderate level (18-27°C, <1350 ppm CO2)
  - Category IV: Low level (outside other categories)

- **BR18** - Danish Building Regulations 2018
- **Danish Guidelines** - Danish indoor climate guidelines

### Report Templates

Report templates are stored in `config/report_templates/`:

- `building_detailed.yaml` - Comprehensive building analysis
- `portfolio_summary.yaml` - High-level portfolio overview

Templates can be customized during the interactive workflow.

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

### Basic Interactive Analysis

```bash
# Start with interactive prompts
hvx ieq start

# Follow the prompts:
# 1. Enter data directory: data/samples/sample-extensive-data
# 2. Select building type: Office
# 3. Choose standards: Recommended for this building type
# 4. Wait for analysis to complete
# 5. Explore results or continue to reports
# 6. Generate report using template
# 7. Export data if needed
```

### Quick Automated Analysis

```bash
# Run complete workflow with defaults
hvx ieq start --directory data/my-buildings --auto

# Results saved to:
# - output/analysis/ (JSON analysis results)
# - output/reports/ (HTML/PDF reports if generated)
```

### Starting from Specific Directory

```bash
# Start workflow with data directory pre-selected
hvx ieq start --directory data/samples/sample-extensive-data

# The workflow will:
# - Load data from the specified directory
# - Continue with building type selection
# - Then proceed with standards and analysis
```

### Getting IEQ Information

```bash
# Display IEQ terminology and concepts
hvx ieq info

# Shows explanations of:
# - Temperature metrics
# - CO2 levels
# - Humidity
# - Standards (EN16798-1, BR18, etc.)
# - Compliance categories
```

## Troubleshooting

### Common Issues

**Issue: Directory structure not recognized**
```
⚠ Directory structure not recognized
```
**Solution:** Ensure your data follows the expected structure:
```
data/
└── buildings/
    ├── building-1/
    │   └── sensors/
    │       └── room1.csv
```

**Issue: Missing timestamp column**
```
✗ Error loading data: Missing required column 'timestamp'
```
**Solution:** Ensure all CSV files have a `timestamp` column with datetime values.

**Issue: No PDF backend available**
```
⚠ No PDF backend available
```
**Solution:** Install a PDF generation library:
```bash
pip install weasyprint  # Recommended
# or
pip install pdfkit
```

**Issue: Analysis fails**
```
✗ Error during analytics: [error message]
```
**Solution:** The workflow offers help options. Choose "Get help" or "Try again" from the error menu.

### Getting Help

Within the interactive workflow:
- Type `help` at any prompt for context-specific assistance
- Type `quit` or `exit` to leave the workflow
- Press `Ctrl+C` to cancel operations

Command-line help:
```bash
hvx --help              # Show all commands
hvx ieq --help          # Show IEQ commands
hvx ieq start --help    # Show start command options
```

## Additional Resources

- [Interactive Workflow Guide](./interactive-workflow.md) - Detailed workflow documentation
- [Chart Library Reference](../CHART_QUICK_REFERENCE.md) - Available visualization types
- [Analytics Executors](../ANALYTICS_EXECUTORS_QUICK_REFERENCE.md) - Analysis engine details
- [Quick Start Guide](../QUICKSTART.md) - Get started in 5 minutes
- [Data Loader Guide](../copilot/DATA_LOADER_QUICKSTART.md) - Data format details

## Support

For issues or questions:
- Use `hvx ieq info` for IEQ terminology
- Check command help with `--help`
- Consult documentation in `docs/`
- Report issues at: https://github.com/bruadam/hvx/issues
