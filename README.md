# HVX CLI - Indoor Environmental Quality & Energy Analytics

A comprehensive command-line tool for analyzing Indoor Environmental Quality (IEQ) and energy efficiency data in buildings. HVX provides an interactive workflow that guides you through data loading, standards selection, hierarchical analysis, and professional report generation.

## Features

- 🎯 **Interactive Workflow** - Guided step-by-step analysis process
- 📊 **Hierarchical Analysis** - Portfolio, building, level, and room-level insights
- 📋 **Standards Compliance** - EN16798-1, BR18, Danish Guidelines, and more
- 📈 **Rich Visualizations** - Extensible chart library with multiple chart types
- 📄 **Professional Reports** - HTML and PDF reports with customizable templates
- 🏢 **Multi-Building Support** - Analyze entire building portfolios
- 🔍 **Data Quality Metrics** - Comprehensive data validation and quality scoring
- 🎯 **Smart Recommendations** - AI-powered improvement suggestions
- 🔌 **Extensible** - JSON-first architecture for easy integration

## Quick Start

```bash
# Clone repository
git clone https://github.com/bruadam/hvx.git
cd hvx

# Install
pip install -e .

# Start interactive IEQ analysis
hvx ieq start

# Or start with a specific data directory
hvx ieq start --directory data/samples/sample-extensive-data
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
- **[IEQ Commands](docs/cli/ieq.md)** - Indoor Environmental Quality analysis
- **[Interactive Workflow](docs/cli/interactive-workflow.md)** - Step-by-step analysis guide

### 📖 Additional Resources

- **[Quick Start Guide](docs/QUICKSTART.md)** - Get started in 5 minutes

## Command Overview

### Indoor Environmental Quality (IEQ)
```bash
hvx ieq start                          # Start interactive IEQ analysis workflow
hvx ieq start --directory <path>       # Start with specific data directory
hvx ieq start --auto                   # Run with default settings (non-interactive)
hvx ieq info                           # Show IEQ terminology and concepts
```

### Energy Efficiency
```bash
hvx energy                             # Energy analysis commands (coming soon)
```

### Settings & Configuration
```bash
hvx settings                           # Manage HVX settings and configurations
```

## Interactive Workflow

HVX provides a guided, step-by-step workflow for IEQ analysis:

```bash
# Start the interactive workflow
hvx ieq start
```

**The workflow guides you through:**

1. **Load Building Data** - Point to your data directory containing building sensor data
2. **Select Building Type** - Office, school, residential, healthcare, or mixed
3. **Choose Standards** - Select compliance standards (EN16798-1, BR18, Danish Guidelines)
4. **Process Analytics** - Automated hierarchical analysis at portfolio, building, level, and room levels
5. **Explore Results** - Interactive exploration of analysis results and metrics
6. **Generate Reports** - Create professional HTML/PDF reports using templates
7. **Export Data** - Save analytics data in various formats (JSON, Excel, CSV, Markdown)

**For automation or scripting:**

```bash
# Run with defaults (no prompts)
hvx ieq start --directory data/my-buildings --auto

# Start from a specific directory
hvx ieq start --directory data/samples/sample-extensive-data
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

### Standards and Tests

HVX includes built-in support for multiple IEQ standards:

- **EN16798-1** - European standard for indoor environmental parameters (Categories I-IV)
- **BR18** - Danish Building Regulations 2018
- **Danish Guidelines** - Danish indoor climate guidelines

Standards are configured during the interactive workflow or can be customized in:
- `src/core/analytics/ieq/config/standards/` - Standard definitions (EN16798-1, BR18, Danish Guidelines)
- `config/report_templates/` - Report templates (building_detailed.yaml, portfolio_summary.yaml)

See the [interactive workflow documentation](docs/cli/interactive-workflow.md) for configuration details.

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
# Start interactive workflow
hvx ieq start --directory data/samples/sample-extensive-data

# The interactive workflow will guide you through:
# 1. Confirming data directory and loading buildings
# 2. Selecting building type (office, school, etc.)
# 3. Choosing applicable standards (EN16798-1, BR18, etc.)
# 4. Running hierarchical analysis
# 5. Exploring results
# 6. Generating reports
# 7. Exporting data
```

### Automated Analysis

```bash
# Run with defaults (non-interactive)
hvx ieq start --directory data/samples/sample-extensive-data --auto

# Results will be saved to:
# - output/analysis/ - Analysis results (JSON)
# - output/reports/ - Generated reports (HTML/PDF)
```

### Get IEQ Information

```bash
# Show IEQ terminology and concepts
hvx ieq info
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
