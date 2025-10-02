# HVX CLI - Indoor Environmental Quality & Energy Analytics

A comprehensive command-line tool for analyzing Indoor Environmental Quality (IEQ) and energy efficiency data in buildings. HVX provides portfolio-wide hierarchical analysis, visualization, and reporting capabilities.

## Features

- 📊 **Hierarchical Analysis** - Portfolio, building, level, and room-level insights
- 📈 **Rich Visualizations** - Extensible chart library with multiple chart types
- 📄 **PDF Reports** - Professional reports with customizable templates
- 🏢 **Multi-Building Support** - Analyze entire building portfolios
- 🔍 **Data Quality Metrics** - Comprehensive data validation and quality scoring
- 🎯 **Investment Priorities** - Identify buildings needing attention
- 🔌 **Extensible** - JSON-first architecture for easy integration

## Quick Start

```bash
# Clone repository
git clone https://github.com/bruadam/hvx.git
cd hvx

# Install
pip install -e .

# Load building data
hvx data load data/samples/sample-extensive-data -o output/dataset.pkl -f pickle

# Run hierarchical analysis
hvx analyze run output/dataset.pkl --portfolio-name "My Portfolio"

# View results
hvx analyze summary output/analysis
```

## Installation

### From Source

```bash
# Clone repository
git clone https://github.com/bruadam/hvx.git
cd hvx

# Install in development mode
pip install -e .

# Verify installation
hvx --version
```

### Requirements

- Python 3.9+
- See [setup.py](setup.py) for full dependencies

## Documentation

### 📚 Complete CLI Documentation

- **[CLI Overview](docs/cli/README.md)** - Complete command reference and workflows
- **[Data Commands](docs/cli/data.md)** - Load and inspect building data
- **[Analyze Commands](docs/cli/analyze.md)** - Hierarchical portfolio analysis
- **[Analytics Commands](docs/cli/analytics.md)** - Legacy single-building analysis
- **[Graphs Commands](docs/cli/graphs.md)** - Chart library and previews
- **[Templates Commands](docs/cli/templates.md)** - Report template management
- **[Reports Commands](docs/cli/reports.md)** - PDF report generation

### 📖 Additional Resources

- **[Quick Start Guide](docs/QUICKSTART.md)** - Get started in 5 minutes
- **[Data Loader Guide](docs/copilot/DATA_LOADER_QUICKSTART.md)** - Data loading details
- **[Publishing Guide](docs/copilot/PUBLISHING_QUICKSTART.md)** - Package publishing

## Command Overview

### Data Management
```bash
hvx data load <directory>              # Load multi-building data
hvx data inspect <dataset.pkl>         # Inspect loaded data
```

### Analysis
```bash
hvx analyze run <dataset.pkl>          # Hierarchical analysis (modern)
hvx analyze summary <analysis_dir>     # View analysis results

hvx analytics run <csv_file>           # Single building analysis (legacy)
hvx analytics show <name>              # View analysis details
```

### Visualization & Reporting
```bash
hvx graphs list                        # List available charts
hvx graphs preview <chart_id>          # Preview chart with dummy data

hvx templates create                   # Create report template
hvx templates list                     # List available templates

hvx reports generate <template> --data <analysis>  # Generate PDF report
```

## Workflows

### Modern Workflow (Portfolio Analysis)

For analyzing multiple buildings across a portfolio:

```bash
# 1. Load data from directory structure
hvx data load data/my-buildings -o output/dataset.pkl -f pickle

# 2. Run hierarchical analysis
hvx analyze run output/dataset.pkl --portfolio-name "Q1 2024"

# 3. View portfolio summary
hvx analyze summary output/analysis

# 4. Drill down to specific building
hvx analyze summary output/analysis --level building --entity-id building-1

# 5. Review problematic rooms
hvx analyze summary output/analysis --level room --entity-id building_1_0_room_101
```

### Legacy Workflow (Single Building)

For quick analysis of a single building CSV file:

```bash
# 1. Run analysis
hvx analytics run data/building.csv --name my_building

# 2. Generate report
hvx reports generate simple_report --data my_building

# 3. View report
open output/reports/*.pdf
```

## Data Format

### Directory Structure (for portfolio analysis)

```
data/
└── buildings/
    ├── building-1/
    │   ├── climate/
    │   │   └── climate-data.csv
    │   └── sensors/
    │       ├── room1.csv
    │       └── room2.csv
    └── building-2/
        └── sensors/
            └── room1.csv
```

### CSV Format

All CSV files require:
- `timestamp` column in ISO 8601 format
- Sensor columns: `temperature`, `co2`, `humidity`, `occupancy`, etc.

```csv
timestamp,temperature,co2,humidity,occupancy
2024-01-01 00:00:00,20.5,450,55,0
2024-01-01 01:00:00,20.3,430,54,0
```

See [Data Commands Documentation](docs/cli/data.md) for detailed format requirements.

## Architecture

### Analysis Pipeline

```
Directory Structure → Data Loader → Dataset (Pickle)
                                      ↓
                                   Analysis Engine
                                      ↓
                              Hierarchical Results (JSON)
                                      ↓
                            ┌─────────┴─────────┐
                         Reports            Dashboards
```

### Output Structure

```
output/
├── dataset.pkl              # Loaded data
├── dataset.json            # Data summary
├── analysis/               # Analysis results
│   ├── portfolio.json
│   ├── buildings/*.json
│   ├── levels/*.json
│   └── rooms/*.json
├── charts/                 # Generated charts
└── reports/                # PDF reports
```

## Configuration

### Analysis Configuration (`config/tests.yaml`)

Define test criteria for IEQ parameters:

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

See documentation for complete configuration options.

## Development

### Running Tests

```bash
# Run test workflow
./tests/test_hvx_workflow.sh

# Run specific tests
pytest tests/
```

### Project Structure

```
analytics/
├── src/                    # Source code
│   ├── cli/               # CLI commands
│   ├── core/              # Core analytics engine
│   ├── models/            # Data models
│   ├── services/          # Service layer
│   ├── graphs/            # Chart library
│   └── reporting/         # Report templates
├── config/                # Configuration files
├── docs/                  # Documentation
├── tests/                 # Test files
└── output/               # Generated outputs
```

## Examples

### Complete Analysis Example

```bash
# Load data
hvx data load data/samples/sample-extensive-data -o output/dataset.pkl -f pickle

# Inspect data
hvx data inspect output/dataset.pkl

# Run analysis
hvx analyze run output/dataset.pkl --portfolio-name "HTK Portfolio"

# View portfolio summary
hvx analyze summary output/analysis --level portfolio

# Check specific building
hvx analyze summary output/analysis --level building --entity-id building-1

# Generate custom report (legacy workflow)
hvx templates create
hvx analytics run data/building.csv --name building1
hvx reports generate my_template --data building1
```

### Explore Charts

```bash
# List available charts
hvx graphs list

# Preview chart
hvx graphs preview co2_compliance_bar -o preview.png

# Get chart details
hvx graphs info temperature_timeseries
```

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

MIT License - See [LICENSE](LICENSE) for details

## Support

- **Documentation**: [docs/cli/](docs/cli/)
- **Issues**: [GitHub Issues](https://github.com/bruadam/hvx/issues)
- **Quick Start**: [docs/QUICKSTART.md](docs/QUICKSTART.md)

## Acknowledgments

Built for facility management and building performance analysis. Open source, transparent, and extensible.
