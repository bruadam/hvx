# HVX

Professional Indoor Environmental Quality (IEQ) Analytics Platform

## Overview

A clean, scalable, type-safe analytics platform for analyzing building environmental quality data (temperature, CO2, humidity, etc.) against international standards like EN16798-1 and BR18.

## Features

- **🎨 YAML-Driven Reports**: Define reports in YAML with automatic analytics execution
- **📊 Rich Visualizations**: Heatmaps, timeseries with RED violation highlighting, bar charts
- **🔧 Modular Analytics Engine**: Pluggable evaluators for different compliance standards
- **✅ Type-Safe**: Full Pydantic models with comprehensive validation
- **🏢 Hierarchical Analysis**: Room → Level → Building → Portfolio
- **💡 Smart Recommendations**: AI-powered insights based on data patterns
- **📄 Multiple Output Formats**: HTML and PDF reports
- **🔌 Extensible**: Easy to add new standards, charts, and analytics

### Chart Types

- **Heatmaps**: Hours on Y-axis, days/months on X-axis showing temporal patterns
- **Timeseries**: Non-compliant periods highlighted in RED for immediate visibility
- **Bar Charts**: Compare rooms/buildings by compliance %, quality, or violations
- **KPI Dashboards**: Building and portfolio-level gauges and metrics
- **Compliance Matrix**: All rooms × all tests matrix view

### Pre-built Report Templates

- **Comprehensive Building Report**: Full analysis with all rooms and charts
- **Problematic Rooms Report**: Focus on failing rooms only
- **Building KPI Report**: Executive summary with KPIs only
- **Portfolio Overview Report**: Multi-building analysis
- **Seasonal Analysis Report**: Winter/summer focused analysis
- **Top/Bottom Performers Report**: Best and worst rooms comparison

## Architecture

```
clean/
├── core/           # Main package
│   ├── domain/             # Domain models (entities, value objects)
│   ├── application/        # Application services & use cases
│   ├── infrastructure/     # External integrations (data loading, file I/O)
│   ├── analytics/          # Analytics engine & evaluators
│   ├── reporting/          # Report generation & rendering
│   └── cli/               # Command-line interface
├── config/                # Configuration files
│   ├── standards/         # Standard definitions (EN16798-1, BR18, etc.)
│   ├── report_templates/  # Report YAML templates
│   └── filters/           # Time filters & periods
├── data/                  # Data directory (gitignored)
├── output/               # Output directory (gitignored)
└── tests/                # Test suite

```

## Quick Start

### 1. Installation
```bash
# Install package
pip install -e .
```

### 2. Test Report Generation
```bash
# Run comprehensive report generation test
python test_report_generation.py
```

This will:
- Create sample IEQ data for 8 rooms
- Generate reports from all available templates
- Save HTML reports to `output/reports/generated_reports/`

### 3. Generate Custom Reports
```python
from pathlib import Path
from ieq_analytics.reporting import ReportGenerator
from ieq_analytics.infrastructure.data_loaders.csv_loader import CSVDataLoader

# Load your data
loader = CSVDataLoader()
room = loader.load_room(Path("data/room.csv"), "room_01", "Conference Room")

# Generate report
generator = ReportGenerator()
generator.generate_from_template(
    template_path=Path("config/report_templates/comprehensive_building_report.yaml"),
    rooms=[room],
    building_name="Building A",
    output_path=Path("output/report.html")
)
```

See [REPORT_GENERATION.md](docs/REPORT_GENERATION.md) for detailed documentation.

## Project Structure

### Domain Layer (`domain/`)
Pure business logic with no external dependencies:
- **models/**: Core domain entities (Room, Building, Analysis Results)
- **enums/**: Type-safe enumerations
- **value_objects/**: Immutable value types

### Application Layer (`application/`)
Orchestrates business logic:
- **use_cases/**: High-level operations
- **services/**: Application services
- **interfaces/**: Abstract interfaces (ports)

### Infrastructure Layer (`infrastructure/`)
External system interactions:
- **data_loaders/**: CSV/Excel/JSON data loading
- **file_storage/**: File system operations
- **external_apis/**: Weather data, etc.

### Analytics Layer (`analytics/`)
IEQ-specific analytics:
- **engine/**: Core analysis engine
- **evaluators/**: Standard-specific evaluators
- **metrics/**: Calculation functions
- **filters/**: Time-based filters

### Reporting Layer (`reporting/`)
Report generation:
- **template_engine/**: YAML template processor
- **renderers/**: HTML/PDF renderers
- **charts/**: Chart generation
- **validators/**: Template validators

## Development Principles

1. **One class per file** - Easy to navigate and maintain
2. **Type safety** - Pydantic models throughout
3. **SOLID principles** - Single responsibility, dependency inversion
4. **Clean architecture** - Domain-driven design
5. **Testability** - Pure functions, dependency injection
6. **Documentation** - Comprehensive docstrings

## License

Proprietary - HVX Analytics
