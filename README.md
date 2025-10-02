# HVX - HVAC Analytics

A command-line tool for analyzing Indoor Environmental Quality (IEQ) and energy efficiency data in buildings.

## Features

- **Graph Library**: 3 built-in charts (CO2 compliance, temperature, occupancy)
- **Template Management**: Create custom report templates
- **Analytics Engine**: Run IEQ analysis on sensor data
- **PDF Reports**: Generate professional reports with charts
- **JSON-First**: All analysis results saved as JSON for reusability

## Installation

```bash
# Install in development mode
python3 -m pip install -e .

# Verify installation
hvx --version
```

## Quick Start

```bash
# 1. Explore available charts
hvx graphs list
hvx graphs preview co2_compliance_bar

# 2. Run analysis on your data
hvx analytics run data/samples/building_sample.csv --name my_building

# 3. Generate a report
hvx reports generate simple_report --data my_building

# Your report is ready in output/reports/
```

## Documentation

- **[Quick Start Guide](docs/QUICKSTART.md)** - Get started in 5 minutes
- **[Complete Implementation](docs/HVX_CLI_IMPLEMENTATION_COMPLETE.md)** - Full technical documentation

## Commands

### Graph Commands
```bash
hvx graphs list                    # List all available charts
hvx graphs info <chart_id>         # Show chart details
hvx graphs preview <chart_id>      # Generate preview with dummy data
```

### Template Commands
```bash
hvx templates list                 # List all templates
hvx templates show <name>          # Show template configuration
hvx templates delete <name>        # Delete a user template
```

### Analytics Commands
```bash
hvx analytics run <csv_file>       # Run analysis on data
hvx analytics list                 # List all analyses
hvx analytics show <name>          # Show analysis summary
```

### Report Commands
```bash
hvx reports generate <template> --data <analysis>  # Generate PDF report
hvx reports list                                   # List all reports
```

## Architecture

### JSON-First Workflow
```
CSV Data → Analytics Service → JSON → Report Service → PDF
                                 ↓
                            Charts (PNG)
```

### Directory Structure
```
src/                      # Main package (formerly ieq_analytics)
├── core/                 # Core analytics engine
│   └── analytics_engine.py
├── models/               # Data models
│   ├── enums.py
│   └── analysis_result.py
├── utils/                # Utilities
├── graphs/               # Graph library
│   ├── renderers/        # Modular chart renderers
│   │   ├── bar_charts.py
│   │   ├── line_charts.py
│   │   ├── heatmaps.py
│   │   └── compliance_charts.py
│   ├── registry.yaml
│   └── fixtures/         # Dummy data
├── services/             # Service layer
│   ├── graph_service.py
│   ├── template_service.py
│   ├── analytics_service.py
│   └── report_service.py
├── cli/                  # CLI commands
│   ├── main.py
│   └── commands/
└── reporting/            # Report templates

User Data:
~/.hvx/templates/         # User templates

Output:
output/
├── analysis/             # JSON results
├── charts/               # Generated charts
└── reports/              # PDF reports
```

## Data Format

Your CSV file should contain:
- `timestamp` column (datetime)
- Sensor data columns: `temperature`, `co2`, `humidity`, `occupancy`, etc.

Example:
```csv
timestamp,temperature,co2,humidity,occupancy
2024-01-01 00:00:00,20.5,450,55,0
2024-01-01 01:00:00,20.3,430,54,0
```

## Available Charts

1. **co2_compliance_bar** - CO2 compliance by period (bar chart)
2. **temperature_timeseries** - Temperature over time (line chart)
3. **occupancy_heatmap** - Occupancy patterns by day/hour (heatmap)

## Requirements

- Python 3.9+
- pandas >= 2.0.0
- matplotlib >= 3.7.0
- click >= 8.0.0
- rich >= 13.0.0
- reportlab >= 4.0.0

See [setup.py](setup.py) for full dependencies.

## Testing

```bash
# Run the test workflow
./test_hvx_workflow.sh

# Generate sample data
python3 -c "
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

timestamps = [datetime(2024,1,1) + timedelta(hours=i) for i in range(168)]
df = pd.DataFrame({
    'timestamp': timestamps,
    'temperature': 20 + 3*np.sin(np.linspace(0,14*np.pi,168)),
    'co2': 400 + 300*np.sin(np.linspace(0,14*np.pi,168)),
    'humidity': 50 + 10*np.sin(np.linspace(0,7*np.pi,168))
})
df.to_csv('my_data.csv', index=False)
print('Sample data created: my_data.csv')
"
```

## Contributing

This is an open-source project. Contributions welcome!

## License

MIT License

## Support

For issues or questions, see:
- [Complete Documentation](docs/HVX_CLI_IMPLEMENTATION_COMPLETE.md)
- [Quick Start Guide](docs/QUICKSTART.md)
